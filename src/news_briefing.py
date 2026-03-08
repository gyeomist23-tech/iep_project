import argparse
import html
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
DEFAULT_LOOKBACK_DAYS = 7


@dataclass
class NewsItem:
    title: str
    link: str
    summary: str
    section: str


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
            title = normalize_text(entry.get("title", ""))
            summary = normalize_text(entry.get("summary", entry.get("description", "")))
            link = normalize_link(entry)
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
            seen_links.add(link)
            collected.append(NewsItem(title=title, link=link, summary=summary, section=section))

    return collected


def limit_news(items: List[NewsItem], max_per_section: int, max_total: int) -> Dict[str, List[NewsItem]]:
    limited_by_section: Dict[str, List[NewsItem]] = {section: [] for section in SECTION_ORDER}

    for item in items:
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
            if index != len(sections[section]) - 1:
                lines.append("")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_output(base_dir: str, target_date: datetime, content: str) -> Path:
    year = f"{target_date.year:04d}"
    month = f"{target_date.month:02d}"
    out_dir = Path(base_dir) / year / month
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = f"daily_news_{target_date.year:04d}{target_date.month:02d}{target_date.day:02d}.txt"
    output_path = out_dir / filename
    output_path.write_text(content, encoding="utf-8")
    return output_path


def run() -> Path:
    args = parse_args()
    target_date = now_in_timezone(args.timezone)
    try:
        collected = collect_news(target_date, args.lookback_days, args.timezone)
    except Exception:
        collected = []
    sections = limit_news(collected, args.max_per_section, args.max_total)
    content = format_output(target_date, sections, args.header_suffix)
    return write_output(args.out_dir, target_date, content)


if __name__ == "__main__":
    output_path = run()
    print(output_path)
