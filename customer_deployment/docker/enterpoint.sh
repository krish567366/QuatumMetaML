#!/bin/bash

# Verify TPM presence
if ! tpm2_getrandom 8 >/dev/null; then
    echo "TPM 2.0 required" >&2
    exit 1
fi

# Check license against hardware
python3 -c "from security.tpm_binder import TPMEnforcer; \
TPMEnforcer().verify_hardware('$LICENSE_KEY')"

# Start quantum worker with credits
exec quantum_worker --credits $(python3 get_credits.py $LICENSE_KEY)