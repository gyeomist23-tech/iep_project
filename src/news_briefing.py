import argparse
import html
import re
import time
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Optional
from urllib.parse import quote_plus
from zoneinfo import ZoneInfo

import feedparser
import requests
from dateutil import parser as date_parser


SPECIAL_ED_TERMS = [
    "특수교육","특수교육대상자","장애학생","장애아동","특수학교","특수학급","특수교사",
    "지적장애","자폐","자폐스펙트럼","발달장애","정서행동","ADHD","학습장애","지체장애","뇌병변",
    "시각장애","청각장애","중복장애","중증","중도중복",
    "개별화교육","개별화교육계획","IEP","개별화지원","진단평가","재평가","배치","전환교육","자립생활",
    "보완대체의사소통","AAC","의사소통지원","보조공학","접근성","학습접근성","읽기장애","난독",
    "긍정적행동지원","PBS","행동중재","문제행동","도전행동","위기행동","인권","인권지원단",
    "특수교육지원센터","치료지원","치료지원비","바우처","지원인력","특수교육실무원","보조인력",
    "순회교육","순회교사","특수교육대상자 선정"
]
INCLUSION_TERMS = [
    "통합교육","통합학급","통합지원","통합수업","통합교육 지원","협력교수","협력수업",
    "일반학급","일반교사","특수교사 협력","공동수업","팀티칭","코티칭","Co-teaching",
    "또래지원","또래중재","또래도움","학급 공동체","학교 적응","사회성","관계","학부모 협력",
    "장애이해교육","통합교육 환경","합리적 편의","장애학생 지원","차별","인권"
]
DIGITAL_TERMS = [
    "디지털교육","디지털 기반 교육","디지털교과서","AI 디지털교과서","AIDT","디지털 전환",
    "에듀테크","교육용 앱","코스웨어","학습 플랫폼","LMS","학습분석","러닝애널리틱스",
    "UDL","보편적 학습 설계","보편적학습설계","학습자 접근성","웹접근성","정보접근성",
    "스크린리더","TTS","STT","자막","대체텍스트","키보드 접근","읽기 지원",
    "디지털 리터러시","미디어 리터러시","AI 리터러시","디지털 시민성","디지털 안전",
    "가짜뉴스","팩트체크","개인정보","프라이버시","저작권",
    "수업혁신","블렌디드","원격수업","온라인수업","하이브리드","스마트기기","태블릿"
]
AI_TERMS = [
    "인공지능","AI","생성형 AI","생성형AI","LLM","대규모언어모델","챗GPT","ChatGPT",
    "에이전트","AI 에이전트","에이전틱","에이전틱AI","Agentic","코파일럿","Copilot",
    "AI 튜터","AI튜터","AI 보조교사","AI 코스웨어","적응형 학습","맞춤형 학습","개별화 학습",
    "평가 자동화","피드백 자동화","수업 설계","학습 지원","학습 분석","추천 시스템",
    "IEP 자동화","개별화교육계획 자동","AAC 생성","접근성 AI","보조공학 AI","특수교육 AI"
]
MUST_HAVE_TERMS = [
    "특수","통합","장애","IEP","AAC","UDL",
    "디지털","디지털교과서","AIDT","에듀테크","리터러시",
    "AI","인공지능","생성형","에이전트","에이전틱"
]

KEYWORD_QUERIES = [
    "특수교육 IEP","보완대체의사소통 AAC","특수교육지원센터 지원인력","긍정적행동지원 PBS",
    "통합교육 협력교수","통합학급 장애학생 지원","합리적 편의 학교",
    "AI 디지털교과서 AIDT","디지털 리터러시 교육","UDL 접근성 에듀테크","학습분석 LMS",
    "에이전틱AI 교육","생성형 AI 교사 수업","AI 튜터 교육","AI 코스웨어"
]

