"""
배틀그라운드 공식카페(clubid=28866679)의 특정 게시판(menuid=107)을
주기적으로 확인해서 새 글이 생기면 Slack Webhook으로 알려주는 스크립트.

- 상태(마지막으로 확인한 글 번호)는 state/last_article_id.txt 에 저장됨
- 첫 실행에서는 알림을 보내지 않고 "현재 최신 글 번호"만 기준점으로 저장함
  (과거 글이 한꺼번에 쏟아지는 것을 막기 위함)
- GitHub Actions 워크플로(.github/workflows/watch-cafe.yml)가 이 스크립트를
  주기적으로 실행하고, state 파일 변경을 커밋함

필요한 환경변수:
- SLACK_WEBHOOK_URL : Slack Incoming Webhook 주소
"""

import json
import os
import urllib.error
import urllib.request

CLUB_ID = "28866679"          # 배틀그라운드 공식카페
MENU_ID = "107"                # 감시할 게시판
CAFE_URL_NAME = "playbattlegrounds"  # https://cafe.naver.com/playbattlegrounds
PER_PAGE = 20

STATE_FILE = os.path.join(os.path.dirname(__file__), "..", "state", "last_article_id.txt")

API_URL = (
    "https://apis.naver.com/cafe-web/cafe2/ArticleListV2dot1.json"
    f"?search.clubid={CLUB_ID}&search.menuid={MENU_ID}"
    f"&search.perPage={PER_PAGE}&search.page=1&search.queryType=lastArticle"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": f"https://cafe.naver.com/{CAFE_URL_NAME}",
    "Accept": "application/json, text/plain, */*",
}


def fetch_articles():
    req = urllib.request.Request(API_URL, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"HTTP {e.code} 오류: {body[:500]}") from e
    return json.loads(raw)


def extract_article_list(data):
    # 네이버 응답 구조가 바뀔 수 있어 방어적으로 접근
    try:
        return data["message"]["result"]["articleList"]
    except (KeyError, TypeError):
        raise RuntimeError(
            "예상한 형태의 응답이 아닙니다. 원본 응답 일부:\n"
            + json.dumps(data, ensure_ascii=False)[:1000]
        )


def load_last_seen():
    if not os.path.exists(STATE_FILE):
        return None
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        content = f.read().strip()
    return int(content) if content else None


def save_last_seen(article_id):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        f.write(str(article_id))


def send_slack(webhook_url, article):
    article_id = article.get("articleId")
    subject = article.get("subject") or "(제목 없음)"
    writer = article.get("writerNickName") or ""
    url = f"https://cafe.naver.com/{CAFE_URL_NAME}/{article_id}"

    payload = {"text": f"*새 글 등록*\n<{url}|{subject}>\n작성자: {writer}"}

    req = urllib.request.Request(
        webhook_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        resp.read()


def main():
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook_url:
        raise SystemExit("환경변수 SLACK_WEBHOOK_URL 이 설정되어 있지 않습니다.")

    data = fetch_articles()
    articles = extract_article_list(data)

    if not articles:
        print("게시글을 찾지 못했습니다.")
        return

    # 최신 글이 맨 위에 오도록 정렬 (방어적으로)
    articles.sort(key=lambda a: int(a.get("articleId", 0)), reverse=True)

    last_seen_id = load_last_seen()

    if last_seen_id is None:
        newest_id = int(articles[0].get("articleId"))
        save_last_seen(newest_id)
        print(f"첫 실행: 기준 글 번호를 {newest_id} 로 초기화했습니다. (알림 없음)")
        return

    new_articles = [a for a in articles if int(a.get("articleId", 0)) > last_seen_id]

    if not new_articles:
        print("새 글이 없습니다.")
        return

    # 오래된 글부터 순서대로 전송
    for article in reversed(new_articles):
        send_slack(webhook_url, article)
        print(f"Slack 전송: {article.get('articleId')} - {article.get('subject')}")

    newest_id = int(new_articles[0].get("articleId"))
    save_last_seen(newest_id)
    print(f"{len(new_articles)}개의 새 글을 전송했습니다. 기준을 {newest_id} 로 갱신.")


if __name__ == "__main__":
    main()
