"""Flask REST API server — shared by desktop (pywebview) and mobile (Android WebView)."""

import os
import sys
import webbrowser
from flask import Flask, jsonify, request, render_template
from config_manager import load_config, save_config
from searcher import gather_context
from analyzer import analyze, fetch_models, detect_provider


def _resource_path(relative):
    """Resolve path for dev, PyInstaller, and Android environments."""
    if getattr(sys, "_MEIPASS", None):
        return os.path.join(sys._MEIPASS, relative)
    if "ANDROID_ARGUMENT" in os.environ:
        return os.path.join(os.environ["ANDROID_ARGUMENT"], relative)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative)


app = Flask(__name__, template_folder=_resource_path("templates"))
_config = load_config()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health")
def health():
    return "OK", 200


# ── Config endpoints ────────────────────────────────────────────

@app.route("/api/config", methods=["GET"])
def get_config():
    cfg = _config.copy()
    if cfg.get("api_key"):
        key = cfg["api_key"]
        cfg["api_key_display"] = key[:6] + "\u2022" * 10 + key[-4:] if len(key) > 12 else "\u2022" * len(key)
    else:
        cfg["api_key_display"] = ""
    return jsonify(cfg)


@app.route("/api/detect-models", methods=["POST"])
def detect_and_fetch_models():
    data = request.get_json(silent=True) or {}
    api_key = data.get("api_key", "").strip()
    if not api_key or len(api_key) < 5:
        return jsonify(error=True, message="API 키를 입력해주세요.")

    provider = detect_provider(api_key)
    if not provider:
        for prov in ("openai", "gemini"):
            result = fetch_models(prov, api_key)
            if not result.get("error"):
                return jsonify(error=False, provider=prov, models=result["models"])
        return jsonify(error=True, message="API 키를 인식할 수 없습니다. OpenAI(sk-...) 또는 Gemini(AI...) 키를 확인해주세요.")

    result = fetch_models(provider, api_key)
    if result.get("error"):
        return jsonify(error=True, message=result["message"])
    return jsonify(error=False, provider=provider, models=result["models"])


@app.route("/api/settings", methods=["POST"])
def save_settings():
    data = request.get_json(silent=True) or {}
    _config["api_provider"] = data.get("provider", _config.get("api_provider"))
    _config["api_key"] = data.get("api_key", _config.get("api_key"))
    _config["model"] = data.get("model", _config.get("model"))
    save_config(_config)
    return jsonify(success=True)


# ── Analysis endpoint ───────────────────────────────────────────

@app.route("/api/analyze", methods=["POST"])
def run_analysis():
    data = request.get_json(silent=True) or {}
    query = data.get("query", "").strip()

    if not _config.get("api_key"):
        return jsonify(error=True, message="API 키가 설정되지 않았습니다. ⚙️ 설정에서 API 키를 입력해주세요.")
    if not _config.get("model"):
        return jsonify(error=True, message="모델이 선택되지 않았습니다. ⚙️ 설정에서 모델을 선택해주세요.")
    if not query:
        return jsonify(error=True, message="검색어를 입력해주세요.")

    try:
        search_context = gather_context(query)
    except Exception:
        search_context = "웹 검색 결과를 가져올 수 없습니다."

    try:
        report = analyze(
            user_query=query,
            search_context=search_context,
            api_provider=_config["api_provider"],
            api_key=_config["api_key"],
            model=_config["model"],
        )
        return jsonify(error=False, report=report)
    except Exception as e:
        return jsonify(error=True, message=f"분석 중 오류가 발생했습니다: {str(e)}")


# ── Utility ─────────────────────────────────────────────────────

@app.route("/api/open-url", methods=["POST"])
def open_url():
    data = request.get_json(silent=True) or {}
    url = data.get("url", "")
    if url:
        webbrowser.open(url)
    return jsonify(success=True)
