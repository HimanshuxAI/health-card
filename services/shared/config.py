import os

JWT_SECRET = os.getenv("JWT_SECRET", "demo-secret-change-me")
JWT_ALG = "HS256"
JWT_EXP_HOURS = 24

SHARED_TOKEN = os.getenv("SHARED_TOKEN", "internal-demo-token")
