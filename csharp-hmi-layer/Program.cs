using System;
using System.Windows.Forms;
using MODAX.HMI.Views;

namespace MODAX.HMI
{
    /// <summary>
    /// Main entry point for MODAX HMI application
    /// Fault-tolerant startup with comprehensive error handling
    /// </summary>
    static class Program
    {
        [STAThread]
        static void Main()
        {
            // Set up global exception handlers for fault tolerance
            Application.ThreadException += Application_ThreadException;
            AppDomain.CurrentDomain.UnhandledException += CurrentDomain_UnhandledException;

            try
            {
                Application.EnableVisualStyles();
                Application.SetCompatibleTextRenderingDefault(false);
                Application.SetHighDpiMode(HighDpiMode.SystemAware);
                
                // Application must always start, even if backend is unavailable
                // The MainForm handles connection errors gracefully
                Application.Run(new MainForm());
            }
            catch (Exception ex)
            {
                // Critical startup error - show message and log
                string errorMessage = $"Critical error starting MODAX HMI:\n\n{ex.Message}\n\n" +
                                    $"Type: {ex.GetType().Name}\n\n" +
                                    "The application will now exit.";
                
                MessageBox.Show(
                    errorMessage,
                    "MODAX HMI - Startup Error",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Error
                );
                
                // Log to console/file if available
                Console.WriteLine($"[FATAL] {DateTime.Now}: {ex}");
                
                Environment.Exit(1);
            }
        }

        /// <summary>
        /// Handle unhandled exceptions in application threads
        /// </summary>
        private static void Application_ThreadException(object sender, System.Threading.ThreadExceptionEventArgs e)
        {
            try
            {
                string errorMessage = $"An unexpected error occurred:\n\n{e.Exception.Message}\n\n" +
                                    "The application will attempt to continue.";
                
                Console.WriteLine($"[ERROR] {DateTime.Now}: Thread exception: {e.Exception}");
                
                MessageBox.Show(
                    errorMessage,
                    "MODAX HMI - Error",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Warning
                );
            }
            catch
            {
                // If we can't even show the error dialog, try to exit gracefully
                try
                {
                    MessageBox.Show(
                        "A critical error occurred. The application will now exit.",
                        "MODAX HMI - Critical Error",
                        MessageBoxButtons.OK,
                        MessageBoxIcon.Error
                    );
                }
                finally
                {
                    Environment.Exit(1);
                }
            }
        }

        /// <summary>
        /// Handle unhandled exceptions in non-UI threads
        /// </summary>
        private static void CurrentDomain_UnhandledException(object sender, UnhandledExceptionEventArgs e)
        {
            try
            {
                Exception? ex = e.ExceptionObject as Exception;
                string message = ex?.Message ?? "Unknown error";
                string details = ex?.ToString() ?? e.ExceptionObject?.ToString() ?? "No details available";
                
                Console.WriteLine($"[FATAL] {DateTime.Now}: Unhandled exception: {details}");
                
                string errorMessage = $"A fatal error occurred:\n\n{message}\n\n" +
                                    $"Terminating: {e.IsTerminating}\n\n" +
                                    "Please check logs for more details.";
                
                MessageBox.Show(
                    errorMessage,
                    "MODAX HMI - Fatal Error",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Error
                );
            }
            catch
            {
                // Last resort - try to notify user
                MessageBox.Show(
                    "A fatal error occurred. The application will now exit.",
                    "MODAX HMI - Fatal Error",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Error
                );
            }
            finally
            {
                if (e.IsTerminating)
                {
                    Environment.Exit(1);
                }
            }
        }
    }
}
