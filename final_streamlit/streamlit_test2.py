# streamlit_test_refactored_v4_no_structured_output.py
import streamlit as st
import os
import fitz  # PyMuPDF
from PIL import Image
import io
import json
import traceback # 오류 추적을 위한 traceback 모듈 임포트
from dotenv import load_dotenv # 환경 변수 로드를 위한 dotenv 모듈 임포트
from typing import List, Tuple, Dict, Any, Optional # 타입 힌팅을 위한 typing 모듈 임포트

from langchain_google_genai import ChatGoogleGenerativeAI # Langchain Google Generative AI 모델 임포트
from langchain_core.messages import HumanMessage # Langchain 메시지 타입 임포트
from langchain_core.outputs import LLMResult # LLM 응답 결과 타입을 위한 임포트 (오류 처리 시 사용 가능)

# --- 외부 파일에서 프롬프트 및 스키마 설명 임포트 ---
try:
    # prompts.py에서 LLM에 전달할 프롬프트 (개선된 버전 사용 가정)
    from prompts import PATENT_DATA_SCHEMA_FOR_LLM_PROMPT_FULL
    # schema_descriptions.py에서 UI에 표시할 각 필드에 대한 한글 설명 (개선된 버전 사용 가정)
    from schema_descriptions import SCHEMA_FIELD_DESCRIPTIONS
except ImportError:
    st.error("오류: `prompts.py` 또는 `schema_descriptions.py` 파일을 찾을 수 없습니다. 해당 파일들이 이 스크립트와 동일한 디렉토리에 있는지 확인해주세요.")
    PATENT_DATA_SCHEMA_FOR_LLM_PROMPT_FULL = "{}" # LLM 호출 시도를 위해 최소한의 빈 JSON 형태라도 설정
    SCHEMA_FIELD_DESCRIPTIONS = {} # 빈 딕셔너리로 설정
    # st.stop() # 또는 앱 실행을 중단할 수 있음

# --- 전역 설정 및 상수 ---
class AppConfig:
    # 사용할 Gemini 모델 이름
    GEMINI_MODEL_NAME = "gemini-2.5-flash-preview-05-20" # 혹은 "gemini-1.5-pro-latest" 등 사용 가능한 최신 모델
    # 모델의 창의성/일관성 조절 (0.0은 가장 일관성 있는 답변)
    TEMPERATURE = 0.0
    # LLM API 요청 타임아웃 시간 (초 단위, 예: 20분)
    API_REQUEST_TIMEOUT_STRUCTURED_DATA = 1200
    # PDF 페이지 이미지 뷰어용 DPI (해상도)
    DEFAULT_DPI_PDF_PREVIEW = 150

class SessionStateKeys:
    # Streamlit 세션 상태에서 사용할 키 값들 정의
    ANALYSIS_COMPLETE = 'analysis_complete' # 분석 완료 여부
    STRUCTURED_DATA = 'structured_data'     # 추출된 구조화 데이터
    PDF_PAGE_TEXTS = 'pdf_page_texts'       # PDF 페이지별 텍스트 리스트
    CURRENT_PAGE_PDF_VIEW = 'current_page_for_pdf_view' # PDF 뷰어 현재 페이지 번호
    ORIGINAL_FILENAME = 'original_filename' # 원본 파일명
    PDF_BYTES_FOR_VIEWER = 'pdf_bytes_for_viewer' # PDF 뷰어용 바이트 데이터

# --- 환경 변수 로드 및 LLM 초기화 ---
load_dotenv() # .env 파일에서 환경 변수 로드
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") # GOOGLE_API_KEY 환경 변수 가져오기
llm: Optional[ChatGoogleGenerativeAI] = None # LLM 객체 초기화

if not GOOGLE_API_KEY:
    # 이 메시지는 개발 중 콘솔에 출력됨
    # Streamlit 앱에서는 분석 시작 시 llm 객체가 None이면 UI에 오류를 표시함
    print("치명적 오류: GOOGLE_API_KEY 환경변수가 설정되지 않았습니다. 앱 실행 시 오류가 발생할 수 있습니다.")
