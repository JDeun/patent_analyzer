import streamlit as st
import os
import fitz  # PyMuPDF
from PIL import Image
import io
import base64 # PDF 뷰어에서 직접 사용되진 않지만, 다른 기능에 필요할 수 있음
import json
import traceback
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

# --- 외부 파일에서 프롬프트 및 스키마 설명 임포트 ---
try:
    from prompts import PATENT_DATA_SCHEMA_FOR_LLM_PROMPT_FULL
    from schema_descriptions import SCHEMA_FIELD_DESCRIPTIONS
except ImportError:
    st.error("오류: `prompts.py` 또는 `schema_descriptions.py` 파일을 찾을 수 없습니다. 해당 파일들이 main 스크립트와 동일한 디렉토리에 있는지 확인해주세요.")
    # 대체 값으로 실행 중단 또는 기본값 설정
    PATENT_DATA_SCHEMA_FOR_LLM_PROMPT_FULL = "{}" # 빈 JSON이라도 LLM 호출은 시도될 수 있음
    SCHEMA_FIELD_DESCRIPTIONS = {}
    # st.stop() # 또는 앱 실행을 중단

# --- 전역 설정 변수 ---
GEMINI_MODEL_NAME = "gemini-2.5-flash-preview-05-20"
TEMPERATURE = 0.0
API_REQUEST_TIMEOUT_STRUCTURED_DATA = 1200 # 초 단위 (20분)

DEFAULT_DPI = 300 # PDF 페이지 이미지 변환 시 DPI (디버깅용)

# 디버깅 관련 설정
SAVE_DEBUG_PDF_IMAGES = True
DEBUG_OUTPUT_BASE_DIR = "debug_output"
# ---------------------

# .env 파일에서 환경 변수 로드
load_dotenv()

# Google API 키 확인 및 LLM 초기화
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
llm = None
if not GOOGLE_API_KEY:
    # Streamlit 앱에서는 st.error를 먼저 사용할 수 없으므로, 나중에 앱 실행 시점에 확인
    print("CRITICAL: GOOGLE_API_KEY 환경변수가 설정되지 않았습니다. 앱 실행 시 오류가 발생합니다.")
else:
    try:
        llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL_NAME, google_api_key=GOOGLE_API_KEY, temperature=TEMPERATURE)
        print(f"Gemini 모델 '{GEMINI_MODEL_NAME}' 초기화 성공.")
    except Exception as e_model_init:
        print(f"Gemini 모델 '{GEMINI_MODEL_NAME}' 초기화 중 심각한 오류: {e_model_init}")
        llm = None

def extract_text_from_pdf_page_st(page: fitz.Page) -> str:
    try:
        text = page.get_text("text", sort=True)
        return text
    except Exception as e:
        st.error(f"페이지 텍스트 추출 오류: {e}")
        return ""

def convert_pdf_to_text_st(uploaded_file_content: bytes, pdf_filename_for_debug: str) -> tuple[list[str], str]:
    full_text_for_extraction = ""
    page_texts = []

    debug_image_dir = None
    if SAVE_DEBUG_PDF_IMAGES:
        pdf_base_filename = os.path.splitext(pdf_filename_for_debug)[0]
        debug_image_dir = os.path.join(DEBUG_OUTPUT_BASE_DIR, pdf_base_filename, "pdf_to_images_debug")
        os.makedirs(debug_image_dir, exist_ok=True)

    try:
        doc = fitz.open(stream=uploaded_file_content, filetype="pdf")
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            actual_page_num = page_num + 1
            text = extract_text_from_pdf_page_st(page)
            page_texts.append(text)
            full_text_for_extraction += f"\n\n<<<<< PAGE {actual_page_num} / {len(doc)} >>>>>\n\n" + text

            if SAVE_DEBUG_PDF_IMAGES and debug_image_dir:
                zoom = DEFAULT_DPI / 72
                matrix = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=matrix, alpha=False)
                img_bytes = pix.tobytes("png")
                pil_image = Image.open(io.BytesIO(img_bytes))
                img_save_path = os.path.join(debug_image_dir, f"{os.path.splitext(pdf_filename_for_debug)[0]}_page_{actual_page_num}_dpi{DEFAULT_DPI}.png")
                try:
                    pil_image.save(img_save_path)
                except Exception as e_save_img_debug:
                    st.warning(f"디버그 이미지 저장 실패 (페이지 {actual_page_num}): {e_save_img_debug}")
        doc.close()

        if page_texts:
            pdf_base_filename = os.path.splitext(pdf_filename_for_debug)[0]
            debug_text_dir = os.path.join(DEBUG_OUTPUT_BASE_DIR, pdf_base_filename)
            os.makedirs(debug_text_dir, exist_ok=True)
            text_output_file = os.path.join(debug_text_dir, f"{pdf_base_filename}_extracted_full_text.txt")
            try:
                with open(text_output_file, "w", encoding="utf-8") as f:
                    f.write(full_text_for_extraction)
                st.sidebar.info(f"추출된 텍스트가 '{text_output_file}'에 저장되었습니다.")
            except Exception as e_text_save:
                st.sidebar.warning(f"추출된 텍스트 파일 저장 중 오류: {e_text_save}")
        return page_texts, full_text_for_extraction
    except Exception as e:
        st.error(f"PyMuPDF로 PDF 처리 중 오류: {e}")
        return [], ""

