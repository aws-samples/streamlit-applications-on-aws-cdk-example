from aws_cdk import aws_route53 as route53, aws_certificatemanager as acm

from constructs import Construct


class DNSResources:
    def __init__(self, scope: Construct, zone_id: str, zone_name: str, hostname: str):
        self.zone_id = zone_id
        self.zone_name = zone_name
        self.hostname = hostname

        self.hosted_zone = route53.HostedZone.from_hosted_zone_attributes(
            scope, "HostedZone", hosted_zone_id=zone_id, zone_name=zone_name
        )

        self.certificate = acm.Certificate(
            scope,
            "Certificate",
            domain_name=self.app_domain,
            validation=acm.CertificateValidation.from_dns(self.hosted_zone),
        )

    @property
    def app_domain(self) -> str:
        return f"{self.hostname}.{self.zone_name}"
