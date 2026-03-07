# Daily News Briefing

매일 Google News RSS에서 특수교육/통합교육/디지털교육/인공지능 관련 뉴스를 수집하고, 카카오톡 전체방에 바로 붙여넣기 좋은 텍스트 파일을 생성하는 저장소입니다.

## 로컬 실행

```bash
python src/news_briefing.py --max-per-section 3 --max-total 12
```

필요 시 의존성을 먼저 설치하세요.

```bash
pip install -r requirements.txt
```

## 결과 파일 위치

실행 결과는 아래 경로에 저장됩니다.

```text
output/YYYY/MM/daily_news_YYYYMMDD.txt
```

예시:

```text
output/2026/03/daily_news_20260303.txt
```

## GitHub Actions 동작 방식

- 매일 KST 오전 07:30에 스케줄 실행됩니다.
- GitHub Actions는 Python 3.11 환경에서 의존성을 설치한 뒤 스크립트를 실행합니다.
- 결과 파일에 변경이 있으면 `output/` 경로를 커밋하고 원격 저장소로 푸시합니다.
- 커밋 메시지 형식은 `chore: daily news YYYY-MM-DD` 입니다.
- 필요하면 `workflow_dispatch`로 수동 실행할 수 있습니다.

## 카카오톡 업로드 방법

- 생성된 텍스트 파일을 엽니다.
- 전체 내용을 복사합니다.
- 카카오톡 전체방에 붙여넣어 수동으로 전송합니다.

카카오톡 자동 전송 기능은 포함하지 않습니다.
