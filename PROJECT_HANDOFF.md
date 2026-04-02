# QuantInsight 프로젝트 인수인계 문서

작성 기준 시각: 2026-04-02 (KST)

이 문서는 현재 워크스페이스만 보고 복원한 상태 문서다. 이 폴더에는 Git 이력이 없어서, "지금까지 무엇이 어떻게 진행되었는지"는 코드 구조, 파일 타임스탬프, 빌드 산출물, 실행 흔적을 기반으로 정리했다.

## 1. 한눈에 요약

- 제품명은 `QuantInsight`이고, 현재 폴더명은 `Quant Stock Daily`다.
- 앱 목적은 한국어 UI에서 종목/질문을 입력받아, 웹 검색 결과 + LLM(OpenAI 또는 Gemini)로 단기 주가/섹터 분석 리포트를 생성하는 것이다.
- 실행 대상은 2개다.
  - Windows 데스크톱: Flask 서버 + `pywebview` GUI
  - Android: `python-for-android` webview bootstrap + 로컬 Flask 서버
- 현재 소스는 존재하고 기본 import/syntax는 통과한다.
- EXE/APK 빌드 산출물도 이미 존재한다.
- 다만 Git, README, 테스트, CI가 없어서 "정식 관리 상태"라고 보기는 어렵다.
- 가장 중요한 실무 포인트는 아래 3개다.
  - 현재 소스 수정 시각과 빌드 산출물 시각이 다르다. 즉, 지금 있는 EXE/APK가 최신 소스와 일치한다고 보장할 수 없다.
  - 검색 로직이 DuckDuckGo Lite HTML 스크래핑에 의존한다.
  - `searcher.py`에 연도 `2026`이 하드코딩되어 있어 시간이 지나면 검색 품질이 떨어질 가능성이 높다.

## 2. 현재 확인된 사실

### 2.1 저장소 상태

- 현재 폴더는 Git 저장소가 아니다.
- `.git` 디렉터리가 없어서 커밋 이력, 브랜치, PR, 작업 단위 변경 이력은 확인할 수 없다.
- 문서 파일(`README`, `docs`, `tests`)도 현재 없다.

### 2.2 소스 파일 상태

핵심 소스 파일들은 모두 2026-04-02 09:55(KST)에 수정된 것으로 보인다.

- `main.py`
- `app_server.py`
- `analyzer.py`
- `searcher.py`
- `config_manager.py`
- `templates/index.html`
- `build.bat`
- `build_apk.sh`
- `buildozer.spec`
- `requirements.txt`
- `requirements-mobile.txt`

이 패턴은 "같은 시각에 한 번에 정리/복사/저장된 소스 묶음"일 가능성이 높다.

### 2.3 빌드 산출물 상태

이미 만들어진 산출물은 확인된다.

- 루트 APK: `quantinsight-1.0.0-arm64-v8a-debug.apk`
  - 수정 시각: 2026-02-22 07:11(KST)
  - 크기: 약 12.10 MB
- 데스크톱 EXE: `dist/QuantInsight.exe`
  - 수정 시각: 2026-02-22 02:21(KST)
  - 크기: 약 81.24 MB

즉, 소스는 2026-04-02 기준으로 더 최근이고, 산출물은 2026-02-22 기준이다.

실무적으로는 아래처럼 보는 것이 맞다.

- 소스는 최근에 다시 저장되었거나 수정되었다.
- EXE/APK는 그 이전 시점 결과물이다.
- 따라서 지금 있는 실행 파일이 "현재 소스의 최신 빌드"라고 단정하면 안 된다.

### 2.4 실행 흔적

- `dist/.quant_insight/config.json` 파일이 존재한다.
- 즉, 패키징된 EXE는 적어도 한 번은 실행된 흔적이 있다.
- 반면 프로젝트 루트에는 `.quant_insight`가 없어서, 개발 모드로 실행한 흔적은 현재 워크스페이스 기준으로 보이지 않는다.

### 2.5 Python 환경

- 현재 전역 Python: `3.13.12`
- 현재 `.venv` Python: `3.13.12`
- 그런데 PyInstaller 빌드 산출물 추적 파일(`build/QuantInsight/*`)에는 Python 3.10 경로 흔적이 있다.

