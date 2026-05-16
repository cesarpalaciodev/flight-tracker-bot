import logging
from datetime import datetime

import stripe

from src.utils.config import (
    CRYPTO_WALLET_BTC,
    CRYPTO_WALLET_USDT,
    NEQUI_API_TOKEN,
    NEQUI_API_URL,
    STRIPE_PRICE_PREMIUM,
    STRIPE_PRICE_PRO,
    STRIPE_SECRET_KEY,
    STRIPE_WEBHOOK_SECRET,
)

logger = logging.getLogger(__name__)

PLANS = {
    "premium": {"price": 5, "searches": 500, "routes": 3, "dashboard": True, "price_id_stripe": STRIPE_PRICE_PREMIUM},
    "pro": {
        "price": 10,
        "searches": -1,
        "routes": 10,
        "dashboard": True,
        "sms": True,
        "price_id_stripe": STRIPE_PRICE_PRO,
    },
    "trial": {"price": 0, "searches": 10, "routes": 1, "dashboard": False, "trial_days": 7},
}


def get_plan_features(plan: str) -> dict:
    return PLANS.get(plan, PLANS["trial"])


class PaymentService:
    def __init__(self):
        self.stripe_available = bool(STRIPE_SECRET_KEY)
        self.nequi_available = bool(NEQUI_API_URL and NEQUI_API_TOKEN)
        self.crypto_available = bool(CRYPTO_WALLET_USDT)
        if self.stripe_available:
            stripe.api_key = STRIPE_SECRET_KEY

    def create_stripe_checkout(self, chat_id: str, plan: str, success_url: str, cancel_url: str) -> str | None:
        if not self.stripe_available:
            logger.warning("Stripe not configured")
            return None
        plan_info = get_plan_features(plan)
        price_id = plan_info.get("price_id_stripe")
        if not price_id:
            logger.error(f"No Stripe price_id for plan {plan}")
            return None
        try:
            session = stripe.checkout.Session.create(
                mode="subscription",
                line_items=[{"price": price_id, "quantity": 1}],
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={"chat_id": chat_id, "plan": plan},
                client_reference_id=chat_id,
            )
            logger.info(f"Stripe session created: {session.id} for {chat_id}")
            return session.url
        except Exception as e:
            logger.error(f"Stripe checkout error: {e}")
            return None

    def verify_stripe_webhook(self, payload: bytes, sig_header: str) -> dict | None:
        if not self.stripe_available:
            return None
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
            return event
        except Exception as e:
            logger.error(f"Stripe webhook verification failed: {e}")
            return None

    def create_nequi_payment(self, chat_id: str, plan: str) -> str | None:
        if not self.nequi_available:
            logger.warning("Nequi not configured")
            return None
        plan_info = get_plan_features(plan)
        amount = plan_info["price"]
        try:
            from src.providers.base import BaseProvider

            provider = BaseProvider()
            result = provider._post(
                NEQUI_API_URL + "/payment",
                json_data={
                    "amount": amount,
                    "currency": "COP",
                    "reference": f"ft_{chat_id}",
                    "description": f"Flight Tracker {plan}",
                },
            )
            if result.is_ok and result.data:
                return result.data.get("payment_url") or result.data.get("qr_code")
            logger.error(f"Nequi error: {result.error}")
        except Exception as e:
            logger.error(f"Nequi request failed: {e}")
        return None

    def create_crypto_payment(self, chat_id: str, plan: str, currency: str = "USDT") -> dict | None:
        if not self.crypto_available:
            logger.warning("Crypto not configured")
            return None
        plan_info = get_plan_features(plan)
        amount = plan_info["price"]
        wallet = CRYPTO_WALLET_USDT if currency == "USDT" else CRYPTO_WALLET_BTC
        if not wallet:
            logger.warning(f"No wallet for {currency}")
            return None
        return {
            "wallet": wallet,
            "amount": amount,
            "currency": currency,
            "network": "TRC20" if currency == "USDT" else "Bitcoin",
            "reference": f"ft_{chat_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "instructions": f"Send exactly ${amount} USDT (TRC20) to:\n{wallet}\n\nReference: ft_{chat_id}_...",
        }

    def get_available_methods(self) -> list[str]:
        methods = []
        if self.stripe_available:
            methods.append("stripe")
        if self.nequi_available:
            methods.append("nequi")
        if self.crypto_available:
            methods.append("crypto")
        return methods


def get_payment_service() -> PaymentService:
    return PaymentService()