PREFERRED_SOURCE_TERMS = [
    "교육신문","교육플러스","한국교육신문","베리타스알파","대학저널","교수신문",
    "한국대학신문","에듀동아","지디넷코리아","전자신문","조선일보","중앙일보",
    "동아일보","한겨레","경향신문","한국일보","서울신문","국민일보","세계일보",
    "매일경제","한국경제","머니투데이","연합뉴스","뉴스1","뉴시스","조선비즈",
    "인스타그램","Instagram","Nature","ScienceDirect","Springer","Wiley","ERIC",
    "Scopus","KCI","DBpia","RISS"
]
EXCLUDED_SOURCE_TERMS = [
    "교육청","교육지원청","교육지원청","교육연수원","교육지원센터","교육지원단",
    "도교육청","시교육청","교육지원국","교육지원과"
]
EXCLUDED_TITLE_TERMS = [
    "교육청","교육지원청","교육지원청","교육지원센터 소식","교육청 보도자료"
]
KEYWORD_PRIORITY_TERMS = SPECIAL_ED_TERMS + INCLUSION_TERMS + DIGITAL_TERMS + AI_TERMS + MUST_HAVE_TERMS
MAX_KEYWORDS_PER_ITEM = 5

GOOGLE_NEWS_RSS_TEMPLATE = "https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"
SECTION_ORDER = ["특수교육", "통합교육", "디지털교육", "인공지능"]
SECTION_TERMS = OrderedDict(
    [
        ("특수교육", SPECIAL_ED_TERMS),
        ("통합교육", INCLUSION_TERMS),
        ("인공지능", AI_TERMS),
        ("디지털교육", DIGITAL_TERMS),
    ]
)
REQUEST_TIMEOUT = 20
MAX_RETRIES = 3
BACKOFF_SECONDS = [1, 2]
USER_AGENT = "Mozilla/5.0 (compatible; DailyNewsBriefing/1.0; +https://github.com/)"
DEFAULT_LOOKBACK_DAYS = 28


@dataclass
class NewsItem:
    title: str
    link: str
    summary: str
    keywords: List[str]
    source: str
    section: str


@dataclass
class OutputPaths:
    text_path: Path
    html_path: Path
    index_path: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a daily Google News RSS briefing.")
    parser.add_argument("--max-per-section", type=int, default=3)
    parser.add_argument("--max-total", type=int, default=12)
    parser.add_argument("--out-dir", default="output")
    parser.add_argument("--header-suffix", default="디지털 기반 교육 관련 새소식을 전달해드립니다.")
    parser.add_argument("--timezone", default="Asia/Seoul")
    parser.add_argument("--lookback-days", type=int, default=DEFAULT_LOOKBACK_DAYS)
    return parser.parse_args()


def now_in_timezone(timezone_name: str) -> datetime:
    return datetime.now(ZoneInfo(timezone_name))


def build_rss_url(query: str) -> str:
    return GOOGLE_NEWS_RSS_TEMPLATE.format(query=quote_plus(query))


def normalize_text(value: Optional[str]) -> str:
    if not value:
        return ""
    cleaned = html.unescape(value)
    return " ".join(cleaned.split())


