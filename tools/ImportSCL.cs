using System;
using System.IO;
using System.Reflection;
using System.Linq;
using Siemens.Engineering;
using Siemens.Engineering.HW;
using Siemens.Engineering.HW.Features;
using Siemens.Engineering.SW;
using Siemens.Engineering.SW.Blocks;
using Siemens.Engineering.SW.ExternalSources;
using Siemens.Engineering.SW.Tags;
using Siemens.Engineering.Compiler;

namespace TIAPortalSCLImporter
{
    class Program
    {
        static void Main(string[] args)
        {
            if (args.Length < 3)
            {
                Console.WriteLine("錯誤：至少需要三個參數。");
                Console.WriteLine("用法: ImportSCL.exe <TIA專案路徑> <SCL檔案路徑> <PLC設備名稱> [TSV變數表路徑]");
                Environment.Exit(1);
            }

            AppDomain.CurrentDomain.AssemblyResolve += MyResolver;
            RunImport(args);
        }

        private static Assembly MyResolver(object sender, ResolveEventArgs args)
        {
            var assemblyName = new AssemblyName(args.Name);
            if (assemblyName.Name.Equals("Siemens.Engineering"))
            {
                string path = @"C:\Program Files\Siemens\Automation\Portal V17\PublicAPI\V17\Siemens.Engineering.dll";
                if (File.Exists(path))
                {
                    return Assembly.LoadFrom(path);
                }
            }
            return null;
        }