즉, 정리하면:

- 현재 작업 환경은 Python 3.13 계열
- 과거 Windows EXE 빌드는 Python 3.10 환경에서 수행된 흔적이 강함
- 재빌드 시 Python 버전 차이로 결과가 달라질 수 있음

## 3. 이 프로젝트가 하는 일

사용자 관점의 핵심 플로우는 아래와 같다.

1. 앱 실행
2. 설정 모달에서 API 키 입력
3. API 키 prefix 또는 실제 모델 조회 결과로 OpenAI/Gemini 제공자 판별
4. 사용 가능한 모델 목록 로드
5. 종목명 또는 자연어 질문 입력
6. 백엔드가 DuckDuckGo Lite 기반 검색 컨텍스트 수집
7. LLM에게 한국어 분석 프롬프트와 검색 결과 전달
8. 결과를 Markdown 리포트로 받아서 UI에 섹션별 카드 형태로 표시
9. References 링크 클릭 시 브라우저로 원문 열기

출력 리포트는 프롬프트상 아래 5개 섹션으로 유도된다.

- Macro Insight
- Stock Screening
- Micro Analysis
- Probability & Reasoning
- References

## 4. 현재 코드 구조

### 4.1 파일 맵

- `main.py`
  - 통합 엔트리 포인트
  - Android 환경 여부를 감지해서 데스크톱/모바일 분기
- `app_server.py`
  - Flask 앱과 REST API 엔드포인트 정의
- `config_manager.py`
  - 설정 파일 저장/로드
  - API provider, API key, model 저장
- `searcher.py`
  - DuckDuckGo Lite HTML 스크래핑
  - 검색 결과를 LLM 프롬프트용 텍스트로 포맷
- `analyzer.py`
  - OpenAI/Gemini 모델 조회
  - 분석 프롬프트 정의
  - 실제 분석 API 호출
- `templates/index.html`
  - 단일 페이지 UI
  - Tailwind CDN + `marked` CDN 사용
- `build.bat`
  - Windows EXE 빌드 스크립트
- `QuantInsight.spec`
  - PyInstaller 설정
- `buildozer.spec`
  - Android 빌드 설정
- `build_apk.sh`
  - Android APK 빌드 및 p4a 사전 패치 스크립트
- `android_res/xml/network_security_config.xml`
  - localhost cleartext 허용용 리소스 파일
- `main_mobile.py`
  - Android용 별도 엔트리 포인트처럼 보이지만 현재 설정상 실제 빌드에서는 제외됨

### 4.2 논리 구조

#### A. 데스크톱 실행

- `main.py`가 Android 환경이 아니면 빈 포트를 하나 찾는다.
- Flask 서버를 백그라운드 스레드로 띄운다.
- `pywebview`가 있으면 앱 창을 띄운다.
- `pywebview` import가 실패하면 시스템 브라우저로 fallback 한다.

#### B. Android 실행

- `main.py`가 `ANDROID_ARGUMENT` 환경변수를 기준으로 Android 실행을 감지한다.
- Android 내부 저장소(`ANDROID_PRIVATE`)에 `quantinsight.log` 로그 파일을 남기도록 되어 있다.
- Flask 앱을 `127.0.0.1:5000`에 띄운다.
- `buildozer.spec`의 `android.webview_url = http://localhost:5000`와 연결된다.

#### C. 분석 요청 처리

- 프론트의 `runAnalysis()`가 `/api/analyze`를 호출한다.
- `app_server.py`가 query와 설정값을 검증한다.
- `searcher.gather_context()`가 검색 컨텍스트를 만든다.
- `analyzer.analyze()`가 provider별 API를 호출한다.
- 응답 Markdown을 프론트에서 `marked`로 렌더링한다.

## 5. 백엔드 API 정리

`app_server.py` 기준 엔드포인트는 아래와 같다.

- `GET /`
  - 메인 UI 렌더링
- `GET /health`
  - 헬스체크
- `GET /api/config`
  - 현재 설정 반환
  - API 키는 `api_key_display`로 마스킹해서 함께 반환
