FROM ubuntu:latest

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates r-base libxml2 libxml2-dev libfontconfig1-dev libtiff-dev libcurl4-openssl-dev libsodium-dev python3.12 python3.12-venv python3-pip

WORKDIR /server

# Install UV
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin/:$PATH"

# Install python dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

# Install R dependencies
COPY requirements.r ./
RUN Rscript requirements.r

COPY . .

# Install the app
RUN uv pip install .

# Start the server
# RUN uv run hydroshift/app.py --server.port 8501 --server.headless true
