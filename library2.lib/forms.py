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

from Autodesk.Revit.UI import TaskDialog, TaskDialogCommonButtons, TaskDialogResult, TaskDialogCommandLinkId, TaskDialogIcon

from paths import APPDATA_VERSION_PATH, SETTINGS_FILE
from version_manager import get_version_numbers


uidoc = __revit__.ActiveUIDocument
doc = uidoc.Document
doc_title = doc.Title


class SimpleForm(Form):
    def __init__(self, titre):
        Form.__init__(self)

        # Window settings - modern style like email form
        self.Text = "Calculer le projet"
        self.StartPosition = FormStartPosition.CenterScreen
        self.Size = Size(460, 280)
        self.BackColor = Color.FromArgb(248, 249, 250)  # Modern gray background
        self.FormBorderStyle = FormBorderStyle.FixedDialog
        self.MaximizeBox = False
        self.MinimizeBox = False

        margin_left = 30

        # Title - modern style
        self.title_label = Label()
        self.title_label.Text = "Choisissez une option"
        self.title_label.Font = Font("Segoe UI", 14.0, FontStyle.Bold, GraphicsUnit.Point)
        self.title_label.ForeColor = Color.FromArgb(33, 37, 41)  # Modern dark text
        self.title_label.AutoSize = True
        self.title_label.Location = Point(margin_left, 20)
        self.Controls.Add(self.title_label)

        # RadioButton : Créer une nouvelle version - modern style
        self.new_version_radiobutton = RadioButton()
        self.new_version_radiobutton.Text = "Créer une nouvelle version"
        self.new_version_radiobutton.Font = Font("Segoe UI", 9.0, FontStyle.Regular, GraphicsUnit.Point)
        self.new_version_radiobutton.ForeColor = Color.FromArgb(33, 37, 41)
        self.new_version_radiobutton.Checked = True
        self.new_version_radiobutton.Location = Point(margin_left, 60)
        self.new_version_radiobutton.Size = Size(370, 30)
        self.Controls.Add(self.new_version_radiobutton)

        # RadioButton : Mettre à jour une version - modern style
        self.update_version_radiobutton = RadioButton()
        self.update_version_radiobutton.Text = "Mettre à jour une version"
        self.update_version_radiobutton.Font = Font("Segoe UI", 9.0, FontStyle.Regular, GraphicsUnit.Point)
        self.update_version_radiobutton.ForeColor = Color.FromArgb(33, 37, 41)
        self.update_version_radiobutton.Location = Point(margin_left, 95)
        self.update_version_radiobutton.CheckedChanged += self.radio_button_checked
        self.update_version_radiobutton.Size = Size(370, 30)
        self.Controls.Add(self.update_version_radiobutton)

        # ComboBox - modern style
        self.version_dropdown = ComboBox()
        self.version_dropdown.Font = Font("Segoe UI", 9.0, FontStyle.Regular, GraphicsUnit.Point)
        self.version_dropdown.Enabled = False
        self.version_dropdown.Size = Size(370, 23)
        self.version_dropdown.Location = Point(margin_left + 10, 130)
        self.Controls.Add(self.version_dropdown)

        # Bouton Valider - modern style like email form
        self.validate_button = Button()
        self.validate_button.Text = "Valider"
        self.validate_button.Font = Font("Segoe UI", 9.0, FontStyle.Bold, GraphicsUnit.Point)
        self.validate_button.BackColor = Color.FromArgb(40, 167, 69)  # Modern green
        self.validate_button.ForeColor = Color.White
        self.validate_button.Size = Size(100, 32)
        self.validate_button.Location = Point(180, 180)
        self.Controls.Add(self.validate_button)

        self.validate_button.Click += self.validate_button_clicked

    def radio_button_checked(self, sender, event):
        self.version_dropdown.Enabled = self.update_version_radiobutton.Checked

    def close_button_clicked(self, sender, event):
        self.Close()

    def update_version_checked_changed(self, sender, args):
        # Activer/désactiver la ComboBox selon l'état du RadioButton
        self.version_dropdown.Enabled = self.update_version_radiobutton.Checked

    def validate_button_clicked(self, sender, args):
        # Check the number of selected options
        selected_options = [
            self.new_version_radiobutton.Checked,
            self.update_version_radiobutton.Checked,
        ]

        # Ensure that only one option is selected
        if sum(selected_options) == 0:
            MessageBox.Show(
                "Veuillez cocher une case.",
                "Erreur",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error,
            )
        elif sum(selected_options) != 1:
            MessageBox.Show(
                "Veuillez cocher une seule case.",
                "Erreur",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error,
            )
        elif self.update_version_radiobutton.Checked and not self.version_dropdown.SelectedItem:
            MessageBox.Show(
                "Veuillez choisir une version à mettre à jour.",
                "Erreur",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error,
            )
        else:
            self.DialogResult = DialogResult.OK
            self.Close()


