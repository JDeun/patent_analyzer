# prompts.py

PATENT_DATA_SCHEMA_FOR_LLM_PROMPT_FULL = """
You are an expert in chemistry and material science patent analysis.
Given the full text of a patent document (provided below), extract the specified information
and structure it as a JSON object. Populate all fields as accurately and completely as possible
based ONLY on the provided text. If information for a field is not found, use null or an
empty string/list as appropriate for that field type.

IMPORTANT DATA FORMATTING INSTRUCTIONS:

1.  **Language for Extracted Values**:
    * All extracted textual values (strings) MUST be in **English**, unless specified otherwise below. This includes technical terms, descriptions, roles, purposes, etc.
    * **Exceptions to English-only**:
        * `title_original_language`: This field should contain the title in its original language.
        * `applicants`, `inventors`: For names of people or companies, provide the most common English representation if readily available (e.g., "Samsung Electronics Co., Ltd."). If an official English name is not apparent, provide the name as it appears in the original document, followed by a Romanized version in parentheses if applicable (e.g., "삼성전자 (Samsung Jeonja)"). Strive for consistency.
        * Proper nouns like specific geographical locations or unique, untranslatable trade names if they do not have a common English equivalent.
        * Direct quotes from the patent text if specifically requested by a field description (though generally, information should be summarized or categorized in English).
    * Fields like `document_summary_for_user` should also be in clear English.

2.  **Chemical Terminology**:
    * For all chemical formulas, element names, or lists of chemical elements (e.g., in 'chemical_formula_general', 'elements_involved', 'chemical_identity'), YOU MUST USE standard English chemical symbols (e.g., 'Fe', 'NaCl', 'H2O', ['Ti', 'V', 'Al']). Do not use full element names (e.g., 'Iron') or names in other languages.

3.  **Date Format**:
    * All date information (e.g., `publication_date`, `filing_date`, `priority_date`) MUST be extracted and formatted as **'YYYY-MM-DD'**.
    * If only partial date information is available (e.g., "March 2022"), attempt to fit it into 'YYYY-MM-DD' as best as possible (e.g., '2022-03-DD' or provide as '2022-03' if day is unknown and note uncertainty if possible, though 'YYYY-MM-DD' is strongly preferred). If conversion is impossible, provide the date as written in the original text and add a note in a relevant description field if such a field exists for that specific item. For the primary date fields, strive for 'YYYY-MM-DD'.

4.  **Units, Conditions, Ranges**:
    * Pay close attention to units, conditions, and ranges. Where possible, use SI units or units commonly accepted in the specific scientific field (e.g., 'mAh/g', 'S/cm', '°C', 'wt%').
    * For numerical ranges, clearly specify 'X to Y', 'X-Y', '>=X', '<=Y'. If a preferred or optimal value is given alongside a range, capture both if the schema allows.

5.  **General Field Population**:
    * Populate all fields as accurately and completely as possible based ONLY on the provided text.
    * If information for a field is not found, use `null` for singular optional fields or an empty list `[]` for list-type fields. Use an empty string `""` only if the field is a required string and truly represents an empty text value found in the patent (which is rare for most descriptive fields). Prefer `null` for absent optional string information.

The 'language_of_document' should be the primary language identified in the text (e.g., 'English', 'Korean', 'Japanese', 'Chinese').
The 'source_file_name' will be provided to you and should be included in the JSON output.
The 'document_summary_for_user' field should contain a concise 3-5 sentence general summary of the patent's main points, in English, focusing on the invention's purpose, key materials/methods, and primary advantages.

The desired JSON output structure is as follows:

{
    "patent_info": {
        "publication_number": "string (e.g., 'EP 3 968 410 A1', 'US 11,000,000 B2', 'KR 10-2024-0011099 A')",
        "publication_date": "string (MUST be 'YYYY-MM-DD', e.g., '2022-03-16')",
        "application_number": "string (e.g., '20859053.9', '10-2023-0092193', '17/123,456')",
        "filing_date": "string (MUST be 'YYYY-MM-DD', e.g., '2020-08-28')",
        "priority_data": [
            {
                "priority_number": "string (e.g., 'CN 201910800432', 'US 63/123,456', 'KR 10-2022-0001234')",
                "priority_date": "string (MUST be 'YYYY-MM-DD')",
                "priority_country": "string (2-letter ISO country code like 'CN', 'KR', 'US', 'EP', 'JP'. If WIPO, use 'WO'.)"
            }
        ],
        "applicants": ["string (List all applicants. Provide English names if available, otherwise original name with Romanization if applicable. E.g., 'Contemporary Amperex Technology Co., Limited', 'LG Energy Solution, Ltd.', 'Samsung Electronics Co., Ltd.', 'Guizhou Zhenhua E-chem Inc.')"],
        "inventors": ["string (List all inventors. Provide English names if available (e.g., LASTNAME, Firstname), otherwise original name with Romanization if applicable. E.g., 'LIU, Qian', 'KIM, Chul-Soo', 'Zhou, Chaoyi')"],
        "title_original_language": "string (The full title as it appears in its original language. This field is an exception to the English-only rule.)",
        "title_english_translation": "string (If original title is not in English, provide an accurate English translation. If already English, this can be the same as title_original_language.)"
    },
    "material_description": {
        "application_focus": "string (English. Briefly describe the main application or purpose of the material, e.g., 'Positive electrode material for sodium-ion battery', 'Single-crystal cathode material for sodium-ion batteries', 'Electrolyte for lithium-sulfur batteries')",
        "material_system_type": "string (English. General classification of the material, e.g., 'Sodium Halophosphate-Carbon Composite', 'Layered Oxide (O3-type)', 'Phosphate-based material', 'Solid Polymer Electrolyte')",
        "chemical_formula_general": "string (The most representative general chemical formula presented, using standard chemical symbols. E.g., 'Na2M1hM2k(PO4)X/C', 'Na(1+a)Ni(1-x-y-z)Mn(x)Fe(y)M(z)O2', 'LiNi(x)Mn(y)Co(z)O2 where x+y+z=1')",
        "formula_parameters": [
            {
                "parameter_name": "string (The variable/symbol in the formula, e.g., 'M1', 'h', 'X', 'a', 'x', 'M')",
                "elements_involved": ["string (List of standard chemical symbols this parameter can represent. MUST use standard chemical symbols ONLY. E.g., ['Ti', 'V', 'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn'] or ['F', 'Cl', 'Br', 'I'])"],
                "value_range": "string (Stoichiometric range or value, e.g., '0 <= x <= 1', 'h+k=1', '-0.40 <= a <= 0.25', '0.01 < z < 0.1')",
                "preferred_value_range": "string (If a preferred or optional narrower range is specified, e.g., '0.1 <= x <= 0.5', 'optionally a = 0')",
                "description": "string (English. Brief explanation of the parameter, e.g., 'Transition metal ion', 'Halogen ion', 'Stoichiometric coefficient for Na', 'Dopant element M')"
            }
        ],
        "key_additive_or_dopant_info": [
            {
                "type_or_name": "string (English. Name or type of the additive/dopant, e.g., 'Carbon coating', 'M element doping', 'Binder XYZ', 'LiF additive')",
                "chemical_identity": "string (Chemical formula or symbol. MUST use standard chemical symbols or formulas. E.g., 'C', 'Al2O3', 'TiO2', 'PVDF', 'LiF', 'Mg')",
                "role_or_purpose": "string (English. E.g., 'Improve conductivity', 'Enhance structural stability', 'Electrode binder', 'Suppress dendrite growth', 'Improve thermal stability')",
                "content_description": "string (English. Amount or concentration, including units. E.g., '0.05 wt% to 15 wt%', 'z from 0.01 to 0.05 in the formula', 'typically 1-5 wt% of electrode mass', '10 mol% relative to Li salts')",
                "source_materials_if_specified": ["string (English name or formula of precursor materials if specified for this additive/dopant. E.g., 'glucose for carbon', 'acetylene black', 'Al(NO3)3 for Al doping')"]
            }
        ]
    },
    "morphology_structure": {
        "particle_form_summary": "string (English. Overall description of the particle nature, e.g., 'Composite of sodium halophosphate with carbon', 'Single-crystal particles with specific facets', 'Polycrystalline agglomerates of nano-sized primary particles', 'Core-shell structure')",
        "primary_particle_shape_observed": ["string (English. Observed shapes, using standard terms. E.g., 'spherical', 'quasi-spherical', 'polyhedral', 'rod-like', 'platelet', 'flake', 'nanowire', 'irregular')"],
        "size_metrics": [
             {"metric_type": "string (English. E.g., 'Primary Particle Size D50', 'Secondary Particle Size (Agglomerate) D50', 'Grain Size', 'Average Particle Diameter', 'Crystallite Size')", "unit": "string (e.g., 'nm', 'micron', 'Å')", "value_range": "string (e.g., '50 to 500', '2.0-16.0', '>100')", "preferred_value_range": "string (If specified, e.g., '100 to 200', '4.0-13.0', 'preferably <10 micron')"}
        ],
        "specific_surface_area_BET_m2_g": {"value_range": "string (e.g., '0.01 to 30 m2/g', '0.35-1.2 m2/g')", "preferred_value_range": "string (If specified, e.g., '1 to 20 m2/g', 'preferably > 0.5 m2/g')"},
        "density_g_cm3": [
            {"type": "string (English. E.g., 'tap density', 'compacted density', 'true density', 'powder densification')",
             "value_range": "string (e.g., '0.5 to 2.5 g/cm3', '2.8-4.2 g/cm3')",
             "conditions": "string (English. If specified, e.g., 'under a pressure of 8 tons', 'after 100 taps', 'measured by helium pycnometry')",
             "preferred_value_range": "string (If specified, e.g., '0.7 to 2.0 g/cm3', 'ideally > 3.0 g/cm3')"}
        ],
        "crystallinity_features": [
            {"feature_type": "string (English. E.g., 'XRD Peak Position (2-theta)', 'XRD FWHM', 'Crystal Structure Type', 'Degree of Crystallinity', 'Lattice Parameters (a, b, c, alpha, beta, gamma)')",
             "details": "string (English. E.g., 'Peak (110) at 2-theta approx 64.9 deg: FWHM range 0.06-0.35 deg', 'Identified as O3 layered structure by XRD analysis', 'Degree of crystallinity > 80%', 'a=3.05Å, c=10.2Å for hexagonal phase')"
            }
        ],
        "coating_information": {
            "is_coated": "boolean (true if coating is explicitly mentioned as being applied to the primary material, false otherwise)",
            "coating_material": "string (Chemical identity of the coating material using standard symbols/formulas. E.g., 'Carbon', 'Al2O3', 'LiNbO3', 'PEDOT:PSS'. If multiple layers, list them or describe composite.)",
            "coating_thickness": "string (Including units, e.g., '5-20 nm', 'approx. 1 micron', '<100 nm')",
            "coating_purpose": "string (English. E.g., 'Enhance electronic conductivity', 'Protect from electrolyte attack', 'Improve thermal stability', 'Suppress phase transition')",
            "coating_method_if_specified": "string (English. E.g., 'Sol-gel method', 'Chemical Vapor Deposition (CVD)', 'Atomic Layer Deposition (ALD)', 'Wet coating')"
        }
    },
    "physical_chemical_properties_specific": [
         {"property_name": "string (English. E.g., 'Powder Resistivity', 'Ionic Conductivity', 'Moisture Content', 'pH Value', 'Thermal Stability Onset', 'Decomposition Temperature')",
          "unit": "string (e.g., 'ohm-cm', 'S/cm', 'ppm', '', '°C')",
          "value_or_range": "string (e.g., '10 to 5000', '1.2 x 10^-4', '<3000', 'approx. 11.5', '> 250', 'Td = 280')",
          "conditions_of_measurement": "string (English. E.g., 'under a pressure of 12 MPa', 'at 25 °C', 'for a 10% suspension in deionized water', 'TGA analysis under N2 atmosphere at 10°C/min heating rate')",
          "preferred_value_or_range": "string (If specified, e.g., '20 to 2000', '<1000 ppm', 'preferably > 1 x 10^-3 S/cm')"}
    ],
    "preparation_method_summary": {
        "overall_synthesis_route_description": "string (English. Brief overview of the method, e.g., 'Solid-state reaction method', 'Co-precipitation followed by calcination and carbon coating', 'Hydrothermal synthesis with subsequent annealing', 'Spray pyrolysis')",
        "key_steps_and_conditions": [
            {
                "step_id": "integer or string (e.g., 1, 'S1: Raw Material Mixing', 'Calcination Step')",
                "process_name": "string (English. E.g., 'Mixing', 'Milling', 'Pre-sintering', 'Main Sintering', 'Calcination', 'Grinding', 'Washing', 'Drying', 'Coating Application')",
                "detailed_description_of_step": "string (English. What happens in this step, key reagents or transformations)",
                "key_parameters_and_values": [
                    {"parameter_name": "string (English. E.g., 'Temperature', 'Solvent', 'Atmosphere', 'Pressure', 'Duration', 'Mixing Technique', 'Heating Rate', 'pH', 'Molar Ratios of Precursors')",
                     "value_or_range": "string (e.g., '500-700', 'deionized water, ethanol', 'Inert atmosphere (Ar, N2)', '0.1-1 MPa', '6-40 hours', 'Planetary ball mill for 2h', '5 °C/min', 'pH adjusted to 9 with NH4OH', 'Na:P:M = 2.1:1:1')",
                     "unit": "string (e.g., '°C', 'MPa', 'hours', 'rpm')"
                    }
                ]
            }
        ],
        "raw_material_examples_by_type": {
            "sodium_source_examples": ["string (List specific chemical compounds using standard formulas. E.g., 'Na2CO3', 'NaF', 'NaOH', 'CH3COONa')"],
            "lithium_source_examples": ["string (List specific chemical compounds using standard formulas. E.g., 'Li2CO3', 'LiOH', 'LiNO3')"],
            "transition_metal_source_examples": ["string (List specific chemical compounds using standard formulas. E.g., 'FeC2O4·2H2O', 'MnCO3', 'Ni(OH)2', 'V2O5', 'TiO2', 'FePO4')"],
            "phosphate_source_examples": ["string (List specific chemical compounds using standard formulas. E.g., '(NH4)2HPO4', 'NH4H2PO4', 'NaH2PO4', 'Li3PO4')"],
            "halogen_source_examples": ["string (List specific chemical compounds using standard formulas. E.g., 'NaF', 'NaCl', 'NH4F', 'LiCl')"],
            "carbon_source_for_coating_examples": ["string (English name or common term. E.g., 'glucose', 'sucrose', 'acetylene black', 'Ketjen black', 'pitch')"],
            "dopant_M_source_examples": ["string (Source materials for dopants, using standard formulas. E.g., 'Al2O3 for Al', 'MgO for Mg', 'Ti(OC4H9)4 for Ti')"],
            "other_precursor_examples": ["string (English name or formula for other notable precursors. E.g., 'S powder for Li-S batteries', 'SiO2 for silicate materials')"]
        }
    },
    "application_details": {
        "primary_application_field": "string (English. E.g., 'Sodium-ion battery technology', 'Lithium-ion battery technology', 'Energy Storage Systems', 'Solid-state batteries')",
        "specific_component_role": "string (English. E.g., 'Positive electrode active material', 'Cathode material for Na-ion battery', 'Anode material for Li-ion battery', 'Solid electrolyte separator', 'Electrolyte additive')",
        "potential_end_use_devices_or_systems": ["string (English. List potential devices or systems. E.g., 'electric vehicle (EV)', 'hybrid electric vehicle (HEV)', 'energy storage system (ESS)', 'power tools', 'consumer electronics', 'low-cost two-wheeler batteries', 'grid-scale storage')"]
    },
    "key_claimed_advantages_or_problems_solved_by_invention": [
        "string (English. List the main advantages, improvements over prior art, or problems the invention aims to solve, often found in Summary, Background, or Claims sections. Be specific. E.g., 'Improved powder electronic conductivity leading to better rate capability.', 'Enhanced cycle stability due to single-crystal morphology preventing particle cracking.', 'Simplified preparation method suitable for industrial scale-up using lower temperatures.', 'Achieved higher specific capacity compared to undoped material X.', 'Reduced voltage hysteresis.', 'Improved safety characteristics by suppressing thermal runaway.')"
    ],
    "representative_performance_data_from_examples_or_figures": [
        {"metric_name": "string (English. E.g., 'First Cycle Discharge Specific Capacity', 'Initial Coulombic Efficiency', 'Capacity Retention after X cycles', 'Rate Capability (e.g., Discharge capacity at 2C/0.1C ratio)', 'Ionic Conductivity at 25°C', 'Electrochemical Impedance (Charge Transfer Resistance Rct)')",
         "value": "string or number (e.g., '111', '92.5%', '91.03% after 100 cycles', '85% (2C/0.1C)', '1.5 x 10^-4', '55 ohm')",
         "unit": "string (e.g., 'mAh/g', '%', 'S/cm', 'ohm', 'Wh/kg')",
         "conditions_or_context": "string (English. Test conditions, example ID, or figure reference. E.g., 'Example 3, 0.1C charge/discharge, 2.0-4.0V vs Na/Na+', 'Fig. 5a, after 100 cycles at 1C rate', 'BA-C1, 0.1C/0.1C, 4.0V-2.0V, 45°C, 50 cycles', 'Measured using AC impedance spectroscopy with blocking electrodes')",
         "source_reference_in_document": "string (English. E.g., 'Table 1, Example 3', 'Fig. 1a', 'Page X, Paragraph Y', 'Claim 5', '[0088]')"}
    ],
    "document_summary_for_user": "string (English. A concise 3-5 sentence general summary of the patent's main points based on the entire document text. Focus on: What is the invention? What problem does it solve or what is its main purpose? What are the key materials or methods used? What are the claimed primary benefits or outcomes?)",
    "language_of_document": "string (The primary language of the document, e.g., 'English', 'Korean', 'Japanese', 'Chinese')",
    "source_file_name": "string (This will be the PDF filename you provide)"
}
"""