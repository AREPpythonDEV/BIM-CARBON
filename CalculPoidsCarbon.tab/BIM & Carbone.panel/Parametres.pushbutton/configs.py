# -*- coding: utf-8 -*-

from System.Drawing import Size, Color, Font, FontStyle, Font, FontStyle, GraphicsUnit, SystemColors, Point, Rectangle, ContentAlignment
from System.Windows.Forms import (
    Form,
    FormStartPosition,
    FormBorderStyle,
    RadioButton,
    ComboBox,
    Button,
    DialogResult,
    MessageBox,
    MessageBoxButtons,
    MessageBoxIcon,
    Label,
    TextBox,
    FlatStyle,
    Panel,
    FormClosingEventHandler,
    DialogResult,
    BorderStyle,
    CheckBox,
)

import os
import json

from paths import SETTINGS_FILE


def load_settings():
    """Load settings from file"""
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading settings: {e}")
    return {"email": "", "dont_ask_again": False}


def save_settings(settings):
    """Save settings to file"""
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving settings: {e}")
        return False


def show_settings_dialog():
    """Main function to show settings dialog"""
    form = SettingsForm()
    form.ShowDialog()
    return form.settings_updated


class SettingsForm(Form):
    def __init__(self):
        Form.__init__(self)
        self.settings = load_settings()
        self.settings_updated = False

        # Window settings
        self.Text = "BIM & Carbone - Paramètres"
        self.StartPosition = FormStartPosition.CenterScreen
        self.Size = Size(460, 280)
        self.BackColor = Color.FromArgb(248, 249, 250)
        self.FormBorderStyle = FormBorderStyle.FixedDialog
        self.MaximizeBox = False
        self.MinimizeBox = False

        self.setup_ui()

    def setup_ui(self):
        margin_left = 35

        # Title
        title = Label()
        title.Text = "Configuration utilisateur"
        title.Font = Font("Segoe UI", 14.0, FontStyle.Bold, GraphicsUnit.Point)
        title.ForeColor = Color.FromArgb(33, 37, 41)
        title.AutoSize = True
        title.Location = Point(margin_left, 20)
        self.Controls.Add(title)

        # Email label
        email_label = Label()
        email_label.Text = "Adresse e-mail AREP :"
        email_label.Font = Font("Segoe UI", 9.0, FontStyle.Regular, GraphicsUnit.Point)
        email_label.ForeColor = Color.FromArgb(33, 37, 41)
        email_label.AutoSize = True
        email_label.Location = Point(margin_left, 60)
        self.Controls.Add(email_label)

        # Email textbox
        self.email_textbox = TextBox()
        self.email_textbox.Font = Font("Segoe UI", 9.0, FontStyle.Regular, GraphicsUnit.Point)
        self.email_textbox.Size = Size(370, 23)
        self.email_textbox.Location = Point(margin_left, 80)
        self.email_textbox.Text = self.settings.get("email", "")
        self.Controls.Add(self.email_textbox)

        # "Ne plus afficher" checkbox
        self.dont_ask_checkbox = CheckBox()
        self.dont_ask_checkbox.Text = "Ne plus afficher la demande d'e-mail au démarrage"
        self.dont_ask_checkbox.Font = Font("Segoe UI", 9.0, FontStyle.Regular, GraphicsUnit.Point)
        self.dont_ask_checkbox.ForeColor = Color.FromArgb(33, 37, 41)
        self.dont_ask_checkbox.AutoSize = True
        self.dont_ask_checkbox.Location = Point(margin_left, 115)
        self.dont_ask_checkbox.Checked = self.settings.get("dont_ask_again", False)
        self.Controls.Add(self.dont_ask_checkbox)

        # Info label
        info_label = Label()
        info_label.Text = "Note : Si vous cochez cette option, l'e-mail sera sauvegardé et utilisé automatiquement."
        info_label.Font = Font("Segoe UI", 8.0, FontStyle.Regular, GraphicsUnit.Point)
        info_label.ForeColor = Color.FromArgb(108, 117, 125)
        info_label.Size = Size(390, 30)
        info_label.Location = Point(margin_left, 140)
        self.Controls.Add(info_label)

        # Setup buttons
        self.setup_buttons()

    def setup_buttons(self):
        """Setup action buttons with proper spacing"""
        btn_top = 185
        btn_width = 90
        btn_height = 30
        margin_left = 30
        spacing = 10

        # Clear button (left)
        clear_btn = Button()
        clear_btn.Text = "Effacer"
        clear_btn.Font = Font("Segoe UI", 9.0, FontStyle.Regular, GraphicsUnit.Point)
        clear_btn.Size = Size(btn_width, btn_height)
        clear_btn.Location = Point(margin_left, btn_top)
        clear_btn.BackColor = Color.FromArgb(220, 53, 69)
        clear_btn.ForeColor = Color.White
        clear_btn.Click += self.clear_click
        self.Controls.Add(clear_btn)

        # Cancel button (center)
        cancel_btn = Button()
        cancel_btn.Text = "Annuler"
        cancel_btn.Font = Font("Segoe UI", 9.0, FontStyle.Regular, GraphicsUnit.Point)
        cancel_btn.Size = Size(btn_width, btn_height)
        cancel_btn.Location = Point(margin_left + btn_width + spacing + 70, btn_top)
        cancel_btn.BackColor = Color.FromArgb(108, 117, 125)
        cancel_btn.ForeColor = Color.White
        cancel_btn.Click += self.cancel_click
        self.Controls.Add(cancel_btn)

        # Save button (right)
        save_btn = Button()
        save_btn.Text = "Sauvegarder"
        save_btn.Font = Font("Segoe UI", 9.0, FontStyle.Bold, GraphicsUnit.Point)
        save_btn.Size = Size(btn_width, btn_height)
        save_btn.Location = Point(margin_left + (btn_width + spacing) * 2 + 70, btn_top)
        save_btn.BackColor = Color.FromArgb(40, 167, 69)
        save_btn.ForeColor = Color.White
        save_btn.Click += self.save_click
        self.Controls.Add(save_btn)

        self.AcceptButton = save_btn
        self.CancelButton = cancel_btn

    def validate_email(self, email):
        return not email or email.endswith("@arep.fr")

    def save_click(self, sender, event):
        email = self.email_textbox.Text.strip()
        if email and not self.validate_email(email):
            MessageBox.Show("Veuillez entrer une adresse e-mail AREP valide (@arep.fr) ou laisser vide.",
                            "E-mail invalide", MessageBoxButtons.OK, MessageBoxIcon.Warning)
            return

        new_settings = {
            "email": email,
            "dont_ask_again": self.dont_ask_checkbox.Checked
        }

        if save_settings(new_settings):
            self.settings = new_settings
            self.settings_updated = True
            self.Close()
        else:
            MessageBox.Show("Erreur lors de la sauvegarde des paramètres.", "Erreur",
                            MessageBoxButtons.OK, MessageBoxIcon.Error)

    def clear_click(self, sender, event):
        if MessageBox.Show("Êtes-vous sûr de vouloir effacer tous les paramètres ?",
                           "Confirmation", MessageBoxButtons.YesNo,
                           MessageBoxIcon.Question) == DialogResult.Yes:
            self.email_textbox.Text = ""
            self.dont_ask_checkbox.Checked = False

    def cancel_click(self, sender, event):
        self.Close()


# Helper functions for easy access
def get_email():
    """Get saved email"""
    settings = load_settings()
    return settings.get("email", "")


def get_dont_ask_again():
    """Get dont_ask_again setting"""
    settings = load_settings()
    return settings.get("dont_ask_again", False)


def set_email(email):
    """Set email setting"""
    settings = load_settings()
    settings["email"] = email
    return save_settings(settings)


def set_dont_ask_again(value):
    """Set dont_ask_again setting"""
    settings = load_settings()
    settings["dont_ask_again"] = value
    return save_settings(settings)
