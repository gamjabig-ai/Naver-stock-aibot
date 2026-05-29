from openai import OpenAI
import requests
import time
from bs4 import BeautifulSoup
import os

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

HEADERS = {"User-Agent": "Mozilla/5.0"}

TARGETS = [
    {"name": "TIGER 미국우주항공", "type": "naver", "code": "0183J0"},
    {"name": "마이크론", "type": "yahoo", "ticker": "MU"},
    {"name": "샌디스크", "type": "yahoo", "ticker": "SNDK"},
    {"name": "레드와이어", "type": "yahoo", "ticker": "RDW"},
    {"name": "SOXL", "type": "yahoo", "ticker": "SOXL"},
]

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    requests.post(url, data=data)

def get_naver_posts(code, pages=3):
    board_url = f"https://finance.naver.com/item/board.naver?code={code}"
    posts = []

    for page in range(1, pages + 1):
        url = board_url + f"&page={page}"
        res = requests.get(url, headers=HEADERS)
        html = res.content.decode("cp949", errors="ignore")
        soup = BeautifulSoup(html, "html.parser")

        rows = soup.select("table.type2 tr")
        for row in rows:
            title_tag = row.select_one("td.title a")
            if title_tag:
                posts.append(title_tag.get_text(strip=True))

        time.sleep(0.5)

    return posts[:50]

def get_yahoo_news(ticker):
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.content, "xml")

    titles = []
    for item in soup.find_all("item")[:20]:
        title = item.find("title")
        if title:
            titles.append(title.get_text(strip=True))

    return titles

def analyze_target(target):
    name = target["name"]

    if target["type"] == "naver":
        data = get_naver_posts(target["code"])
        source_text = "\n".join(data)
        source_name = "네이버 종목토론방 게시글 제목"
    else:
        data = get_yahoo_news(target["ticker"])
        source_text = "\n".join(data)
        source_name = "Yahoo Finance 최근 뉴스 제목"

    if not source_text.strip():
        return f"[{name}]\n수집된 데이터가 없습니다."

    prompt = f"""
아래 자료를 바탕으로 {name}을 분석해줘.

자료 출처: {source_name}

다음 형식으로 짧고 명확하게 한국어로 작성해줘.

1. 현재 투자심리
2. 상승 요인
3. 하락 요인
4. 핵심 키워드
5. 단기 관전 포인트
6. 종합 판단

자료:
{source_text}
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return f"📌 {name}\n\n{response.choices[0].message.content}"

for target in TARGETS:
    try:
        result = analyze_target(target)
        send_telegram(result)
        time.sleep(2)
    except Exception as e:
        send_telegram(f"⚠️ {target['name']} 분석 중 오류 발생:\n{str(e)}")
