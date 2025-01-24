import urllib.parse
from constructs import Construct
from aws_cdk import aws_cognito as cognito
from stacks.dns_resources import DNSResources


class AuthResources:
    def __init__(self, scope: Construct, dns: DNSResources, cognito_domain: str):
        self.dns = dns
        self.user_pool = cognito.UserPool(
            scope,
            "StreamlitUserPool",
            account_recovery=cognito.AccountRecovery.EMAIL_AND_PHONE_WITHOUT_MFA,
            auto_verify=cognito.AutoVerifiedAttrs(email=True, phone=True),
            self_sign_up_enabled=False,
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(mutable=True, required=True),
                given_name=cognito.StandardAttribute(mutable=True, required=True),
                family_name=cognito.StandardAttribute(mutable=True, required=True),
            ),
        )

        self.user_pool_custom_domain = self.user_pool.add_domain(
            "StreamlitUserPoolDomain",
            cognito_domain=cognito.CognitoDomainOptions(domain_prefix=cognito_domain),
        )

        self.user_pool_client = self.user_pool.add_client(
            "StreamlitUserPoolClient",
            user_pool_client_name="StreamlitAuthentication",
            generate_secret=True,
            o_auth=cognito.OAuthSettings(
                callback_urls=[
                    self.application_url,
                    self.authentication_url,
                ],
                flows=cognito.OAuthFlows(authorization_code_grant=True),
                scopes=[cognito.OAuthScope.OPENID],
            ),
            supported_identity_providers=[
                cognito.UserPoolClientIdentityProvider.COGNITO
            ],
        )

        user_pool_client_cf: cognito.CfnUserPoolClient = (
            self.user_pool_client.node.default_child
        )

        user_pool_client_cf.logout_ur_ls = [self.application_url]

    @property
    def application_url(self):
        return f"https://{self.dns.app_domain}"

    @property
    def authentication_url(self):
        return f"{self.application_url}/oauth2/idpresponse"

    @property
    def logout_url(self):
        cognito_base = self.user_pool_custom_domain.base_url()
        redirect_uri = urllib.parse.quote(self.application_url, safe="")
        return (
            f"{cognito_base}/logout?"
            + f"client_id={self.user_pool_client.user_pool_client_id}&"
            + f"logout_uri={redirect_uri}"
        )
