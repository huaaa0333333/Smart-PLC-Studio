import streamlit as st
import json
from pydantic import BaseModel, Field
from typing import List
from core import prompts
from core.config import DEFAULT_MODEL
from services.llm_service import generate_structured_content

class SafetyAuditOutput(BaseModel):
    thinking: str = Field(description="針對程式碼安全性進行深度思考與邏輯推演過程")
    safety_score: int = Field(description="安全評分 (0-100)，若存在嚴重危險（如缺少互鎖）則必須低於 60 分")
    critical_risks: List[str] = Field(description="偵測到的嚴重安全風險列表 (例如：馬達缺少互鎖、急停未切斷輸出)")
    safety_features_found: List[str] = Field(description="程式碼中已正確實作的安全保護機制")
    recommendations: str = Field(description="給予生成器的具體修正建議，描述如何解決上述風險")

def audit_safety(client, scl_code: str, csv_tags: str) -> SafetyAuditOutput:
    """使用 AI 代理人進行工業安全性稽核"""
    
    prompt = prompts.get_safety_auditor_prompt(scl_code, csv_tags)
    
    res, raw_text = generate_structured_content(
        client=client,
        model=DEFAULT_MODEL,
        contents=prompt,
        schema=SafetyAuditOutput,
        system_instruction="你是一個嚴謹的工業安全專家 (Safety Auditor)，擅長抓出 PLC 程式碼中的隱藏風險，例如致死或毀損設備的邏輯漏洞。",
        temperature=0.1
    )
    
    if not res:
        # 降級處理：如果無法產生結構化 JSON，則手動回傳一個低分並報錯
        return SafetyAuditOutput(
            thinking="解析失敗，模型輸出不符合 JSON 格式。",
            safety_score=30,
            critical_risks=["無法完成自動安全性稽核，系統預設視為高風險"],
            safety_features_found=[],
            recommendations="請重新檢查程式碼邏輯，並確保模型輸出完整。"
        )
        
    return res
