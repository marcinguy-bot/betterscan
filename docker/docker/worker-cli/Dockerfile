FROM python:3.12-slim

# Arguments for non-interactive installation and setting timezone
ARG DEBIAN_FRONTEND=noninteractive
ENV CONTAINER_TIMEZONE=UTC
ENV TZ=${CONTAINER_TIMEZONE}
ENV SHELL=/bin/bash
ENV PIPENV_IGNORE_VIRTUALENVS=1
ENV GOBIN="/usr/local/bin"


# Install basic dependencies and set up environment in one RUN command
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    tar \
    libssl-dev \
    git \
    ssh \
    rubygems \
    python3-pip \
    npm \
    php \
    pipenv \
    unzip \
    jq \
    gcc  \
    build-essential && \
    ln -snf /usr/share/zoneinfo/$CONTAINER_TIMEZONE /etc/localtime && \
    echo $CONTAINER_TIMEZONE > /etc/timezone

# Install Go
RUN GO_JSON=$(curl -s https://go.dev/dl/?mode=json) && \
    GO_LATEST=$(echo "$GO_JSON" | jq -r '.[0].version') && \
    ARCH=$(uname -m) && \
    case $ARCH in \
        x86_64) GO_ARCH="amd64" ;; \
        aarch64) GO_ARCH="arm64" ;; \
        armv7l) GO_ARCH="armv6l" ;; \
        *) echo "Unsupported architecture: $ARCH"; exit 1 ;; \
    esac && \
    GO_URL="https://dl.google.com/go/${GO_LATEST}.linux-${GO_ARCH}.tar.gz" && \
    curl -O $GO_URL && \
    tar -C /usr/local -xzf ${GO_LATEST}.linux-${GO_ARCH}.tar.gz && \
    rm ${GO_LATEST}.linux-${GO_ARCH}.tar.gz

# Set up Go environment variables
ENV PATH=$PATH:/usr/local/go/bin

# Install Ruby and npm packages
RUN gem install brakeman

# Clone the checkmate repository and install
RUN pip install --upgrade pip && pip install checkmate5 aigraphcodescan

# Clone and install other repositories
RUN git clone https://github.com/marcinguy-bot/betterscan.git /srv/scanmycode


# Create symbolic link
RUN ln -s /srv/scanmycode/quantifiedcode/settings/default.yml /srv/scanmycode/settings.yml


# Install Go tools
RUN mkdir -p /root/bin
RUN go install github.com/securego/gosec/v2/cmd/gosec@latest
RUN cp /usr/local/bin/gosec /root/bin/gosec
RUN go install github.com/google/osv-scanner/cmd/osv-scanner@v1
RUN cp /usr/local/bin/osv-scanner /root/bin/osv-scanner
RUN go install honnef.co/go/tools/cmd/staticcheck@latest
RUN cp /usr/local/bin/staticcheck /root/bin/staticcheck

# Install other tools
RUN gem install brakeman
RUN pip install bandit
RUN npm install -g jshint

# Download and extract PMD
RUN wget https://github.com/pmd/pmd/releases/download/pmd_releases%2F7.17.0/pmd-dist-7.17.0-bin.zip
RUN unzip pmd-dist-7.17.0-bin.zip

# Copy analyzer files
RUN mkdir /root/phpscan/
RUN cp /srv/scanmycode/analyzers/progpilot_dev20180720-215434.phar /root/phpscan/
RUN cp /srv/scanmycode/analyzers/find_unicode_control2.py /usr/local/bin/
RUN cp -pr /srv/scanmycode/analyzers/custom-semgrep /root
RUN cp /srv/scanmycode/analyzers/*.yml /root/
RUN mkdir -p /usr/local/lib/python3.12/site-packages/checkmate-4.3.0-dev2-py3.12.egg/checkmate/contrib/plugins/javascript/jshint/js
RUN cp /srv/scanmycode/analyzers/json_reporter.js /usr/local/lib/python3.12/site-packages/checkmate-4.3.0-dev2-py3.12.egg/checkmate/contrib/plugins/javascript/jshint/js/

# Install more Python packages
RUN pip install checkov
RUN pip install yara-scanner

# Install Kubescape
RUN curl -s https://raw.githubusercontent.com/armosec/kubescape/master/install.sh | /bin/bash

# Download and extract Insider
RUN wget https://github.com/insidersec/insider/releases/download/3.0.0/insider_3.0.0_linux_x86_64.tar.gz
RUN tar -xzf insider_3.0.0_linux_x86_64.tar.gz

# Clone additional repositories
WORKDIR /root
RUN mkdir /root/yara
RUN cp -pr /srv/scanmycode/analyzers/yara/* /root/yara

# Install Nix
ADD https://nixos.org/nix/install /tmp
RUN bash -c "bash /tmp/install --daemon"
RUN bash -c "/root/.nix-profile/bin/nix-env -if https://github.com/fluidattacks/makes/archive/22.11.tar.gz"
RUN bash -c "/root/.nix-profile/bin/m gitlab:fluidattacks/universe@trunk /skims"