def strip_html_tags(value: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", value)
    return normalize_text(without_tags)


def extract_source_name(title: str, entry: feedparser.FeedParserDict) -> str:
    source = entry.get("source", {})
    if isinstance(source, dict):
        source_title = normalize_text(source.get("title", ""))
        if source_title:
            return source_title
    source_title = normalize_text(entry.get("source_title", ""))
    if source_title:
        return source_title
    normalized_title = normalize_text(title)
    if " - " in normalized_title:
        return normalized_title.rsplit(" - ", 1)[-1]
    return ""


def clean_title_for_output(title: str, source_name: str) -> str:
    normalized_title = normalize_text(title)
    if source_name and normalized_title.endswith(f" - {source_name}"):
        return normalized_title[: -(len(source_name) + 3)].strip()
    return normalized_title


def normalize_link(entry: feedparser.FeedParserDict) -> str:
    link = normalize_text(entry.get("link", ""))
    if link:
        return link
    links = entry.get("links", [])
    if links:
        return normalize_text(links[0].get("href", ""))
    return ""


def parse_entry_published_at(entry: feedparser.FeedParserDict, timezone_name: str) -> Optional[datetime]:
    parsed_struct = entry.get("published_parsed") or entry.get("updated_parsed")
    if parsed_struct:
        return datetime(*parsed_struct[:6], tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo(timezone_name))

    raw_value = entry.get("published") or entry.get("updated")
    if not raw_value:
        return None

    try:
        parsed_datetime = date_parser.parse(str(raw_value))
    except (ValueError, TypeError, OverflowError):
        return None

    if parsed_datetime.tzinfo is None:
        parsed_datetime = parsed_datetime.replace(tzinfo=ZoneInfo("UTC"))
    return parsed_datetime.astimezone(ZoneInfo(timezone_name))


def is_within_lookback_window(
    entry: feedparser.FeedParserDict,
    reference_time: datetime,
    lookback_days: int,
    timezone_name: str,
) -> bool:
    published_at = parse_entry_published_at(entry, timezone_name)
    if not published_at:
        return False
    earliest_allowed = reference_time - timedelta(days=lookback_days)
    return earliest_allowed <= published_at <= reference_time


def fetch_feed(url: str) -> feedparser.FeedParserDict:
    headers = {"User-Agent": USER_AGENT}
    last_error: Optional[Exception] = None
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            parsed = feedparser.parse(response.content)
            if getattr(parsed, "bozo", 0):
                raise ValueError(getattr(parsed, "bozo_exception", "Invalid RSS feed"))
            return parsed
        except Exception as exc:
            last_error = exc
            if attempt < MAX_RETRIES - 1:
                sleep_seconds = BACKOFF_SECONDS[min(attempt, len(BACKOFF_SECONDS) - 1)]
                time.sleep(sleep_seconds)
    raise RuntimeError(f"Failed to fetch feed: {url}") from last_error


def contains_any_term(text: str, terms: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(term.lower() in lowered for term in terms)


def is_preferred_source(source_name: str) -> bool:
    return contains_any_term(source_name, PREFERRED_SOURCE_TERMS)


def is_education_office_source(source_name: str, title: str) -> bool:
    return contains_any_term(source_name, EXCLUDED_SOURCE_TERMS) or contains_any_term(title, EXCLUDED_TITLE_TERMS)


def sort_news_priority(items: List[NewsItem]) -> List[NewsItem]:
    def priority(item: NewsItem) -> tuple[int, str]:
        if is_preferred_source(item.source):
            return (0, item.title)
        if is_education_office_source(item.source, item.title):
            return (1, item.title)
        return (2, item.title)

    return sorted(items, key=priority)


def build_summary(title: str, summary: str) -> str:
    normalized_summary = strip_html_tags(summary)
    normalized_title = normalize_text(title)
    if not normalized_summary:
        return normalized_title
    if normalized_summary.lower().startswith(normalized_title.lower()):
        return normalized_summary
    return f"{normalized_title} {normalized_summary}".strip()


def build_keywords(title: str, summary: str, section: str, source_name: str) -> List[str]:
    text = f"{normalize_text(title)} {normalize_text(summary)}"
    found_keywords: List[str] = []
    for term in KEYWORD_PRIORITY_TERMS:
        if term not in found_keywords and term.lower() in text.lower():
            found_keywords.append(term)
        if len(found_keywords) >= MAX_KEYWORDS_PER_ITEM:
            break
    if section not in found_keywords:
        found_keywords.insert(0, section)
    if source_name and source_name not in found_keywords and len(found_keywords) < MAX_KEYWORDS_PER_ITEM:
        found_keywords.append(source_name)
    return found_keywords[:MAX_KEYWORDS_PER_ITEM]


def is_candidate(title: str) -> bool:
    return contains_any_term(title, MUST_HAVE_TERMS) or any(
        contains_any_term(title, terms) for terms in SECTION_TERMS.values()
    )


def classify_item(title: str, summary: str) -> Optional[str]:
    title_text = normalize_text(title)
    summary_text = normalize_text(summary)
    for section_name in ["특수교육", "통합교육", "인공지능", "디지털교육"]:
        terms = SECTION_TERMS[section_name]
        if contains_any_term(title_text, terms):
            return section_name
        if contains_any_term(summary_text, terms):
            return section_name
    return None


def collect_news(reference_time: datetime, lookback_days: int, timezone_name: str) -> List[NewsItem]:
    collected: List[NewsItem] = []
    seen_links = set()

    for query in KEYWORD_QUERIES:
        url = build_rss_url(query)
        try:
            feed = fetch_feed(url)
        except Exception:
            continue

        for entry in feed.entries:
            raw_title = normalize_text(entry.get("title", ""))
            summary = normalize_text(entry.get("summary", entry.get("description", "")))
            link = normalize_link(entry)
            source_name = extract_source_name(raw_title, entry)
            title = clean_title_for_output(raw_title, source_name)
            if not title or not link:
                continue
            if link in seen_links:
                continue
            if not is_candidate(title):
                continue
            if not is_within_lookback_window(entry, reference_time, lookback_days, timezone_name):
                continue
            section = classify_item(title, summary)
            if not section:
                continue
            item_summary = build_summary(title, summary)
            item_keywords = build_keywords(title, item_summary, section, source_name)
            seen_links.add(link)
            collected.append(
                NewsItem(
                    title=title,
                    link=link,
                    summary=item_summary,
                    keywords=item_keywords,
                    source=source_name,
                    section=section,
                )
            )

    return collected


def limit_news(items: List[NewsItem], max_per_section: int, max_total: int) -> Dict[str, List[NewsItem]]:
    limited_by_section: Dict[str, List[NewsItem]] = {section: [] for section in SECTION_ORDER}

    prioritized_items = sort_news_priority(items)

    for item in prioritized_items:
        bucket = limited_by_section[item.section]
        if len(bucket) < max_per_section:
            bucket.append(item)

    final_sections: Dict[str, List[NewsItem]] = {section: [] for section in SECTION_ORDER}
    total_count = 0
    for section in SECTION_ORDER:
        for item in limited_by_section[section]:
            if total_count >= max_total:
                break
            final_sections[section].append(item)
            total_count += 1
    return final_sections


def format_output(target_date: datetime, sections: Dict[str, List[NewsItem]], header_suffix: str) -> str:
    lines: List[str] = []
    header = f"{target_date.year:04d}년 {target_date.month:02d}월 {target_date.day:02d}일 {header_suffix}"
    lines.append(header)
    lines.append("")

    for section in SECTION_ORDER:
        lines.append(f"[{section}]")
        if not sections.get(section):
            lines.append("(없음)")
            lines.append("")
            continue
        for index, item in enumerate(sections[section]):
            lines.append(f"제목 : {item.title}")
            lines.append(f"링크 : {item.link}")
            lines.append(f"요약 : {item.summary}")
            lines.append(f"키워드 : {', '.join(item.keywords)}")
            if index != len(sections[section]) - 1:
                lines.append("")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def format_html_output(target_date: datetime, sections: Dict[str, List[NewsItem]], header_suffix: str) -> str:
    page_title = f"{target_date.year:04d}년 {target_date.month:02d}월 {target_date.day:02d}일 뉴스 브리핑"
    header = f"{target_date.year:04d}년 {target_date.month:02d}월 {target_date.day:02d}일 {header_suffix}"

    section_blocks: List[str] = []
    for section in SECTION_ORDER:
        items = sections.get(section, [])
        if not items:
            body = '<div class="empty">(없음)</div>'
        else:
            cards: List[str] = []
            for item in items:
                keywords = "".join(
                    f'<span class="tag">{html.escape(keyword)}</span>' for keyword in item.keywords
                )
                source_html = ""
                if item.source:
                    source_html = f'<div class="meta">출처: {html.escape(item.source)}</div>'
                cards.append(
                    "\n".join(
                        [
                            '<article class="card">',
                            f'  <h3>{html.escape(item.title)}</h3>',
                            f'  <a class="link" href="{html.escape(item.link)}" target="_blank" rel="noopener noreferrer">기사 바로가기</a>',
                            source_html,
                            f'  <p class="summary">{html.escape(item.summary)}</p>',
                            f'  <div class="tags">{keywords}</div>',
                            '</article>',
                        ]
                    )
                )
            body = "\n".join(cards)
        section_blocks.append(
            "\n".join(
                [
                    '<section class="section">',
                    f'  <h2>{html.escape(section)}</h2>',
                    f'  <div class="section-body">{body}</div>',
                    '</section>',
                ]
            )
        )

    return """<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{page_title}</title>
  <style>
    :root {{ color-scheme: light; }}
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f5f7fb; color: #1f2937; }}
    .container {{ max-width: 980px; margin: 0 auto; padding: 40px 20px 64px; }}
    .hero {{ margin-bottom: 28px; padding: 28px; border-radius: 20px; background: linear-gradient(135deg, #2563eb, #7c3aed); color: white; box-shadow: 0 18px 40px rgba(37, 99, 235, 0.18); }}
    .hero h1 {{ margin: 0 0 8px; font-size: 32px; line-height: 1.3; }}
    .hero p {{ margin: 0; opacity: 0.92; }}
    .section {{ margin-bottom: 24px; }}
    .section h2 {{ margin: 0 0 12px; font-size: 24px; }}
    .section-body {{ display: grid; gap: 14px; }}
    .card {{ background: #ffffff; border-radius: 18px; padding: 20px; box-shadow: 0 12px 28px rgba(15, 23, 42, 0.08); border: 1px solid #e5e7eb; }}
    .card h3 {{ margin: 0 0 10px; font-size: 20px; line-height: 1.5; }}
    .link {{ display: inline-block; margin-bottom: 10px; color: #2563eb; text-decoration: none; font-weight: 600; }}
    .link:hover {{ text-decoration: underline; }}
    .meta {{ margin-bottom: 10px; color: #6b7280; font-size: 14px; }}
    .summary {{ margin: 0 0 12px; line-height: 1.7; color: #374151; }}
    .tags {{ display: flex; flex-wrap: wrap; gap: 8px; }}
    .tag {{ padding: 6px 10px; border-radius: 999px; background: #eff6ff; color: #1d4ed8; font-size: 13px; font-weight: 600; }}
    .empty {{ padding: 20px; border-radius: 16px; background: #ffffff; border: 1px dashed #cbd5e1; color: #64748b; }}
  </style>
</head>
<body>
  <main class="container">
    <header class="hero">
      <h1>{page_title}</h1>
      <p>{header}</p>
    </header>
    {sections_html}
  </main>
</body>
</html>
""".format(
        page_title=html.escape(page_title),
        header=html.escape(header),
        sections_html="\n".join(section_blocks),
    )


def write_output(base_dir: str, target_date: datetime, content: str) -> Path:
    year = f"{target_date.year:04d}"
    month = f"{target_date.month:02d}"
    out_dir = Path(base_dir) / year / month
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = f"daily_news_{target_date.year:04d}{target_date.month:02d}{target_date.day:02d}.txt"
    output_path = out_dir / filename
    output_path.write_text(content, encoding="utf-8")
    return output_path


def write_html_output(base_dir: str, target_date: datetime, content: str) -> Path:
    year = f"{target_date.year:04d}"
    month = f"{target_date.month:02d}"
    out_dir = Path(base_dir) / year / month
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = f"daily_news_{target_date.year:04d}{target_date.month:02d}{target_date.day:02d}.html"
    output_path = out_dir / filename
    output_path.write_text(content, encoding="utf-8")
    return output_path


def write_latest_index(content: str) -> Path:
    output_path = Path("index.html")
    output_path.write_text(content, encoding="utf-8")
    return output_path


def run() -> OutputPaths:
    args = parse_args()
    target_date = now_in_timezone(args.timezone)
    try:
        collected = collect_news(target_date, args.lookback_days, args.timezone)
    except Exception:
        collected = []
    sections = limit_news(collected, args.max_per_section, args.max_total)
    text_content = format_output(target_date, sections, args.header_suffix)
    html_content = format_html_output(target_date, sections, args.header_suffix)
    text_path = write_output(args.out_dir, target_date, text_content)
    html_path = write_html_output(args.out_dir, target_date, html_content)
    index_path = write_latest_index(html_content)
    return OutputPaths(text_path=text_path, html_path=html_path, index_path=index_path)


if __name__ == "__main__":
    output_paths = run()
    print(output_paths.text_path)
    print(output_paths.html_path)
    print(output_paths.index_path)
