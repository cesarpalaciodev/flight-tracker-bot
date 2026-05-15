import os

# Stripe
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRICE_PREMIUM = os.getenv("STRIPE_PRICE_PREMIUM", "")
STRIPE_PRICE_PRO = os.getenv("STRIPE_PRICE_PRO", "")

# Nequi
NEQUI_API_URL = os.getenv("NEQUI_API_URL", "")
NEQUI_API_TOKEN = os.getenv("NEQUI_API_TOKEN", "")

# Crypto
CRYPTO_WALLET_USDT = os.getenv("CRYPTO_WALLET_USDT", "")
CRYPTO_WALLET_BTC = os.getenv("CRYPTO_WALLET_BTC", "")

# Dashboard
JWT_SECRET = os.getenv("JWT_SECRET", "change_this")
DASHBOARD_URL = os.getenv("DASHBOARD_URL", "http://localhost:8000")
ADMIN_CHAT_IDS = [x.strip() for x in os.getenv("ADMIN_CHAT_IDS", "").split(",") if x.strip()]

# Max API requests per user per month
API_REQUESTS_LIMIT_FREE = int(os.getenv("API_REQUESTS_LIMIT_FREE", "10"))
API_REQUESTS_LIMIT_PREMIUM = int(os.getenv("API_REQUESTS_LIMIT_PREMIUM", "500"))
API_REQUESTS_LIMIT_PRO = int(os.getenv("API_REQUESTS_LIMIT_PRO", "-1"))  # -1 = unlimited
