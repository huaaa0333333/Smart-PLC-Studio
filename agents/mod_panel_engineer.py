import streamlit as st
import json
import os
import io
from pydantic import BaseModel, Field
import pandas as pd
from core import prompts
from services.llm_service import generate_structured_content

class BOMItem(BaseModel):
    category: str = Field(description="分類 (PLC / HMI / Power / Protection / Switching / Terminal / Accessories 等)")
    part_name: str = Field(description="元件名稱")
    model_number: str = Field(description="型號/料號")
    quantity: int = Field(description="數量")
    unit: str = Field(description="單位 (台/只/A/...)")
    remark: str = Field(description="備註")

class PanelEngineeringOutput(BaseModel):
    plc_selection: str = Field(description="選定的 PLC 型號")
    hmi_selection: str = Field(description="選定的 HMI 型號")
    panel_spec: str = Field(description="控制箱的整體規格描述（尺寸預估、防護等級如IP54、散熱與走線規劃）")
    bom_items: list[BOMItem] = Field(description="詳細的控制箱元件 BOM 表")
    panel_wireframe: str = Field(description="使用 ASCII Art 繪製的盤面佈局線框圖")
    wiring_notes: str = Field(description="配線與工安注意事項")

def _load_catalog(filename: str) -> dict:
    """讀取 JSON 型錄"""
    catalog_path = os.path.join(os.path.dirname(__file__), '..', 'data', filename)
    if not os.path.exists(catalog_path):
        catalog_path = f'data/{filename}'
    try:
        with open(catalog_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def format_catalog_options(catalog: dict) -> str:
    if not catalog:
        return ""
    lines = [f"  - {name}" for name in catalog.keys()]
    return "\n".join(lines)

def generate_panel_engineering(client, user_input: str) -> PanelEngineeringOutput:
    """產生控制箱工程規劃結果"""
    plc_catalog = _load_catalog('plc_catalog.json')
    hmi_catalog = _load_catalog('hmi_catalog.json')
    
    plc_options = format_catalog_options(plc_catalog)
    hmi_options = format_catalog_options(hmi_catalog)

    prompt = prompts.get_panel_engineer_prompt(user_input, plc_options, hmi_options)
    
    res, raw_text = generate_structured_content(
        client=client,
        model='gemini-2.5-flash',
        contents=prompt,
        schema=PanelEngineeringOutput,
        system_instruction="你是一個嚴謹且具備高度工安意識的自動化硬體與控制箱設計工程師。",
        temperature=0.2
    )
    if not res:
        raise ValueError(f"控制箱工程規劃產生失敗，無法解析為標準輸出格式！原始模型輸出:\n{raw_text}")
    return res

def export_bom_to_excel(bom_items: list[BOMItem]) -> bytes:
    """將 BOM_items 轉換為 Excel 二進位內容供下載"""
    data = []
    for item in bom_items:
        data.append({
            "分類": item.category,
            "元件名稱": item.part_name,
            "型號/料號": item.model_number,
            "數量": item.quantity,
            "單位": item.unit,
            "備註": item.remark
        })
    df = pd.DataFrame(data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='BOM')
        # 調整欄寬
        worksheet = writer.sheets['BOM']
        for column in worksheet.columns:
            max_length = 0
            column = [cell for cell in column]
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2)
            worksheet.column_dimensions[column[0].column_letter].width = adjusted_width
            
    processed_data = output.getvalue()
    return processed_data
