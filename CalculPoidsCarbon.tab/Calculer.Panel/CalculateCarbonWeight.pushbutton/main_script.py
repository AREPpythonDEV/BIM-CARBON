#! python3
# -*- coding: utf-8 -*-

import os
import pickle

from Autodesk.Revit.DB import FilteredElementCollector, ProjectInfo

from debug import debug_print, pretty_format
from extraction import compressed_dico_extraction, get_latest_verison, generate_component_list
from forms import show_user_choice_dialog, show_user_name_dialog, show_taskdialog
from misc import create_project_parameter, assign_project_id_value, worksharing_check
from paths import APPDATA_VERSION_PATH, APP_DATA_PATH
from version_manager import create_version_csv, add_version
from error import CustomError, ErrorCode, OperationResult  # Import your error system

uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document
doc_title = doc.Title

csv_file_path = os.path.join(APPDATA_VERSION_PATH, f"{doc_title}.csv")
csv_file_exists = os.path.exists(csv_file_path)

def send_request(request_parameters):
    """Send request to API and return results"""
    import time
    start_time = time.time()

    try:
        # Apply pyRevit requests fix if needed
        try:
            import requests
        except ImportError:
            debug_print("Applying pyRevit 5.2 requests fix...")
            from pyrevit_requests import fix_requests
            fix_requests()
            import requests
            debug_print("✓ requests fix applied")

        # url = "http://192.168.96.212:82/api/v3/get_component_impacts"
        # url = 'http://127.0.0.1:8050/api/v3/get_component_impacts'
        # url = "http://192.168.96.189:83/api/v3/get_component_impacts"
        url = "http://192.168.96.189:8080/api/v3/get_component_impacts"

        r = requests.post(url, json=request_parameters, headers={"Authorization" : "Wha4xLNZDR2XcFzrrcJjKN"})

        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            debug_print(f"HTTP Error occurred: {http_err}")
            debug_print(f"Response content: {r.text}")
            return None

        end_time = time.time()
        elapsed_ms = (end_time - start_time) * 1000
        debug_print(f"⏱️ Request: {elapsed_ms:.1f}ms")

        return r.json()

    except Exception as e:
        end_time = time.time()
        elapsed_ms = (end_time - start_time) * 1000
        debug_print(f"⏱️ send_request: {elapsed_ms:.1f}ms (FAILED)")
        debug_print(f"Error sending request: {e}")
        debug_print(f"Request parameters: {pretty_format(request_parameters)}")
        return None

def get_project_info_parameters(doc):
    """
    Get project info and extract relevant parameters

    Returns:
        OperationResult with dict containing project_id, phase_name, project_name
    """
    try:
        project_info = FilteredElementCollector(doc).OfClass(ProjectInfo).FirstElement()
        if not project_info:
            return OperationResult.error_result(
                ErrorCode.DOCUMENT_ACCESS_ERROR,
                message="Impossible de récupérer les informations du projet",
                context='get_project_info_parameters'
            )

        parameters = project_info.Parameters

        project_id = None
        phase_name = None
        project_name = None

        for info in parameters:
            param_name = info.Definition.Name

            if param_name == "Project_Id":
                project_id = info.AsString()
            elif param_name == "Etat du projet":
                phase_name = info.AsString()
            elif param_name in ["_INF_PRJ_NOM", "Nom du bâtiment"]:
                project_name = info.AsString()
                if param_name == "_INF_PRJ_NOM":
                    break

        return OperationResult.success_result({
            'project_info': project_info,
            'parameters': parameters,
            'project_id': project_id,
            'phase_name': phase_name,
            'project_name': project_name
        })

    except Exception as e:
        return OperationResult.error_result(
            ErrorCode.PARAMETER_ACCESS_ERROR,
            details=str(e),
            context='get_project_info_parameters'
        )


def ensure_project_parameter_exists(doc):
    """
    Ensure Project_Id parameter exists, create if needed

    Returns:
        OperationResult with project_id value (can be None if not set yet)
    """
    try:
        # Get project info parameters
        params_result = get_project_info_parameters(doc)
        if not params_result.success:
            return params_result

        param_data = params_result.data
        parameters = param_data['parameters']
        project_id = param_data['project_id']

        # Check if Project_Id parameter exists
        param_names = [p.Definition.Name for p in parameters]

        if "Project_Id" not in param_names:
            debug_print("Project_Id parameter not found, creating it...")

            # Create the parameter
            creation_result = create_project_parameter(doc)
            if not creation_result.success:
                return creation_result  # Propagate error

            debug_print("project_parameter_creation", creation_result.data)
        else:
            debug_print("project_parameter_creation", "Project_Id already exists in document", "Value:{}".format(project_id))

        # Return the project_id value (can be None)
        return OperationResult.success_result(project_id)

    except Exception as e:
        return OperationResult.error_result(
            ErrorCode.UNKNOWN_ERROR,
            details=str(e),
            context='ensure_project_parameter_exists'
        )


