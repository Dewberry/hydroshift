#!/bin/bash

set -euo pipefail

source .env

aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ${ECR_AWS_ACCOUNT_ID}.dkr.ecr.${ECR_AWS_REGION}.amazonaws.com


docker compose -f docker-compose.yml pull
docker compose -f docker-compose.yml up -d
docker compose -f docker-compose.yml logs -f
