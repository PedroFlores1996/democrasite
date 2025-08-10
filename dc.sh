#!/bin/bash
# Docker Compose convenience script for Democrasite
# Usage: ./dc.sh [docker-compose commands]
# Examples:
#   ./dc.sh up -d                    # Start development environment
#   ./dc.sh --profile postgres up -d # Start production environment
#   ./dc.sh logs -f                  # View logs
#   ./dc.sh down                     # Stop services

exec docker-compose -f docker/docker-compose.yml "$@"