FROM debian:13-slim
RUN apt-get update && apt-get install -y --no-install-recommends mosquitto mosquitto-clients python3 python3-venv sqlite3 git openssl ca-certificates nginx sudo ufw openssh-server systemd && rm -rf /var/lib/apt/lists/*
COPY server/requirements.txt /tmp/server-requirements.txt
RUN python3 -m venv /opt/iot/venv && /opt/iot/venv/bin/pip install -r /tmp/server-requirements.txt && /opt/iot/venv/bin/pip install 'requests>=2.32,<3' nbformat nbclient ipykernel
WORKDIR /proef
