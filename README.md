# 특허 문서 분석 프로토타입 (내부 테스트용)

##  프로젝트 개요

본 프로젝트는 PDF 형식의 특허 문서를 업로드하면, Google Gemini 언어 모델을 활용하여 문서 내 주요 정보를 추출하고 구조화된 JSON 형식으로 제공하는 Streamlit 기반 웹 애플리케이션입니다. 추출된 정보와 함께 각 항목에 대한 설명을 확인할 수 있어 특허 분석 업무의 기초 자료로 활용될 수 있습니다.

현재 이 프로젝트는 내부 테스트 및 기능 검증 목적으로 개발되었습니다.

## 주요 기능

* PDF 특허 문서 업로드 기능
* PyMuPDF (fitz)를 이용한 PDF 텍스트 추출
* Langchain 및 Google Gemini API를 통한 특허 정보 구조화 및 JSON 생성
    * 특허 기본 정보 (공개번호, 출원일 등)
    * 재료 기술 관련 정보 (화학식, 물성, 제조법 등)
    * 발명의 핵심 이점 및 요약
* Streamlit을 사용한 웹 인터페이스 제공
    * PDF 원문 페이지별 보기 (이미지 기반)
    * 추출된 JSON 데이터 표시 및 다운로드
    * JSON 각 항목에 대한 설명 및 추출된 값 확인 기능
* 디버깅을 위한 추출 텍스트 및 PDF 페이지 이미지 저장 기능 (선택적)

## 프로젝트 구조

주요 파일 구성은 다음과 같습니다:

* `streamlit_app.py`: Streamlit 애플리케이션의 메인 로직을 포함하는 파일입니다. UI 구성, PDF 처리, LLM 호출 등의 기능을 담당합니다.
* `prompts.py`: LLM에 전달될 기본 프롬프트 (JSON 스키마 포함) 문자열 (`PATENT_DATA_SCHEMA_FOR_LLM_PROMPT_FULL`)을 정의하는 파일입니다.
* `schema_descriptions.py`: 추출된 JSON 데이터의 각 필드에 대한 설명 (`SCHEMA_FIELD_DESCRIPTIONS`)을 담고 있는 딕셔너리 파일입니다.
* `.env`: Google API 키와 같은 환경 변수를 저장하는 파일입니다. (이 파일은 저장소에 포함되지 않아야 합니다.)
* `requirements.txt`: 프로젝트 실행에 필요한 Python 라이브러리 목록입니다.
* `debug_output/`: (선택 사항) PDF 텍스트 추출 및 이미지 변환 시 생성되는 디버그 파일들이 저장되는 디렉터리입니다. (자동 생성)

## 사전 준비 사항

* Python (3.8 이상 권장)
* pip (Python 패키지 관리자)

## 설치 및 설정 방법

1.  **저장소 복제 (Clone Repository):**
    ```bash
    git clone <저장소_URL>
    cd <프로젝트_디렉터리>
    ```

2.  **가상 환경 생성 및 활성화 (권장):**
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **필요 라이브러리 설치:**
    `requirements.txt` 파일이 프로젝트 루트에 있다면 다음 명령어로 설치합니다. (만약 파일이 없다면, 아래 주요 라이브러리를 직접 설치해주세요.)
    ```bash
    pip install streamlit langchain langchain-google-genai google-generativeai python-dotenv PyMuPDF Pillow
    ```
    * `streamlit`
    * `langchain`
    * `langchain-google-genai`
    * `google-generativeai`
    * `python-dotenv`
    * `PyMuPDF` (fitz)
    * `Pillow` (PIL)

4.  **환경 변수 설정 (`.env` 파일 생성):**
    프로젝트 루트 디렉터리에 `.env` 파일을 생성하고, Google Gemini API 사용을 위한 API 키를 다음과 같이 입력합니다.
    ```env
    GOOGLE_API_KEY="여기에_실제_API_키를_입력하세요"
    ```
    **주의:** `.env` 파일은 `.gitignore`에 추가하여 Git 저장소에 포함되지 않도록 하는 것이 좋습니다.

## 애플리케이션 실행 방법

1.  터미널 또는 명령 프롬프트에서 프로젝트 루트 디렉터리로 이동합니다.
2.  가상 환경이 활성화되어 있는지 확인합니다.
3.  다음 명령어를 실행하여 Streamlit 애플리케이션을 시작합니다:
    ```bash
    streamlit run streamlit_app.py
    ```
4.  웹 브라우저가 자동으로 열리거나, 터미널에 표시된 URL (보통 `http://localhost:8501`)로 접속하여 애플리케이션을 사용합니다.

## 사용 방법

1.  애플리케이션이 실행되면, "특허 PDF 파일을 업로드하세요" 섹션을 통해 분석할 PDF 파일을 업로드합니다.
2.  "특허 분석 시작" 버튼을 클릭합니다.
3.  분석이 진행되는 동안 잠시 기다립니다. (PDF 크기 및 내용에 따라 시간이 소요될 수 있습니다.)
4.  분석이 완료되면 결과가 탭 형태로 표시됩니다:
    * **PDF 원문 보기**: 업로드한 PDF를 페이지별 이미지로 볼 수 있습니다.
    * **분석 요약 및 JSON**: 특허 기본 정보, LLM이 생성한 문서 요약, 그리고 추출된 전체 JSON 데이터를 확인할 수 있습니다. JSON 데이터 다운로드도 가능합니다.
    * **항목별 상세 설명**: JSON 데이터의 각 항목(필드)을 선택하면, 해당 항목에 대한 설명과 함께 LLM이 추출한 실제 값을 확인할 수 있습니다.

## 내부 테스트 참고사항

* 본 애플리케이션은 현재 내부 테스트 및 기능 검증 단계에 있습니다.
* LLM의 응답은 프롬프트 및 모델의 특성에 따라 달라질 수 있으며, 항상 100% 정확성을 보장하지는 않습니다.
* `prompts.py` 와 `schema_descriptions.py` 파일의 내용을 수정하여 추출 대상 정보나 설명을 변경/개선할 수 있습니다.
* `SAVE_DEBUG_PDF_IMAGES` 설정을 `streamlit_app.py` 상단에서 `True`로 두면 PDF 처리 과정의 중간 산출물(텍스트, 이미지)이 `debug_output` 폴더에 저장되어 문제 발생 시 분석에 도움이 될 수 있습니다.

---
