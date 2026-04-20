import stat
import time
import threading
import logging
from typing import List, Dict
import pandas as pd
import snap7
from snap7.util import set_bool, get_bool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ChaosRunner")

class ChaosEngine:
    def __init__(self, ip: str = '192.168.0.1', rack: int = 0, slot: int = 1):
        """初始化 Snap7 客戶端以連接 PLCSIM Advanced"""
        self.ip = ip
        self.rack = rack
        self.slot = slot
        self.client = snap7.client.Client()
        self.connected = False
        
        # 用於解析變數表位址的內部映射字典
        self.tag_map = {} 

    def connect(self) -> bool:
        """連接至 PLCSIM Advanced"""
        try:
            # 這裡假設 PLCSIM Advanced 虛擬網卡已經設置好並運行中
            self.client.connect(self.ip, self.rack, self.slot)
            self.connected = self.client.get_connected()
            if self.connected:
                logger.info(f"✅ 成功連接至 PLC模擬器 ({self.ip})")
            else:
                logger.error(f"❌ 無法連接至 PLC模擬器 ({self.ip})")
            return self.connected
        except Exception as e:
            logger.error(f"❌ 連接 PLC 時發生錯誤: {e}")
            return False

    def disconnect(self):
        if self.connected:
            self.client.disconnect()
            self.connected = False
            logger.info("🔌 已斷開 PLC 連接")

    def load_tag_table(self, csv_tags: str):
        """解析 CSV 變數表以建立 Tag 名稱到記憶體位址的映射。
           在此簡化實作中，假設是 I 點與 Q 點的 Bool 型態，例如 %I0.0, %Q0.1"""
        import io
        import re
        try:
            df = pd.read_csv(io.StringIO(csv_tags), dtype=str)
            for _, row in df.iterrows():
                name = row.get("Name", "")
                addr = row.get("Logical Address", "")
                if name and addr:
                    # 簡易解析: %I0.0 -> area(I), byte(0), bit(0)
                    match = re.match(r"%([IQM])(\d+)\.(\d+)", addr)
                    if match:
                        area_str, byte_str, bit_str = match.groups()
                        area = snap7.types.Areas.PA if area_str == 'I' else (
                               snap7.types.Areas.PE if area_str == 'Q' else snap7.types.Areas.MK)
                        self.tag_map[name] = {
                            "area": area,
                            "byte": int(byte_str),
                            "bit": int(bit_str)
                        }
            logger.info(f"✅ 成功解析 {len(self.tag_map)} 個 PLC 變數映射。")
        except Exception as e:
            logger.error(f"解析變數表失敗: {e}")

    def write_tag_bool(self, tag_name: str, value: bool):
        """向指定的 Tag 寫入布林值"""
        if not self.connected or tag_name not in self.tag_map:
            return
            
        tag = self.tag_map[tag_name]
        try:
            # 讀取該 byte 的現有狀態
            data = self.client.read_area(tag["area"], 0, tag["byte"], 1)
            # 修改對應 bit
            set_bool(data, 0, tag["bit"], value)
            # 寫回 PLC
            self.client.write_area(tag["area"], 0, tag["byte"], data)
            logger.debug(f">> 寫入 {tag_name} = {value}")
        except Exception as e:
            logger.error(f"寫入變數 {tag_name} 失敗: {e}")

    def read_tag_bool(self, tag_name: str) -> bool:
        """讀取指定的 Tag 布林值"""
        if not self.connected or tag_name not in self.tag_map:
            return False
            
        tag = self.tag_map[tag_name]
        try:
            data = self.client.read_area(tag["area"], 0, tag["byte"], 1)
            return get_bool(data, 0, tag["bit"])
        except Exception as e:
            logger.error(f"讀取變數 {tag_name} 失敗: {e}")
            return False

    def execute_chaos_action(self, action: 'ChaosAction'): # type: ignore
        """執行大腦傳來的單一破壞動作"""
        action_type = action.action_type
        targets = action.target_tags
        params = action.parameters
        
        logger.info(f"🧨 執行 Chaos Action [{action_type}]: 攻擊目標 {targets} - {action.description}")
        
        if action_type == "bouncing":
            # 信號反彈 (Signal Bouncing)
            # 在極短時間內切換 True/False
            toggles = params.get("toggles", 10)
            delay = params.get("duration_ms", 100) / toggles / 1000.0
            for _ in range(toggles):
                for t in targets:
                    self.write_tag_bool(t, True)
                time.sleep(delay)
                for t in targets:
                    self.write_tag_bool(t, False)
                time.sleep(delay)
                
        elif action_type == "concurrency":
            # 衝突併發 (Concurrency Conflict)
            # 同時將衝突按鈕都壓下
            val_to_set = params.get("value", True)
            for t in targets:
                self.write_tag_bool(t, val_to_set)
                
        elif action_type == "timing":
            # 非法時序 (Illegal Timing)
            # 強制寫入並保持一段時間
            hold_sec = params.get("hold_time_ms", 500) / 1000.0
            for t in targets:
                self.write_tag_bool(t, True)
            time.sleep(hold_sec)
            for t in targets:
                self.write_tag_bool(t, False)

    def run_chaos_test(self, plan: 'ChaosTestPlan', csv_tags: str) -> List[str]: # type: ignore
        """執行整套混沌測試，並回傳發生的災難日誌"""
        self.load_tag_table(csv_tags)
        
        # 注意：實際開發中，PLCSIM 啟動通常需要約 30 秒至 1 分鐘，並要確保虛擬 IP 正確
        # 這裡會嘗試連接，若失敗則回傳模擬日誌供 UI 展示
        if not self.connect():
            logger.warning("未能真實連接 PLCSIM Advanced 實體，將返回【模擬執行日誌】。請確保環境內已啟動 PLCSIM Adv. 並將 IP 設為 192.168.0.1。")
            
            # (模擬回傳) - 在未連接硬體的情況下，假裝執行並回饋結果以延續展示流程
            sim_report = []
            sim_report.append(f"🔌 嘗試連接 PLCSIM Advanced (192.168.0.1)... 未連接實體設備。進入模擬預演模式。")
            for act in plan.chaos_actions:
                sim_report.append(f"🧨 [執行攻擊] {act.action_type} 針對 {act.target_tags}")
                sim_report.append(f"   👉 預期破壞結果: {act.description}")
            sim_report.append("🚨 壓力測試完成。")
            return sim_report
            
        # 若成功連線的真實測試邏輯
        report = []
        report.append(f"🔌 成功建立與 PLCSIM 高頻 Snap7 通訊。")
        
        # 啟動監控線程
        stop_monitoring = False
        def monitor_task():
            while not stop_monitoring:
                for cond in plan.monitoring_conditions:
                    # 簡易邏輯解析: "Motor_FWD == True AND Motor_REV == True"
                    # 此處僅為示意，實務上需寫 parser。我們簡易驗證 target 是否同時為 True
                    if " AND " in cond.logic_expression:
                        vars_to_check = [v.split("==")[0].strip() for v in cond.logic_expression.split("AND")]
                        all_true = True
                        for v in vars_to_check:
                            if not self.read_tag_bool(v):
                                all_true = False
                                break
                        if all_true:
                            msg = f"🚨 【災難發生】 {cond.severity}: {cond.condition_name} ({cond.logic_expression})"
                            if msg not in report:
                                report.append(msg)
                                logger.error(msg)
                time.sleep(0.01) # 10ms 監測頻率

        monitor_thread = threading.Thread(target=monitor_task)
        monitor_thread.start()

        # 依序放狗咬人
        for action in plan.chaos_actions:
            report.append(f"🧨 [執行攻擊] {action.action_type} -> {action.target_tags}")
            self.execute_chaos_action(action)
            time.sleep(0.2) # 動作間隔

        # 停止監控
        time.sleep(0.5)
        stop_monitoring = True
        monitor_thread.join()
        self.disconnect()
        
        report.append("✅ 混沌壓力測試執行完畢。")
        return report
