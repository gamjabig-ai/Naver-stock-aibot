from openai import OpenAI
import requests
import time
from bs4 import BeautifulSoup
import os

client = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"]
)

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

BOARD_URL = "https://finance.naver.com/item/board.naver?code=0183J0"

headers = {
    "User-Agent": "Mozilla/5.0"
}

def get_posts(page=1):

    url = BOARD_URL + f"&page={page}"

    res = requests.get(url, headers=headers)

    soup = BeautifulSoup(res.t
