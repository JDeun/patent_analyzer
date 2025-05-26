# prompts.py

PATENT_DATA_SCHEMA_FOR_LLM_PROMPT_FULL = """
You are an expert in chemistry and material science patent analysis.
Given the full text of a patent document (provided below), extract the specified information
and structure it as a JSON object. Populate all fields as accurately and completely as possible
based ONLY on the provided text. If information for a field is not found, use null or an
empty string/list as appropriate for that field type. Pay close attention to units, conditions, and ranges.
The 'language_of_document' should be the primary language identified in the text (e.g., 'English', 'Korean').
The 'source_file_name' will be provided to you and should be included in the JSON output.
Generate the 'document_summary_for_user' field with a concise 3-5 sentence general summary of the patent's main points.

The desired JSON output structure is as follows:

{
    "patent_info": {
        "publication_number": "string (e.g., 'EP 3 968 410 A1', '10-2024-0011099 A')",
        "publication_date": "string (YYYY-MM-DD format if possible, otherwise as written)",
        "application_number": "string (e.g., '20859053.9', '10-2023-0092193')",
        "filing_date": "string (YYYY-MM-DD format if possible, otherwise as written)",
        "priority_data": [
            {
                "priority_number": "string (e.g., 'CN 201910800432', '202210841494.0')",
                "priority_date": "string (YYYY-MM-DD format if possible, otherwise as written)",
                "priority_country": "string (2-letter country code like 'CN', 'KR', 'US', 'EP' or full name if code not obvious)"
            }
        ],
        "applicants": ["string (List all applicants, e.g., 'Contemporary Amperex Technology Co., Limited', '구이저우 전화 이-켐 컴퍼니 리미티드')"],
        "inventors": ["string (List all inventors, e.g., 'LIU, Qian', '조우 차오이')"],
        "title_original_language": "string (The full title as it appears in its original language)",
        "title_english_translation": "string (If original title is not in English, provide an English translation. If already English, this can be the same as original_language_title.)"
    },
    "material_description": {
        "application_focus": "string (Briefly describe the main application or purpose of the material, e.g., 'Positive electrode material for sodium-ion battery', 'Single-crystal cathode material for sodium-ion batteries')",
        "material_system_type": "string (General classification of the material, e.g., 'Sodium Halophosphate-Carbon Composite', 'Layered Oxide (e.g., O3-type)', 'Phosphate-based material')",
        "chemical_formula_general": "string (The most representative general chemical formula presented, e.g., 'Na2M1hM2k(PO4)X/C', 'Na(1+a)Ni(1-x-y-z)Mn(x)Fe(y)M(z)O2')",
        "formula_parameters": [
            {
                "parameter_name": "string (The variable/symbol in the formula, e.g., 'M1', 'h', 'X', 'a', 'x', 'M')",
                "elements_involved": ["string (List of chemical symbols this parameter can represent, e.g., ['Ti', 'V', 'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn'] or ['F', 'Cl', 'Br'])"],
                "value_range": "string (Stoichiometric range or value, e.g., '0 to 1', 'h+k=1', '-0.40 <= a <= 0.25', '0 <= z < 0.26')",
                "preferred_value_range": "string (If a preferred or optional narrower range is specified, e.g., '0.05 to 5 micron', 'optionally 0.5 wt% to 5 wt%')",
                "description": "string (Brief explanation of the parameter, e.g., 'Transition metal ion', 'Halogen ion', 'Stoichiometric coefficient for Na')"
            }
        ],
        "key_additive_or_dopant_info": [
            {
                "type_or_name": "string (e.g., 'Carbon coating', 'M element doping', 'Binder XYZ')",
                "chemical_identity": "string (e.g., 'C', 'Ti, Zn, Al,...', 'PVDF')",
                "role_or_purpose": "string (e.g., 'Improve conductivity', 'Enhance structural stability', 'Electrode binder')",
                "content_description": "string (Amount or concentration, e.g., '0.05 wt% to 15 wt%', 'z from 0 to <0.26', 'typically 1-5 wt% of electrode mass')",
                "source_materials_if_specified": ["string (e.g., 'glucose', 'acetylene black', 'specific oxide precursors for dopant M')"]
            }
        ]
    },
    "morphology_structure": {
        "particle_form_summary": "string (Overall description of the particle nature, e.g., 'Composite of sodium halophosphate with carbon', 'Single-crystal particles', 'Polycrystalline agglomerates')",
        "primary_particle_shape_observed": ["string (Observed shapes, e.g., 'flake', 'sphere', 'polyhedron', 'lamellar', 'quasi-spherical')"],
        "size_metrics": [
             {"metric_type": "string (e.g., 'Grain Size D', 'Particle Size D50', 'Average Particle Size')", "unit": "string (e.g., 'micron', 'nm')", "value_range": "string (e.g., '0.01 to 20', '2.0-16.0')", "preferred_value_range": "string (If specified, e.g., '0.05 to 5', '4.0-13.0')"}
        ],
        "specific_surface_area_BET_m2_g": {"value_range": "string (e.g., '0.01 to 30', '0.35-1.2')", "preferred_value_range": "string (If specified, e.g., '1 to 20')"},
        "density_g_cm3": [
            {"type": "string (e.g., 'tap', 'compacted', 'powder densification')",
             "value_range": "string (e.g., '0.5 to 2.5', '2.8-4.2')",
             "conditions": "string (If specified, e.g., 'under a pressure of 8 tons', 'under 7000-9000kg pressure')",
             "preferred_value_range": "string (If specified, e.g., '0.7 to 2.0')"}
        ],
        "crystallinity_features": [
            {"feature_type": "string (e.g., 'XRD FWHM', 'Crystal structure type')",
             "details": "string (e.g., 'Peak (110) at 2theta approx 64.9 deg: FWHM range 0.06-0.35', 'Identified as O3 layered structure by XRD')"
            }
        ],
        "coating_information": {
            "is_coated": "boolean (true if coating is explicitly mentioned, false otherwise)",
            "coating_material": "string (e.g., 'Carbon', 'Al2O3')",
            "coating_purpose": "string (e.g., 'Enhance electronic conductivity', 'Protect from electrolyte')"
        }
    },
    "physical_chemical_properties_specific": [
         {"property_name": "string (e.g., 'Powder Resistivity', 'Moisture Content', 'pH Value', 'First Cycle Discharge Specific Capacity')",
          "unit": "string (e.g., 'ohm-cm', 'ppm', 'mAh/g')",
          "value_or_range": "string (e.g., '10 to 5000', '<3000', '13.1 이내', '111')",
          "conditions_of_measurement": "string (e.g., 'under a pressure of 12 MPa', 'for a 10% suspension in deionized water', '0.1C rate')",
          "preferred_value_or_range": "string (If specified, e.g., '20 to 2000', '<2500')"}
    ],
    "preparation_method_summary": {
        "overall_synthesis_route_description": "string (Brief overview of the method, e.g., 'Solid-state reaction method', 'Co-precipitation followed by calcination')",
        "key_steps_and_conditions": [
            {
                "step_id": "integer or string (e.g., 1, 'Raw Material Mixing', 'Sintering')",
                "process_name": "string (e.g., 'Mixing', 'Thermal Treatment', 'Sintering', 'Grinding', 'Washing', 'Drying')",
                "detailed_description_of_step": "string (What happens in this step)",
                "key_parameters_and_values": [
                    {"parameter_name": "string (e.g., 'Temperature', 'Solvent', 'Atmosphere', 'Pressure', 'Duration', 'Mixing Technique', 'Heating Rate')",
                     "value_or_range": "string (e.g., '500-700', 'deionized water, ethanol', 'inert atmosphere', '0.1-1 MPa', '6-40 hours', 'ball mill')",
                     "unit": "string (e.g., '°C', 'MPa', 'hours')"
                    }
                ]
            }
        ],
        "raw_material_examples_by_type": {
            "sodium_source_examples": ["string (e.g., 'NaF', 'Na2CO3', 'Sodium Perchlorate (for electrolyte)')"],
            "transition_metal_source_examples": ["string (e.g., 'Ferrous Oxalate', 'MnCO3', 'Ni(OH)2')"],
            "phosphate_source_examples": ["string (e.g., 'Sodium Phosphate Monobasic', 'Ammonium Dihydrogen Phosphate')"],
            "halogen_source_examples": ["string (e.g., 'NaF', 'NaCl')"],
            "carbon_source_for_coating_examples": ["string (e.g., 'glucose', 'acetylene black', 'Ketjen black')"],
            "dopant_M_source_examples": ["string (e.g., 'CaO', 'Al2O3', 'TiO2')"]
        }
    },
    "application_details": {
        "primary_application_field": "string (e.g., 'Sodium-ion battery technology', 'Energy Storage')",
        "specific_component_role": "string (e.g., 'Positive electrode active material', 'Cathode material for Na-ion battery')",
        "potential_end_use_devices_or_systems": ["string (e.g., 'electric vehicle (EV)', 'hybrid electric vehicle (HEV)', 'energy storage system (ESS)', 'power tools', 'consumer electronics', '저가형 이륜차 배터리')"]
    },
    "key_claimed_advantages_or_problems_solved_by_invention": [
        "string (List the main advantages, improvements over prior art, or problems the invention aims to solve, often found in Summary or Background sections. E.g., 'Improved powder conductivity leading to better electrochemical performance.', 'Enhanced cycle stability due to single-crystal morphology preventing particle cracking.', 'Simplified preparation method suitable for industrial scale-up.')"
    ],
    "representative_performance_data_from_examples_or_figures": [
        {"metric_name": "string (e.g., 'First Cycle Discharge Specific Capacity', '2C Discharge Specific Capacity', 'Capacity Retention after 50 cycles', 'Powder Resistivity of Example X')",
         "value": "string or number (e.g., '111', '100', '91.03%', '100 ohm-cm')",
         "unit": "string (e.g., 'mAh/g', '%', 'ohm-cm')",
         "conditions_or_context": "string (Test conditions, example ID, or figure reference. E.g., 'Example 3, 0.1C charge/discharge', 'Example 3, Glucose carbon, 3wt% C, 0.1um grain', 'BA-C1, 0.1C/0.1C, 4.0V-2.0V, 45°C, 50 cycles')",
         "source_reference_in_document": "string (e.g., 'Table 1, Example 3', 'Fig. 1', 'Page X, Paragraph Y', '표 4, 실시예 1의 BA-C1')"
        }
    ],
    "document_summary_for_user": "string (A concise 3-5 sentence general summary of the patent's main points based on the entire document text.)",
    "language_of_document": "string",
    "source_file_name": "string (This will be the PDF filename you provide)"
}
"""