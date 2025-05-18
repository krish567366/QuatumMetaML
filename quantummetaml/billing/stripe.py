import stripe
from pydantic import BaseModel
from typing import Optional
from fastapi import HTTPException

class BillingConfig(BaseModel):
    api_key: str
    currency: str = "usd"
    tax_rate: float = 0.2

class QuantumBilling:
    def __init__(self, config: BillingConfig):
        stripe.api_key = config.api_key
        
    def create_subscription(self, customer_id: str, plan_id: str) -> dict:
        try:
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{"price": plan_id}],
                payment_behavior="default_incomplete",
                expand=["latest_invoice.payment_intent"]
            )
            return {
                "subscription_id": subscription.id,
                "client_secret": subscription.latest_invoice.payment_intent.client_secret
            }
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=str(e))