- `POST /api/detect-models`
  - API 키 기반 제공자 감지 + 모델 목록 조회
- `POST /api/settings`
  - provider / api_key / model 저장
- `POST /api/analyze`
  - 실제 검색 + LLM 분석 수행
- `POST /api/open-url`
  - 링크를 시스템 브라우저로 열기

구조는 매우 단순하다.

- 인증/세션 없음
- DB 없음
- 캐시 없음
- 분석 히스토리 저장 없음
- 백엔드는 거의 "설정 저장 + 중계 + 렌더링 지원" 역할

## 6. 프론트엔드 상태

UI는 `templates/index.html` 단일 파일에 몰려 있다.

### 6.1 확인된 기능

- 다크 톤 대시보드형 랜딩 UI
- 예시 질의 버튼 제공
- 분석 중 로딩 상태 문구 순환 표시
- 설정 모달 제공
- API 키 입력 후 모델 자동 조회
- 제공자 badge 표시
- 결과 Markdown을 섹션 카드로 분리 렌더링
- References 링크 클릭 시 `/api/open-url` 호출

### 6.2 프론트 의존성

로컬 번들링이 아니라 CDN에 의존한다.

- Tailwind CDN
- `marked` CDN
- Google Fonts

따라서 이 앱은 아래 두 층에서 네트워크 의존성이 있다.

- 핵심 기능: 검색 + OpenAI/Gemini API
- UI 렌더링 자산: Tailwind/marked/fonts CDN

즉, 네트워크가 막히면 분석뿐 아니라 UI 표현도 일부 깨질 수 있다.

## 7. 검색 로직 정리

`searcher.py`는 DuckDuckGo Lite의 HTML을 POST 요청으로 받아 파싱한다.

### 7.1 흐름

- 기본 검색: 사용자가 입력한 원문 query
- 파생 검색:
  - 한국어면 주가 전망 / 관련주 / 재무제표 / 증권사 리포트
  - 영어면 stock analysis / earnings / price target
- 뉴스 검색:
  - `"{query} 최신 뉴스 2026"`
  - 한국어면 `"{query} 주식 뉴스 시장"`
  - 영어면 `"{query} stock market news"`
- 매크로 보조 검색:
  - 한국어면 글로벌 증시/코스피 코스닥 이번주 검색
  - 영어면 글로벌 증시/Fed 전망 검색

### 7.2 출력 형태

검색 결과는 최종적으로 아래처럼 LLM 프롬프트에 주입된다.

- 제목
- URL
- 스니펫 일부

### 7.3 중요 리스크

- DuckDuckGo Lite HTML 구조가 바뀌면 파서가 깨질 수 있다.
- 검색 실패 시 빈 결과 또는 "검색 결과를 가져올 수 없습니다."로 떨어진다.
- 뉴스 검색어에 `2026`이 하드코딩되어 있어서 내년 이후 품질 저하 가능성이 크다.

## 8. LLM 분석 로직 정리

`analyzer.py`가 핵심 분석 계층이다.

### 8.1 제공자 지원

- OpenAI
- Google Gemini

### 8.2 모델 감지 방식

- OpenAI 키: `sk-` prefix
- Gemini 키: `AI` prefix
- prefix로 판단 못 하면 OpenAI/Gemini 양쪽에 실제 모델 조회를 시도해서 살아있는 쪽을 반환

### 8.3 OpenAI 모델 필터링

모델 조회 후 아래 기준으로 필터링한다.

- `gpt-4`, `gpt-3.5`, `o1`, `o3`, `o4`, `chatgpt-` prefix 허용
- `:`
  포함 모델 제외
- `-realtime`, `-audio`, `-transcribe`, `-search`, `instruct`, `0125`, `0314`, `0613` 포함 모델 제외

### 8.4 Gemini 모델 필터링

- `generateContent` 지원 모델만 허용
- `models/` prefix 제거 후 `gemini` 계열만 허용
- `gemini-X.Y-...` 버전형 모델만 허용

### 8.5 분석 프롬프트 특징

