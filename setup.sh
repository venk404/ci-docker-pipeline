#!/bin/bash

# Function to update system packages

export DEBIAN_FRONTEND=noninteractive
export TZ=UTC

# Pre-configure timezone package
ln -snf /usr/share/zoneinfo/$TZ /etc/localtime
echo $TZ > /etc/timezone

update_system() {
    echo "Updating system packages..."
    apt-get update -y
    apt-get upgrade -y
}

# Function to install Docker
install_docker() {
    echo "Installing Docker..."
    apt-get install -y apt-transport-https ca-certificates curl software-properties-common
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
    add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io
    
    # Note: systemctl won't work in Docker container, so skipping start and enable Docker commands here
    echo "Docker installation completed."
    
    # Add current user to Docker group (if not root)
    if [ "$USER" != "root" ]; then
        usermod -aG docker $USER
    fi
}

# Function to install Docker Compose
install_docker_compose() {
    echo "Installing Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
}

# Function to install Make
install_make() {
    echo "Installing Make..."
    apt-get install -y make
}

# Main execution
main() {
    update_system
    install_docker
    install_docker_compose
    install_make
    echo "Setup completed successfully!"
}

# Run main function
main