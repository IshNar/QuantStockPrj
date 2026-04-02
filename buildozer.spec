[app]

title = QuantInsight
package.name = quantinsight
package.domain = org.quantinsight

source.dir = .
source.include_exts = py,html,css,js,json,xml
source.include_patterns = templates/*,android_res/**/*
source.exclude_dirs = .buildozer,.venv,build,dist,__pycache__,.quant_insight
source.exclude_patterns = build.bat,*.spec,*.exe,main_mobile.py

version = 1.0.0

requirements = python3,setuptools,flask,werkzeug,jinja2,markupsafe,itsdangerous,click,blinker,requests,urllib3,charset-normalizer,idna,certifi,beautifulsoup4,soupsieve

p4a.bootstrap = webview

android.webview_url = http://localhost:5000

android.permissions = INTERNET
android.api = 33
android.minapi = 24
android.ndk_api = 24
android.arch = arm64-v8a

orientation = portrait
fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 1
