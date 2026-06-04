from openai import OpenAI
import requests
import time
from bs4 import BeautifulSoup
import os

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

HEADERS = {
"User-Agent": "Mozilla/5.0"
}

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

```
requests.post(
    url,
    data={
        "chat_id": CHAT_ID,
        "text": msg[:3900]
    }
)
```

def is_clean_title(title):
if not title:
return False

```
if any(word in title for word in BAD_WORDS):
    return False

hangul_count = sum(
    1 for c in title
    if "가" <= c <= "힣"
)

if len(title) > 0:
    if hangul_count / len(title) < 0.4:
        return False

return True
```

def get_naver_posts(code):
posts = []

```
for page in range(1, 6):
    url = f"https://finance.naver.com/item/board.naver?code={code}&page={page}"

    res = requests.get(
        url,
        headers=HEADERS,
        timeout=15
    )

    res.encoding = "euc-kr"

    soup = BeautifulSoup(
        res.text,
        "html.parser"
    )

    for row in soup.select("table.type2 tr"):
        title_tag = row.select_one("td.title a")

        if not title_tag:
            continue

        title = title_tag.get_text(
            " ",
            strip=True
        )

        if is_clean_title(title):
            posts.append(title)

    time.sleep(0.5)

return posts[:100]
```

def analyze_target(name, posts):
text_data = "\n".join(posts)

```
prompt = f"""
```

아래는 네이버 종목토론방 게시글 제목입니다.

종목명: {name}

중요 규칙

1. 글자가 깨진 게시글 제외
2. 의미 없는 감탄문 제외
3. 단순 매수/매도 외침 제외
4. 단순 상승/하락 주장 제외
5. 상승 또는 하락 이유가 있는 글만 반영
6. 긍정/부정 비율은 합계 100%
7. 실제 게시글 제목 출력 금지
8. 깨진 문자 절대 출력 금지
9. 게시글 의미만 요약
10. 투자자가 바로 이해할 수 있게 작성

출력 형식

📌 {name}

1. 긍정/부정 비율
   긍정 XX% / 부정 XX%

2. 상승 이유 TOP3

* 이유
* 이유
* 이유

3. 하락 이유 TOP3

* 이유
* 이유
* 이유

4. 종합 판단
   2줄 이내 요약

게시글:

{text_data}
"""

```
response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[
        {
            "role": "user",
            "content": prompt
        }
    ]
)

return response.choices[0].message.content
```

send_telegram(
"🚀 삼성전자 / SK스퀘어 종토방 심리 분석을 시작합니다."
)

for target in TARGETS:

```
try:

    posts = get_naver_posts(
        target["code"]
    )

    if not posts:
        send_telegram(
            f"📌 {target['name']}\n\n분석 가능한 게시글이 없습니다."
        )
        continue

    result = analyze_target(
        target["name"],
        posts
    )

    send_telegram(result)

    time.sleep(3)

except Exception as e:

    send_telegram(
        f"⚠️ {target['name']} 분석 오류\n{str(e)}"
    )

    time.sleep(2)
```

send_telegram(
"✅ 삼성전자 / SK스퀘어 분석이 완료되었습니다."
)
