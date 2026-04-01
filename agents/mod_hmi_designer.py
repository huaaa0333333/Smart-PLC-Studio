import streamlit as st
from pydantic import BaseModel, Field
from core import prompts
from services.llm_service import generate_structured_content

# 定義 HMI 代理人的專屬結構化輸出
class HMIOutput(BaseModel):
    design_concept: str = Field(description="HMI 設計理念、色彩規範 (如紅停綠走) 與防呆建議")
    wireframe: str = Field(description="使用 ASCII Art 繪製的 HMI 主畫面佈局圖 (必須保持對齊)")
    tag_mapping: str = Field(description="HMI 元件與 PLC 變數的對應表 (Markdown 表格格式)")

def generate_hmi(client, user_input: str) -> HMIOutput:
    """純邏輯：根據系統需求或 I/O 清單生成 HMI 規劃"""
    prompt = prompts.get_hmi_designer_prompt(user_input)
    res, _ = generate_structured_content(
        client=client,
        model='gemini-1.5-pro',
        contents=prompt,
        schema=HMIOutput,
        system_instruction="你是一個嚴謹的 HMI 設計師，產出的 ASCII Wireframe 必須極度對齊且具備工業美感。",
        temperature=0.4
    )
    return res
def render(client):
    st.title("🖥️ HMI 介面規劃師 (HMI Engineer Agent)")
    st.markdown("身為智慧代理人團隊的介面專家，我能根據系統需求與 I/O 清單，自動為您繪製出符合工業標準的 HMI 佈局圖與變數對應表。")
    
    # UI 元件：接收需求
    user_input = st.text_area(
        "請輸入系統需求或已知的 I/O 點位：", 
        height=150, 
        placeholder="例如：這是一個簡單的輸送帶控制系統。輸入包含啟動按鈕、停止按鈕、急停按鈕；輸出包含馬達運轉訊號與狀態指示燈。請幫我設計一個 7 吋的觸控螢幕畫面。"
    )

    if st.button("🎨 啟動 HMI 規劃代理人", type="primary"):
        if not user_input.strip():
            st.warning("請先輸入系統需求或 I/O 清單！")
            return
            
        # 視覺化代理人協作過程 (模擬論文中的 Agent 運作)
        with st.status("🤖 HMI 代理人正在思考中...", expanded=True) as status:
            st.write("📥 接收架構師的 I/O 規格...")
            st.write("📐 正在規劃 7 吋螢幕的 UI/UX 佈局...")
            st.write("🎨 正在應用工業色彩規範與防呆機制...")
            
            try:
                # 呼叫純邏輯函式
                res = generate_hmi(client, user_input)
                status.update(label="✅ HMI 規劃完成！", state="complete", expanded=False)
                
                # 將結果存入專屬歷史紀錄
                st.session_state.history_hmi.insert(0, {
                    "prompt": user_input,
                    "concept": res.design_concept,
                    "wireframe": res.wireframe,
                    "mapping": res.tag_mapping
                })
            except Exception as e:
                status.update(label="❌ 代理人作業失敗", state="error")
                st.error(f"生成異常：{e}")

    # ==========================================
    # 歷史紀錄與展示區塊
    # ==========================================
    st.divider()
    st.markdown("### 🗂️ HMI 規劃圖紙庫")
    
    if "history_hmi" not in st.session_state:
        st.session_state.history_hmi = []
        
    if not st.session_state.history_hmi:
        st.info("尚無設計圖紙。請在上方輸入需求並啟動代理人！")
    else:
        for idx, record in enumerate(st.session_state.history_hmi):
            task_title = f"設計草圖 #{len(st.session_state.history_hmi) - idx} | {record['prompt'][:20]}..."
            with st.expander(task_title, expanded=(idx == 0)):
                st.success(f"**💡 UI/UX 設計理念與規範：**\n{record['concept']}")
                
                st.markdown("#### 📐 HMI 主畫面線框圖 (Wireframe)")
                # 使用 st.code 來強制等寬字體，確保 ASCII Art 絕對不會跑版
                st.code(record['wireframe'], language="text")
                
                st.markdown("#### 🔗 元件與 PLC 變數對應表 (Tag Mapping)")
                st.markdown(record['mapping'])
