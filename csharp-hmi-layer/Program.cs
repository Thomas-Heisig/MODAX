using System;
using System.Windows.Forms;
using MODAX.HMI.Views;

namespace MODAX.HMI
{
    /// <summary>
    /// Main entry point for MODAX HMI application
    /// </summary>
    static class Program
    {
        [STAThread]
        static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.SetHighDpiMode(HighDpiMode.SystemAware);
            
            Application.Run(new MainForm());
        }
    }
}
