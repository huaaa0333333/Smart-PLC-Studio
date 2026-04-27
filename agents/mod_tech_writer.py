import json
from pydantic import BaseModel, Field
from core import prompts
from core.config import DEFAULT_MODEL
from services.llm_service import generate_structured_content
import logging

logger = logging.getLogger(__name__)

class TechManualOutput(BaseModel):
    thinking: str = Field(description="編纂手冊的邏輯推導，描述如何翻譯程式碼與建立故障排除表")
    mermaid_chart: str = Field(description="純粹的 Mermaid.js 語法腳本，不包含 markdown backticks")
    markdown_manual: str = Field(description="高度格式化且符合 ISO/IEC 標準的系統維護手冊全文 (Markdown格式)")

def generate_tech_manual(
    client, 
    bom_data: str, 
    io_tags: str, 
    scl_code: str, 
    safety_chaos_log: str
) -> TechManualOutput:
    """使用 AI 代理人聚合資料並生成標準化技術手冊"""
    prompt = prompts.get_tech_writer_prompt(bom_data, io_tags, scl_code, safety_chaos_log)
    
    res, raw_text = generate_structured_content(
        client=client,
        model=DEFAULT_MODEL,
        contents=prompt,
        schema=TechManualOutput,
        system_instruction="你是一位專精於撰寫工業 ISO/IEC 標準備準檔案的資深技術寫手，非常擅長把程式邏輯翻譯為人類語言，且絕對確保手冊的變數名稱與實體程式碼完全吻合。",
        temperature=0.3
    )
    
    if not res:
        # Fallback
        return TechManualOutput(
            thinking="手冊生成失敗",
            mermaid_chart="graph TD;\n  A[Error] --> B[Failed to generate manual];",
            markdown_manual="# 系統維護手冊\n\n自動編纂失敗，請檢查輸入內容是否過長。"
        )
        
    return res
