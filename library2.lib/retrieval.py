# -*- coding: utf-8 -*-

import os
import pickle
import json
from System import Int64

from Autodesk.Revit.DB import ElementId

from paths import APP_DATA_PATH
from py2_extraction import create_element_id_dict
from debug import debug_print, pretty_format

uidoc = __revit__.ActiveUIDocument
doc = uidoc.Document

#TODO: add try except to catch FileNotFoundError
with open(os.path.join(APP_DATA_PATH, "compressed_dico.pickle"), "rb") as h:
    compressed_dico = pickle.load(h)

with open(os.path.join(APP_DATA_PATH, "api_response_data.pickle"), "rb") as g:
    carbon_results = pickle.load(g)
for result in carbon_results:
    debug_print("carbon_results", pretty_format(result))

with open(os.path.join(APP_DATA_PATH, "element_ids_with_material_volume.json"), "r") as f:
    element_ids = json.load(f)

# Loop through compressed_dico and carbon_results simultaneously to calculate the carbon weight per element using the percentages previously calculated
# Meant to update individual ratios with actual carbon weight

debug_print("**compressed_dico right from the pickle file**", pretty_format(compressed_dico))

for dico in compressed_dico:
    for result in carbon_results:
        if dico["material"] == result["Macro-composant de niveau 4"] and dico["sous-projet"] == result[
            "Macro-composant de niveau 3"]:

            for index, ratio in enumerate(dico["individual_quantities"]):
                element_carbon_weight = ratio * result["Impact sur le changement climatique (kgCO2e)"]
                dico["individual_quantities"][index] = element_carbon_weight

element_quantity_dict, category_quantity_dict = create_element_id_dict(compressed_dico)


def extract_macrocomponents_impact(carbon_results):
    """
    Extrait pour chaque Macro-composant de niveau 3 son Macro-composant de niveau 4
    et l'impact sur le changement climatique (kgCO2e).
    """
    extracted_impact = {}
    for entry in carbon_results:
        macro_comp_3 = entry.get("Macro-composant de niveau 3")
        macro_comp_4 = entry.get("Macro-composant de niveau 4")
        impact = entry.get("Impact sur le changement climatique (kgCO2e)")

        if macro_comp_3 and macro_comp_4 and impact is not None:
            if macro_comp_3 not in extracted_impact:
                extracted_impact[macro_comp_3] = {}
            extracted_impact[macro_comp_3][macro_comp_4] = impact
    for k,v in extracted_impact.items():
        debug_print("{}: {}".format(k, v))
    return extracted_impact


def extract_macrocomponents():
    """Extrait pour chaque macrocomposant 3 son macrocomposant 4 et sa quantité."""

    extracted_data = {}

    for entry in carbon_results:

        macrocomp_3 = entry.get("Macro-composant de niveau 3")
        macrocomp_4 = entry.get("Macro-composant de niveau 4")
        quantity = entry.get("Quantite")

        if macrocomp_4 and quantity is not None:
            if macrocomp_3 not in extracted_data:
                extracted_data[macrocomp_3] = {}
            extracted_data[macrocomp_3][macrocomp_4] = quantity

    return extracted_data


def get_poids_carbon_parameter_id(material_list):
    for element in material_list:
        carbon_parameter = element.LookupParameter("_POIDS_CARBONE")
        if carbon_parameter:
            return carbon_parameter.Id
    return None


extracted_data = extract_macrocomponents()
elements_with_material_volume = [doc.GetElement(ElementId(Int64(element_id))) for element_id in element_ids]
impact_data = extract_macrocomponents_impact(carbon_results)

POIDS_CARBON_PARAMETER_ID = get_poids_carbon_parameter_id(elements_with_material_volume)