else:
    try:
        # ChatGoogleGenerativeAI 객체 생성 (JSON 모드 설정 제거)
        llm = ChatGoogleGenerativeAI(
            model=AppConfig.GEMINI_MODEL_NAME,
            google_api_key=GOOGLE_API_KEY,
            temperature=AppConfig.TEMPERATURE
            # model_kwargs={"generation_config": {"response_mime_type": "application/json"}} # JSON 모드 설정 제거
        )
        print(f"Gemini 모델 '{AppConfig.GEMINI_MODEL_NAME}' 초기화 성공 (일반 텍스트 모드).")
    except Exception as e_model_init:
        print(f"Gemini 모델 '{AppConfig.GEMINI_MODEL_NAME}' 초기화 중 심각한 오류: {e_model_init}")
        llm = None # 초기화 실패 시 llm을 None으로 확실히 설정

# --- PDF 처리 유틸리티 ---
def convert_pdf_to_text(
    uploaded_file_content: bytes # 업로드된 파일의 바이트 내용
) -> Tuple[List[str], str]:
    """
    PDF의 각 페이지에서 텍스트를 추출합니다.
    페이지별 텍스트 리스트와 전체 연결된 텍스트를 반환합니다.
    """
    full_text_for_extraction = "" # 전체 텍스트를 저장할 변수
    page_texts = [] # 페이지별 텍스트를 저장할 리스트

    try:
        doc = fitz.open(stream=uploaded_file_content, filetype="pdf") # 바이트 스트림으로 PDF 문서 열기
        for page_num_idx, page in enumerate(doc): # 각 페이지에 대해 반복 (페이지 객체 직접 사용)
            actual_page_num = page_num_idx + 1 # 실제 페이지 번호 (1부터 시작)
            try:
                text = page.get_text("text", sort=True) # 페이지에서 텍스트 추출 (정렬 옵션 사용)
            except Exception as e_page_text:
                st.warning(f"페이지 {actual_page_num} 텍스트 추출 오류: {e_page_text}")
                text = "" # 오류 발생 시 해당 페이지 텍스트는 비움

            page_texts.append(text) # 추출된 텍스트를 리스트에 추가
            # 전체 텍스트에 페이지 구분자와 함께 추가
            full_text_for_extraction += f"\n\n<<<<< PAGE {actual_page_num} / {len(doc)} >>>>>\n\n{text}"
        doc.close() # PDF 문서 닫기
        return page_texts, full_text_for_extraction # 페이지별 텍스트 리스트와 전체 텍스트 반환
    except Exception as e:
        st.error(f"PyMuPDF로 PDF 처리 중 오류: {e}")
        return [], "" # 오류 발생 시 빈 리스트와 빈 문자열 반환

# --- LLM 상호작용 유틸리티 ---
def _build_llm_extraction_prompt(full_patent_text: str, pdf_filename: str) -> str:
    """LLM에 전달할 전체 프롬프트를 구성합니다."""
    return (
        PATENT_DATA_SCHEMA_FOR_LLM_PROMPT_FULL +
        f"\n\nIMPORTANT INSTRUCTIONS FOR THIS SPECIFIC TASK:\n" +
        f"- The 'source_file_name' field in the JSON output MUST be exactly: \"{pdf_filename}\"\n" +
        "Here is the full patent text to analyze:\n\n--- BEGIN PATENT TEXT ---\n" +
        full_patent_text +
        "\n--- END PATENT TEXT ---\n\n" +
        # JSON 모드를 사용하지 않으므로, LLM이 JSON을 포함한 텍스트를 반환하도록 유도
        "Based on the schema and instructions provided above, generate a response containing the JSON object. The JSON object should be enclosed in ```json ... ```."
    )

