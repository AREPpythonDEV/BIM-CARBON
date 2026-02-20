#! python3
# -*- coding: utf-8 -*-

import json
import os
import re
from collections import defaultdict, OrderedDict
from datetime import datetime
from openpyxl import Workbook

from Autodesk.Revit.DB import FilteredElementCollector, ElementId, BuiltInParameter
from Autodesk.Revit.UI import TaskDialog

from debug import debug_print, pretty_format
from error import OperationResult, ErrorCode
from forms import show_scope_selection_dialog, show_taskdialog
from material import material_mapping, known_materials
from misc import convert_to_cubic_meters, process_and_export_to_excel, get_element_id_value
from paths import APP_DATA_PATH, D_MODEL_DIRECTORY_PATH
from worket_names_mapping import ws_mapping, alt_ws_mapping


def get_filtered_elements(uidoc, allow_selection=False):
    """Récupère et filtre les éléments du document Revit en fonction de la sélection de l'utilisateur et des critères définis."""
    doc = uidoc.Document
    filtered_elements = []
    try:
        if allow_selection:
            user_choice = show_scope_selection_dialog(['selection', 'view', 'all'])
            selection = uidoc.Selection.GetElementIds()
            debug_print(f"Éléments sélectionnés: {len(selection)}")

            all_elements = []

            if user_choice == "selection":
                if selection:
                    all_elements = [doc.GetElement(id) for id in selection]
                else:
                    try:
                        show_taskdialog("Calculer le projet - Erreur",
                                        "Aucun élément sélectionné.",
                                        "Veuillez sélectionner des éléments à calculer.")
                        while not all_elements:
                            all_elements = uidoc.Selection.PickElementsByRectangle()
                    except Exception:
                        return OperationResult.error_result(
                            ErrorCode.NO_ELEMENTS_SELECTED,
                            context='get_filtered_elements'
                        )
                    except:
                        return OperationResult.error_result(
                            ErrorCode.SELECTION_CANCELLED,
                            context='get_filtered_elements'
                        )

                debug_print("get_filtered_elements", f"selection: {len(all_elements)}")
            elif user_choice == "view":
                all_elements = FilteredElementCollector(doc, doc.ActiveView.Id).WhereElementIsNotElementType().ToElements()
                debug_print("get_filtered_elements", f"view: {len(all_elements)}")
            elif user_choice == "all":
                all_elements = FilteredElementCollector(doc).WhereElementIsNotElementType().ToElements()
                debug_print("get_filtered_elements", f"all: {len(all_elements)}")
            else:
                return OperationResult.error_result(
                    ErrorCode.NO_USER_SELECTION,
                    context='get_filtered_elements'
                )

        else:
            all_elements = FilteredElementCollector(doc).WhereElementIsNotElementType().ToElements()

        for element in all_elements:
            try:
                family_param = element.LookupParameter("Famille")
                phase_param = element.LookupParameter("Phase de création")

                if family_param and phase_param:

                    phase_created_param = element.LookupParameter("Phase de création")
                    if phase_created_param:
                        phase_created_id = phase_created_param.AsElementId()
                        created_phase_element = doc.GetElement(phase_created_id)
                        if created_phase_element:
                            phase_name = created_phase_element.Name
                            if "Exi" not in phase_name and "EXI" not in phase_name:
                                filtered_elements.append(element)

            except Exception as e:

                print(f"Erreur lors du traitement de l'élément {element.Id}: {e}")

        if not filtered_elements:
            return OperationResult.error_result(
                ErrorCode.NO_FILTERED_ELEMENTS,
                context='get_filtered_elements'
            )

        return OperationResult.success_result(filtered_elements)

    except Exception as e:
        return OperationResult.error_result(
            ErrorCode.ELEMENT_PROCESSING_ERROR,
            details=str(e),
            context='get_filtered_elements'
        )


