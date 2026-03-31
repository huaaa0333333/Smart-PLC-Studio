import streamlit as st
from pydantic import BaseModel, Field
from core import prompts
from core import utils
from services.llm_service import generate_structured_content

# 定義架構師的專屬結構化輸出
class ArchitectureOutput(BaseModel):
    req_analysis: str = Field(description="系統需求分析 (包含 I/O 總數統計、特殊通訊或安全機制評估)")
    hardware_selection: str = Field(description="硬體架構設計與 PLC 選型 (建議適合的 PLC 廠牌型號及選用理由)")
    io_allocation: str = Field(description="I/O 點位配置表 (以 Markdown 表格呈現，包含變數名稱、類型、節點說明)")

def generate_architecture(client, user_input: str) -> ArchitectureOutput:
    """純邏輯：根據使用者需求生成硬體與 I/O 架構"""
    prompt = prompts.get_architecture_prompt(user_input)
    res, _ = generate_structured_content(
        client=client,
        model='gemini-3.0-pro',
        contents=prompt,
        schema=ArchitectureOutput,
        system_instruction="你是一個嚴謹且具備高度工安意識的自動化系統架構師。",
        temperature=0.2
    )
    return res

def render(client):
    st.title("🧠 PLC 架構設計師 (Architecture Designer)")
    st.markdown("身為團隊的首席架構師，我能將您口語化、模糊的專案需求，轉化為嚴謹的系統需求分析、硬體選型建議與標準化的 I/O 點位配置表。")
    
    # UI 元件：接收模糊需求
    user_input = st.text_area(
        "請輸入您的口語化專案需求：", 
        height=150, 
        placeholder="例如：老闆要我做一個輸送帶，按下啟動按鈕馬達就會轉，有綠色運轉燈，還要能按急停按鈕讓整台機器瞬間停下來。預算不高，越簡單越好。"
    )

    if st.button("📐 啟動架構規劃", type="primary"):
        if not user_input.strip():
            st.warning("請先輸入您的專案需求！")
            return
            
        # 視覺化代理人協作過程
        with st.status("🤖 架構設計師正在評估系統...", expanded=True) as status:
            st.write("🔍 正在進行系統需求與安全機制分析...")
            st.write("⚙️ 正在評估適合的 PLC 硬體規格...")
            st.write("📋 正在編列 I/O 節點配置表...")
            
            try:
                # 呼叫純邏輯函式
                res = generate_architecture(client, user_input)
                status.update(label="✅ 架構規劃完成！", state="complete", expanded=False)
                
                # 將結果存入專屬歷史紀錄
                st.session_state.history_arch.insert(0, {
                    "prompt": user_input,
                    "analysis": res.req_analysis,
                    "hardware": res.hardware_selection,
                    "io": res.io_allocation
                })
            except Exception as e:
                status.update(label="❌ 代理人作業失敗", state="error")
                st.error(f"生成異常：{e}")

    # ==========================================
    # 歷史紀錄與展示區塊
    # ==========================================
    st.divider()
    st.markdown("### 🗂️ 系統架構規劃書")
    
    if "history_arch" not in st.session_state:
        st.session_state.history_arch = []
        
    if not st.session_state.history_arch:
        st.info("尚無規劃書。請在上方輸入需求並啟動架構師！")
    else:
        for idx, record in enumerate(st.session_state.history_arch):
            task_title = f"架構專案 #{len(st.session_state.history_arch) - idx} | {record['prompt'][:20]}..."
            with st.expander(task_title, expanded=(idx == 0)):
                
                st.markdown("#### 1️⃣ 系統需求分析 (System Requirements Analysis)")
                st.info(record['analysis'].replace('. ', '。\n\n').replace('。 ', '。\n\n'))
                
                st.markdown("#### 2️⃣ 硬體架構與選型 (Hardware Architecture Design)")
                st.success(record['hardware'].replace('. ', '。\n\n').replace('。 ', '。\n\n'))
                
                st.markdown("#### 3️⃣ I/O 點位配置表 (I/O Allocation)")
                st.markdown(record['io'].replace('||', '|\n|'))