def _parse_llm_text_response(response_content_str: str, pdf_filename: str, full_patent_text_for_lang_detect: str) -> Dict[str, Any]:
    """
    LLM의 일반 텍스트 응답에서 JSON 객체를 추출하고 파싱합니다.
    필수 기본 필드들이 있는지 확인 및 기본값을 설정합니다.
    """
    # 응답 문자열이 비어있는 경우 먼저 확인
    if not response_content_str or not response_content_str.strip():
        st.error("LLM 응답이 비어있습니다.")
        return {"error": "LLM response is empty", "raw_response": response_content_str, "source_file_name": pdf_filename, "language_of_document": "Unknown"}

    # ```json ... ``` 블록 추출
    json_block_match = None
    try:
        # 정규 표현식 대신 단순 문자열 검색으로 변경 (더 견고할 수 있음)
        start_index = response_content_str.find("```json")
        if start_index != -1:
            start_index += len("```json") # "```json" 이후부터 시작
            end_index = response_content_str.find("```", start_index)
            if end_index != -1:
                json_block_str = response_content_str[start_index:end_index].strip()
                if json_block_str: # 추출된 JSON 문자열이 비어있지 않은지 확인
                    json_block_match = json_block_str
    except Exception as e_find: # 문자열 검색 중 예외 발생 시 (일반적이지 않음)
         st.warning(f"LLM 응답에서 JSON 블록 검색 중 오류: {e_find}")
         json_block_match = None


    if not json_block_match:
        # 만약 ```json ... ``` 블록이 없다면, 응답 전체를 JSON으로 가정하고 파싱 시도
        # 또는 다른 휴리스틱 (예: 첫 { 와 마지막 } 사이)을 사용할 수 있으나, 우선 전체 시도
        st.warning("LLM 응답에서 ```json ... ``` 블록을 찾지 못했습니다. 응답 전체를 JSON으로 간주하고 파싱을 시도합니다.")
        json_to_parse = response_content_str.strip()
        # 응답 전체가 JSON이 아닐 가능성이 높으므로, 간단한 유효성 검사
        if not json_to_parse.startswith("{") or not json_to_parse.endswith("}"):
            st.error("LLM 응답이 유효한 JSON 형식이 아닙니다 (```json ... ``` 블록 없음, 전체 내용도 JSON 아님).")
            st.text_area("LLM 원본 응답 (형식 오류)", response_content_str[:3000], height=150)
            return {"error": "LLM response does not contain a JSON block and is not a valid JSON object itself.", "raw_response": response_content_str, "source_file_name": pdf_filename, "language_of_document": "Unknown"}
    else:
        json_to_parse = json_block_match


    try:
        structured_data = json.loads(json_to_parse)
    except json.JSONDecodeError as json_e:
        st.error(f"LLM 응답 JSON 파싱 오류: {json_e}")
        st.text_area("파싱 시도한 JSON 부분", json_to_parse[:3000], height=150)
        st.text_area("LLM 전체 원본 응답 (파싱 실패 시)", response_content_str[:3000], height=150)
        return {"error": "Failed to parse extracted JSON from LLM response", "extracted_json_to_parse": json_to_parse, "raw_response": response_content_str, "source_file_name": pdf_filename, "language_of_document": "Unknown"}
    except TypeError as type_e:
        st.error(f"LLM 응답 JSON 파싱 중 TypeError: {type_e}")
        st.text_area("LLM 원본 응답 (TypeError)", str(response_content_str)[:3000], height=300)
        return {"error": "LLM response was not suitable for JSON parsing (e.g. None type)", "raw_response": str(response_content_str), "source_file_name": pdf_filename, "language_of_document": "Unknown"}

    # 필수 필드가 누락된 경우 기본값 설정
    if "source_file_name" not in structured_data:
        structured_data["source_file_name"] = pdf_filename
    if "language_of_document" not in structured_data or not structured_data["language_of_document"]:
        if any(char.isalpha() and ord(char) > 127 for char in full_patent_text_for_lang_detect[:2000]):
            structured_data["language_of_document"] = "Non-English (Auto-Detected)"
        else:
            structured_data["language_of_document"] = "English (Auto-Detected)"
    if "document_summary_for_user" not in structured_data or not structured_data["document_summary_for_user"]:
        structured_data["document_summary_for_user"] = "요약 정보가 생성되지 않았습니다."

    return structured_data

def _handle_llm_error_response(response: Optional[LLMResult], pdf_filename: str) -> Dict[str, Any]:
    """LLM 응답이 유효하지 않거나 오류(예: 안전 필터)를 나타내는 경우를 처리합니다."""
    st.error("LLM으로부터 유효한 콘텐츠 응답을 받지 못했습니다 (구조화 데이터 추출).")
    err_payload: Dict[str, Any] = {
        "error": "Invalid or empty content from LLM for structured data extraction.",
        "source_file_name": pdf_filename,
        "language_of_document": "Unknown"
    }
    if response and response.generations:
        for i, gen_list in enumerate(response.generations):
            for j, gen in enumerate(gen_list):
                finish_reason = gen.generation_info.get('finish_reason', 'N/A') if gen.generation_info else 'N/A'
                safety_ratings = gen.generation_info.get('safety_ratings', []) if gen.generation_info else []
                err_payload[f'generation_{i}_{j}_finish_reason'] = str(finish_reason)
                err_payload[f'generation_{i}_{j}_safety_ratings'] = str(safety_ratings)
    elif response and hasattr(response, 'llm_output') and response.llm_output:
         err_payload['llm_output_details'] = str(response.llm_output)

    st.json(err_payload)
    return err_payload