- 한국어 응답 고정
- 1~2주 단기 방향성 분석 강조
- 재무는 하방 리스크 필터, 최신 뉴스/이슈는 단기 모멘텀 근거로 사용하도록 지시
- 반드시 검색 결과에서 확인된 URL만 References에 쓰도록 강하게 제한
- 결과 형식을 5개 섹션 Markdown 구조로 강제

### 8.6 에러 처리

- API 키/Bearer 토큰이 에러 메시지에 섞여 나가지 않도록 정규식으로 마스킹
- OpenAI/Gemini 각각에 대해 400/401/403/404/429/timeout 메시지 분기

## 9. 설정 저장 방식

`config_manager.py` 기준으로 설정 파일은 JSON 1개다.

### 9.1 저장 위치

- Android:
  - `ANDROID_PRIVATE/.quant_insight/config.json`
- frozen EXE:
  - `실행파일 위치/.quant_insight/config.json`
- 개발 모드:
  - `프로젝트 루트/.quant_insight/config.json`

### 9.2 저장 키

- `api_provider`
- `api_key`
- `model`

### 9.3 보안 관점

- API 키는 평문 JSON으로 저장된다.
- UI에서는 마스킹 표시를 제공하지만, 파일 자체는 암호화되지 않는다.
- 다음 작업자가 보안 개선을 할 계획이라면 여기부터 손대면 된다.

## 10. 빌드 체계 정리

### 10.1 Windows EXE 빌드

`build.bat`와 `QuantInsight.spec`가 존재한다.

빌드 특징:

- PyInstaller onefile/windowed
- `webview`, `clr` hidden import 추가
- `webview` 전체 수집
- `templates` 폴더 데이터 포함
- `PyQt6` 제외

의도는 명확하다.

- 데스크톱에서 Flask + pywebview 앱을 단일 EXE로 배포하려는 구조다.

출력 위치:

- `dist/QuantInsight.exe`

### 10.2 Android APK 빌드

`buildozer.spec`와 `build_apk.sh`가 존재한다.

`buildozer.spec` 핵심 설정:

- 패키지명: `quantinsight`
- 버전: `1.0.0`
- bootstrap: `webview`
- webview URL: `http://localhost:5000`
- min API: 24
- target API: 33
- arch: `arm64-v8a`

`build_apk.sh` 핵심 역할:

1. 모바일 의존성 설치
2. buildozer / p4a 다운로드
3. p4a webview bootstrap 사전 패치
4. 클린 빌드
5. 결과 검증

사전 패치 내용:

- AndroidManifest에 `usesCleartextTraffic=true` 주입
- `networkSecurityConfig` 참조 주입
- `network_security_config.xml` 생성
- `AbsoluteLayout` -> `FrameLayout` 치환
- WebView에 DOM storage / database 활성화 코드 삽입 시도

### 10.3 Android 빌드 시 주의점

- `build_apk.sh`는 Linux/WSL용 Bash 스크립트다.
- 스크립트 내부에서 `rm -rf`로 `.buildozer` 하위 산출물을 지운다.
- 즉, "안전한 조회용" 스크립트가 아니라 실제로 빌드 디렉터리를 재생성하는 공격적인 스크립트다.
- Android 패키징 문제를 우회하려고 p4a 내부 파일을 직접 patch하는 방식이라 유지보수성이 낮다.

## 11. `main_mobile.py`의 위치와 의미

`main_mobile.py`는 Android 엔트리 포인트처럼 생겼지만, 현재 `buildozer.spec`의 `source.exclude_patterns`에 `main_mobile.py`가 포함되어 있다.

즉 현재 상태 해석은 아래 둘 중 하나다.

- 예전 실험용 파일이고 지금은 죽은 코드다.
- 혹은 Android 진입 방식을 바꾸다가 남겨둔 파일이다.

현재 실제 모바일 경로는 `main.py` Android 분기 + `buildozer.spec` + `build_apk.sh` 쪽으로 보는 것이 맞다.

## 12. 추정 가능한 진행 이력

이 섹션은 Git이 아니라 파일 타임스탬프 기반 추정이다.

### 추정 1: 2026-02-21 밤 ~ 2026-02-22 새벽

초기 제품 뼈대와 핵심 기능이 구현된 것으로 보인다.