def extract_elements_with_material_volume(filtered_elements, document):
    """Extrait les éléments ayant des volumes de matériaux."""
    minimum_volume_threshold = 0.0001
    elements_with_material_volume = set()
    filtered_element_ids = {element.Id for element in filtered_elements}

    def element_has_significant_material_volume(element, volume_threshold):
        material_ids = element.GetMaterialIds(False)
        for material_id in material_ids:
            try:
                if element.GetMaterialVolume(material_id) >= volume_threshold:
                    return True
            except Exception:
                pass
        return False

    def element_has_significant_host_volume(element, volume_threshold):
        try:
            if element.StructuralMaterialId == ElementId.InvalidElementId:
                return False
        except Exception as exception:
            # debug_print("Exception raised when accessing StructuralMaterialId", str(exception))
            return False

        for parameter in element.Parameters:
            try:
                if (
                    parameter.Definition.BuiltInParameter == BuiltInParameter.HOST_VOLUME_COMPUTED
                    and parameter.HasValue
                ):
                    return parameter.AsDouble() >= volume_threshold
            except Exception:
                continue

        return False

    for element in filtered_elements:
        dependent_element_ids = element.GetDependentElements(None)

        for dependent_element_id in dependent_element_ids:
            if dependent_element_id in filtered_element_ids and dependent_element_id != element.Id:
                continue

            dependent_element = document.GetElement(dependent_element_id)
            if not dependent_element or dependent_element.ViewSpecific:
                continue

            has_significant_volume = (
                element_has_significant_material_volume(dependent_element, minimum_volume_threshold)
                or element_has_significant_host_volume(dependent_element, minimum_volume_threshold)
            )

            if has_significant_volume:
                elements_with_material_volume.add(dependent_element)

    if elements_with_material_volume:
        return OperationResult.success_result(list(elements_with_material_volume))

    return OperationResult.error_result(
        ErrorCode.NO_MATERIAL_VOLUMES_FOUND,
        context='extract_materials_with_volume'
    )


def filter_elements_by_category(elements):
    """Filtre les éléments par catégorie pour exclure les garde-corps et barreaux."""
    filtering_errors = 0
    filtered_elements = []
    discarded_count = 0
    discarded_element_ids = []
    for element in elements:
        try:
            if element and element.Category:
                if get_element_id_value(element.Category.Id) not in [-2000126, -2000127]:
                    filtered_elements.append(element)
                else:
                    discarded_count += 1
                    discarded_element_ids.append(get_element_id_value(element.Id))

        except Exception:
            filtering_errors += 1
            continue
    debug_print("filter_elements_by_category", f"Discarded {discarded_count} elements due to category filtering.",
                discarded_element_ids)
    return filtered_elements