def extract_structured_data_with_llm(
    full_patent_text: str,
    model: ChatGoogleGenerativeAI,
    pdf_filename: str
) -> Dict[str, Any]:
    """
    LLM을 사용하여 특허 텍스트에서 구조화된 데이터를 추출합니다.
    프롬프트 구성, API 호출, 응답 파싱 및 오류 보고를 처리합니다.
    """
    if not full_patent_text.strip():
        st.warning("구조화된 데이터 추출을 위한 입력 텍스트가 비어 있습니다.")
        return {"error": "Input text for structured data extraction is empty.", "source_file_name": pdf_filename, "language_of_document": "Unknown"}

    final_prompt = _build_llm_extraction_prompt(full_patent_text, pdf_filename)
    messages = [HumanMessage(content=final_prompt)]

    try:
        st.info(f"LLM ({AppConfig.GEMINI_MODEL_NAME}) 호출하여 특허 핵심 정보 추출 중 (일반 텍스트 모드)... (파일명: {pdf_filename}). 이 작업은 최대 {AppConfig.API_REQUEST_TIMEOUT_STRUCTURED_DATA // 60}분 정도 소요될 수 있습니다.")
        response = model.invoke(
            messages,
            config={"request_timeout": AppConfig.API_REQUEST_TIMEOUT_STRUCTURED_DATA}
        )

        # LLM 응답 내용 디버깅을 위해 임시로 출력 (문제가 해결되면 삭제)
        # st.warning("LLM 응답 내용 확인 (디버그용):")
        # if hasattr(response, 'content'):
        #     st.text_area("LLM Raw Response Content", str(response.content), height=200)
        # else:
        #     st.error("LLM 응답 객체에 'content' 속성이 없습니다. 응답 객체 전체를 확인합니다:")
        #     try:
        #         st.json(response)
        #     except Exception:
        #         st.text(str(response))


        if response and hasattr(response, 'content') and isinstance(response.content, str) :
            if response.content.strip():
                return _parse_llm_text_response(response.content, pdf_filename, full_patent_text)
            else:
                st.error("LLM 응답 내용은 있으나 비어있는 문자열입니다.")
                return {"error": "LLM response content is an empty string.", "raw_response": response.content, "source_file_name": pdf_filename, "language_of_document": "Unknown"}
        else:
            return _handle_llm_error_response(response if hasattr(response, 'generations') else None, pdf_filename)

    except Exception as e:
        st.error(f"LLM API 호출 중 오류 (구조화 데이터 추출): {e}")
        st.text_area("LLM API 호출 오류 상세", traceback.format_exc(), height=300)
        return {"error": f"API call failed: {str(e)}", "traceback": traceback.format_exc(), "source_file_name": pdf_filename, "language_of_document": "Unknown"}

# --- UI 렌더링 유틸리티 ---
@st.cache_data
def render_pdf_page_as_image(pdf_bytes: bytes, page_num: int, dpi: int = AppConfig.DEFAULT_DPI_PDF_PREVIEW) -> Optional[Image.Image]:
    """PDF의 특정 페이지를 PIL Image 객체로 렌더링합니다. 결과는 캐시됩니다."""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        if 0 <= page_num < len(doc):
            page = doc.load_page(page_num)
            zoom = dpi / 72
            matrix = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            doc.close()
            return img
        doc.close()
        return None
    except Exception as e:
        st.warning(f"PDF 페이지 이미지 렌더링 중 오류 (페이지 {page_num + 1}): {e}")
        return None

def get_value_by_path(data_dict: Dict[str, Any], path_string: str) -> Any:
    """점(.)으로 구분된 경로 문자열을 사용하여 딕셔너리에서 중첩된 값을 안전하게 가져옵니다."""
    keys = path_string.split('.')
    val = data_dict
    try:
        for key in keys:
            if isinstance(val, list) and key.isdigit():
                idx = int(key)
                if 0 <= idx < len(val):
                    val = val[idx]
                else:
                    return None
            elif isinstance(val, dict):
                val = val.get(key)
                if val is None: return None
            else:
                return None
        return val
    except (TypeError, IndexError, AttributeError):
        return None

