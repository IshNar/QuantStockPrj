import re
import requests

OPENAI_CHAT_PREFIXES = ("gpt-4", "gpt-3.5", "o1", "o3", "o4", "chatgpt-")
OPENAI_EXCLUDE_PATTERNS = (
    "-realtime", "-audio", "-transcribe", "-search",
    "instruct", "0125", "0314", "0613",
)

_KEY_PATTERN = re.compile(r"(key=)[^\s&]+", re.IGNORECASE)
_BEARER_PATTERN = re.compile(r"(Bearer\s+)\S+", re.IGNORECASE)


def _sanitize(msg):
    """Strip API keys from error messages to prevent accidental exposure."""
    msg = _KEY_PATTERN.sub(r"\1***", msg)
    msg = _BEARER_PATTERN.sub(r"\1***", msg)
    return msg


def fetch_models(api_provider, api_key):
    if api_provider == "openai":
        return _fetch_openai_models(api_key)
    elif api_provider == "gemini":
        return _fetch_gemini_models(api_key)
    return {"error": True, "message": "지원하지 않는 제공자입니다."}


def _fetch_openai_models(api_key):
    url = "https://api.openai.com/v1/models"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        models = []
        for m in data.get("data", []):
            mid = m["id"]
            if not any(mid.startswith(p) for p in OPENAI_CHAT_PREFIXES):
                continue
            if ":" in mid:
                continue
            if any(ex in mid for ex in OPENAI_EXCLUDE_PATTERNS):
                continue
            models.append(mid)
        models.sort(key=_openai_sort_key)
        return {"error": False, "models": models}
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response else "?"
        if status == 401:
            return {"error": True, "message": "API 키가 유효하지 않습니다."}
        return {"error": True, "message": f"HTTP {status} 오류가 발생했습니다."}
    except Exception as e:
        return {"error": True, "message": _sanitize(str(e))}


def _openai_sort_key(model_id):
    priority = {
        "chatgpt-4o-latest": 0,
        "gpt-4.1": 1, "gpt-4.1-mini": 2, "gpt-4.1-nano": 3,
        "gpt-4o": 10, "gpt-4o-mini": 11,
        "o4-mini": 20, "o3": 25, "o3-mini": 26, "o1": 30, "o1-mini": 31,
    }
    return priority.get(model_id, 50)


_GEMINI_VERSIONED = re.compile(r"^gemini-(\d+\.\d+)-")


def _fetch_gemini_models(api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}&pageSize=100"
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        models = []
        for m in data.get("models", []):
            name = m.get("name", "").replace("models/", "")
            supported = m.get("supportedGenerationMethods", [])
            if "generateContent" not in supported:
                continue
            if not name.startswith("gemini"):
                continue
            if not _GEMINI_VERSIONED.match(name):
                continue
            models.append(name)
        models.sort(key=_gemini_sort_key)
        return {"error": False, "models": models}
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response else "?"
        if status in (400, 403):
            return {"error": True, "message": "API 키가 유효하지 않습니다."}
        return {"error": True, "message": f"HTTP {status} 오류가 발생했습니다."}
    except Exception as e:
        return {"error": True, "message": _sanitize(str(e))}


def _gemini_sort_key(model_id):
    if "2.5-pro" in model_id:
        return 0
    if "2.5-flash" in model_id:
        return 1
    if "2.0-flash" in model_id:
        return 5
    if "1.5-pro" in model_id:
        return 10
    if "1.5-flash" in model_id:
        return 11
    return 50


def detect_provider(api_key):
    if not api_key:
        return None
    if api_key.startswith("sk-"):
        return "openai"
    if api_key.startswith("AI"):
        return "gemini"
    return None


