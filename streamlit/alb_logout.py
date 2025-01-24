import os
import html
import streamlit as st
from streamlit.runtime.scriptrunner_utils.script_run_context import get_script_run_ctx
from streamlit import runtime
from typing import cast
from tornado.web import RequestHandler

import logging

logging.basicConfig(level=logging.INFO)

LOGOUT_URL = os.environ.get("LOGOUT_URL", None)
if LOGOUT_URL is None:
    logging.warning("LOGOUT_URL not set")
    LOGOUT_URL = "/"

LOGOUT_PAGE = r"/logout"


class LogoutHandler(RequestHandler):
    def get(self):
        self.clear_cookie("AWSELBAuthSessionCookie-0")
        self.clear_cookie("AWSELBAuthSessionCookie-1")
        self.redirect(LOGOUT_URL)


def register_logout_handler():
    ctx = get_script_run_ctx()
    if ctx is None:
        logging.warning("No script run context found")
        return None
    session_client = runtime.get_instance().get_client(ctx.session_id)
    if session_client is None:
        logging.warning("No session client found")
        return None

    if (
        f"{type(session_client).__module__}.{type(session_client).__qualname__}"
        != "streamlit.web.server.browser_websocket_handler.BrowserWebSocketHandler"
    ):
        logging.warning("Session client is not a BrowserWebSocketHandler")
        return None

    request_handler = cast("RequestHandler", session_client)
    application = request_handler.application
    try:
        application.reverse_url(LOGOUT_PAGE)
    except KeyError:
        logging.info("Registering logout handler")
        request_handler.application.add_handlers(r".*", [(LOGOUT_PAGE, LogoutHandler)])