def extract_structured_data_from_full_text_st(
    full_patent_text: str,
    model: ChatGoogleGenerativeAI,
    pdf_filename: str
) -> dict:
    if not full_patent_text.strip():
        st.warning("구조화된 데이터 추출을 위한 입력 텍스트가 비어 있습니다.")
        return {"error": "Input text for structured data extraction is empty.", "source_file_name": pdf_filename, "language_of_document": "Unknown"}

    # PATENT_DATA_SCHEMA_FOR_LLM_PROMPT_FULL은 prompts.py에서 임포트됩니다.
    final_prompt = PATENT_DATA_SCHEMA_FOR_LLM_PROMPT_FULL + \
                   f"\n\nIMPORTANT:\n" + \
                   f"- The 'source_file_name' field in the JSON output MUST be exactly: \"{pdf_filename}\"\n" + \
                   f"- Identify the primary language of the patent text and set the 'language_of_document' field accordingly (e.g., 'English', 'Korean').\n" + \
                   f"- Ensure the 'document_summary_for_user' field contains a concise 3-5 sentence general summary.\n\n" + \
                   "Here is the full patent text to analyze:\n\n--- BEGIN PATENT TEXT ---\n" + \
                   full_patent_text + \
                   "\n--- END PATENT TEXT ---\n\n" + \
                   "Extract the information based on the schema provided above and provide ONLY the JSON object as your response."
    
    messages = [HumanMessage(content=final_prompt)]

    try:
        st.info(f"LLM ({GEMINI_MODEL_NAME}) 호출하여 특허 핵심 정보 추출 중... (파일명: {pdf_filename}). 이 작업은 몇 분 정도 소요될 수 있습니다.")
        response = model.invoke(messages, config={"request_timeout": API_REQUEST_TIMEOUT_STRUCTURED_DATA})

        if response and hasattr(response, 'content') and isinstance(response.content, str) and response.content.strip():
            content_str = response.content.strip()
            if content_str.startswith("```json"):
                content_str = content_str[len("```json"):].strip()
            if content_str.endswith("```"):
                content_str = content_str[:-len("```")].strip()

            try:
                structured_data = json.loads(content_str)
                if "source_file_name" not in structured_data: # LLM이 빼먹었을 경우 대비
                    structured_data["source_file_name"] = pdf_filename
                if "language_of_document" not in structured_data:
                    if any(char.isalpha() and ord(char) > 127 for char in full_patent_text[:2000]):
                        structured_data["language_of_document"] = "Non-English (Auto-Detected)"
                    else:
                        structured_data["language_of_document"] = "English (Auto-Detected)"
                if "document_summary_for_user" not in structured_data:
                     structured_data["document_summary_for_user"] = "요약 정보가 생성되지 않았습니다."
                return structured_data
            except json.JSONDecodeError as json_e:
                st.error(f"LLM 응답 JSON 파싱 오류: {json_e}")
                st.text_area("LLM 원본 응답 (파싱 실패)", content_str[:3000], height=300)
                return {"error": "Failed to parse LLM response as JSON", "raw_response": content_str, "source_file_name": pdf_filename, "language_of_document": "Unknown"}
            except TypeError as type_e:
                st.error(f"LLM 응답 JSON 파싱 중 TypeError: {type_e}")
                st.text_area("LLM 원본 응답 (TypeError)", str(content_str)[:3000], height=300)
                return {"error": "LLM response was not suitable for JSON parsing (e.g. None type)", "raw_response": str(content_str), "source_file_name": pdf_filename, "language_of_document": "Unknown"}
        else:
            st.error("LLM으로부터 유효한 응답을 받지 못했습니다 (구조화 데이터 추출).")
            err_payload = {"error": "Invalid or empty response from LLM for structured data extraction.", "source_file_name": pdf_filename, "language_of_document": "Unknown"}
            if response and hasattr(response, 'candidates') and response.candidates:
                for i, cand in enumerate(response.candidates):
                    finish_reason = getattr(cand, 'finish_reason', 'N/A')
                    safety_ratings = getattr(cand, 'safety_ratings', [])
                    err_payload[f'candidate_{i}_finish_reason'] = str(finish_reason)
                    err_payload[f'candidate_{i}_safety_ratings'] = str(safety_ratings)
            elif response and hasattr(response, 'parts') and not response.parts:
                 err_payload['details'] = "Response object had no 'parts'."
            st.json(err_payload)
            return err_payload

    except Exception as e:
        st.error(f"LLM 호출 중 오류 (구조화 데이터 추출): {e}")
        st.text_area("LLM 호출 오류 상세", traceback.format_exc(), height=300)
        return {"error": f"API call failed: {str(e)}", "traceback": traceback.format_exc(), "source_file_name": pdf_filename, "language_of_document": "Unknown"}

