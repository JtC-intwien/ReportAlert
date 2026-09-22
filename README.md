markdown
# PUBG 공식카페 게시판 → Slack 알림

배틀그라운드 공식카페(`https://cafe.naver.com/playbattlegrounds`)의
특정 게시판(menuid=107)에 새 글이 올라오면 Slack으로 알려주는 GitHub Actions 봇입니다.

## 설정 방법

1. **이 폴더 전체를 새 GitHub 저장소에 올리기**
   - GitHub에서 새 저장소 생성 (Public/Private 둘 다 무료로 가능)
   - 이 폴더의 내용을 그대로 push
```bash
     cd pubg-cafe-watch
     git init
     git add .
     git commit -m "init"
     git branch -M main
     git remote add origin <내 저장소 URL>
     git push -u origin main
```

2. **Slack Webhook을 GitHub Secret으로 등록**
   - 저장소 → Settings → Secrets and variables → Actions → "New repository secret"
   - Name: `SLACK_WEBHOOK_URL`
   - Value: Slack Incoming Webhook 주소 (`https://hooks.slack.com/services/...`)
   - **코드에는 절대 이 값을 직접 적지 않습니다.** 이렇게 Secret으로만 등록합니다.

3. **Actions 활성화 확인**
   - 저장소 → Actions 탭 → 워크플로가 보이는지 확인 (fork한 경우 활성화 버튼을 눌러야 할 수 있음)

4. **첫 실행 (수동)**
   - Actions 탭 → "PUBG 공식카페 게시판 감시" 선택 → "Run workflow" 버튼으로 수동 실행
   - **첫 실행에서는 Slack 알림이 오지 않는 게 정상입니다.** 현재 최신 글 번호를 기준점으로만 저장하기 때문입니다 (과거 글이 한꺼번에 알림 오는 것을 막기 위함).
   - `state/last_article_id.txt` 파일이 생기고 커밋되는지 확인하세요.

5. **이후부터는 자동**
   - 10분마다 자동 실행되어, 기준점보다 새 글이 있으면 Slack으로 전송하고 기준점을 갱신합니다.

## 문제가 생기면

- Actions 탭 → 실행 기록 → 로그에서 에러 메시지 확인
- 네이버 API 응답 구조가 바뀌었거나(`extract_article_list` 에러), 요청이 차단된 경우(HTTP 403 등) 로그에 메시지가 남습니다. 이 내용을 알려주시면 스크립트를 그에 맞게 수정해드릴 수 있어요.
- GitHub Actions 무료 사용량(월 2,000분, public 저장소는 무제한)을 초과하면 알림이 멈출 수 있습니다. 10분 간격이면 한 달에 대략 130~150분 정도 사용하므로 보통은 문제 없습니다.

## 다른 게시판/카페로 바꾸고 싶다면

`scripts/watch_cafe.py` 상단의 `CLUB_ID`, `MENU_ID`, `CAFE_URL_NAME` 값만 바꾸면 됨.