def generate_dico(has_material_volume, document):
    """Génère un dictionnaire de données sur les éléments, incluant volumes, composants, etc."""
    allowed_prefixes = ('2_', '3_', '4_')
    filtered_ws_mapping = {k: v for k, v in ws_mapping.items() if k.startswith(allowed_prefixes)}

    workset_table = document.GetWorksetTable()

    # 2) Initialisations
    elements_with_unknown_materials = []
    mat_not_in_db = []
    dico = []
    debug_print("**has_material_volume**", pretty_format(has_material_volume))
    processed_materials = 0
    skipped_materials = 0

    for element in has_material_volume:
        # 1) Matériaux via GetMaterialIds
        materials = list(element.GetMaterialIds(False))

        # 1 bis) Fallback : StructuralMaterialId + Volume Definition (HOST_VOLUME_COMPUTED)
        use_structural_material = False
        if not materials and element.StructuralMaterialId != ElementId.InvalidElementId:
            materials = [element.StructuralMaterialId]
            use_structural_material = True

        processed_materials += len(materials)

        element_id = element.Id
        sous_projet = workset_table.GetWorkset(element.WorksetId).Name
        lot = "N/A"

        for mat_id in materials:
            revit_mat = document.GetElement(mat_id)
            material_class = revit_mat.MaterialClass

            # Volume : soit par GetMaterialVolume, soit par HOST_VOLUME_COMPUTED
            if use_structural_material:
                vol_param = (
                        element.LookupParameter("Volume")
                        or element.get_Parameter(BuiltInParameter.HOST_VOLUME_COMPUTED)
                )
                if not vol_param or not vol_param.HasValue:
                    skipped_materials += 1
                    continue
                volume_m3 = convert_to_cubic_meters(vol_param.AsDouble())
            else:
                volume_m3 = convert_to_cubic_meters(element.GetMaterialVolume(mat_id))

            # 4) Déterminer la classe connue
            known_class = None
            for known_material_class, possible_materials in known_materials.items():
                if material_class.lower() in possible_materials:
                    known_class = known_material_class
                    break
            # debug_print("**known_class**", known_class)
            if known_class is None:
                mat_not_in_db.append(material_class)
                elements_with_unknown_materials.append(element)
                skipped_materials += 1
                continue

            # 5) Calculer quantité
            component_id, density = material_mapping[known_class]
            # debug_print("**volume_m3**", volume_m3)
            # debug_print("**density**", density)
            quantity = round(volume_m3 * density, 6)

            # 6) N’ajouter que si le sous-projet est autorisé
            if sous_projet.startswith(allowed_prefixes):
                dico.append(OrderedDict(
                    (
                        ("sous-projet", ws_mapping.get(sous_projet, alt_ws_mapping.get(sous_projet[0], None))),
                        ("lot", str(lot)),
                        ("volume", round(volume_m3, 3)),
                        ("unit", "kg"),
                        ("component_id", str(component_id)),
                        ("material", known_class),
                        ("element_id", str(element_id)),
                        ("category", element.Category.Name),
                        ("quantity", quantity)
                    )
                ))

    if skipped_materials == processed_materials:
        return OperationResult.error_result(
            ErrorCode.NO_KNOWN_MATERIALS_FOUND,
            details='All materials were skipped because none matched the known materials database',
            context='generate_dico'
        )
    if not dico:
        # No elements were in valid worksets (2_, 3_, 4_)
        plural = len(has_material_volume) > 1
        return OperationResult.error_result(
            ErrorCode.NO_VALID_WORKSETS,
            details=f"{len(has_material_volume)} élément{'s' if plural else ''} {'ont' if plural else 'a'} été retrouvé{'s' if plural else ''}, "
                    f"{'mais aucun' if plural else 'il'} n'appartient {'' if plural else 'pas '}aux sous-projets valides commencant par 2_, 3_ ou 4_",
            context='generate_dico'
        )

    return OperationResult.success_result({
        'dico': dico,
        'elements_with_unknown_materials': elements_with_unknown_materials
    })


def aggregate_data(dico):
    """Agrège les données par composant et somme les quantités."""
    cw_agg_dict = OrderedDict()

    for dictionary in dico:
        component_id = dictionary["component_id"]
        material = dictionary["material"]
        element_id = dictionary["element_id"]
        volume = dictionary["volume"]
        quantity = dictionary["quantity"]

        cw_key = (component_id, element_id)

        if cw_key in cw_agg_dict:
            cw_agg_dict[cw_key]["volume"] += volume
            cw_agg_dict[cw_key]["quantity"] += quantity
        else:
            cw_agg_dict[cw_key] = {
                "sous-projet": dictionary["sous-projet"],
                "lot": dictionary["lot"],
                "component_id": component_id,
                "material": material,
                "volume": volume,
                "unit": dictionary["unit"],
                "element_id": element_id,
                "category": dictionary["category"],
                "quantity": quantity
            }

    result = list(cw_agg_dict.values())
    sorted_result = sorted(result, key=lambda x: x["element_id"])
    return sorted_result