def show_user_choice_dialog():
    form = SimpleForm("Calculer le projet")
    user_choice = {}
    # Populate dropdown with version numbers from a CSV file
    form.version_dropdown.Items.AddRange(get_version_numbers(APPDATA_VERSION_PATH, doc_title))

    result = form.ShowDialog()

    if result == DialogResult.OK:
        user_choice['cancelled'] = False
        user_choice['new_version'] = form.new_version_radiobutton.Checked
        update_version = form.update_version_radiobutton.Checked
        user_choice['selected_version'] = form.version_dropdown.SelectedItem if update_version else None
    else:
        user_choice['cancelled'] = True
        user_choice['new_version'] = None
        user_choice['selected_version'] = None

    return user_choice

class UserNameForm(Form):
    def __init__(self, default_email=""):
        Form.__init__(self)
        self.username = None
        self.dont_ask_again = False

        # Modern window settings
        self.Text = "Calculer le projet"
        self.StartPosition = FormStartPosition.CenterScreen
        self.Size = Size(500, 280)
        self.BackColor = Color.FromArgb(248, 249, 250)  # Light gray background
        self.FormBorderStyle = FormBorderStyle.FixedDialog
        self.MaximizeBox = False
        self.MinimizeBox = False

        self.FormClosing += FormClosingEventHandler(self.on_form_closing)
        self.setup_ui(default_email)

    def setup_ui(self, default_email):

        # Title label
        title_label = Label()
        title_label.Text = "Authentification AREP"
        title_label.Font = Font("Segoe UI", 14.0, FontStyle.Bold, GraphicsUnit.Point)
        title_label.ForeColor = Color.FromArgb(33, 37, 41)
        title_label.AutoSize = True
        title_label.Location = Point(30, 25)
        self.Controls.Add(title_label)

        # Subtitle/description
        desc_label = Label()
        desc_label.Text = "Veuillez renseigner votre adresse e-mail AREP pour continuer."
        desc_label.Font = Font("Segoe UI", 9.0, GraphicsUnit.Point)
        desc_label.ForeColor = Color.FromArgb(108, 117, 125)
        desc_label.AutoSize = True
        desc_label.Location = Point(30, 55)
        self.Controls.Add(desc_label)

        # Email label
        email_label = Label()
        email_label.Text = "Adresse e-mail :"
        email_label.Font = Font("Segoe UI", 9.0, FontStyle.Regular, GraphicsUnit.Point)
        email_label.ForeColor = Color.FromArgb(33, 37, 41)
        email_label.AutoSize = True
        email_label.Location = Point(30, 90)
        self.Controls.Add(email_label)

        # TextBox for email
        self.textBox = TextBox()
        self.textBox.Font = Font("Segoe UI", 10.0, GraphicsUnit.Point)
        self.textBox.ForeColor = Color.FromArgb(33, 37, 41)
        self.textBox.Size = Size(400, 25)
        self.textBox.Location = Point(30, 110)
        self.textBox.Text = default_email
        self.Controls.Add(self.textBox)

        # "Ne plus demander" checkbox
        self.checkbox = CheckBox()
        self.checkbox.Text = "Ne plus demander (sauvegarder pour les prochaines fois)"
        self.checkbox.Font = Font("Segoe UI", 8.5, GraphicsUnit.Point)
        self.checkbox.ForeColor = Color.FromArgb(108, 117, 125)
        self.checkbox.AutoSize = True
        self.checkbox.Location = Point(30, 160)
        self.Controls.Add(self.checkbox)

        # Cancel button
        self.cancel_button = Button()
        self.cancel_button.Text = "Annuler"
        self.cancel_button.Font = Font("Segoe UI", 9.0, GraphicsUnit.Point)
        self.cancel_button.BackColor = Color.FromArgb(248, 249, 250)
        self.cancel_button.ForeColor = Color.FromArgb(108, 117, 125)
        self.cancel_button.Size = Size(90, 35)
        self.cancel_button.Location = Point(240, 195)
        self.cancel_button.Click += self.cancel_click
        self.Controls.Add(self.cancel_button)

        # Validate button
        self.validate_button = Button()
        self.validate_button.Text = "Valider"
        self.validate_button.Font = Font("Segoe UI", 9.0, FontStyle.Bold, GraphicsUnit.Point)
        self.validate_button.BackColor = Color.FromArgb(0, 123, 255)
        self.validate_button.ForeColor = Color.White
        self.validate_button.Size = Size(90, 35)
        self.validate_button.Location = Point(340, 195)
        self.validate_button.Click += self.validate_click
        self.Controls.Add(self.validate_button)

        # Set default buttons
        self.AcceptButton = self.validate_button
        self.CancelButton = self.cancel_button

        # Add hover effects
        self.add_button_hover_effects()

    def add_button_hover_effects(self):
        """Add modern hover effects to buttons"""

        def on_validate_enter(sender, e):
            sender.BackColor = Color.FromArgb(0, 86, 179)  # Darker blue on hover

        def on_validate_leave(sender, e):
            sender.BackColor = Color.FromArgb(0, 123, 255)  # Original blue

        def on_cancel_enter(sender, e):
            sender.BackColor = Color.FromArgb(233, 236, 239)  # Light gray on hover

        def on_cancel_leave(sender, e):
            sender.BackColor = Color.FromArgb(248, 249, 250)  # Original light gray

        self.validate_button.MouseEnter += on_validate_enter
        self.validate_button.MouseLeave += on_validate_leave
        self.cancel_button.MouseEnter += on_cancel_enter
        self.cancel_button.MouseLeave += on_cancel_leave

    def validate_click(self, sender, event):
        email = self.textBox.Text.strip()

        if not email:
            self.show_error("Veuillez entrer une adresse e-mail.")
            return

        if not email.endswith("@arep.fr"):
            self.show_error("Veuillez entrer une adresse e-mail AREP valide (@arep.fr).")
            return

        self.username = email

        # Save email using your existing function
        save_email(email)

        # Save "don't ask again" preference if checked
        if self.checkbox.Checked:
            save_dont_ask_again_setting(True)

        self.Close()

    def cancel_click(self, sender, event):
        self.Close()

    def show_error(self, message):
        """Show modern error message"""
        MessageBox.Show(
            message,
            "Erreur de validation",
            MessageBoxButtons.OK,
            MessageBoxIcon.Warning
        )

    def on_form_closing(self, sender, event):
        pass  # TODO: trouver un moyen safe pour quitter

    # def on_form_closing(self, sender, event):
    #     # If user closes without clicking a button, treat as cancel
    #     if self.DialogResult == DialogResult.None:
    #         self.DialogResult = DialogResult.Cancel


