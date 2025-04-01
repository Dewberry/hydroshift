FROM ubuntu:latest

RUN apt-get update && apt-get install -y --no-install-recommends git curl ca-certificates r-base build-essential libxml2 libxml2-dev libfontconfig1-dev libtiff-dev libcurl4-openssl-dev libsodium-dev python3.12 python3.12-venv python3-pip

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

# Install python dependencies
COPY pyproject.toml uv.lock ./
RUN uv venv .venv
RUN uv sync --frozen --no-install-project

# Copy project files
COPY . .

# Install the app
RUN uv pip install -e .

# Start the server
# RUN uv run streamlit run hydroshift/app.py --server.port 8501 --server.headless true
