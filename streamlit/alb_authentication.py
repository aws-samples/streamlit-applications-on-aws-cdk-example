import os
from urllib.error import HTTPError
import jwt
import base64
import json
import logging
import streamlit as st
import requests

OIDC_DATA_HEADER = "x-amzn-oidc-data"

ALB_ARN = os.environ.get("ALB_ARN", None)
if ALB_ARN is None:
    raise ValueError("ALB_ARN environment variable is not set")

COGNITO_POOL_ID = os.environ.get("COGNITO_POOL_ID", None)
if COGNITO_POOL_ID is None:
    raise ValueError("COGNITO_POOL_ID environment variable is not set")

AWS_REGION = os.environ.get("AWS_REGION", None)
if AWS_REGION is None:
    raise ValueError("AWS_REGION environment variable is not set")

STREAMLIT_DOMAIN = os.environ.get("STREAMLIT_DOMAIN", None)
if STREAMLIT_DOMAIN is None:
    raise ValueError("STREAMLIT_DOMAIN environment variable is not set")


def alb_authenticate():
    # See: https://docs.aws.amazon.com/elasticloadbalancing/latest/application/listener-authenticate-users.html#user-claims-encoding
    logging.info(f"Authenticating session [ALB: {ALB_ARN} - Signer: {COGNITO_POOL_ID}]")
    alb_authentication = st.context.headers.get(OIDC_DATA_HEADER)
    if alb_authentication is None:
        logging.warning("No authentication header found from ALB")
        return None
    jwt_headers = alb_authentication.split(".")[0]
    decoded_jwt_headers = base64.b64decode(jwt_headers)
    decoded_jwt_headers = decoded_jwt_headers.decode("utf-8")
    decoded_json = json.loads(decoded_jwt_headers)
    received_alb_arn = decoded_json["signer"]
    if received_alb_arn != ALB_ARN:
        logging.warning(f"ALB ARN mismatch: {received_alb_arn} != {ALB_ARN}")
        return None
    kid = decoded_json["kid"]
    key_url = f"https://public-keys.auth.elb.{AWS_REGION}.amazonaws.com/{kid}"
    try:
        response = requests.get(key_url, timeout=30)
        response.raise_for_status()
    except HTTPError as http_error:
        logging.error(f"Error fetching public key: {http_error}")
        return None
    pub_key = response.text
    payload = jwt.decode(alb_authentication, pub_key, algorithms=["ES256"])
    return payload