def show_user_name_dialog():
    """Main function to get username - checks settings first"""
    try:
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
            # If "don't ask again" is enabled and we have a saved email, use it
            if data.get("dont_ask_again", False) and data.get("email", ""):
                return data["email"]
    except:
        pass

    saved = load_saved_email()
    form = UserNameForm(default_email=saved)
    form.ShowDialog()
    return form.username


def load_saved_email():
    """Load saved email from settings file"""
    try:
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
            return data.get("email", "")
    except:
        return ""


def save_email(email):
    """Save email to settings file"""
    try:
        # Load existing settings to preserve dont_ask_again flag
        existing_data = {}
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r") as f:
                existing_data = json.load(f)
    except:
        existing_data = {}

    # Update email while preserving other settings
    existing_data["email"] = email

    with open(SETTINGS_FILE, "w") as f:
        json.dump(existing_data, f)


def save_dont_ask_again_setting(dont_ask_again):
    """Save the 'don't ask again' preference"""
    try:
        # Load existing settings
        existing_data = {}
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r") as f:
                existing_data = json.load(f)
    except:
        existing_data = {}

    # Update dont_ask_again setting
    existing_data["dont_ask_again"] = dont_ask_again

    with open(SETTINGS_FILE, "w") as f:
        json.dump(existing_data, f)


