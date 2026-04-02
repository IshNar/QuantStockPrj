import json
import os
import sys


def get_app_dir():
    if "ANDROID_ARGUMENT" in os.environ:
        base = os.environ.get("ANDROID_PRIVATE", os.path.expanduser("~"))
    elif getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    app_dir = os.path.join(base, ".quant_insight")
    os.makedirs(app_dir, exist_ok=True)
    return app_dir


CONFIG_FILE = os.path.join(get_app_dir(), "config.json")

DEFAULT_CONFIG = {
    "api_provider": "openai",
    "api_key": "",
    "model": "",
}


def load_config():
    if not os.path.exists(CONFIG_FILE):
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        for key in DEFAULT_CONFIG:
            if key not in config:
                config[key] = DEFAULT_CONFIG[key]
        return config
    except Exception:
        return DEFAULT_CONFIG.copy()


def save_config(config):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
