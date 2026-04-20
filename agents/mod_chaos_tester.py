import json
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from core import prompts
from services.llm_service import generate_structured_content

class ChaosAction(BaseModel):
    action_type: str = Field(description="攻擊手法：'bouncing' (反彈), 'timing' (非法時序), 或 'concurrency' (衝突併發)")
    target_tags: List[str] = Field(description="受到攻擊的輸入變數名稱列表")
    description: str = Field(description="此攻擊動作的具體描述與預期達到的破壞效果")
    parameters: Dict[str, Any] = Field(description="攻擊參數，例如 bouncing 的 duration_ms、concurrency 的 value 組合等", default_factory=dict)

class MonitorCondition(BaseModel):
    condition_name: str = Field(description="監控條件的名稱（例如：馬達短路）")
    logic_expression: str = Field(description="判斷崩潰的邏輯條件（例如：Motor_FWD == True AND Motor_REV == True）")
    severity: str = Field(description="嚴重程度：'HIGH' 或 'CRITICAL'")

class ChaosTestPlan(BaseModel):
    thinking: str = Field(description="針對程式碼弱點的深度分析與攻擊劇本設計思路")
    chaos_actions: List[ChaosAction] = Field(description="排定的連續或併發破壞動作列表")
    monitoring_conditions: List[MonitorCondition] = Field(description="需要嚴密監控並視為『系統崩潰或損壞』的輸出狀態組合")

def generate_chaos_plan(client, scl_code: str, csv_tags: str) -> ChaosTestPlan:
    """使用 AI 代理人產生混亂壓力測試 (Chaos Test) 的攻擊劇本"""
    
    prompt = prompts.get_chaos_tester_prompt(scl_code, csv_tags)
    
    res, raw_text = generate_structured_content(
        client=client,
        model='gemini-2.0-flash',
        contents=prompt,
        schema=ChaosTestPlan,
        system_instruction="你是一個極具破壞性的軟體測試專家 (Chaos Agent)，擅長透過邊界條件、信號反彈與併發衝突等手段來催毀脆弱的 PLC 程式邏輯。",
        temperature=0.4 # Higher temperature for more creative attacks
    )
    
    if not res:
        # Fallback if generation fails
        return ChaosTestPlan(
            thinking="無法成功產生混亂劇本，退回預設基礎測試。",
            chaos_actions=[
                ChaosAction(
                    action_type="bouncing",
                    target_tags=["Start_Btn"],
                    description="對啟動按鈕進行基本的 100ms 抖動測試",
                    parameters={"duration_ms": 100, "toggles": 5}
                )
            ],
            monitoring_conditions=[]
        )
        
    return res
