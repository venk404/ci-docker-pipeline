#!/bin/bash

# Function to update system packages

export DEBIAN_FRONTEND=noninteractive
export TZ=UTC

# Pre-configure timezone package
ln -snf /usr/share/zoneinfo/$TZ /etc/localtime
echo $TZ > /etc/timezone

# Version requirements
DOCKER_COMPOSE_MIN_VERSION="2.20.0"

update_system() {
    echo "Updating system packages..."
    apt-get update -y
    apt-get upgrade -y
}

# Function to compare versions
version_compare() {
    printf '%s\n%s\n' "$1" "$2" | sort -V | head -n1
}

# Function to check if Docker is installed and up to date
check_docker() {
    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version | grep -oP 'Docker version \K[0-9]+\.[0-9]+\.[0-9]+')
        echo "Docker is already installed (version: $DOCKER_VERSION)"
        return 0
    else
        return 1
    fi
}

# Function to check if Docker Compose is installed and up to date
check_docker_compose() {
    if command -v docker-compose &> /dev/null; then
        COMPOSE_VERSION=$(docker-compose --version | grep -oP 'Docker Compose version v?\K[0-9]+\.[0-9]+\.[0-9]+')
        echo "Found Docker Compose version: $COMPOSE_VERSION"
        
        # Compare versions
        if [ "$(version_compare "$COMPOSE_VERSION" "$DOCKER_COMPOSE_MIN_VERSION")" = "$DOCKER_COMPOSE_MIN_VERSION" ]; then
            echo "Docker Compose is up to date (version: $COMPOSE_VERSION)"
            return 0
        else
            echo "Docker Compose version $COMPOSE_VERSION is older than required $DOCKER_COMPOSE_MIN_VERSION"
            return 1
        fi
    else
        return 1
    fi
}

# Function to check if Make is installed
check_make() {
    if command -v make &> /dev/null; then
        MAKE_VERSION=$(make --version | head -n1 | grep -oP 'GNU Make \K[0-9]+\.[0-9]+')
        echo "Make is already installed (version: $MAKE_VERSION)"
        return 0
    else
        return 1
    fi
}

# Function to install Docker
install_docker() {
    if check_docker; then
        echo "Skipping Docker installation - already installed"
        # Still fix permissions even if Docker is installed
        fix_docker_permissions
        return 0
    fi
    
    echo "Installing Docker..."
    apt-get install -y apt-transport-https ca-certificates curl software-properties-common
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
    add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io
    
    # Fix Docker permissions
    fix_docker_permissions
    
    echo "Docker installation completed."
}

# Function to fix Docker permissions
fix_docker_permissions() {
    echo "Fixing Docker permissions..."
    
    # Create docker group if it doesn't exist
    groupadd docker 2>/dev/null || true
    
    # Add current user to docker group
    if [ "$USER" != "root" ] && [ -n "$USER" ]; then
        usermod -aG docker $USER
        echo "Added $USER to docker group"
    fi
    
    # Fix socket permissions
    if [ -S /var/run/docker.sock ]; then
        chown root:docker /var/run/docker.sock
        chmod 666 /var/run/docker.sock
        echo "Fixed Docker socket permissions"
    fi
    
    # Start Docker service if not running
    if command -v systemctl &> /dev/null; then
        systemctl start docker 2>/dev/null || true
        systemctl enable docker 2>/dev/null || true
        echo "Started Docker service"
    fi
}

# Function to install Docker Compose
install_docker_compose() {
    if check_docker_compose; then
        echo "Skipping Docker Compose installation - already installed and up to date"
        return 0
    fi
    
    echo "Installing Docker Compose..."
    # Remove old version if exists
    if command -v docker-compose &> /dev/null; then
        echo "Removing old Docker Compose version..."
        rm -f /usr/local/bin/docker-compose
    fi
    
    curl -L "https://github.com/docker/compose/releases/download/v${DOCKER_COMPOSE_MIN_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    echo "Docker Compose installation completed."
}

# Function to install Make
install_make() {
    if check_make; then
        echo "Skipping Make installation - already installed"
        return 0
    fi
    
    echo "Installing Make..."
    apt-get install -y make
    echo "Make installation completed."
}

# Main execution
main() {
    echo "Starting system setup..."
    echo "========================="
    
    update_system
    
    echo ""
    echo "Checking and installing Docker..."
    install_docker
    
    echo ""
    echo "Checking and installing Docker Compose..."
    install_docker_compose
    
    echo ""
    echo "Checking and installing Make..."
    install_make
    
    echo ""
    echo "========================="
    echo "Setup completed successfully!"
    echo ""
    echo "Installed versions:"
    echo "- Docker: $(docker --version 2>/dev/null || echo 'Not available')"
    echo "- Docker Compose: $(docker-compose --version 2>/dev/null || echo 'Not available')"
    echo "- Make: $(make --version 2>/dev/null | head -n1 || echo 'Not available')"
}

# Run main function
main