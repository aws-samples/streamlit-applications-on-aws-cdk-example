#!/usr/bin/env python3
import os
import aws_cdk as cdk

from stacks.streamlit_stack import StreamlitStack

streamlit_app = cdk.App()
StreamlitStack(streamlit_app, "StreamlitStack")
streamlit_app.synth()
