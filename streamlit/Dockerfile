FROM python:3.9-slim@sha256:2851c06da1fdc3c451784beef8aa31d1a313d8e3fc122e4a1891085a104b7cfb
COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip3 install --no-cache-dir -r requirements.txt
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl  \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
RUN useradd -m streamlit && \
    chown -R streamlit:streamlit /app
EXPOSE 8501
COPY . /app
USER streamlit
HEALTHCHECK CMD ["curl", "--fail", "http://localhost:8501/_stcore/health"]
ENTRYPOINT ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