def organize_by_project(result):
    """Organise les éléments par projet et composant."""
    projet_dict = OrderedDict()

    for item in result:
        projet_key = item["sous-projet"]
        component_id = item["component_id"]

        if projet_key not in projet_dict:
            projet_dict[projet_key] = defaultdict(list)

        projet_dict[projet_key][component_id].append(item)

    return projet_dict


def compress_data(projet_dict):
    """Compresse les données organisées en une liste finale."""
    compressed_dico = []

    for projet_key, component_dict in projet_dict.items():
        for component_id, component_items in component_dict.items():
            combined_item = OrderedDict((
                ("sous-projet", projet_key),
                ("category", [item["category"] for item in component_items]),
                ("component_id", component_id),
                ("material", component_items[0]["material"]),
                ("quantity", sum(item["quantity"] for item in component_items)),
                ("unit", component_items[0]["unit"]),
                ("elements", [item["element_id"] for item in component_items]),
                ("individual_quantities", [item["quantity"] for item in component_items]),
                ("lot", [item["lot"] for item in component_items])
            ))
            compressed_dico.append(combined_item)

    return compressed_dico


def save_element_ids(has_material_volume, path):
    """Enregistre les identifiants des éléments dans un fichier JSON."""
    element_ids_with_material_volume = [get_element_id_value(element.Id) for element in has_material_volume]
    os.makedirs(path, exist_ok=True)
    with open(os.path.join(path, "element_ids_with_material_volume.json"), "w") as f:
        json.dump(element_ids_with_material_volume, f)


def compressed_dico_extraction(ui_document):
    """Extrait les éléments compressés après filtrage et génération des dictionnaires."""
    context = 'compressed_dico_extraction'
    try:
        document = ui_document.Document

        filtered_result = get_filtered_elements(ui_document, True)
        if not filtered_result.success:
            return filtered_result.add_context(context)

        filtered_elements = filtered_result.data

        materials_result = extract_elements_with_material_volume(filtered_elements, document)

        if not materials_result.success:
            return materials_result.add_context(context)

        elements_with_material_volumes = materials_result.data
        debug_print("elements_with_material_volumes", elements_with_material_volumes)

        elements_with_material_volumes = filter_elements_by_category(elements_with_material_volumes)
        debug_print("elements_with_material_volumes", elements_with_material_volumes)

        dico_result = generate_dico(elements_with_material_volumes, document)
        if not dico_result.success:
            return dico_result.add_context(context)

        dico = dico_result.data['dico']
        elements_with_unknown_materials = dico_result.data['elements_with_unknown_materials']
        debug_print("**dico**", pretty_format(dico))

        if elements_with_unknown_materials:
            show_taskdialog("Classes de matériaux inconnues",
                            "Certains matériaux ont des classes inconnues",
                            "Les éléments avec les classes en question ne seront pas pris en compte dans le calcul.")
            debug_print('**elements_with_unknown_materials**', elements_with_unknown_materials)
            process_and_export_to_excel(ui_document, elements_with_unknown_materials)

        result = aggregate_data(dico)
        projet_dict = organize_by_project(result)
        compressed_dico = compress_data(projet_dict)
        save_element_ids(elements_with_material_volumes, APP_DATA_PATH)

        return OperationResult.success_result(compressed_dico)

    except Exception as e:
        return OperationResult.error_result(
            ErrorCode.UNKNOWN_ERROR,
            details=str(e),
            context=context
        )


def get_datetime(date_time_string):
    """
    gets the datetime object from the date time string
    workarounds the strptime issue with the date time string in CPython

    Parameters
    ----------
    date_time_string : str
        the date time string.

    Returns
    -------
    datetime
        the datetime object from the date time string.
    """
    timestamp = date_time_string[date_time_string.find("(") + 1:date_time_string.find(")")]
    date_part, time_part = timestamp.split()
    day, month, year = date_part.split('-')
    hour, minute, second_microsecond = time_part.split(':')
    second, microsecond = second_microsecond.split('.')

    date_time_integers = map(int, [year, month, day, hour, minute, second, microsecond])
    date_time_object = datetime(*date_time_integers)

    return date_time_object