SYSTEM_PROMPT = """당신은 20년 경력의 월가 수석 퀀트 애널리스트입니다. 거시경제(Macro)의 본질적 흐름을 읽고, 기업의 재무 펀더멘털(Micro)과 단기 모멘텀(뉴스/센티먼트)을 결합하여 시장의 확률적 우위를 도출하는 전문가입니다.

[Objective]
현재 시점 기준의 글로벌 이슈를 바탕으로 향후 1~2주간에 영향을 받을 주식들의 단기 방향성(상승/하락)을 확률(%)로 제시하고, 그 근거를 재무제표와 최신 뉴스를 융합하여 심층적으로 분석합니다.

[Strict Rules]
1. 분석에 사용된 모든 데이터(재무제표 수치, 거시 지표, 뉴스 기사)는 반드시 아래 제공된 웹 검색 결과에서 확인된 실제 URL을 출처로 명시해야 합니다. 존재하지 않는 URL을 절대 만들어내지 마십시오.
2. 1~2주의 단기 예측이므로 '재무제표(장기 가치)'는 기업의 하방 경직성을 확인하는 리스크 필터로 사용하고, '최신 뉴스 및 글로벌 이슈(단기 모멘텀 및 센티먼트)'를 주된 단기 방향성 근거로 삼으십시오.
3. 제공된 웹 검색 결과를 적극적으로 활용하여 분석하십시오. 검색 결과에 포함된 URL만 References에 사용하십시오.

[Output Format - 반드시 아래 5단계 Markdown 구조로 답변]

## 🌍 Macro Insight (글로벌 이슈 본질 분석)
현재 시장을 지배하는 핵심 글로벌 매크로 이슈 2~3가지를 분석하고, 이것이 자본 시장의 유동성과 섹터 흐름에 미치는 본질적인 영향을 서술합니다.

## 🎯 Stock Screening (상승/하락 모멘텀 종목 도출)
위 이슈를 바탕으로 향후 1~2주간 가장 강한 상승 모멘텀을 받을 종목 1개와 하락 리스크가 큰 종목 1개를 선정합니다. 사용자가 특정 종목을 질문한 경우, 해당 종목이 속한 섹터의 경쟁사 대비 매력도로 분석합니다.

## 📊 Micro Analysis (펀더멘털 & 센티먼트 융합)
- **재무 분석**: 선정된 종목의 최근 분기 실적(매출성장률, 영업이익률, PER/PBR, FCF 등) 핵심 수치 기반 기초 체력 진단
- **뉴스 분석**: 최근 1주일 내 글로벌 뉴스 센티먼트(긍정/부정 비율) 및 기관 투자자 동향

## 🎲 Probability & Reasoning (확률 및 퀀트적 근거)
향후 1~2주간의 상승/하락 확률을 정확한 퍼센트(%)로 제시합니다. 재무적 필터링과 뉴스 모멘텀이 어떻게 상호작용했는지 논리적으로 심층 분석합니다.

## 🔗 References (공식 참조 링크)
분석에 사용된 공식 뉴스 기사, 재무 데이터 출처의 정확한 URL을 불릿 포인트로 나열합니다.

모든 답변은 반드시 한국어로 작성합니다."""


def analyze(user_query, search_context, api_provider, api_key, model):
    if api_provider == "openai":
        return _call_openai(user_query, search_context, api_key, model)
    elif api_provider == "gemini":
        return _call_gemini(user_query, search_context, api_key, model)
    else:
        return "지원하지 않는 API 제공자입니다."


def _call_openai(user_query, search_context, api_key, model):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    user_message = f"""## 웹 검색 결과 (실시간 데이터)
아래는 현재 시점에서 수집된 실제 웹 검색 결과입니다. 이 데이터를 기반으로 분석하십시오.

{search_context}

---

## 사용자 질문
{user_query}"""

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.7,
        "max_tokens": 4096,
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response else "Unknown"
        if status == 401:
            return "❌ **API 키 오류**: OpenAI API 키가 유효하지 않습니다. 설정에서 확인해주세요."
        elif status == 429:
            return "❌ **요청 제한 초과**: API 호출 한도에 도달했습니다. 잠시 후 다시 시도하거나, 설정에서 다른 모델을 선택해주세요."
        elif status == 404:
            return f"❌ **모델 오류**: 모델 '{model}'을(를) 찾을 수 없습니다. 설정에서 모델을 변경해주세요."
        return f"❌ **API 오류** (HTTP {status}): 요청 처리에 실패했습니다."
    except requests.exceptions.Timeout:
        return "❌ **시간 초과**: API 응답이 너무 오래 걸립니다. 네트워크를 확인하고 다시 시도해주세요."
    except Exception as e:
        return f"❌ **오류 발생**: {_sanitize(str(e))}"


def _call_gemini(user_query, search_context, api_key, model):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    combined_prompt = f"""{SYSTEM_PROMPT}

## 웹 검색 결과 (실시간 데이터)
아래는 현재 시점에서 수집된 실제 웹 검색 결과입니다. 이 데이터를 기반으로 분석하십시오.

{search_context}

---

## 사용자 질문
{user_query}"""

    payload = {
        "contents": [{"parts": [{"text": combined_prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 4096,
        },
    }

    try:
        resp = requests.post(url, json=payload, params={"key": api_key}, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        candidates = data.get("candidates", [])
        if not candidates:
            block_reason = data.get("promptFeedback", {}).get("blockReason", "Unknown")
            return f"❌ **콘텐츠 차단**: Gemini가 응답을 차단했습니다. 사유: {block_reason}"
        return candidates[0]["content"]["parts"][0]["text"]
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response else "Unknown"
        if status == 400:
            return "❌ **요청 오류**: 모델이 해당 요청을 처리할 수 없습니다. 설정에서 다른 모델을 선택해주세요."
        elif status == 403:
            return "❌ **API 키 오류**: Gemini API 키가 유효하지 않거나 권한이 부족합니다."
        elif status == 429:
            return f"❌ **요청 제한 초과**: 모델 '{model}'의 호출 한도에 도달했습니다.\n\n**해결 방법**: 설정에서 **gemini-2.0-flash** 또는 **gemini-2.5-flash** 등 무료 한도가 높은 모델로 변경해주세요."
        return f"❌ **API 오류** (HTTP {status}): 요청 처리에 실패했습니다."
    except requests.exceptions.Timeout:
        return "❌ **시간 초과**: API 응답이 너무 오래 걸립니다. 네트워크를 확인하고 다시 시도해주세요."
    except Exception as e:
        return f"❌ **오류 발생**: {_sanitize(str(e))}"
