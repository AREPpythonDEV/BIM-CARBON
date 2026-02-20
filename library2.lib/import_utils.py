# -*- coding: utf-8 -*-
import Autodesk.Revit.Exceptions as Exceptions
from Autodesk.Revit.DB import Transaction, TransactionStatus

from debug import debug_print
from retrieval import element_quantity_dict, elements_with_material_volume

uidoc = __revit__.ActiveUIDocument
doc = uidoc.Document


def inject_carbon_results_per_element():
    """Inject calculated carbon results into elements."""
    t = Transaction(doc, "Update _POIDS_CARBONE")
    t.Start()

    for el in elements_with_material_volume:
        element_id = el.Id.ToString()
        if element_id not in element_quantity_dict:
            continue

        qty = element_quantity_dict[element_id]
        param = el.LookupParameter("_POIDS_CARBONE")

        if param and not param.IsReadOnly:
            try:
                param.Set(qty)
            except Exceptions.InvalidOperationException:
                debug_print("import_utils", "Skipping read-only element: {}".format(el.Id))
            except Exception as err:
                debug_print("import_utils", "Erreur param {}: {}".format(el.Id, err))

    t.Commit()
    return t.GetStatus() == TransactionStatus.Committed


def sum_carbon_weight_by_type(elements):
    """
    Regroupe les éléments par leur TypeId et somme les résultats carbone.
    Retourne un dict {ElementId : (type_name, total_weight)}.
    """
    weight_by_type = {}
    for el in elements:
        if el is None:
            continue
        element_id = el.Id.ToString()
        if element_id not in element_quantity_dict:
            continue
        tid = el.GetTypeId()
        w = element_quantity_dict[element_id]

        try:
            sym = el.Symbol
            type_name = sym.Name
        except Exception:
            try:
                te = doc.GetElement(tid)
                type_name = te.Name
            except Exception:
                type_name = str(tid.IntegerValue)

        prev_name, prev_w = weight_by_type.get(tid, (type_name, 0.0))
        weight_by_type[tid] = (prev_name, prev_w + w)

    return weight_by_type


def inject_carbon_results_by_type():
    """Inject aggregated carbon results per type into elements."""
    weight_by_type = sum_carbon_weight_by_type(elements_with_material_volume)
    t = Transaction(doc, "Update _POIDS_CARBONE by Type")
    t.Start()

    for el in elements_with_material_volume:
        element_id = el.Id.ToString()
        if element_id not in element_quantity_dict:
            continue
        param = el.LookupParameter("_POIDS_CARBONE")
        if param and not param.IsReadOnly:
            total_weight = weight_by_type.get(el.GetTypeId(), (None, None))[1]
            if total_weight is None:
                continue
            try:
                param.Set(total_weight)
            except Exceptions.InvalidOperationException:
                debug_print("import_utils", "Skipping read-only element: {}".format(el.Id))
            except Exception as err:
                debug_print("import_utils", "Erreur param {}: {}".format(el.Id, err))

    t.Commit()
    return t.GetStatus() == TransactionStatus.Committed
