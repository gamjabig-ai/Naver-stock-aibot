from openai import OpenAI
import requests
import time
from bs4 import BeautifulSoup
import os

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

BOARD_URL = "https://finance.naver.com/item/board.naver?code=0183J0"
headers = {"User-Agent": "Mozilla/5.0"}

def get_posts(page=1):
    url = BOARD_URL + f"&page={page}"
    res = requests.get(url, headers=headers)
    html = res.content.decode("cp949", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")

    rows = soup.select("table.type2 tr")
    posts = []

    for row in rows:
        title_tag = row.select_one("td.title a")
        if not title_tag:
            continue
        posts.append(title_tag.get_text(strip=True))

    return posts

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    requests.post(url, data=data)

all_posts = []

for p in range(1, 4):
    all_posts.extend(get_posts(p))
    time.sleep(0.5)

text_data = "\n".join(all_posts[:50])

prompt = f"""
아래는 네이버 종목토론방 게시글 제목이다.

1. 현재 투자심리
2. 상승론 요약
3. 하락론 요약
4. 핵심 키워드
5. 전체 분위기

를 분석해줘.

게시글:
{text_data}
"""

response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[{"role": "user", "content": prompt}]
)

result = response.choices[0].message.content
print(result)
send_telegram(result)
