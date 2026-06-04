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
    {"name": "삼성전자", "code": "005930"},
    {"name": "SK스퀘어", "code": "402340"},
]

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg[:3900]})

def get_naver_posts(code):
    posts = []
    for page in range(1, 5):
        url = f"https://finance.naver.com/item/board.naver?code={code}&page={page}"
        res = requests.get(url, headers=HEADERS, timeout=15)
        html = res.content.decode("cp949", errors="ignore")
        soup = BeautifulSoup(html, "html.parser")

        for row in soup.select("table.type2 tr"):
            title_tag = row.select_one("td.title a")
            if title_tag:
                title = title_tag.get_text(strip=True)
                if title:
                    posts.append(title)

        time.sleep(0.5)

    return posts[:80]

def analyze_target(name, posts):
    text_data = "\n".join(posts)

    prompt = f"""
아래는 네이버 종목토론방 게시글 제목입니다.
종목명: {name}

중요 조건:
- 단순히 "오른다", "간다", "상승", "하락", "망했다", "끝났다"처럼 이유 없는 주장성 글은 분석에서 제외해줘.
- 상승 이유나 하락 이유가 들어간 글만 의미 있게 반영해줘.
- 긍정/부정 비율은 반드시 퍼센트로만 표시해줘. 예: 긍정 60% / 부정 40%
- 상승 이유가 있는 실제 게시글 제목은 직접 보여줘.
- 하락 이유가 있는 실제 게시글 제목도 직접 보여줘.
- 깨진 문자, 의미 없는 글, 욕설성 글, 단순 감정글은 제외해줘.
- 너무 길게 쓰지 말고 투자자가 바로 볼 수 있게 정리해줘.

출력 형식:

📌 {name}

1. 긍정/부정 비율
긍정 __% / 부정 __%

2. 상승 이유가 있는 게시글
- 게시글 제목 1
- 게시글 제목 2
- 게시글 제목 3

3. 하락 이유가 있는 게시글
- 게시글 제목 1
- 게시글 제목 2
- 게시글 제목 3

4. 요약 판단
- 한두 문장으로만 요약

게시글:
{text_data}
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content

send_telegram("🚀 삼성전자 / SK스퀘어 종토방 심리 분석을 시작합니다.")

for target in TARGETS:
    try:
        posts = get_naver_posts(target["code"])
        result = analyze_target(target["name"], posts)
        send_telegram(result)
        time.sleep(3)
    except Exception as e:
        send_telegram(f"⚠️ {target['name']} 분석 오류\n{str(e)}")
        time.sleep(2)

send_telegram("✅ 삼성전자 / SK스퀘어 분석이 완료되었습니다.")
