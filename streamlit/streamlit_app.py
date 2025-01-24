import os
import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
import logging
import json
from alb_logout import register_logout_handler, LOGOUT_PAGE

logging.basicConfig(level=logging.INFO)
register_logout_handler()

LOCAL = os.environ.get("LOCAL", False)
if LOCAL:
    logging.info("Running in local mode")

if not LOCAL:
    from alb_authentication import alb_authenticate
    authenticated_user = alb_authenticate()
    if authenticated_user is None:
        st.error("Unauthorized access")
        st.stop()
else:
    authenticated_user = None

f"""
# Welcome to Streamlit!

## Authentication Info

```json
{json.dumps(authenticated_user, indent=2)}
```
[Logout]({LOGOUT_PAGE})
"""

"""
Edit `/streamlit_app.py` to customize this app to your heart's desire :heart:.
If you have any questions, checkout our [documentation](https://docs.streamlit.io) and [community
forums](https://discuss.streamlit.io).

In the meantime, below is an example of what you can do with just a few lines of code:
"""

num_points = st.slider("Number of points in spiral", 1, 10000, 1100)
num_turns = st.slider("Number of turns in spiral", 1, 300, 31)

indices = np.linspace(0, 1, num_points)
theta = 2 * np.pi * num_turns * indices
radius = indices

x = radius * np.cos(theta)
y = radius * np.sin(theta)

df = pd.DataFrame(
    {
        "x": x,
        "y": y,
        "idx": indices,
        "rand": np.random.randn(num_points),
    }
)

st.altair_chart(
    alt.Chart(df, height=700, width=700)
    .mark_point(filled=True)
    .encode(
        x=alt.X("x", axis=None),
        y=alt.Y("y", axis=None),
        color=alt.Color("idx", legend=None, scale=alt.Scale()),
        size=alt.Size("rand", legend=None, scale=alt.Scale(range=[1, 150])),
    )
)