@st.cache_data
def render_pdf_page_as_image(pdf_bytes, page_num, dpi=150):
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
    except Exception:
        return None

def get_value_by_path(data_dict, path_string):
    keys = path_string.split('.')
    val = data_dict
    try:
        for key in keys:
            if isinstance(val, list) and key.isdigit():
                idx = int(key)
                if 0 <= idx < len(val):
                    val = val[idx]
                else:
                    return None # Index out of bounds
            elif isinstance(val, dict):
                val = val[key]
            else: # Path tries to go deeper, but current val is not a dict or list
                return None
        return val
    except (KeyError, TypeError, IndexError, AttributeError):
        return None

# --- Streamlit UI 구성 ---
st.set_page_config(page_title="특허 문서 분석 프로토타입", layout="wide")
st.title("📜 특허 문서 분석 프로토타입 v3 (스키마 설명 분리)")
st.markdown("PDF 특허 문서를 업로드하면 주요 정보를 분석하여 구조화된 JSON 데이터로 제공하고, 각 항목에 대한 설명을 함께 보여줍니다.")

# 세션 상태 초기화
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False
if 'structured_data' not in st.session_state:
    st.session_state.structured_data = None
if 'pdf_page_texts' not in st.session_state:
    st.session_state.pdf_page_texts = []
if 'current_page_for_pdf_view' not in st.session_state:
    st.session_state.current_page_for_pdf_view = 0
if 'original_filename' not in st.session_state:
    st.session_state.original_filename = ""

uploaded_file = st.file_uploader("특허 PDF 파일을 업로드하세요 (.pdf)", type="pdf", key="pdf_uploader")

