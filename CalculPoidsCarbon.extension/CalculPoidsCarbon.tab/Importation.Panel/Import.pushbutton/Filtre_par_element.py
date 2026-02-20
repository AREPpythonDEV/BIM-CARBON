# -*- coding: utf-8 -*-
from System.Collections.Generic import List

from Autodesk.Revit.DB import ElementId, TransactionGroup

from debug import debug_print
from forms import show_taskdialog
from import_utils import inject_carbon_results_per_element
from retrieval import elements_with_material_volume
from views import (create_view_filters,
                   calculate_total_carbon_weight,
                   create_3d_view,
                   delete_existing_templates,
                   set_view_name_and_template,
                   create_carbon_template)

uidoc = __revit__.ActiveUIDocument
doc = uidoc.Document


def filter_relevant_categories(elements):
    """Purge None elements and None categories and retrieve ElementId Net List"""
    filtered_category_list = set()
    for element in elements:
        if element is None or element.Category is None:
            continue

        param = element.LookupParameter("_POIDS_CARBONE")
        if param is not None:
            filtered_category_list.add(element.Category.Id)
        else:
            debug_print(
                "⚠ Avertissement :",
                "La catégorie '{}' ne possède pas le paramètre '_POIDS_CARBONE'.".format(element.Category.Name)
            )
    return List[ElementId](filtered_category_list)


def main():
    if not inject_carbon_results_per_element():
        show_taskdialog("Info", "Le script s'est arrêté avant le filtre.")
        return

    total_weight = calculate_total_carbon_weight(elements_with_material_volume)
    # TODO: Check if total weight is not already in the response pickle file
    filtered_category_ilist = filter_relevant_categories(elements_with_material_volume)

    if total_weight == 0:
        show_taskdialog("Alerte", "Aucun poids carbone valide trouvé pour les éléments.")
        return

    tg = TransactionGroup(doc, "Importer les valeurs par élément")
    tg.Start()

    carbon_view = create_3d_view(doc)
    create_view_filters(doc, carbon_view, filtered_category_ilist, total_weight)

    delete_existing_templates(doc, "CLC_CARBON_")
    carbon_template = create_carbon_template(doc, carbon_view)

    set_view_name_and_template(doc, carbon_view, carbon_template)
    uidoc.ActiveView = carbon_view

    tg.Assimilate()


if __name__ == "__main__":
    main()
