# -*- coding: utf-8 -*-
import os
from debug import debug_print

doc = __revit__.ActiveUIDocument.Document
doc_title = doc.Title

MAIN_DIRECTORY = "AREP_Calcul Carbone"
VERSIONS_DIRECTORY = "Versions"
APP_DATA_LOCAL_PATH = os.path.normpath(os.path.expanduser("~/AppData/Local"))
D_USER_PATH = r"D:/"

def set_output_paths(model_name):
    """
    Initialise les chemins globaux PATH et VERSION_PATH pour une maquette donnée.

    Args:
        model_name (str): Nom de la maquette pour générer les chemins associés.
    Returns:
        tuple: Contient les chemins suivants :
            - APP_DATA_PATH (str): Chemin vers le répertoire local des données de l'application pour la maquette.
            - APPDATA_VERSION_PATH (str): Chemin vers le répertoire des versions pour la maquette.
            - D_MODEL_DIRECTORY_PATH (str): Chemin vers le répertoire d'export utilisateur pour la maquette.
            - SETTINGS_FILE (str): Chemin vers le fichier de paramètres global.
    """
    # Create application local data directory
    appdata_main_carbon_directory = os.path.join(APP_DATA_LOCAL_PATH, MAIN_DIRECTORY)
    if not os.path.exists(appdata_main_carbon_directory):
        os.mkdir(appdata_main_carbon_directory)
    appdata_model_directory_path = os.path.join(APP_DATA_LOCAL_PATH, MAIN_DIRECTORY, "Calcul Carbone_{}".format(model_name))
    appdata_model_versions_path = os.path.join(appdata_model_directory_path, VERSIONS_DIRECTORY)
    appdata_settings_file = os.path.join(appdata_main_carbon_directory, "settings.json")

    if not os.path.exists(appdata_model_directory_path):
        debug_print("appdata_model_directory_path does not exist, creating it.")
        os.mkdir(appdata_model_directory_path)
        if os.path.exists(appdata_model_versions_path):
            debug_print("appdata_model_directory_path created")
        else:
            debug_print("failed to create appdata_model_directory_path")
    if not os.path.exists(appdata_model_versions_path):
        debug_print("appdata_model_versions_path does not exist, creating it.")
        os.mkdir(appdata_model_versions_path)
        if os.path.exists(appdata_model_versions_path):
            debug_print("appdata_model_versions_path created")
        else:
            debug_print("failed to create appdata_model_versions_path")

    # Create user export directory
    d_main_carbon_directory = os.path.join(D_USER_PATH, MAIN_DIRECTORY)
    if not os.path.exists(d_main_carbon_directory):
        os.mkdir(d_main_carbon_directory)
    d_model_directory_path = os.path.join(D_USER_PATH, MAIN_DIRECTORY, "Calcul Carbone_{}".format(model_name))

    if not os.path.exists(d_model_directory_path):
        os.mkdir(d_model_directory_path)

    return appdata_model_directory_path, appdata_model_versions_path, d_model_directory_path, appdata_settings_file


APP_DATA_PATH, APPDATA_VERSION_PATH, D_MODEL_DIRECTORY_PATH, SETTINGS_FILE = set_output_paths(doc_title)
