using System;
using System.IO;
using System.Reflection;
using System.Collections.Generic;
using Siemens.Engineering;
using Siemens.Engineering.HW;
using Siemens.Engineering.HW.Features;
using Siemens.Engineering.SW;
using Siemens.Engineering.SW.Blocks;

namespace TIAPortalExporter
{
    class Program
    {
        static void Main(string[] args)
        {
            if (args.Length < 3)
            {
                Console.WriteLine("用法:");
                Console.WriteLine(" 1. 列出所有區塊: ExportSCL.exe list_blocks <TIA專案路徑> <PLC名稱>");
                Console.WriteLine(" 2. 匯出特定區塊 XML: ExportSCL.exe export_block <TIA專案路徑> <PLC名稱> <區塊名稱> <輸出XML檔案路徑>");
                Environment.Exit(1);
            }

            AppDomain.CurrentDomain.AssemblyResolve += MyResolver;
            RunCommand(args);
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

        static void RunCommand(string[] args)
        {
            string mode = args[0];
            string projectPathStr = args[1];
            string plcName = args[2];

            FileInfo projectPath = new FileInfo(projectPathStr);
            if (!projectPath.Exists)
            {
                Console.WriteLine($"[ERROR] 找不到專案: {projectPath.FullName}");
                Environment.Exit(1);
            }

            try
            {
                // Connect to a running portal or start a new one gently without UI to save time
                TiaPortal portal = new TiaPortal(TiaPortalMode.WithoutUserInterface);
                Project project = null;

                try 
                {
                    project = portal.Projects.Open(projectPath);
                }
                catch(Exception ex)
                {
                    Console.WriteLine($"[ERROR] 開啟專案失敗: {ex.Message}");
                    portal.Dispose();
                    Environment.Exit(1);
                }

                PlcSoftware plcSoftware = FindPlcSoftware(project, plcName);
                if (plcSoftware == null)
                {
                    Console.WriteLine($"[ERROR] 專案中找不到命名為 {plcName} 的 PLC。");
                    project.Close();
                    portal.Dispose();
                    Environment.Exit(1);
                }

                if (mode == "list_blocks")
                {
                    Console.WriteLine("=== BLOCK LIST START ===");
                    ListBlocksRecursive(plcSoftware.BlockGroup);
                    Console.WriteLine("=== BLOCK LIST END ===");
                }
                else if (mode == "export_block")
                {
                    if (args.Length < 4)
                    {
                        Console.WriteLine("[ERROR] 缺少匯出路徑參數");
                        Environment.Exit(1);
                    }
                    string blockName = args[3];
                    string targetXmlPath = args[4];

                    PlcBlock targetBlock = FindBlockRecursive(plcSoftware.BlockGroup, blockName);
                    if (targetBlock == null)
                    {
                        Console.WriteLine($"[ERROR] 找不到區塊: {blockName}");
                    }
                    else
                    {
                        FileInfo targetXml = new FileInfo(targetXmlPath);
                        if (targetXml.Exists) targetXml.Delete();
                        targetBlock.Export(targetXml, ExportOptions.WithDefaults);
                        Console.WriteLine($"[SUCCESS] 區塊 {blockName} 已匯出至: {targetXmlPath}");
                    }
                }

                project.Close();
                portal.Dispose();
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[ERROR] 執行期間發生錯誤: {ex.Message}");
                if (ex.InnerException != null) Console.WriteLine(ex.InnerException.Message);
                Environment.Exit(1);
            }
        }

        static void ListBlocksRecursive(PlcBlockGroup group)
        {
            foreach (PlcBlock block in group.Blocks)
            {
                // OB, FC, FB only. Exclude internal system blocks if possible.
                if (block is OB || block is FC || block is FB)
                {
                    Console.WriteLine(block.Name);
                }
            }
            foreach (PlcBlockGroup subGroup in group.Groups)
            {
                ListBlocksRecursive(subGroup);
            }
        }

        static PlcBlock FindBlockRecursive(PlcBlockGroup group, string blockName)
        {
            foreach (PlcBlock block in group.Blocks)
            {
                if (block.Name.Equals(blockName, StringComparison.OrdinalIgnoreCase))
                {
                    return block;
                }
            }
            foreach (PlcBlockGroup subGroup in group.Groups)
            {
                PlcBlock result = FindBlockRecursive(subGroup, blockName);
                if (result != null) return result;
            }
            return null;
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