def main():
    """Main function with integrated error handling"""
    debug_print("Starting main() in main_script")

    try:
        # Step 1: Get username
        username = show_user_name_dialog()
        if not username:
            show_taskdialog("Calcul abandonné", "Nom d'utilisateur requis")
            return

        # Step 2: Check worksharing
        worksharing_result = worksharing_check(doc)
        if not worksharing_result.success:
            worksharing_result.show_error_dialog()
            return

        # Step 3: Ensure Project_Id parameter exists and get project info
        param_result = ensure_project_parameter_exists(doc)
        if not param_result.success:
            param_result.show_error_dialog()
            return

        project_id = param_result.data  # Can be None if not set yet

        info_result = get_project_info_parameters(doc)
        if not info_result.success:
            info_result.show_error_dialog()
            return

        phase_name = info_result.data['phase_name']
        project_name = info_result.data['project_name']

        compressed_dico_result = compressed_dico_extraction(uidoc)
        if not compressed_dico_result.success:
            compressed_dico_result.show_error_dialog()
            return

        compressed_dico = compressed_dico_result.data
        debug_print("**compressed_dico**", pretty_format(compressed_dico))

        components = generate_component_list(doc_title, phase_name, compressed_dico)

        new_version = False
        update_version = False
        selected_version = None
        version_id = None

        if project_id:
            user_choice = show_user_choice_dialog()

            if user_choice['cancelled']:
                show_taskdialog("Calcul abandonné", "Vous avez annulé le calcul.")
                return

            new_version = user_choice['new_version']
            selected_version = user_choice['selected_version']

            if selected_version:
                version_id = selected_version.split(";")[1]

        common_params = {
            "project_name": doc_title,
            "project_lifetime": 50,
            "method": "static",
            "user": username,
            "persist": True
        }

        debug_print("**common_params**", pretty_format(common_params))

        # Build request based on project state
        if project_id is None:
            debug_print("Project_id is None, sending components only")
            request_parameters = {**common_params, "components": components}
        elif project_id=="":
            debug_print("Project_id is empty string, sending components only")
            request_parameters = {**common_params, "components": components}
        elif project_id and new_version:
            request_parameters = {**common_params, "project_id": project_id, "components": components}
        elif project_id and update_version:
            request_parameters = {**common_params, "project_id": project_id, "version_id": version_id, "components": components}
        else:
            show_taskdialog(
                "Calculer le projet - Calcul abandonné",
                "Les éléments de la maquette n'ont pas pu être extraits."
            )
            return

        debug_print("**request_parameters**", pretty_format(request_parameters))

        results = send_request(request_parameters)
        debug_print("**results**", pretty_format(results))

        if not results:
            show_taskdialog(
                "Erreur de communication",
                "Impossible de communiquer avec l'API de calcul.",
                "Veuillez vérifier que le serveur est accessible et réessayer."
            )
            return

        if 'error1' in results:
            show_taskdialog(
                "Calculer le projet - Calcul abandonné",
                "La valeur du paramètre Project_Id n'a pas été reconnue par l'outil 'Empreinte Carbone'",
                "Veuillez supprimer la valeur du paramètre Project_Id dans les paramètres du projet, puis relancer le calcul."
                "\nSi le problème persiste, veuillez contacter l'équipe BIM & Méthodes.",
                icon='error'
            )
            return

        if 'error0' in results:
            show_taskdialog(
                "Calculer le projet - Calcul abandonné",
                "Une erreur inattendue s'est produite lors du calcul de l'empreinte dans la calculette carbone.",
                "Veuillez contacter l'équipe BIM & Méthodes.",
                icon='error'
            )
        response_data, version_name = get_latest_verison(results, return_version_name=True)

        if not response_data:
            show_taskdialog(
                "Calculer le projet - Calcul abandonné",
                "Erreur lors de la récupération de la dernière version."
            )
            return

        debug_print("**Response Data**", pretty_format(response_data))

        with open(os.path.join(APP_DATA_PATH, "api_response_data.pickle"), "wb") as g:
            pickle.dump(response_data, g, protocol=0)

        with open(os.path.join(APP_DATA_PATH, "compressed_dico.pickle"), "wb") as h:
            pickle.dump(compressed_dico, h, protocol=0)

        if not csv_file_exists:
            create_version_csv(csv_file_path, results, version_name)
            debug_print("CSV file created at:", csv_file_path)
        elif new_version:
            add_version(csv_file_path, results, version_name)
            debug_print("CSV file updated with new version at:", csv_file_path)

        if not project_id:
            assign_project_id_value(doc, results)
            debug_print("Assigned new Project_Id to project.")

        show_taskdialog(
            "Calculer le projet - Calcul réussi",
            "L'extraction et le processus de calcul ont réussi",
            "A partir du panel importation, vous pouvez importer les calculs dans les éléments du projet pour visualiser leurs impacts carbone ou bien générer un rapport."
        )

    except CustomError as e:
        e.show_error_dialog()
        return

    except Exception as e:
        show_taskdialog(
            "Erreur inattendue",
            "Une erreur inattendue s'est produite.",
            str(e)
        )
        debug_print(f"Unexpected error in main: {str(e)}")
        import traceback
        debug_print(traceback.format_exc())
        return


if __name__ == "__main__":
    main()
