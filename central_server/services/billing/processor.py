# quantumml/billing/processor.py
import stripe
from pydantic import BaseModel
from typing import Optional
from fastapi import HTTPException
from .license.manager import LicenseValidator

class BillingConfig(BaseModel):
    stripe_secret: str
    currency: str = "usd"
    trial_days: int = 14

class BillingManager:
    def __init__(self, config: BillingConfig, license_manager: LicenseValidator):
        stripe.api_key = config.stripe_secret
        self.config = config
        self.license_manager = license_manager

    def create_subscription(self, customer_data: dict) -> dict:
        try:
            customer = stripe.Customer.create(**customer_data)
            
            subscription = stripe.Subscription.create(
                customer=customer.id,
                items=[{"price": self._get_price_id(customer_data["tier"])}],
                payment_behavior="default_incomplete",
                expand=["latest_invoice.payment_intent"]
            )
            
            self._provision_license(customer, subscription)
            return {
                "subscription_id": subscription.id,
                "client_secret": subscription.latest_invoice.payment_intent.client_secret
            }
        except stripe.error.StripeError as e:
            raise HTTPException(400, detail=f"Payment failed: {e.user_message}")

    def _get_price_id(self, tier: str) -> str:
        tiers = {
            "starter": "price_1PABCDEFG",
            "pro": "price_1PHIJKLMN",
            "enterprise": "price_1PQRSTUVW"
        }
        return tiers[tier.lower()]

    def _provision_license(self, customer, subscription):
        license_key = self.license_manager.generate_license(
            features=self._get_features_for_tier(subscription["tier"]),
            days=self.config.trial_days
        )
        stripe.Customer.modify(
            customer.id,
            metadata={"license_key": license_key}
        )

    def _get_features_for_tier(self, tier: str) -> list:
        return {
            "starter": ["quantum_basic", "automl_basic"],
            "pro": ["quantum_pro", "automl_pro", "meta_learning"],
            "enterprise": ["all"]
        }[tier]