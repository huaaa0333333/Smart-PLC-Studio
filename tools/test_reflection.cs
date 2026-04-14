using System;
using System.Reflection;
using Siemens.Engineering;
using Siemens.Engineering.SW;
using Siemens.Engineering.SW.ExternalSources;

class Program
{
    static void Main()
    {
        AppDomain.CurrentDomain.AssemblyResolve += MyResolver;
        Run();
    }

    private static Assembly MyResolver(object sender, ResolveEventArgs args)
    {
        var assemblyName = new AssemblyName(args.Name);
        if (assemblyName.Name.Equals("Siemens.Engineering"))
        {
            string path = @"C:\Program Files\Siemens\Automation\Portal V17\PublicAPI\V17\Siemens.Engineering.dll";
            return Assembly.LoadFrom(path);
        }
        return null;
    }

    static void Run()
    {
        Type extSourceType = typeof(PlcExternalSource);
        Console.WriteLine("PlcExternalSource Methods:");
        foreach (var m in extSourceType.GetMethods())
        {
            Console.WriteLine(" - " + m.Name + "()");
            foreach (var p in m.GetParameters())
            {
                   Console.WriteLine("    param: " + p.ParameterType.Name + " " + p.Name);
            }
        }
    }
}
