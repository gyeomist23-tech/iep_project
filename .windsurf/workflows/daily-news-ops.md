---
description: Daily news briefing generation, verification, and GitHub Actions maintenance workflow
---

# Daily News Ops Workflow

1. 요구사항 확인
   - 출력 포맷, 섹션 순서, 최대 기사 수, 스케줄 시간, 최근 기사 허용 기간을 먼저 확인한다.
   - 이번 변경이 `스크립트`, `README`, `GitHub Actions`, `키워드 세트` 중 어디에 영향을 주는지 분류한다.

2. 코드 변경
   - 수집/필터링/분류/출력 규칙 변경은 `src/news_briefing.py` 에 반영한다.
   - 실행 방법 또는 운영 가이드가 바뀌면 `README.md` 도 함께 반영한다.
   - 스케줄/커밋/권한 관련 변경은 `.github/workflows/daily.yml` 에 반영한다.

3. 로컬 검증
   - 아래 명령으로 가상환경과 의존성을 준비한다.
   - `python3 -m venv .venv`
   - `. .venv/bin/activate`
   - `python -m pip install -r requirements.txt`
   - 아래 명령으로 스크립트를 실행한다.
   - `python src/news_briefing.py --max-per-section 3 --max-total 12 --lookback-days 7`
   - 생성된 `output/YYYY/MM/daily_news_YYYYMMDD.txt` 파일을 열어 포맷을 확인한다.

4. 포맷 검토
   - 헤더 문구가 정확한지 확인한다.
   - 섹션 순서가 `[특수교육]`, `[통합교육]`, `[디지털교육]`, `[인공지능]` 인지 확인한다.
   - 실행 시점 기준 최근 7일 이내 기사만 포함되는지 확인한다.
   - 기사 없는 섹션이 `(없음)` 으로 표시되는지 확인한다.
   - 각 기사 항목이 두 줄 형식을 지키는지 확인한다.

5. 자동화 검토
   - GitHub Actions의 cron이 `30 22 * * *` 인지 확인한다.
   - `contents: write`, `fetch-depth: 0`, Python 3.11 설정이 유지되는지 확인한다.
   - 커밋 메시지가 `chore: daily news YYYY-MM-DD` 형식을 지키는지 확인한다.

6. 완료 기준
   - 실패 상황에서도 결과 파일이 생성된다.
   - README의 실행 예시와 실제 명령이 일치한다.
   - 출력 포맷이 사용자 카카오톡 복붙 용도에 맞게 유지된다.