- 검색기(`searcher.py`)
- 분석기(`analyzer.py`)
- 설정 저장(`config_manager.py`)
- Flask 서버(`app_server.py`)
- 통합 엔트리(`main.py`)
- 단일 페이지 UI(`templates/index.html`)

### 추정 2: 2026-02-22 새벽

Windows EXE 빌드가 먼저 진행된 흔적이 있다.

- `dist/QuantInsight.exe` 생성 시각이 2026-02-22 02:21(KST)
- `build/QuantInsight/*` 산출물도 함께 존재

### 추정 3: 2026-02-22 오전

Android 빌드/호환성 패치 작업이 이어진 것으로 보인다.

- `build_apk.sh` 내용이 단순 빌드가 아니라 호환성 우회 스크립트 수준
- 루트 APK 수정 시각이 2026-02-22 07:11(KST)
- 네트워크 보안, cleartext, webview bootstrap patch에 상당한 시간을 쓴 흔적이 있음

### 추정 4: 2026-02-27

가상환경이 세팅/갱신된 흔적이 있다.

- `.venv` 디렉터리 수정 시각이 2026-02-27

### 추정 5: 2026-04-02

소스 파일이 한 번 더 일괄 저장되었다.

- 핵심 소스들이 모두 2026-04-02 09:55(KST)
- 그런데 EXE/APK는 재생성되지 않음

따라서 가장 보수적인 해석은 아래와 같다.

- 앱은 2월에 기능 구현 + 빌드까지 한 번 끝냈다.
- 4월에 소스를 다시 정리하거나 일부 수정했다.
- 그러나 최신 소스 기준 재빌드는 아직 안 했을 가능성이 높다.

## 13. 실제로 확인한 검증 결과

이 문서를 만들면서 확인한 것은 아래까지다.

### 13.1 성공

- `python -m py_compile main.py app_server.py analyzer.py searcher.py config_manager.py main_mobile.py`
  - 성공
- Flask test client로 `GET /health`
  - `200`
- Flask test client로 `GET /`
  - `200`

### 13.2 확인하지 못한 것

- OpenAI 실 API 호출
- Gemini 실 API 호출
- DuckDuckGo 검색 실제 응답 품질
- EXE 실행 결과
- APK 실행 결과
- Android 디바이스/에뮬레이터 실구동
- 현재 소스 기준 재빌드 성공 여부

즉, "코드가 완전히 죽어 있다"는 증거는 없지만, "현재 소스로 끝까지 정상 동작한다"는 실사용 검증도 아직 없다.

## 14. 현재 가장 중요한 리스크 / 기술부채

### 14.1 문서/이력 부재

- Git 없음
- README 없음
- 테스트 없음
- 변경 이력 없음

다음 작업자가 맥락을 잃기 쉬운 구조다.

### 14.2 소스와 산출물 불일치 가능성

- 소스는 2026-04-02
- EXE/APK는 2026-02-22

배포판이 현재 소스 기준 최신이라고 가정하면 위험하다.

### 14.3 검색 연도 하드코딩

`searcher.py`에서 아래 문자열이 고정되어 있다.

- `최신 뉴스 2026`
- `글로벌 증시 전망 이번주 2026`

이건 가까운 시점에는 괜찮아도 시간이 지나면 반드시 문제 된다.

### 14.4 검색기 취약성

- DuckDuckGo Lite HTML 스크래핑은 구조 변경에 취약
- 예외 시 대부분 빈 결과로 조용히 실패

### 14.5 보안

- API 키 평문 저장
- 링크 열기 API는 브라우저 호출만 하지만 사용자에게 노출되는 URL 검증 로직은 별도 없음

### 14.6 프론트 자산의 CDN 의존

- Tailwind CDN
- `marked` CDN
- Google Fonts

내부망/제한망/차단 환경에서는 UI 품질이 바로 떨어질 수 있다.

### 14.7 Android 빌드 유지보수성

- p4a 내부를 직접 patch하는 방식
- bootstrap 구조가 바뀌면 `build_apk.sh`가 바로 깨질 수 있음

### 14.8 dead code / 중복 구조 가능성

- `main_mobile.py`는 현재 사용되지 않는 것으로 보임
- `android_res/xml/network_security_config.xml`는 존재하지만, 실제 빌드 스크립트는 별도로 XML을 생성함

