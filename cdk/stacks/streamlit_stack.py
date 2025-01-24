from aws_cdk import (
    Stack,
)
from constructs import Construct
from stacks.auth_resources import AuthResources
from stacks.ecs_resources import ECSResources
from stacks.dns_resources import DNSResources


class StreamlitStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        route53_zone_id = self.node.try_get_context("zone_id")
        if not route53_zone_id:
            raise ValueError(
                "Route53 zone id is required - pass with '-c zone_id=\"Zone ID\"' "
            )
        route53_zone_name = self.node.try_get_context("zone_name")
        if not route53_zone_name:
            raise ValueError(
                "Route53 zone name is required - pass with '-c zone_name=\"example.com\"' "
            )
        route53_hostname = self.node.try_get_context("hostname")
        if not route53_hostname:
            raise ValueError(
                "Route53 hostname is required - pass with '-c hostname=\"streamlit\"' "
            )
        cognito_domain_prefix = self.node.try_get_context("cognito_domain")
        if not cognito_domain_prefix:
            cognito_domain_prefix = f"streamlit-auth-{Stack.of(self).account}"

        dns_resources = DNSResources(
            self,
            zone_id=route53_zone_id,
            zone_name=route53_zone_name,
            hostname=route53_hostname,
        )
        auth_resources = AuthResources(
            self, dns=dns_resources, cognito_domain=cognito_domain_prefix
        )
        ecs_resources = ECSResources(self, auth=auth_resources, dns=dns_resources)
