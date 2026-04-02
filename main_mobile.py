"""Android entry point — runs Flask server only (Android WebView connects to it)."""

from app_server import app


def main():
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
