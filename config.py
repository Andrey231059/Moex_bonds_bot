import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
    MOEX_API_URL = "https://iss.moex.com/iss"
    REQUEST_TIMEOUT = 10
    BONDS_LIMIT = 10