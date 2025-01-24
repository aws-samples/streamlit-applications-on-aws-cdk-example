import os
from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
    aws_logs as logs,
    aws_ecr_assets as ecr_assets,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_elasticloadbalancingv2_actions as elbv2_actions,
    aws_elasticloadbalancingv2 as elb,
    aws_ec2 as ec2,
)

from constructs import Construct

from stacks.auth_resources import AuthResources
from stacks.dns_resources import DNSResources


class ECSResources:
    def __init__(self, scope: Construct, dns: DNSResources, auth: AuthResources):
        streamlit_image = ecr_assets.DockerImageAsset(
            scope,
            "StreamlitImage",
            directory=os.path.join(os.getcwd(), "..", "streamlit"),
            platform=ecr_assets.Platform.LINUX_ARM64,
        )

        task_definition = ecs.FargateTaskDefinition(
            scope,
            "StreamlitTaskDef",
            cpu=1024,
            memory_limit_mib=4096,
            runtime_platform=ecs.RuntimePlatform(
                cpu_architecture=ecs.CpuArchitecture.ARM64,
                operating_system_family=ecs.OperatingSystemFamily.LINUX,
            ),
        )

        log_group = logs.LogGroup(
            scope,
            "StreamlitLogGroup",
            log_group_name=f"/ecs/streamlit/{Stack.of(scope).stack_name}",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY,
        )

        container = task_definition.add_container(
            "StreamlitContainer",
            image=ecs.ContainerImage.from_docker_image_asset(streamlit_image),
            port_mappings=[ecs.PortMapping(container_port=8501)],
            logging=ecs.LogDriver.aws_logs(
                log_group=log_group, stream_prefix="streamlit"
            ),
            health_check=ecs.HealthCheck(
                command=[
                    "CMD-SHELL",
                    "curl -f http://127.0.0.1:8501/healthz  || exit 1",
                ],
                interval=Duration.seconds(5),
                retries=2,
                start_period=Duration.seconds(30),
                timeout=Duration.seconds(3),
            ),
        )

        vpc = ec2.Vpc(scope, "StreamlitVPC", max_azs=2)
        cluster = ecs.Cluster(scope, "StreamlitCluster", vpc=vpc)

        self.service = ecs_patterns.ApplicationLoadBalancedFargateService(
            scope,
            "StreamlitService",
            cluster=cluster,
            task_definition=task_definition,
            health_check_grace_period=Duration.seconds(30),
            desired_count=1,
            public_load_balancer=True,
            certificate=dns.certificate,
            domain_name=dns.app_domain,
            domain_zone=dns.hosted_zone,
        )

        container.add_environment(
            "ALB_ARN", self.service.load_balancer.load_balancer_arn
        )
        container.add_environment("COGNITO_POOL_ID", auth.user_pool.user_pool_id)
        container.add_environment("AWS_REGION", Stack.of(scope).region)
        container.add_environment("LOGOUT_URL", auth.logout_url)
        container.add_environment("STREAMLIT_DOMAIN", dns.app_domain)

        lb_security_group = self.service.load_balancer.connections.security_groups[0]
        lb_security_group.add_egress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port(
                protocol=ec2.Protocol.TCP,
                string_representation="443",
                from_port=443,
                to_port=443,
            ),
            description="Outbound HTTPS traffic to get to Cognito",
        )

        self.service.target_group.configure_health_check(
            interval=Duration.seconds(5),
            healthy_threshold_count=2,
            timeout=Duration.seconds(3),
            path="/healthz",
            healthy_http_codes="200",
            unhealthy_threshold_count=2,
        )

        self.service.listener.add_action(
            "StreamlitAuthenticationRule",
            priority=1000,
            action=elbv2_actions.AuthenticateCognitoAction(
                next=elb.ListenerAction.forward(
                    target_groups=[self.service.target_group]
                ),
                user_pool=auth.user_pool,
                user_pool_client=auth.user_pool_client,
                user_pool_domain=auth.user_pool_custom_domain,
            ),
            conditions=[elb.ListenerCondition.host_headers([dns.app_domain])],
        )
