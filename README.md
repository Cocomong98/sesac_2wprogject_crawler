# 📈 Solar Pro 2 주식 뉴스 수집 및 요약기

네이버 증권의 종목 뉴스를 실시간으로 수집하고, **Upstage Solar Pro 2 API**를 사용하여 핵심 내용을 요약하는 경량 크롤러입니다. 중복 수집 방지(ID 기반) 및 일별 증분 저장 기능이 포함되어 있습니다.

## 🚀 주요 기능
- **수동 종목 입력**: 원하는 종목 코드(6자리)를 입력하여 즉시 수집 시작.
- **ID 기반 증분 수집**: 네이버 뉴스 고유 ID(oid, aid)를 대조하여 이미 수집된 기사는 건너뛰고 새 기사만 추가.
- **Solar Pro 2 요약**: 긴 기사 본문을 [논조], [관련종목], [핵심내용]으로 깔끔하게 한 문장 요약.
- **일별 데이터 관리**: `news/종목코드_YYYYMMDD.json` 형태로 매일 새로운 파일 생성 및 업데이트.

---

## 💻 윈도우 PC 실행 가이드 (Setup & Run)

다른 윈도우 PC에서 프로젝트를 가져와 실행할 때 아래 순서를 따르세요.

### 1. 환경 준비
*   **Python 설치**: [Python.org](https://www.python.org/)에서 3.10 버전 이상을 설치하세요.
*   **uv 설치**: PowerShell(파워쉘)을 열고 아래 명령어를 입력하여 파이썬 패키지 매니저 `uv`를 설치합니다.
    ```powershell
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```
    *(설치 후 터미널을 껐다 다시 켜주세요.)*

### 2. 프로젝트 가져오기 및 설정
```bash
# 리포지토리 복제
git clone https://github.com/사용자아이디/리포지토리이름.git
cd 리포지토리이름

# 환경 변수 설정
copy .env.example .env