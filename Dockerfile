FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    r-base \
    build-essential \
    libxml2-dev \
    libfontconfig1-dev \
    libtiff-dev \
    libcurl4-openssl-dev \
    libsodium-dev \
    python3 \
    python3-venv \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /server

# Install UV
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin/:$PATH"

# Install R dependencies
RUN R -e "install.packages('renv', repos = c(CRAN = 'https://cloud.r-project.org'))"

COPY renv.lock renv.lock
RUN mkdir -p renv
COPY .Rprofile .Rprofile
COPY renv/activate.R renv/activate.R
COPY renv/settings.json renv/settings.json
RUN R -e "renv::restore()"

# Python deps
COPY pyproject.toml uv.lock ./
RUN uv venv .venv
RUN uv sync --frozen --no-install-project

# Copy project
COPY . .

# Install app
RUN uv pip install -e .

EXPOSE 80

CMD ["bash", "-c", "uv run hydroshift/add_analytics.py && uv run streamlit run hydroshift/streamlit_app.py --server.port=80 --server.address=0.0.0.0 --server.headless=true"]
