import os
import subprocess
import shutil
import tempfile
import logging

logger = logging.getLogger(__name__)

class TIAExtractor:
    """與 TIA Portal (ExportSCL.exe) 溝通，進行專案區塊導出"""

    def __init__(self, exe_path: str = "tools/ExportSCL.exe"):
        self.exe_path = os.path.abspath(exe_path)

    def is_tool_available(self) -> bool:
        return os.path.exists(self.exe_path)

    def get_block_list(self, project_path: str, plc_name: str) -> list[str]:
        """
        列出專案下指定 PLC 的所有一般區塊 (OB, FC, FB)
        """
        if not self.is_tool_available():
            logger.warning("ExportSCL.exe 工具不存在，返回模擬的區塊列表供 UI 測試。")
            return ["Main [OB1]", "LegacyPump_FC [FC1]", "OldConveyor_FB [FB1]"]

        cmd = [self.exe_path, "list_blocks", os.path.abspath(project_path), plc_name]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, encoding="utf-8-sig", timeout=60
            )
            output = result.stdout
            
            blocks = []
            capturing = False
            for line in output.split("\n"):
                line = line.strip()
                if line == "=== BLOCK LIST START ===":
                    capturing = True
                    continue
                if line == "=== BLOCK LIST END ===":
                    break
                if capturing and line:
                    blocks.append(line)
            return blocks
        except Exception as e:
            logger.error(f"獲取區塊列表失敗: {e}")
            raise Exception(f"提取失敗: {e}")

    def extract_block_xml(self, project_path: str, plc_name: str, block_name: str) -> str:
        """
        將特定區塊匯出為 XML 並讀取內容後返回。
        如果需要重構的是整個專案的連動，此工具也能輕易處理單一塊。
        """
        if not self.is_tool_available():
            logger.warning("ExportSCL.exe 工具不存在，返回模擬的遺留代碼片段供 UI 測試。")
            return f"""<?xml version="1.0" encoding="utf-8"?>
<Document>
  <Engineering version="V17" />
  <DocumentInfo>
    <Created>2023-11-01T12:00:00.0000000Z</Created>
    <ExportSetting>WithDefaults</ExportSetting>
  </DocumentInfo>
  <SW.Blocks.FC ID="1">
    <AttributeList>
      <Name>{block_name}</Name>
      <Number>1</Number>
    </AttributeList>
    <ObjectList>
      <MultilingualText ID="2" CompositionName="Title">
        <ObjectList>
          <MultilingualTextItem ID="3" CompositionName="Items">
            <AttributeList>
              <Culture>zh-TW</Culture>
              <Text>祖傳義大利麵邏輯</Text>
            </AttributeList>
          </MultilingualTextItem>
        </ObjectList>
      </MultilingualText>
      <SW.Blocks.CompileUnit ID="4" CompositionName="CompileUnits">
        <AttributeList>
          <NetworkSource><StructuredText xmlns="http://www.siemens.com/automation/Openness/SPI/NetworkSource/StructuredText/v3">
  <Token Text="IF" TokenType="Keyword" />
  <Token Text=" " TokenType="WhiteSpace" />
  <Access Scope="GlobalVariable" UId="21">
    <Symbol>
      <Component Name="M0.0" />
    </Symbol>
  </Access>
  <Token Text=" " TokenType="WhiteSpace" />
  <Token Text="AND" TokenType="Keyword" />
  <Token Text=" " TokenType="WhiteSpace" />
  <Access Scope="GlobalVariable" UId="22">
    <Symbol>
      <Component Name="I0.1" />
    </Symbol>
  </Access>
  <Token Text=" " TokenType="WhiteSpace" />
  <Token Text="THEN" TokenType="Keyword" />
  <Token Text="&#xD;&#xA;" TokenType="NewLine" />
  <Token Text="  " TokenType="WhiteSpace" />
  <Access Scope="GlobalVariable" UId="23">
    <Symbol>
      <Component Name="Q0.0" />
    </Symbol>
  </Access>
  <Token Text=" " TokenType="WhiteSpace" />
  <Token Text=":=" TokenType="Assignment" />
  <Token Text=" " TokenType="WhiteSpace" />
  <Token Text="TRUE" TokenType="Keyword" />
  <Token Text=";" TokenType="Default" />
  <Token Text="&#xD;&#xA;" TokenType="NewLine" />
  <Token Text="END_IF" TokenType="Keyword" />
  <Token Text=";" TokenType="Default" />
</StructuredText></NetworkSource>
          <ProgrammingLanguage>SCL</ProgrammingLanguage>
        </AttributeList>
      </SW.Blocks.CompileUnit>
    </ObjectList>
  </SW.Blocks.FC>
</Document>"""

        # 建立暫存檔
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_xml_path = os.path.join(tmp_dir, f"{block_name}.xml")
            cmd = [
                self.exe_path,
                "export_block",
                os.path.abspath(project_path),
                plc_name,
                block_name,
                temp_xml_path
            ]
            try:
                result = subprocess.run(
                    cmd, capture_output=True, text=True, encoding="utf-8-sig", timeout=120
                )
                if "[ERROR]" in result.stdout:
                    raise Exception(result.stdout)
                
                if not os.path.exists(temp_xml_path):
                    raise Exception("匯出失敗，找不到生成的 XML 檔案。")
                    
                with open(temp_xml_path, "r", encoding="utf-8-sig", errors="ignore") as f:
                    xml_content = f.read()
                return xml_content
            except Exception as e:
                logger.error(f"讀取 XML 內容失敗: {e}")
                raise Exception(f"匯出失敗: {e}")