if uploaded_file is not None:
    if st.button("특허 분석 시작", key="analyze_button"):
        st.session_state.analysis_complete = False
        st.session_state.structured_data = None
        st.session_state.pdf_page_texts = []
        st.session_state.current_page_for_pdf_view = 0
        st.session_state.original_filename = uploaded_file.name

        with st.spinner(f"'{uploaded_file.name}' 분석 중... PDF 텍스트 추출 후 LLM 호출 중입니다. 몇 분 정도 소요될 수 있습니다..."):
            if llm is None:
                st.error("LLM 모델이 초기화되지 않아 분석을 진행할 수 없습니다. GOOGLE_API_KEY를 확인해주세요.")
                st.stop()

            try:
                pdf_bytes = uploaded_file.getvalue()
                st.session_state.pdf_bytes_for_viewer = pdf_bytes

                page_texts, full_text_from_pdf = convert_pdf_to_text_st(pdf_bytes, uploaded_file.name)
                st.session_state.pdf_page_texts = page_texts

                if not full_text_from_pdf.strip():
                    st.error("PDF에서 텍스트를 추출하지 못했습니다. 파일 내용을 확인해주세요.")
                    st.stop()

                extracted_data = extract_structured_data_from_full_text_st(
                    full_text_from_pdf,
                    llm,
                    uploaded_file.name
                )
                st.session_state.structured_data = extracted_data
                st.session_state.analysis_complete = True
                st.success(f"'{uploaded_file.name}' 분석이 완료되었습니다!")

            except Exception as e:
                st.error(f"분석 중 오류 발생: {e}")
                st.exception(e)
                st.session_state.analysis_complete = False

