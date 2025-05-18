#!/bin/bash
# examples/deploy.sh

# Secure production deployment script for QuantumMetaML
set -eo pipefail

export DOCKER_BUILDKIT=1
VERSION=${1:-latest}

# Validate environment
if [[ -z "$LICENSE_MASTER_KEY" || -z "$STRIPE_SECRET" ]]; then
    echo "Missing required environment variables"
    exit 1
fi

# Build hardened Docker image
docker build \
    --tag quantumml:$VERSION \
    --build-arg LICENSE_KEY=$LICENSE_MASTER_KEY \
    --secret id=stripe_key,env=STRIPE_SECRET \
    --no-cache .

# Kubernetes deployment
helm upgrade --install quantumml \
    --set image.tag=$VERSION \
    --set secrets.licenseMasterKey=$LICENSE_MASTER_KEY \
    --set secrets.stripeKey=$STRIPE_SECRET \
    --set service.type=LoadBalancer \
    ./helm-chart

# Post-deployment checks
kubectl rollout status deployment/quantumml
kubectl get svc quantumml -o jsonpath='{.status.loadBalancer.ingress[0].ip}'