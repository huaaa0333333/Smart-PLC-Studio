import os
import subprocess
import logging

logger = logging.getLogger(__name__)

class TIAExporter:
    def __init__(self, tools_dir="tools"):
        """
        初始化 TIA Exporter
        :param tools_dir: 存放 ImportSCL.exe 的目錄，預設為專案的 tools 資料夾
        """
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.exe_path = os.path.join(self.base_dir, tools_dir, "ImportSCL.exe")

    def import_scl_to_tia(self, project_path_or_dir: str, scl_path: str, plc_name: str, tag_tsv_path: str = None, 
                          is_create_mode: bool = False, project_name: str = "", mlfb_string: str = "") -> dict:
        """
        將 SCL 檔案匯入 TIA Portal 專案 (支援更新既有專案或新建專案)
        :param project_path_or_dir: 既有模式下為 .ap17 檔案路徑；創建模式下為專案存放目錄
        :param scl_path: 要匯入的 SCL 檔案路徑
        :param plc_name: TIA 專案中的目標 PLC 設備名稱，例如 'PLC_1'
        :param tag_tsv_path: 可選的 TSV 變數表路徑
        :param is_create_mode: 是否從頭創建新專案
        :param project_name: 新專案名稱 (僅創建模式)
        :param mlfb_string: PLC 硬體型號字串 (僅創建模式)
        :return: 包含狀態、stdout 與 stderr 的字典
        """
        
        # 1. 檢查檔案與前置條件
        if not os.path.exists(self.exe_path):
            return {"success": False, "message": f"找不到 C# 執行檔: {self.exe_path}，請先執行 compile_importer.bat 編譯！"}

        if not is_create_mode and not os.path.exists(project_path_or_dir):
            return {"success": False, "message": f"找不到既有的 TIA 專案: {project_path_or_dir}"}
        
        if is_create_mode and not os.path.exists(project_path_or_dir):
            try:
                os.makedirs(project_path_or_dir, exist_ok=True)
            except Exception as e:
                return {"success": False, "message": f"無法建立目標資料夾: {project_path_or_dir}"}
            
        if not os.path.exists(scl_path):
            return {"success": False, "message": f"找不到 SCL 檔案: {scl_path}"}
            
        if not plc_name:
            return {"success": False, "message": "未提供目標 PLC 名稱。"}

        # 2. 構建命令列參數
        command = [self.exe_path]
        
        if is_create_mode:
            command.extend([
                "--create",
                project_path_or_dir,
                project_name,
                mlfb_string,
                scl_path,
                plc_name
            ])
        else:
            command.extend([
                project_path_or_dir,
                scl_path,
                plc_name
            ])
        
        if tag_tsv_path and os.path.exists(tag_tsv_path):
            command.append(tag_tsv_path)
        
        logger.info(f"正在執行 TIA Portal 匯入工具... 目標 PLC: {plc_name}")
        
        # 3. 呼叫 subprocess 執行
        try:
            # shell=False 比較安全
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                check=False, # 不要自動拋出例外，我們自己處理回傳碼
                encoding='utf-8', 
                errors='replace' # 處理 Windows 中文編碼可能的跑版
            )
            
            # 從輸出日誌判斷是否成功
            # 依賴於我們 C# 腳本中設定若錯誤則 Environment.Exit(1)
            is_success = (result.returncode == 0)
            
            # 擷取最後幾行輸出當作摘要資訊
            output_msg = result.stdout.strip()
            
            if is_success:
                message = "成功匯入 TIA Portal！"
                logger.info(message)
            else:
                message = "TIA Portal 匯入失敗，請檢查工具輸出細節。"
                logger.error(message)
                logger.error(f"STDOUT: {result.stdout}")
                logger.error(f"STDERR: {result.stderr}")
                
            return {
                "success": is_success,
                "message": message,
                "details": output_msg,
                "error": result.stderr.strip() if result.stderr else None
            }
            
        except Exception as e:
            logger.exception("呼叫 ImportSCL.exe 時發生例外錯誤。")
            return {
                "success": False,
                "message": f"呼叫外部程序時發生例外錯誤: {str(e)}",
                "details": "",
                "error": str(e)
            }
