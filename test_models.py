import os
from google import genai
from dotenv import load_dotenv

load_dotenv('.env')
print("API KEY length:", len(os.getenv('GEMINI_API_KEY')) if os.getenv('GEMINI_API_KEY') else 0)
client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

models_to_test = [
    'gemini-1.5-pro',
    'gemini-2.0-pro-exp-0205',
    'gemini-2.5-pro',
    'gemini-3.0-pro'
]

for m in models_to_test:
    try:
        response = client.models.generate_content(model=m, contents='Hi')
        print(f"SUCCESS: {m}")
    except Exception as e:
        print(f"FAILED: {m} - {e}")