if st.session_state.analysis_complete and st.session_state.structured_data:
    data = st.session_state.structured_data
    original_filename_base = os.path.splitext(st.session_state.original_filename)[0]

    st.markdown("---")
    st.header("📊 분석 결과")

    tab1, tab2, tab3 = st.tabs(["📄 PDF 원문 보기 (이미지 기반)", "💡 분석 요약 및 JSON", "🔬 항목별 상세 설명"])

    with tab1:
        st.subheader("PDF 원문 보기")
        if st.session_state.pdf_page_texts:
            total_pages = len(st.session_state.pdf_page_texts)
            # 페이지 번호 입력값이 변경될 때마다 current_page_for_pdf_view를 업데이트
            # value는 1-based로 보여주고, 내부적으로는 0-based 사용
            page_selection = st.number_input(
                f"페이지 번호 (1-{total_pages})",
                min_value=1,
                max_value=total_pages,
                value=st.session_state.current_page_for_pdf_view + 1, # 현재 페이지 + 1을 기본값으로
                key="pdf_page_selector"
            )
            st.session_state.current_page_for_pdf_view = page_selection - 1


            if 'pdf_bytes_for_viewer' in st.session_state:
                page_image = render_pdf_page_as_image(st.session_state.pdf_bytes_for_viewer, st.session_state.current_page_for_pdf_view, dpi=150)
                if page_image:
                    st.image(page_image, caption=f"페이지 {st.session_state.current_page_for_pdf_view + 1}/{total_pages}", use_column_width=True)
                else:
                    st.warning(f"페이지 {st.session_state.current_page_for_pdf_view + 1} 이미지를 렌더링할 수 없습니다.")
            else:
                st.warning("PDF 내용을 로드할 수 없습니다.")
        else:
            st.warning("표시할 PDF 페이지 정보가 없습니다.")

    with tab2:
        st.subheader("특허 기본 정보 (추출 결과 기반)")
        if "patent_info" in data and isinstance(data["patent_info"], dict):
            for key, val in data["patent_info"].items():
                display_val = val
                field_title_display = key.replace('_', ' ').title()
                if isinstance(display_val, list):
                    if all(isinstance(item, dict) for item in display_val):
                        st.markdown(f"**{field_title_display}:**")
                        for item_dict in display_val:
                            item_str_list = []
                            for sub_key, sub_val in item_dict.items():
                                item_str_list.append(f"{sub_key.replace('_',' ').title()}: {sub_val}")
                            st.markdown(f"- {', '.join(item_str_list)}")
                    elif display_val: # 내용이 있는 리스트 (딕셔너리가 아닌 경우)
                        st.markdown(f"**{field_title_display}:** {', '.join(map(str, display_val))}")
                    else: # 빈 리스트
                        st.markdown(f"**{field_title_display}:** 정보 없음")

                elif display_val is None:
                    st.markdown(f"**{field_title_display}:** 정보 없음")
                else: # 단순 문자열, 숫자 등
                    st.markdown(f"**{field_title_display}:** {display_val}")

        st.subheader("문서 전체 요약 (LLM 생성)")
        summary_val = data.get("document_summary_for_user")
        if summary_val and isinstance(summary_val, str) and summary_val != "요약 정보가 생성되지 않았습니다.":
            with st.expander("요약 보기", expanded=True):
                st.info(summary_val)
        else:
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

    with tab3:
        st.subheader("주요 항목별 상세 설명 및 추출 값")
        if "error" in data: # LLM 호출 자체에서 오류가 있었던 경우
            st.error(f"데이터 추출 중 오류 발생: {data.get('error')}")
            if "raw_response" in data: # LLM의 원본 응답이 있다면 표시
                st.text_area("LLM 원본 응답 (오류 시)", data['raw_response'][:2000], height=200)
            if "traceback" in data: # API 호출 실패 시 트레이스백이 있다면 표시
                 st.text_area("오류 상세 정보", data['traceback'], height=200)
        elif not SCHEMA_FIELD_DESCRIPTIONS: # 스키마 설명 파일이 비어있는 경우
             st.warning("스키마 설명 정보(`schema_descriptions.py`)가 비어있거나 로드되지 않았습니다.")
        else:
            # SCHEMA_FIELD_DESCRIPTIONS 딕셔너리의 키(JSON 경로)를 정렬하여 선택 옵션으로 사용
            # 사용자가 보기 편한 레이블을 만들거나, 경로 자체를 옵션으로 제공
            field_options = {
                # 경로의 마지막 부분을 레이블로 사용하고, 전체 경로는 값으로 사용. 중복 방지를 위해 전체 경로도 레이블에 포함.
                f"{path.split('.')[-1].replace('_', ' ').title()} (Path: {path})": path
                for path in SCHEMA_FIELD_DESCRIPTIONS.keys()
            }
            # 레이블 기준으로 정렬
            sorted_display_labels = sorted(list(field_options.keys()))

            if not sorted_display_labels:
                st.warning("표시할 스키마 설명 정보가 없습니다. SCHEMA_FIELD_DESCRIPTIONS를 정의해주세요.")
            else:
                selected_display_label = st.selectbox(
                    "상세 설명을 보고 싶은 항목을 선택하세요:",
                    options=sorted_display_labels,
                    key="field_selector_tab3"
                )

                if selected_display_label and selected_display_label in field_options:
                    selected_path = field_options[selected_display_label] # 선택된 레이블로부터 실제 경로 가져오기
                    description = SCHEMA_FIELD_DESCRIPTIONS.get(selected_path, "해당 항목에 대한 설명이 없습니다.")
                    extracted_value = get_value_by_path(data, selected_path)

                    st.markdown(f"#### 📜 항목 경로: `{selected_path}`")

                    st.markdown("**항목 설명 (고정):**")
                    st.info(description)

                    st.markdown("**추출된 값:**")
                    if extracted_value is None:
                        st.markdown("_정보 없음 또는 해당 경로에 값이 없습니다._")
                    elif isinstance(extracted_value, list):
                        if extracted_value:
                            # 리스트 내용이 복잡할 수 있으므로 st.dataframe 이나 st.json으로 표시
                            try:
                                if all(isinstance(i, dict) for i in extracted_value):
                                    st.dataframe(extracted_value)
                                elif all(isinstance(i, (str, int, float, bool)) for i in extracted_value):
                                     st.table(extracted_value) # 간단한 리스트는 테이블로
                                else: # 혼합된 경우 또는 복잡한 객체는 json으로
                                    st.json(extracted_value, expanded=True)
                            except Exception: # 데이터프레임 변환 실패 시 json으로 대체
                                st.json(extracted_value, expanded=True)
                        else:
                            st.markdown("_빈 리스트입니다._")
                    elif isinstance(extracted_value, dict):
                        st.json(extracted_value, expanded=True)
                    else: # 문자열, 숫자, 불리언 등
                        st.markdown(f"`{extracted_value}`") # 마크다운 코드 블록으로 표시
                else:
                    st.warning("설명을 표시할 항목을 목록에서 선택해주세요.")

# 초기 화면 안내
if not uploaded_file:
    st.info("페이지 상단의 파일 업로더를 사용하여 분석할 특허 PDF 파일을 업로드해주세요.")