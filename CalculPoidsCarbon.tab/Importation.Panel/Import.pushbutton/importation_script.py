# -*- coding: utf-8 -*-
from Autodesk.Revit.UI import TaskDialogResult

import Filtre_par_element as filtre_elem
import Filtre_par_Type as filtre_type
from debug import debug_print, pretty_format
from retrieval import element_ids
from forms import show_taskdialog

uidoc = __revit__.ActiveUIDocument
doc = uidoc.Document

def afficher_dialogue_filtre():
    """Affiche le TaskDialog de choix et appelle le module correspondant."""
    result = show_taskdialog(
        title="Importer les valeurs",
        main_instruction="Choisissez le mode d'import des résultats",
        main_content="Comment souhaitez-vous afficher les résultats ?",
        command_links=[
            "Colorer par élément",
            "Colorer par type"
        ],
        icon="Information",
        footer_text="https://bimcarbone.notion.site/importation-des-resultats"
    )

    if result == TaskDialogResult.CommandLink1:
        filtre_elem.main()

    elif result == TaskDialogResult.CommandLink2:
        filtre_type.main()

    else:
        show_taskdialog("Info", "Aucun filtre sélectionné.")


if __name__ == "__main__":
    debug_print(
        "importation_script",
        "element_ids : {0}".format(len(element_ids)),
        element_ids
    )
    afficher_dialogue_filtre()
