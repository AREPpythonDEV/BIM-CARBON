from Autodesk.Revit.DB import StorageType
from Autodesk.Revit.UI import TaskDialog


def print_elements_with_carbon_weight_sorted(document, elements):
    """
    Affiche dans une boîte de dialogue Revit la liste des éléments triés par poids carbone.
    """

    elements_with_weight = []

    for el in elements:
        element_name = el.Name if hasattr(el, 'Name') else "Nom non disponible"
        param = el.LookupParameter("_POIDS_CARBONE")
        if param and param.HasValue and param.StorageType == StorageType.Double:
            value = param.AsDouble()
            elements_with_weight.append((element_name, value))
    elements_with_weight.sort(key=lambda x: x[1], reverse=True)

    if elements_with_weight:
        message = "Liste des éléments triés par poids carbone :\n"
        for name, weight in elements_with_weight:
            message += "• {} - Poids carbone : {:.2f}\n".format(name, weight)
    else:
        message = "⚠ Aucun élément avec un poids carbone valide trouvé."

    TaskDialog.Show("Détails des poids carbone", message)