def display_details_section(title: str, data: Any, expanded: bool = False):
    """제목과 데이터를 가진 섹션을 표시합니다 (주로 st.expander 사용)."""
    with st.expander(title, expanded=expanded):
        if isinstance(data, str):
            st.info(data)
        elif isinstance(data, dict) or isinstance(data, list):
            st.json(data)
        elif data is None:
            st.markdown("_정보 없음_")
        else:
            st.write(data)

def display_patent_info_item(title: str, value: Any):
    """특허 정보의 단일 항목을 적절한 형식으로 표시합니다."""
    display_title = title.replace('_', ' ').title()
    if isinstance(value, list):
        if not value:
            st.markdown(f"**{display_title}:** 정보 없음")
        elif all(isinstance(item, dict) for item in value):
            st.markdown(f"**{display_title}:**")
            for item_dict in value:
                item_str_list = [f"{k.replace('_',' ').title()}: {v}" for k, v in item_dict.items()]
                st.markdown(f"- {', '.join(item_str_list)}")
        else:
            st.markdown(f"**{display_title}:** {', '.join(map(str, value))}")
    elif value is None or str(value).strip() == "":
        st.markdown(f"**{display_title}:** 정보 없음")
    else:
        st.markdown(f"**{display_title}:** {value}")

def display_extracted_value_for_schema_item(value: Any):
    """Tab 3에서 추출된 값을 적절한 Streamlit 요소로 표시합니다."""
    if value is None:
        st.markdown("_정보 없음 또는 해당 경로에 값이 없습니다._")
    elif isinstance(value, list):
        if value:
            try:
                if all(isinstance(i, dict) for i in value):
                    st.dataframe(value)
                elif all(isinstance(i, (str, int, float, bool, type(None))) for i in value):
                    st.table(value)
                else:
                    st.json(value, expanded=True)
            except Exception:
                st.json(value, expanded=True)
        else:
            st.markdown("_빈 리스트입니다._")
    elif isinstance(value, dict):
        st.json(value, expanded=True)
    else:
        st.code(str(value), language=None)

# --- Streamlit UI 구성 및 메인 로직 ---
def initialize_session_state():
    """세션 상태 변수가 존재하지 않으면 초기화합니다."""
    defaults = {
        SessionStateKeys.ANALYSIS_COMPLETE: False,
        SessionStateKeys.STRUCTURED_DATA: None,
        SessionStateKeys.PDF_PAGE_TEXTS: [],
        SessionStateKeys.CURRENT_PAGE_PDF_VIEW: 0,
        SessionStateKeys.ORIGINAL_FILENAME: "",
        SessionStateKeys.PDF_BYTES_FOR_VIEWER: None,
    }
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

def run_analysis_pipeline(uploaded_file_obj):
    """PDF 업로드부터 결과 표시까지 전체 분석 파이프라인을 처리합니다."""
    st.session_state[SessionStateKeys.ORIGINAL_FILENAME] = uploaded_file_obj.name
    st.session_state[SessionStateKeys.ANALYSIS_COMPLETE] = False

    with st.spinner(f"'{uploaded_file_obj.name}' 분석 중... PDF 텍스트 추출 후 LLM 호출 중입니다. 몇 분 정도 소요될 수 있습니다..."):
        if llm is None:
            st.error("LLM 모델이 초기화되지 않아 분석을 진행할 수 없습니다. GOOGLE_API_KEY를 확인해주세요.")
            st.stop()

        try:
            pdf_bytes = uploaded_file_obj.getvalue()
            st.session_state[SessionStateKeys.PDF_BYTES_FOR_VIEWER] = pdf_bytes

            page_texts, full_text_from_pdf = convert_pdf_to_text(pdf_bytes)
            st.session_state[SessionStateKeys.PDF_PAGE_TEXTS] = page_texts

            if not full_text_from_pdf.strip():
                st.error("PDF에서 텍스트를 추출하지 못했습니다. 파일 내용을 확인해주세요.")
                st.session_state[SessionStateKeys.STRUCTURED_DATA] = {"error": "Failed to extract text from PDF."}
                st.session_state[SessionStateKeys.ANALYSIS_COMPLETE] = True
                st.stop()

            extracted_data = extract_structured_data_with_llm(
                full_text_from_pdf,
                llm,
                uploaded_file_obj.name
            )
            st.session_state[SessionStateKeys.STRUCTURED_DATA] = extracted_data
            st.session_state[SessionStateKeys.ANALYSIS_COMPLETE] = True

            if "error" not in extracted_data:
                st.success(f"'{uploaded_file_obj.name}' 분석이 완료되었습니다!")
            else:
                st.error(f"'{uploaded_file_obj.name}' 분석 중 문제가 발생했습니다. 상세 내용을 확인하세요.")
                if "raw_response" in extracted_data:
                    st.text_area("LLM 원본 응답 (분석 파이프라인 오류 시)", extracted_data["raw_response"][:3000], height=150)


        except Exception as e:
            st.error(f"분석 파이프라인 중 예기치 않은 오류 발생: {e}")
            st.exception(e)
            st.session_state[SessionStateKeys.STRUCTURED_DATA] = {"error": f"Unexpected analysis error: {str(e)}", "traceback": traceback.format_exc()}
            st.session_state[SessionStateKeys.ANALYSIS_COMPLETE] = True

