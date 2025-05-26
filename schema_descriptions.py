# schema_descriptions.py

SCHEMA_FIELD_DESCRIPTIONS = {
    "patent_info": "특허의 기본적인 서지 정보입니다. 공개번호, 출원일, 발명자 등을 포함합니다.",
    "patent_info.publication_number": "공개번호: 특허 문서의 고유한 공개번호입니다. (예: 'EP 3 968 410 A1', '10-2024-0011099 A')",
    "patent_info.publication_date": "공개일자: 특허가 공식적으로 공개된 날짜입니다. (YYYY-MM-DD 형식 권장)",
    "patent_info.application_number": "출원번호: 특허청에 제출된 출원의 번호입니다.",
    "patent_info.filing_date": "출원일자: 특허가 출원된 날짜입니다.",
    "patent_info.priority_data": "우선권 데이터: 원출원에 대한 우선권 주장 정보 리스트입니다. 각 항목은 우선권 번호, 날짜, 국가를 포함합니다.",
    "patent_info.applicants": "출원인: 특허를 출원한 개인 또는 법인(들)의 리스트입니다.",
    "patent_info.inventors": "발명자: 발명을 한 개인(들)의 리스트입니다.",
    "patent_info.title_original_language": "원어 제목: 특허 문서에 기재된 원어 그대로의 발명의 명칭입니다.",
    "patent_info.title_english_translation": "영문 제목: 원어 제목이 영어가 아닐 경우 번역된 영문 제목입니다. 원어가 영어면 원어 제목과 동일할 수 있습니다.",

    "material_description": "특허에서 다루는 핵심 재료에 대한 설명입니다.",
    "material_description.application_focus": "재료 응용 분야: 재료의 주요 응용 또는 목적을 간략히 설명합니다. (예: '나트륨 이온 배터리용 양극 활물질')",
    "material_description.material_system_type": "재료 시스템 유형: 재료의 일반적인 분류입니다. (예: 'Sodium Halophosphate-Carbon Composite', 'Layered Oxide')",
    "material_description.chemical_formula_general": "일반 화학식: 제시된 가장 대표적인 일반 화학식입니다. (예: 'Na2M1hM2k(PO4)X/C')",
    "material_description.formula_parameters": "화학식 매개변수: 일반 화학식에 사용된 변수(M1, h, X 등)에 대한 설명 리스트입니다. 각 매개변수는 관련된 원소, 값의 범위 등을 포함합니다.",
    "material_description.key_additive_or_dopant_info": "핵심 첨가제/도펀트 정보: 주요 첨가제 또는 도펀트에 대한 정보 리스트입니다. 유형, 화학적 정체, 역할, 함량 등을 포함합니다.",

    "morphology_structure": "재료의 형태학적 및 구조적 특징입니다.",
    "morphology_structure.particle_form_summary": "입자 형태 요약: 입자의 전반적인 특성에 대한 설명입니다.",
    "morphology_structure.primary_particle_shape_observed": "주요 관찰 입자 형태: 관찰된 입자의 주된 형태(들)입니다. (예: 'flake', 'sphere')",
    "morphology_structure.size_metrics": "크기 지표: 입자 크기, 결정립 크기 등 다양한 크기 관련 지표 리스트입니다. 단위, 값 범위 등을 포함합니다.",
    "morphology_structure.specific_surface_area_BET_m2_g": "BET 비표면적 (m²/g): 재료의 비표면적 값 또는 범위입니다.",
    "morphology_structure.density_g_cm3": "밀도 (g/cm³): 탭 밀도, 압축 밀도 등 다양한 조건에서의 밀도 값 또는 범위 리스트입니다.",
    "morphology_structure.crystallinity_features": "결정성 특징: XRD 피크 정보, 결정 구조 유형 등 결정성과 관련된 특징 리스트입니다.",
    "morphology_structure.coating_information": "코팅 정보: 재료의 코팅 여부, 코팅 물질, 코팅 목적 등을 설명합니다.",

    "physical_chemical_properties_specific": "특정 물리화학적 특성: 언급된 구체적인 물리적, 화학적 특성들의 리스트입니다. 특성명, 단위, 값, 측정 조건 등을 포함합니다.",

    "preparation_method_summary": "제조 방법 요약: 재료의 전반적인 합성 경로 및 주요 단계별 조건에 대한 설명입니다.",
    "preparation_method_summary.overall_synthesis_route_description": "전체 합성 경로 설명: 제조 방법에 대한 간략한 개요입니다.",
    "preparation_method_summary.key_steps_and_conditions": "주요 단계 및 조건: 제조 과정의 주요 단계별 상세 설명 및 관련 파라미터(온도, 시간 등) 리스트입니다.",
    "preparation_method_summary.raw_material_examples_by_type": "유형별 원료 예시: 주요 원소/구성 요소의 공급원 예시입니다.",

    "application_details": "응용 상세 정보: 발명의 주된 응용 분야, 특정 구성 요소로서의 역할, 잠재적 최종 사용처 등에 대한 설명입니다.",
    "application_details.primary_application_field": "주요 응용 분야: 발명이 속하는 주요 기술 분야입니다. (예: '나트륨 이온 배터리 기술')",
    "application_details.specific_component_role": "특정 부품 역할: 발명이 특정 시스템 내에서 수행하는 역할입니다. (예: '양극 활물질')",
    "application_details.potential_end_use_devices_or_systems": "잠재적 최종 사용처: 발명이 적용될 수 있는 최종 제품 또는 시스템 예시 리스트입니다.",

    "key_claimed_advantages_or_problems_solved_by_invention": "핵심 주장 이점/해결 과제: 발명이 해결하고자 하는 문제점, 기존 기술 대비 개선점, 주요 이점 등의 리스트입니다.",
    "representative_performance_data_from_examples_or_figures": "대표적 성능 데이터: 실시예, 표, 그림 등에서 발췌한 구체적인 성능 지표 데이터 리스트입니다.",

    "document_summary_for_user": "문서 전체 요약 (LLM 생성): LLM이 생성한 특허 문서의 주요 내용에 대한 3-5 문장 요약입니다.",
    "language_of_document": "문서 언어: 특허 문서의 주 사용 언어입니다. (예: 'English', 'Korean')",
    "source_file_name": "원본 파일명: 분석된 PDF 파일의 원본 이름입니다."
}
# ** 중요: 위 딕셔너리는 예시이며, 실제 스키마의 모든 필드에 대한 설명을 상세히 작성해야 합니다. **