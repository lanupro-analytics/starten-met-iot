FROM python:3.12-slim

# Git voor versiebeheer; OpenSSH voor het latere serverbeheer.
RUN apt-get update && \
    apt-get install -y --no-install-recommends git openssh-client ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt && \
    python -m ipykernel install --user --name python3 --display-name "Python 3 (ipykernel)"

EXPOSE 8888
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]