def extract_version_name(version_name):
    match = re.match(r"(Version \d+)", version_name)
    return match.group(1) if match else None


def remove_non_utf8_chars(list_of_dicts):
    updated_list_of_dicts = []
    for dictionary in list_of_dicts:
        updated_dict = {}
        for key, value in dictionary.items():
            new_key = key.replace("é", "e")
            updated_dict[new_key] = value
        updated_list_of_dicts.append(updated_dict)

    return updated_list_of_dicts


def get_latest_verison(results, return_version_name=False):
    """
    gets the latest version from the results

    Parameters
    ----------
    results : dict
        dictionary containing the results, that are returned from the carbon API. The results must contain an "impacts" key.

    return_version_name : bool
        whether to return the timestamped version name along with the latest version list.

    Returns
    -------
    latest_version : str
        the latest version from the results.

    """
    if results:
        latest_version_list = []
        impacts = results["impacts"]
        formatted_impacts = remove_non_utf8_chars(impacts)
        latest_version = None
        timestamped_version_name = None
        latest_version_dict = {}
        for version_dict in formatted_impacts:
            version_name = version_dict["Version"]
            if latest_version is None:
                latest_version = get_datetime(version_name)
                latest_version_dict[latest_version] = version_dict["Version"]
            else:
                current_version = get_datetime(version_name)
                if current_version > latest_version:
                    latest_version_dict = {}
                    latest_version = current_version
                    latest_version_dict[latest_version] = version_dict["Version"]

        for version_dict in formatted_impacts:
            if version_dict["Version"] == latest_version_dict[latest_version]:
                latest_version_list.append(version_dict)
                timestamped_version_name = version_dict["Version"]

        if return_version_name:
            return latest_version_list, timestamped_version_name
        else:
            return latest_version_list

    else:
        TaskDialog.Show("Erreur", "Le dictionnaire de résultats n'a pas été correctement traité.")
        return None


def generate_component_list(doc_title, phase_name, compressed_dico):
    """
    generates the component list from the compressed dictionary

    Parameters
    ----------
    doc_title : str
        the document title.
    phase_name : str
        the phase name.
    compressed_dico : list
        the compressed dictionary.

    Returns
    -------
    component_list : list
        the component list.
    """
    components = []
    components.extend([
        {
            "component_id": "0",
            "component_name": doc_title,
            "parent_id": None
        },
        {
            "component_id": "1",
            "component_name": f"Phase {phase_name}",
            "parent_id": "0"
        }
    ])

    added_sous_projet_component = {}

    component_count = 2
    for q in compressed_dico:
        sous_projet = q["sous-projet"]
        if sous_projet not in added_sous_projet_component.keys():
            added_sous_projet_component[sous_projet] = str(component_count)
            # Append "sous-projet" component as parent of material components
            components.append(
                {
                    "component_id": str(component_count),
                    "component_name": sous_projet,
                    "parent_id": "1"
                }
            )
            component_count += 1

        material_id = [key for key, (value, _) in material_mapping.items() if q["component_id"] == value]
        material_id = "".join(material_id)
        product_id = q["component_id"]

        if q["quantity"] != 0:
            percentage_quantities = [r / q["quantity"] for r in q["individual_quantities"]]
            q["individual_quantities"] = percentage_quantities

        components.append(
            {
                "component_id": str(component_count),
                "component_name": material_id,
                "parent_id": added_sous_projet_component[sous_projet],
                "tags": [],
                "product_id": product_id,
                "properties": [{
                    "unit": q["unit"],
                    "quantity": round(float(q["quantity"]), 3)
                }]
            }
        )
        component_count += 1

    return components
