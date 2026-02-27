#! python3
# -*- coding: utf-8 -*-

from configs import show_settings_dialog
from forms import show_taskdialog

# Usage example:
if show_settings_dialog():
    show_taskdialog(
        'BIM & Carbone - Paramètres',
        'Les paramètres ont été mis à jour avec succès.',
    )
