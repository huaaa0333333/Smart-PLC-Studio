import os

files = [
    'services/llm_service.py',
    'scripts/manual_to_qa.py',
    'scripts/extract_io_mapping.py',
    'scripts/extract_advanced.py',
    'agents/mod_pdf_solver.py',
    'agents/mod_hmi_designer.py',
    'agents/mod_generator.py',
    'agents/mod_bug_clinic.py',
    'agents/mod_batch.py',
    'agents/mod_architecture_designer.py',
    'ui.py'
]

for f in files:
    if os.path.exists(f):
        with open(f, 'r', encoding='utf-8') as file:
            content = file.read()
        content = content.replace('gemini-3.0-pro', 'gemini-1.5-pro')
        content = content.replace('Gemini 3.0 Pro', 'Gemini 1.5 Pro')
        with open(f, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f"Updated {f}")
