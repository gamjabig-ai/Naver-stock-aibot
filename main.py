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

BAD_WORDS = [
    "쒯", "빳", "뒷", "렐", "쩔", "냇",
    "뷁", "뺏", "룀", "돔", "源", "浚",
    "媛", "燮", "珉", "갤쌕", "뤠", "짤렐"
]

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg[:3900]})

def is_clean_title(title):
    if not title:
        return False

    if any(word in title for word in BAD_WORDS):
        return False

    hangul_count = sum(1 for c in title if "가" <= c <= "힣")
    if hangul_count < len(title) * 0.3:
        return False

    return True

def get_naver_posts(code):
    posts = []

    for page in range(1, 6):
        url = f"https://finance.naver.com/item/board.naver?code={code}&page={page}"
        res = requests.get(url, headers=HEADERS, timeout=15)
        html = res.content.decode("cp949", errors="ignore")
        soup = BeautifulSoup(html, "html.parser")

        for row in soup.select("table.type2 tr"):
            title_tag = row.select_one("td.title a")
            if not title_tag:
                continue

            title = title_tag.get_text(strip=True)

            if is_clean_title(title):
                posts.append(title)

        time.sleep(0.5)

    return posts[:100]

def analyze_target(name, posts):
    text_data = "\n".join(posts)

    prompt = f"""
아래는 네이버 종목토론방 게시글 제목입니다.

종목명: {name}

중요 규칙:
1. 글자가 깨진 게시글은 무조건 제외.
2. 의미 없는 감탄문은 제외.
3. 단순 매수/매도 외침은 제외.
4. 단순 상승/하락 주장만 있는 글은 제외.
5. 반드시 상승 이유 또는 하락 이유가 포함된 게시글만 분석.
6. 긍정/부정 비율은 합계 100%.
7. 실제 게시글 제목은 최대 3개씩만 인용.
8. 깨진 문자가 보이면 절대 출력하지 말 것.
9. 상승 이유와 하락 이유를 구분해서 정리.
10. 투자자가 바로 볼 수 있게 짧고 명확하게 작성.

출력 형식:

📌 {name}

1. 긍정/부정 비율
긍정 XX% / 부정 XX%

2. 상승 이유 TOP3
- 이유1
- 이유2
- 이유3

상승 근거 게시글
- 게시글 제목
- 게시글 제목
- 게시글 제목

3. 하락 이유 TOP3
- 이유1
- 이유2
- 이유3

하락 근거 게시글
- 게시글 제목
- 게시글 제목
- 게시글 제목

4. 종합 판단
한두 문장으로 간단히 요약.

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

        if not posts:
            send_telegram(f"📌 {target['name']}\n\n분석 가능한 정상 게시글이 없습니다.")
            continue

        result = analyze_target(target["name"], posts)
        send_telegram(result)
        time.sleep(3)

    except Exception as e:
        send_telegram(f"⚠️ {target['name']} 분석 오류\n{str(e)}")
        time.sleep(2)

send_telegram("✅ 삼성전자 / SK스퀘어 분석이 완료되었습니다.")