즉, Android 쪽은 "최종 경로"가 아직 완전히 정리되지 않았을 수 있다.

## 15. 다음 AI가 이어서 작업할 때 권장 순서

아래 순서로 진행하면 맥락 복구 비용이 가장 낮다.

### 1단계: 현재 소스 기준 데스크톱 스모크 테스트

권장 순서:

1. `.venv` 활성화 또는 `.\.venv\Scripts\python.exe` 사용
2. `main.py` 실행
3. 설정 모달에서 유효한 API 키 입력
4. 모델 불러오기 확인
5. 샘플 query로 분석 1회 실행

우선 데스크톱부터 확인하는 이유:

- Android보다 빠르다
- 문제 분리하기 쉽다
- 검색/프롬프트/LLM 응답 형식/프론트 렌더링을 한 번에 볼 수 있다

### 2단계: 검색 연도 하드코딩 제거

가장 먼저 손댈 가치가 높은 유지보수 항목이다.

- `2026` 상수를 현재 연도 또는 실제 날짜 기반으로 바꾸기
- 가능하면 "이번주/최근/최신"을 상대 시점으로 처리

### 3단계: EXE 재빌드

현재 소스와 산출물의 시간 차이가 있으므로, 데스크톱 E2E가 통과하면 EXE를 다시 만드는 것이 맞다.

### 4단계: Android 경로 정리

확인할 것:

- `main_mobile.py` 제거 여부
- `android_res`를 실제 build pipeline에 연결할지
- `build_apk.sh`의 p4a patch를 유지할지, buildozer 설정만으로 단순화할지

### 5단계: 최소 테스트/문서 추가

최소한 아래는 필요하다.

- README
- 설정/실행 방법
- 검색기/모델 감지 로직 테스트
- 빌드 절차 문서화

## 16. 다음 작업자가 빠르게 참고할 명령

### 개발 모드 실행

```powershell
.\.venv\Scripts\python.exe main.py
```

또는

```powershell
python main.py
```

### 기본 문법 체크

```powershell
python -m py_compile main.py app_server.py analyzer.py searcher.py config_manager.py main_mobile.py
```

### Windows EXE 빌드

```powershell
.\build.bat
```

### Android APK 빌드

Linux/WSL Bash 환경 전제:

```bash
bash build_apk.sh
```

## 17. 파일별 핵심 참고 포인트

### `main.py`

- Android/desktop 분기 시작점
- 데스크톱은 free port + background Flask + pywebview
- Android는 로그 파일을 남기며 `127.0.0.1:5000`에서 Flask 실행

### `app_server.py`

- API 전체 진입점
- `_resource_path()`로 dev / PyInstaller / Android 경로 차이 흡수
- `_config`를 import 시점에 한 번 로드

### `analyzer.py`

- 이 프로젝트의 "분석 품질" 핵심 파일
- 모델 필터링 정책
- 시스템 프롬프트
- 에러 메시지/키 마스킹

### `searcher.py`

- 이 프로젝트의 "실시간성" 핵심 파일
- 실제로는 검색 품질이 분석 품질을 많이 좌우함
- 연도 하드코딩 존재

### `templates/index.html`

- UI/UX 전체
- 결과 렌더링, 설정 모달, 로딩 상태, 링크 오픈 제어
- 외부 CDN 의존

### `build_apk.sh`

- Android 빌드 우회/패치의 중심
- 빌드 실패가 나면 제일 먼저 보는 파일

## 18. 결론

현재 프로젝트는 "프로토타입을 넘어 실제 실행물까지 한 번 만든 상태"까지는 와 있다. 다만 관리 체계가 약해서 다음 작업자가 바로 들어오면 아래 세 가지에 먼저 걸린다.

- 최신 소스와 산출물의 불일치 가능성
- Android 빌드 경로의 복잡도
- 문서/테스트/Git 이력 부재

반대로 말하면, 이어받는 AI가 가장 먼저 해야 할 일은 새 기능 추가가 아니라 "현재 소스 기준 정상 실행 여부를 재확인하고, 재현 가능성을 복구하는 것"이다.
