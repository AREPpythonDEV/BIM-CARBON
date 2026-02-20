#! python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import threading
import importlib

from Autodesk.Revit.UI import TaskDialog

required_packages = {
    "openpyxl": "3.1.2"
    "plotly==5.17.0"
}


def is_package_installed(package_name, version):
    """ Vérifie si un package est installé avec la bonne version. """
    try:
        pkg = importlib.import_module(package_name)
        installed_version = getattr(pkg, "__version__", None)
        return installed_version == version
    except ImportError:
        return False


def install_packages():
    """ Installe uniquement les packages manquants en arrière-plan. """
    
    missing_packages = [
        f"{pkg}=={ver}" for pkg, ver in required_packages.items()
        if not is_package_installed(pkg, ver)
    ]
    if not missing_packages:
        TaskDialog.Show("Installation", "Tous les packages sont déjà installés.")
        return
    
    pip_command = [sys.executable, "-m", "pip", "install", "--user", "--upgrade", "--no-cache-dir"] + missing_packages


    def run_installation():
        try:
            process = subprocess.Popen(
                pip_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW  # Empêche l'ouverture de la fenêtre cmd
            )
            stdout, stderr = process.communicate()

            if process.returncode == 0:
                TaskDialog.Show("Installation", "Installation terminée avec succès !\nVous pouvez fermer cette fenêtre.")
            else:
                TaskDialog.Show("Installation", f"Erreur lors de l'installation :\n{stderr.decode()}")
        except Exception as e:
            TaskDialog.Show("Installation", f"Erreur inattendue : {str(e)}")

    TaskDialog.Show("Installation", "Installation en cours... Vous pouvez continuer à travailler, temps attente peut aller jusqu'a 15mn")

    
    thread = threading.Thread(target=run_installation, daemon=True)
    thread.start()