def display_results_tabs():
    """분석 결과를 여러 탭에 나누어 표시합니다."""
    data = st.session_state[SessionStateKeys.STRUCTURED_DATA]
    original_filename_base = os.path.splitext(st.session_state[SessionStateKeys.ORIGINAL_FILENAME])[0]

    st.markdown("---")
    st.header("📊 분석 결과")

    tab1, tab2, tab3 = st.tabs(["📄 PDF 원문 보기 (이미지 기반)", "💡 분석 요약 및 JSON", "🔬 항목별 상세 설명"])

    with tab1:
        st.subheader("PDF 원문 보기")
        if st.session_state[SessionStateKeys.PDF_PAGE_TEXTS]:
            total_pages = len(st.session_state[SessionStateKeys.PDF_PAGE_TEXTS])
            page_selection = st.number_input(
                f"페이지 번호 (1-{total_pages})",
                min_value=1,
                max_value=total_pages,
                value=st.session_state[SessionStateKeys.CURRENT_PAGE_PDF_VIEW] + 1,
                key="pdf_page_selector_input"
            )
            st.session_state[SessionStateKeys.CURRENT_PAGE_PDF_VIEW] = page_selection - 1

            if SessionStateKeys.PDF_BYTES_FOR_VIEWER in st.session_state:
                page_image = render_pdf_page_as_image(
                    st.session_state[SessionStateKeys.PDF_BYTES_FOR_VIEWER],
                    st.session_state[SessionStateKeys.CURRENT_PAGE_PDF_VIEW]
                )
                if page_image:
                    st.image(page_image, caption=f"페이지 {st.session_state[SessionStateKeys.CURRENT_PAGE_PDF_VIEW] + 1}/{total_pages}", use_container_width=True)
                else:
                    st.warning(f"페이지 {st.session_state[SessionStateKeys.CURRENT_PAGE_PDF_VIEW] + 1} 이미지를 렌더링할 수 없습니다.")
            else:
                st.warning("PDF 내용을 로드할 수 없습니다 (세션에 바이트 데이터 없음).")
        else:
            st.warning("표시할 PDF 페이지 정보가 없습니다 (텍스트 추출 실패 또는 파일 없음).")

    with tab2:
        st.subheader("특허 기본 정보 (추출 결과 기반)")
        if "patent_info" in data and isinstance(data["patent_info"], dict):
            for key, val in data["patent_info"].items():
                display_patent_info_item(key, val)
        elif "error" not in data :
            st.markdown("_특허 기본 정보를 찾을 수 없습니다._")

        st.subheader("문서 전체 요약 (LLM 생성)")
        summary_val = data.get("document_summary_for_user")
        if summary_val and isinstance(summary_val, str) and summary_val != "요약 정보가 생성되지 않았습니다.":
            display_details_section("요약 보기", summary_val, expanded=True)
        elif "error" not in data :
            st.warning("문서 요약 정보를 찾을 수 없거나 생성되지 않았습니다.")

        st.subheader("추출된 전체 JSON 데이터")
        st.json(data, expanded=False)

        try:
            json_string = json.dumps(data, ensure_ascii=False, indent=4)
            st.download_button(
                label="JSON 파일 다운로드",
                data=json_string,
                file_name=f"{original_filename_base}_structured_data.json",
                mime="application/json",
                key="json_download_button"
            )
        except Exception as e_json_dl:
            st.error(f"JSON 다운로드 준비 중 오류: {e_json_dl}")

        if "error" in data:
            st.error(f"데이터 추출/표시 중 문제 발생: {data.get('error')}")
            if "raw_response" in data:
                 st.text_area("LLM 원본 응답 (오류 시)", data['raw_response'][:3000], height=150)
            if "extracted_json_to_parse" in data: # 파싱 시도했던 JSON 부분도 표시
                 st.text_area("파싱 시도한 JSON 부분 (오류 시)", data['extracted_json_to_parse'][:3000], height=150)
            if "traceback" in data:
                 st.text_area("오류 상세 정보", data['traceback'], height=150)


    with tab3:
        st.subheader("주요 항목별 상세 설명 및 추출 값")
        if "error" in data:
            st.error(f"데이터 추출 중 오류가 발생하여 항목별 상세 정보를 표시할 수 없습니다: {data.get('error')}")
            if "raw_response" in data:
                st.text_area("LLM 원본 응답 (오류 시)", data['raw_response'][:2000], height=200)
            if "extracted_json_to_parse" in data:
                 st.text_area("파싱 시도한 JSON 부분 (오류 시)", data['extracted_json_to_parse'][:2000], height=150)
            if "traceback" in data:
                 st.text_area("오류 상세 정보 (Traceback)", data['traceback'], height=200)

        elif not SCHEMA_FIELD_DESCRIPTIONS:
             st.warning("스키마 설명 정보(`schema_descriptions.py`)가 비어있거나 로드되지 않았습니다.")
        else:
            field_options = {
                f"{path.split('.')[-1].replace('_', ' ').title()} (Path: {path})": path
                for path in SCHEMA_FIELD_DESCRIPTIONS.keys()
            }
            sorted_display_labels = sorted(list(field_options.keys()))

            if not sorted_display_labels:
                st.warning("표시할 스키마 설명 정보가 없습니다. `schema_descriptions.py` 파일 내용을 확인해주세요.")
            else:
                selected_display_label = st.selectbox(
                    "상세 설명을 보고 싶은 항목을 선택하세요:",
                    options=sorted_display_labels,
                    key="field_selector_tab3"
                )

                if selected_display_label and selected_display_label in field_options:
                    selected_path = field_options[selected_display_label]
                    description = SCHEMA_FIELD_DESCRIPTIONS.get(selected_path, "해당 항목에 대한 설명이 없습니다.")
                    extracted_value = get_value_by_path(data, selected_path)

                    st.markdown(f"#### 📜 항목 경로: `{selected_path}`")
                    st.markdown("**항목 설명 (고정):**")
                    st.info(description)
                    st.markdown("**추출된 값:**")
                    display_extracted_value_for_schema_item(extracted_value)
                else:
                    st.warning("설명을 표시할 항목을 목록에서 선택해주세요.")