def show_taskdialog(title,
                    main_instruction='',
                    main_content='',
                    expanded_content=None,
                    buttons=None,
                    command_links=None,
                    icon=None,
                    footer_text=None,
                    help_replacement=None):
    """
    Show a TaskDialog with the specified title and message.

    Args:
        title (str): The title of the TaskDialog.
        main_instruction (str): The large primary text that appears at the top of a task dialog
        main_content (str): MainContent is the smaller text that appears just below the main instructions.
        expanded_content (str): ExpandedContent is hidden by default and will display at the bottom of the task dialog
            when the "Show details" button is pressed.
        buttons (list): A list of button names to display in the dialog.
    """
    _common_buttons = ['Ok', 'Yes', 'No', 'Cancel', 'Retry', 'Close']
    _common_icons = ['None', 'Shield', 'Information', 'Error', 'Warning']

    dialog = TaskDialog(title)
    dialog.TitleAutoPrefix = False
    dialog.MainInstruction = main_instruction
    dialog.MainContent = main_content

    if expanded_content:
        dialog.ExpandedContent = expanded_content

    footer_text = footer_text or 'https://bimcarbone.notion.site/'
    help_replacement = help_replacement or 'AREP - BIM && Carbone (aide)'

    dialog.FooterText = '<a href="{}">{}</a>'.format(footer_text, help_replacement)

    # Handle buttons
    if buttons:
        common_buttons_names = []
        for button_name in [b.capitalize() for b in buttons]:
            if button_name not in _common_buttons:
                pass
            button_full_name = 'TaskDialogCommonButtons.' + button_name
            common_buttons_names.append(button_full_name)

        if common_buttons_names:
            common_buttons = eval('|'.join(common_buttons_names))
            dialog.CommonButtons = common_buttons
        if 'TaskDialogCommonButtons.No' in common_buttons_names:
            dialog.DefaultButton = TaskDialogResult.No

    # Handle command links
    if command_links:
        for i, command_link in enumerate(command_links):
            command_link_name = 'TaskDialogCommandLinkId.CommandLink{}'.format(i + 1)
            dialog.AddCommandLink(eval(command_link_name), command_link)

    # Handle icon
    if icon:
        if icon.capitalize() in _common_icons:
            dialog.MainIcon = eval('TaskDialogIcon.TaskDialogIcon' + icon.capitalize())
        else:
            dialog.MainIcon = TaskDialogIcon.TaskDialogIconNone

    return dialog.Show()


def show_scope_selection_dialog(dialog_options):
    dialog_title = "Calculer le projet"
    dialog_main_instruction = "Quels éléments voulez-vous inclure dans le calcul ?"
    dialog_main_content = "Choisissez l'une des options suivantes :"

    buttons = ['cancel']

    command_links = [
        "Sélection en cours dans Revit" if 'selection' in dialog_options else None,
        "Les éléments visibles dans la vue" if 'view' in dialog_options else None,
        "Tous les éléments" if 'all' in dialog_options else None
    ]

    result = show_taskdialog(dialog_title, dialog_main_instruction, dialog_main_content, buttons=buttons, command_links=command_links)

    if result == TaskDialogResult.CommandLink1:
        return "selection"
    elif result == TaskDialogResult.CommandLink2:
        return "view"
    elif result == TaskDialogResult.CommandLink3:
        return "all"
    else:
        return None
