"""Unified entry point — Desktop (pywebview) and Android (p4a webview bootstrap)."""

import os
import sys

ON_ANDROID = "ANDROID_ARGUMENT" in os.environ

if ON_ANDROID:
    import logging

    _log_dir = os.environ.get("ANDROID_PRIVATE", ".")
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(os.path.join(_log_dir, "quantinsight.log")),
            logging.StreamHandler(),
        ],
    )
    _logger = logging.getLogger("QuantInsight")
    _logger.info("=== QuantInsight Android start ===")
    _logger.info("ANDROID_ARGUMENT=%s", os.environ.get("ANDROID_ARGUMENT"))
    _logger.info("ANDROID_PRIVATE=%s", os.environ.get("ANDROID_PRIVATE"))
    _logger.info("Python %s", sys.version)

    try:
        from app_server import app

        _logger.info("Flask app imported OK — starting on :5000")
        app.run(host="127.0.0.1", port=5000, debug=False)
    except Exception:
        _logger.exception("Fatal error during Flask startup")
        raise
else:
    from app_server import app
    import threading
    import socket

    def _find_free_port():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]

    def main():
        port = _find_free_port()
        url = f"http://127.0.0.1:{port}"

        server = threading.Thread(
            target=lambda: app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False),
            daemon=True,
        )
        server.start()

        try:
            import webview

            webview.create_window(
                title="\ud034\ud2b8 \uc778\uc0ac\uc774\ud2b8",
                url=url,
                width=1280,
                height=860,
                min_size=(800, 600),
                text_select=True,
            )
            webview.start(debug=False)
        except ImportError:
            import webbrowser

            webbrowser.open(url)
            print(f"\uc11c\ubc84 \uc2e4\ud589 \uc911: {url}")
            server.join()

    main()
