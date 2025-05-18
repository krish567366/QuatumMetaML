# tests/test_commercial.py
import pytest
from unittest.mock import MagicMock
from quantumml.license.manager import LicenseValidator
from quantumml.billing.processor import BillingManager

@pytest.fixture
def mock_stripe():
    stripe = MagicMock()
    stripe.Customer.create.return_value = {"id": "cus_test"}
    stripe.Subscription.create.return_value = {
        "id": "sub_test",
        "latest_invoice": {"payment_intent": {"client_secret": "secret_test"}}
    }
    return stripe

def test_enterprise_license_validation():
    validator = LicenseValidator(master_key="test_key")
    license_key = validator.generate_license(features=["quantum_enterprise"], days=365)
    assert validator.validate_license(license_key, "test_machine")

def test_payment_processing(mock_stripe):
    billing = BillingManager(
        BillingConfig(stripe_secret="sk_test"),
        license_manager=MagicMock()
    )
    result = billing.create_subscription({
        "email": "enterprise@example.com",
        "tier": "enterprise"
    })
    assert "subscription_id" in result