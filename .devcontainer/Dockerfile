# Market Analysis Development Container
ARG PYTHON_VERSION="3.11"
FROM python:${PYTHON_VERSION}-slim

# Avoid warnings by switching to noninteractive
ENV DEBIAN_FRONTEND=noninteractive

# Set up environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="${PATH}:/home/vscode/.local/bin"
ENV PYTHONPATH=/workspaces/market-analysis

# Configure apt and install packages
RUN apt-get update \
    && apt-get -y install --no-install-recommends \
        # Essential development tools
        build-essential \
        curl \
        wget \
        git \
        make \
        jq \
        tree \
        htop \
        vim \
        nano \
        # Network tools
        net-tools \
        iputils-ping \
        telnet \
        # Additional utilities
        ssh \
        sudo \
        ca-certificates \
        gnupg \
        lsb-release \
        # Python development dependencies
        python3-dev \
        python3-pip \
        python3-venv \
        # Database tools
        postgresql-client \
        # Financial data processing dependencies
        libxml2-dev \
        libxslt1-dev \
        libffi-dev \
        libssl-dev \
        # Data science dependencies
        libblas-dev \
        liblapack-dev \
        gfortran \
        # Vault CLI dependencies
        unzip \
    && apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

# Install Docker CLI
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get update \
    && apt-get install -y docker-ce-cli docker-compose-plugin \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

# Install Vault CLI
RUN curl -fsSL https://releases.hashicorp.com/vault/1.15.4/vault_1.15.4_linux_amd64.zip -o vault.zip \
    && unzip vault.zip \
    && mv vault /usr/local/bin/ \
    && rm vault.zip

# Create vscode user
RUN groupadd --gid 1000 vscode \
    && useradd --uid 1000 --gid vscode --shell /bin/bash --create-home vscode

# Create directories
RUN mkdir -p /workspaces/market-analysis \
    && mkdir -p /data \
    && mkdir -p /logs \
    && mkdir -p /home/vscode/.local/bin

# Set up user permissions
RUN usermod -aG docker vscode \
    && echo "vscode ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/vscode \
    && chmod 0440 /etc/sudoers.d/vscode

# Switch to vscode user
USER vscode

# Upgrade pip and install Python development tools
RUN python -m pip install --upgrade pip setuptools wheel \
    && python -m pip install --user \
        # Core development tools
        black \
        ruff \
        mypy \
        pytest \
        pytest-cov \
        pytest-asyncio \
        pytest-mock \
        coverage \
        # FastAPI and web development
        fastapi[all] \
        uvicorn[standard] \
        httpx \
        requests \
        # Database tools
        sqlalchemy \
        psycopg2-binary \
        alembic \
        # Data science and financial analysis
        pandas \
        numpy \
        matplotlib \
        seaborn \
        plotly \
        scipy \
        scikit-learn \
        # Financial data libraries
        yfinance \
        alpha-vantage \
        finnhub-python \
        polygon-api-client \
        # Time series analysis
        statsmodels \
        arch \
        # Utilities
        python-dotenv \
        pydantic \
        pydantic-settings \
        # Vault integration
        hvac \
        # Additional useful tools
        ipython \
        jupyter \
        pre-commit \
        bandit \
        safety

# Create useful aliases and shell configuration
RUN echo 'alias ll="ls -alF"' >> ~/.bashrc \
    && echo 'alias la="ls -A"' >> ~/.bashrc \
    && echo 'alias l="ls -CF"' >> ~/.bashrc \
    && echo 'alias ..="cd .."' >> ~/.bashrc \
    && echo 'alias dc="docker-compose"' >> ~/.bashrc \
    && echo 'alias api-start="uvicorn main:app --reload --host 0.0.0.0 --port 8000"' >> ~/.bashrc \
    && echo 'alias api-test="pytest tests/ -v"' >> ~/.bashrc \
    && echo 'export PATH=$HOME/.local/bin:$PATH' >> ~/.bashrc \
    && echo 'export PYTHONPATH=/workspaces/market-analysis:$PYTHONPATH' >> ~/.bashrc \
    && echo 'export VAULT_ADDR=http://host.docker.internal:8200' >> ~/.bashrc

# Set up git configuration
RUN git config --global init.defaultBranch main \
    && git config --global pull.rebase false \
    && git config --global core.autocrlf input \
    && git config --global core.eol lf

# Create workspace directory and set permissions
RUN sudo mkdir -p /workspaces/market-analysis \
    && sudo chown -R vscode:vscode /workspaces/market-analysis

# Switch back to dialog for any ad-hoc use of apt-get
ENV DEBIAN_FRONTEND=dialog

# Set the working directory
WORKDIR /workspaces/market-analysis

# Default command
CMD ["sleep", "infinity"]