# --- 메인 앱 실행 로직 ---
def main():
    st.set_page_config(page_title="특허 문서 분석 프로토타입", layout="wide")
    st.title("📜 특허 문서 분석 프로토타입 v3.4")
    st.markdown("PDF 특허 문서를 업로드하면 주요 정보를 분석하여 구조화된 JSON 데이터로 제공하고, 각 항목에 대한 설명을 함께 보여줍니다.")

    initialize_session_state()

    uploaded_file = st.file_uploader("특허 PDF 파일을 업로드하세요 (.pdf)", type="pdf", key="pdf_uploader")

    if uploaded_file is not None:
        if st.button("특허 분석 시작", key="analyze_button"):
            st.session_state[SessionStateKeys.STRUCTURED_DATA] = None
            st.session_state[SessionStateKeys.PDF_PAGE_TEXTS] = []
            st.session_state[SessionStateKeys.CURRENT_PAGE_PDF_VIEW] = 0
            run_analysis_pipeline(uploaded_file)

    if st.session_state[SessionStateKeys.ANALYSIS_COMPLETE] and st.session_state[SessionStateKeys.STRUCTURED_DATA]:
        display_results_tabs()
    elif not uploaded_file:
        st.info("페이지 상단의 파일 업로더를 사용하여 분석할 특허 PDF 파일을 업로드해주세요.")

if __name__ == "__main__":
    main()