from google.genai import types

def generate_structured_content(client, model='gemini-2.5-flash', contents=None, schema=None, system_instruction=None, temperature=0.1):
    """
    通用的大語言模型呼叫服務，處理 Gemini API 的結構化輸出呼叫。
    """
    try:
        config_kwargs = {
            "temperature": temperature,
            "response_mime_type": "application/json",
            "response_schema": schema
        }
        if system_instruction:
            config_kwargs["system_instruction"] = system_instruction
            
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(**config_kwargs)
        )
        return response.parsed, response.text
    except Exception as e:
        raise Exception(f"模型生成錯誤: {e}")
