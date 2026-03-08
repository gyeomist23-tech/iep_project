# Daily News Briefing

매일 Google News RSS에서 국내뿐 아니라 미국, 유럽 등 주요 IT 강국의 특수교육, 통합교육, 장애인 디지털 접근성, 에듀테크 및 인공지능 관련 뉴스를 수집하는 저장소입니다. 카카오톡 전체방에 바로 붙여넣기 좋은 텍스트와 HTML 사이트를 생성합니다.
기본적으로 실행 시점 기준 최근 28일 이내 기사만 포함합니다.
가능한 한 교육 전문지, 주요 메이저 언론, 학술지 계열 출처를 우선 반영하며 교육청·교육지원청 소식도 함께 포함할 수 있습니다.

## 로컬 실행

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python src/news_briefing.py --max-per-section 3 --max-total 12 --lookback-days 28
```

기본값 요약:

- `--max-per-section 3`
- `--max-total 12`
- `--lookback-days 28`

## 결과 파일 위치

실행 결과는 아래 경로에 저장됩니다.

```text
output/YYYY/MM/daily_news_YYYYMMDD.txt
output/YYYY/MM/daily_news_YYYYMMDD.html
index.html
```

예시:

```text
output/2026/03/daily_news_20260303.txt
```

## 기사 선정 및 출력 기준

- 출처는 교육 전문지, 메이저 언론, 학술지 계열을 우선 반영합니다.
- 교육청, 교육지원청, 교육지원센터 계열 소식도 허용하되 우선순위는 낮게 둡니다.
- 각 기사에는 제목, 링크와 함께 요약과 주요 키워드를 함께 출력합니다.
- Instagram 계열 소스는 Google News RSS 결과에 포함되는 경우에만 반영됩니다.
- 같은 내용으로 단일 HTML 페이지도 생성되어 사이트 형태로 관리할 수 있습니다.

## GitHub Actions 동작 방식

- 매주 월요일 KST 오전 07:30에 스케줄 실행됩니다.
- GitHub Actions는 Python 3.11 환경에서 의존성을 설치한 뒤 스크립트를 실행합니다.
- 스크립트는 기본적으로 실행 시점 기준 최근 28일 이내 기사만 반영합니다.
- 결과 파일에 변경이 있으면 `output/` 경로를 커밋하고 원격 저장소로 푸시합니다.
- 생성된 txt 파일은 GitHub Actions Artifact로도 업로드되어 GitHub 웹에서 바로 내려받을 수 있습니다.
- 생성된 HTML 파일과 루트 `index.html`도 함께 커밋되어 GitHub Pages/Vercel 같은 정적 호스팅에 바로 사용할 수 있습니다.
- 커밋 메시지 형식은 `chore: daily news YYYY-MM-DD` 입니다.
- 필요하면 `workflow_dispatch`로 수동 실행할 수 있습니다.

## Windsurf 없이 결과 보는 방법

- GitHub 저장소의 `output/` 폴더에서 커밋된 txt 파일을 직접 엽니다.
- GitHub 저장소 루트의 `index.html` 또는 `output/` 폴더의 html 파일을 열어 브라우저로 봅니다.
- 또는 GitHub 저장소의 `Actions` 탭에서 실행 이력을 열고 `weekly-news-txt` artifact를 내려받습니다.

## 카카오톡 업로드 방법

- 배포된 HTML 사이트에 접속합니다.
- 화면 상단의 **"카카오톡 양식으로 전체 복사하기"** 버튼을 클릭합니다.
- 카카오톡 전체방에 바로 붙여넣기 하여 전송합니다.
- (또는 생성된 텍스트 파일의 전체 내용을 수동 복사하여 전송해도 무방합니다.)

카카오톡 자동 전송 기능은 포함하지 않습니다.