        static void RunImport(string[] args)
        {
            if (args.Length < 1) return;

            bool isCreateMode = args[0] == "--create";
            
            // 引數解析
            string projectPathString = "";
            string sclPathString = "";
            string plcName = "";
            string tsvPath = "";
            
            // 創建模式專屬變數
            string newProjectTargetDir = "";
            string newProjectName = "";
            string mlfbString = "";

            if (isCreateMode)
            {
                // Usage: --create <TargetDir> <ProjName> <MLFB> <SCLPath> <PLCName> [TSVPath]
                if (args.Length < 6)
                {
                    Console.WriteLine("[錯誤] 創建模式缺少必要引數！");
                    Environment.Exit(1);
                }
                newProjectTargetDir = args[1];
                newProjectName = args[2];
                mlfbString = args[3];
                sclPathString = args[4];
                plcName = args[5];
                if (args.Length >= 7) tsvPath = args[6];
                
                projectPathString = Path.Combine(newProjectTargetDir, newProjectName, newProjectName + ".ap17"); 
            }
            else
            {
                // 既有模式 (更新模式)
                // Usage: <ProjectPath> <SCLPath> <PLCName> [TSVPath]
                if (args.Length < 3)
                {
                    Console.WriteLine("[錯誤] 更新模式缺少必要引數！");
                    Environment.Exit(1);
                }
                projectPathString = args[0];
                sclPathString = args[1];
                plcName = args[2];
                if (args.Length >= 4) tsvPath = args[3];
            }

            FileInfo sclPath = new FileInfo(sclPathString);
            if (!sclPath.Exists)
            {
                Console.WriteLine("[錯誤] 找不到 SCL 檔案: " + sclPath.FullName);
                Environment.Exit(1);
            }

            Console.WriteLine("=== TIA Portal SCL Importer 開始 ===");
            Console.WriteLine("模式: " + (isCreateMode ? "自動創建新專案" : "更新既有專案"));
            Console.WriteLine("指令目標: " + projectPathString);
            Console.WriteLine("PLC名稱: " + plcName);
            Console.WriteLine("匯入檔案: " + sclPath.FullName);
            Console.WriteLine("------------------------------------------");
            Console.WriteLine("正在啟動 TIA Portal V17 (帶有介面) ... (請稍候)");

            try
            {
                TiaPortal portal = new TiaPortal(TiaPortalMode.WithUserInterface);
                Project project = null;

                if (isCreateMode)
                {
                    // 創建模式邏輯
                    Console.WriteLine("TIA Portal 已啟動，建立新專案中...");
                    DirectoryInfo dirInfo = new DirectoryInfo(newProjectTargetDir);
                    if (!dirInfo.Exists) dirInfo.Create();
                    
                    project = portal.Projects.Create(dirInfo, newProjectName);
                    Console.WriteLine("專案已創建。");

                    Console.WriteLine("正在依據標配型錄 [" + mlfbString + "] 產生硬體設備...");
                    Device myPlc = project.Devices.CreateWithItem(mlfbString, plcName, plcName);
                    Console.WriteLine("硬體實體化完成: " + myPlc.Name);
                }
                else
                {
                    // 更新模式邏輯
                    FileInfo projectPath = new FileInfo(projectPathString);
                    if (!projectPath.Exists)
                    {
                        Console.WriteLine("[錯誤] 找不到 TIA 專案檔案: " + projectPath.FullName);
                        Environment.Exit(1);
                    }
                    Console.WriteLine("TIA Portal 已啟動，開啟專案中...");
                    project = portal.Projects.Open(projectPath);
                    Console.WriteLine("專案成功載入！");
                }

                PlcSoftware plcSoftware = FindPlcSoftware(project, plcName);
                
                if (plcSoftware == null)
                {
                    Console.WriteLine("[錯誤] 專案中找不到名為「" + plcName + "」的 PLC 設備軟體容器。");
                    project.Close();
                    Environment.Exit(1);
                }

                Console.WriteLine("已鎖定目標 PLC 軟體控制器區塊: " + plcName);

                // ==========================================
                // 1. 自動匯入變數表 (如果有提供)
                // ==========================================
                if (!string.IsNullOrEmpty(tsvPath))
                {
                    if (File.Exists(tsvPath))
                    {
                        Console.WriteLine("正在匯入全域變數表 (Tags) ...");
                        PlcTagTableGroup tagTableGroup = plcSoftware.TagTableGroup;
                        PlcTagTable tagTable = tagTableGroup.TagTables.Find("Default tag table");
                        if (tagTable == null)
                        {
                            tagTable = tagTableGroup.TagTables.Create("Default tag table");
                        }

                        string[] lines = File.ReadAllLines(tsvPath);
                        // TSV Columns: Name, DataType, Address, Comment
                        for (int i = 1; i < lines.Length; i++)
                        {
                            string line = lines[i].Trim();
                            if (string.IsNullOrEmpty(line)) continue;
                            string[] cols = line.Split('\t');
                            if (cols.Length >= 2)
                            {
                                string tName = cols[0].Trim();
                                // Index 1 必定是 Path (Default tag table)，我們直接略過它
                                string tType = cols.Length > 2 ? cols[2].Trim() : "";
                                string tAddr = cols.Length > 3 ? cols[3].Trim() : "";
                                
                                if (string.IsNullOrEmpty(tName) || tName.Equals("ParserError", StringComparison.OrdinalIgnoreCase)) continue;
                                
                                PlcTag extTag = tagTable.Tags.Find(tName);
                                if (extTag == null)
                                {
                                    PlcTag newTag = tagTable.Tags.Create(tName);
                                    newTag.DataTypeName = tType;
                                    if (!string.IsNullOrEmpty(tAddr)) newTag.LogicalAddress = tAddr;
                                }
                                else
                                {
                                    extTag.DataTypeName = tType;
                                    if (!string.IsNullOrEmpty(tAddr)) extTag.LogicalAddress = tAddr;
                                }
                            }
                        }
                        Console.WriteLine("變數表匯入完成！");
                    }
                }

                // ==========================================
                // 2. 匯入 SCL 來源檔並轉換成區塊
                // ==========================================
                Console.WriteLine("準備匯入 SCL ...");
                string sourceName = Path.GetFileNameWithoutExtension(sclPath.Name);
                PlcExternalSourceGroup extGroup = plcSoftware.ExternalSourceGroup;
                
                PlcExternalSource existingSource = extGroup.ExternalSources.Find(sourceName);
                if (existingSource != null)
                {
                    existingSource.Delete();
                }

                PlcExternalSource newExtSource = extGroup.ExternalSources.CreateFromFile(sourceName, sclPath.FullName);
                Console.WriteLine("SCL 外部來源檔案已掛載...");

                newExtSource.GenerateBlocksFromSource(GenerateBlockOption.KeepOnError);
                Console.WriteLine("SCL 區塊成功轉換並匯入至 TIA！");

                // ==========================================
                // 3. 自動編譯 (Auto-Compile)
                // ==========================================
                Console.WriteLine("正在執行軟體全自動編譯 ...");
                ICompilable compilable = plcSoftware.GetService<ICompilable>();
                if (compilable != null)
                {
                    CompilerResult compRes = compilable.Compile();
                    if (compRes.State == CompilerResultState.Error)
                    {
                        Console.WriteLine("⚠️ 編譯完成，但包含錯誤。請至 TIA Portal 查看詳細編譯日誌。");
                    }
                    else
                    {
                        Console.WriteLine("✅ 編譯成功！您的 SCL 準備就緒！");
                    }
                }

                // 儲存專案
                Console.WriteLine("正在儲存 TIA 專案變更...");
                project.Save();
                Console.WriteLine("專案已儲存，請在 TIA Portal 視窗中確認成果與編譯狀態。");
                
                Console.WriteLine("=== 匯入任務圓滿完成 ===");
            }
            catch (Exception ex)
            {
                Console.WriteLine("\n[錯誤例外] 執行期間發生錯誤：");
                Console.WriteLine(ex.Message);
                if (ex.InnerException != null)
                {
                    Console.WriteLine("詳細原因: " + ex.InnerException.Message);
                }
                Environment.Exit(1);
            }
        }

        static PlcSoftware FindPlcSoftware(Project project, string targetPlcName)
        {
            foreach (Device device in project.Devices)
            {
                foreach (DeviceItem item in device.DeviceItems)
                {
                    if (item.Name.Equals(targetPlcName, StringComparison.OrdinalIgnoreCase))
                    {
                        SoftwareContainer softwareContainer = item.GetService<SoftwareContainer>();
                        if (softwareContainer != null && softwareContainer.Software is PlcSoftware)
                        {
                            return (PlcSoftware)softwareContainer.Software;
                        }
                    }
                    
                    PlcSoftware result = RecursiveFindPlcSoftware(item, targetPlcName);
                    if (result != null) return result;
                }
            }
            return null;
        }

        static PlcSoftware RecursiveFindPlcSoftware(DeviceItem item, string targetPlcName)
        {
            foreach (DeviceItem child in item.DeviceItems)
            {
                if (child.Name.Equals(targetPlcName, StringComparison.OrdinalIgnoreCase))
                {
                    SoftwareContainer softwareContainer = child.GetService<SoftwareContainer>();
                    if (softwareContainer != null && softwareContainer.Software is PlcSoftware)
                    {
                        return (PlcSoftware)softwareContainer.Software;
                    }
                }
                
                PlcSoftware result = RecursiveFindPlcSoftware(child, targetPlcName);
                if (result != null) return result;
            }
            return null;
        }
    }
}
