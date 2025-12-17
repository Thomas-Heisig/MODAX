using System;
using System.Drawing;
using System.Windows.Forms;

namespace MODAX.HMI.Views
{
    /// <summary>
    /// Base class for MDI child forms
    /// </summary>
    public class MdiChildForm : Form
    {
        protected MdiChildForm()
        {
            // Common MDI child properties
            FormBorderStyle = FormBorderStyle.Sizable;
            ShowIcon = true;
            Icon = SystemIcons.Application;
            MinimizeBox = true;
            MaximizeBox = true;
            ControlBox = true;
            
            // Set default size
            Size = new Size(800, 600);
            StartPosition = FormStartPosition.CenterParent;
        }
        
        /// <summary>
        /// Override to provide custom initialization
        /// </summary>
        protected virtual void InitializeChildForm()
        {
            // To be implemented by derived classes
        }
        
        protected override void OnLoad(EventArgs e)
        {
            base.OnLoad(e);
            InitializeChildForm();
        }
    }
}
