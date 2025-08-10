#!/bin/bash
# Docker Compose convenience script for Democrasite
# Usage: ./run-docker.sh [docker-compose commands]
# Examples:
#   ./run-docker.sh up -d                    # Start development environment
#   ./run-docker.sh --profile postgres up -d # Start production environment
#   ./run-docker.sh logs -f                  # View logs
#   ./run-docker.sh down                     # Stop services

exec docker-compose -f docker/docker-compose.yml "$@"