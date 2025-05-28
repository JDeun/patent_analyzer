TEST_PROMPT = """
You are an expert in patent analysis.
Given the full text of a patent document, extract the specified information
and structure it as a JSON object.
Respond ONLY with a valid JSON object.

The desired JSON output structure is as follows:
{
    "patent_info": {
        "publication_number": "string",
        "title_original_language": "string"
    },
    "source_file_name": "string (This will be the PDF filename you provide)"
}

IMPORTANT INSTRUCTIONS FOR THIS SPECIFIC TASK:
- The 'source_file_name' field in the JSON output MUST be exactly: "{pdf_filename}"

Here is the full patent text to analyze:
--- BEGIN PATENT TEXT ---
{full_patent_text}
--- END PATENT TEXT ---

Based on the schema and instructions provided above, generate ONLY the JSON object as your response.
"""
# _build_llm_extraction_prompt 함수 내에서 final_prompt를 위 테스트 프롬프트로 교체하여 테스트