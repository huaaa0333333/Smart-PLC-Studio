import json
from pydantic import BaseModel, Field
from core import prompts
from services.llm_service import generate_structured_content
import logging

logger = logging.getLogger(__name__)

class ArchaeologistOutput(BaseModel):
    thinking: str = Field(description="推導過程：解釋舊代碼中特定硬體位址與 M 點的物理意義，以及重構為新結構的理由")
    refactored_scl: str = Field(description="重構且現代化命名後的最佳實踐 SCL 程式碼")
    new_tag_table: str = Field(description="推導出的新版變數表 (CSV格式: Name,DataType,Logical Address,Comment)")

def reverse_engineer_block(client, legacy_xml: str) -> ArchaeologistOutput:
    """使用 AI 代理人讀取並重構舊有 XML Block"""
    prompt = prompts.get_archaeologist_prompt(legacy_xml)
    
    res, raw_text = generate_structured_content(
        client=client,
        model='gemini-2.0-flash',
        contents=prompt,
        schema=ArchaeologistOutput,
        system_instruction="你是一個專精於將祖傳梯形圖與 SCL 轉換為現代化、單一職責、且命名優雅的重構大師。",
        temperature=0.2
    )
    
    if not res:
        # Fallback
        return ArchaeologistOutput(
            thinking="解析失敗，請重新嘗試或檢查 XML 是否過長。",
            refactored_scl="// 解析失敗",
            new_tag_table="Name,DataType,Logical Address,Comment\nParserError,Bool,,Error parsing"
        )
        
    return res
