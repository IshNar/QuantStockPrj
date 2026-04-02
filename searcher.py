"""Web search module using DuckDuckGo Lite (HTML scraping) for reliable Korean search."""

import requests
from bs4 import BeautifulSoup

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}

DDG_LITE_URL = "https://lite.duckduckgo.com/lite/"


def search_web(query, max_results=10):
    """Search DuckDuckGo Lite and return results with title, URL, snippet."""
    try:
        resp = requests.post(DDG_LITE_URL, data={"q": query}, headers=_HEADERS, timeout=15)
        if resp.status_code != 200:
            return []
        return _parse_ddg_lite(resp.text, max_results)
    except Exception:
        return []


def search_news(query, max_results=10):
    """Search for news by appending time-sensitive keywords."""
    return search_web(f"{query} 최신 뉴스 2026", max_results=max_results)


def _parse_ddg_lite(html, max_results):
    soup = BeautifulSoup(html, "html.parser")
    results = []
    rows = soup.select("table:nth-of-type(2) tr") or soup.select("table tr")

    current = {}
    for tr in rows:
        a = tr.select_one("a.result-link")
        if a:
            if current.get("href"):
                results.append(current)
                if len(results) >= max_results:
                    break
            current = {
                "title": a.get_text(strip=True),
                "href": a.get("href", ""),
                "body": "",
            }
        else:
            snippet_td = tr.select_one("td.result-snippet")
            if snippet_td and current:
                current["body"] = snippet_td.get_text(strip=True)

    if current.get("href") and len(results) < max_results:
        results.append(current)

    return results


def _has_korean(text):
    return any("\uac00" <= ch <= "\ud7a3" for ch in text)


def gather_context(user_query):
    """Build comprehensive search context adaptive to user's query language and topic."""
    all_results = []
    is_korean = _has_korean(user_query)

    # ── 1. Direct search: user's exact query (most important) ──
    all_results.extend(search_web(user_query, max_results=10))

    # ── 2. Financial/stock-focused variations ──
    if is_korean:
        variations = [
            f"{user_query} 주가 전망 분석",
            f"{user_query} 관련주 테마주 종목 대장주",
            f"{user_query} 재무제표 실적 매출",
            f"{user_query} 증권사 리포트 목표가",
        ]
    else:
        variations = [
            f"{user_query} stock analysis forecast",
            f"{user_query} financial fundamentals earnings",
            f"{user_query} investment outlook price target",
        ]

    for q in variations:
        all_results.extend(search_web(q, max_results=5))

    # ── 3. News: most recent articles ──
    all_results.extend(search_news(user_query, max_results=10))

    if is_korean:
        all_results.extend(search_news(f"{user_query} 주식 뉴스 시장", max_results=5))
    else:
        all_results.extend(search_news(f"{user_query} stock market news", max_results=5))

    # ── 4. Macro context (supplementary) ──
    if is_korean:
        macro = ["글로벌 증시 전망 이번주 2026", "코스피 코스닥 시장 동향 이번주"]
    else:
        macro = ["global stock market outlook this week", "Fed interest rate economy outlook"]
    for q in macro:
        all_results.extend(search_web(q, max_results=4))

    return format_results(all_results)


def format_results(results):
    if not results:
        return "검색 결과를 가져올 수 없습니다."

    seen_urls = set()
    formatted = []
    for r in results:
        url = r.get("href") or r.get("url", "")
        if url in seen_urls or not url:
            continue
        seen_urls.add(url)

        title = r.get("title", "N/A")
        body = r.get("body") or r.get("excerpt", "")
        date = r.get("date", "")

        entry = f"- **{title}**"
        if date:
            entry += f" ({date})"
        entry += f"\n  URL: {url}"
        if body:
            entry += f"\n  {body[:400]}"
        formatted.append(entry)

    return "\n\n".join(formatted)
