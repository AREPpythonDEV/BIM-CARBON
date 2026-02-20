#! python3
# -*- coding: utf-8 -*-

from Autodesk.Revit.DB import Transaction
from Autodesk.Revit.UI import TaskDialogResult

from extraction import get_filtered_elements
from forms import show_taskdialog

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument

PARAM_NAME = "_POIDS_CARBONE"


def reset_carbon_weight(elements, doc):
    t = Transaction(doc, "Effacer poids carbone")
    t.Start()

    reset_count = 0

    try:
        for element in elements:
            param = element.LookupParameter(PARAM_NAME)
            if param and not param.IsReadOnly and param.AsDouble() > 0.0:
                param.Set(0)
                reset_count += 1

        t.Commit()
        return reset_count, True

    except Exception as e:
        print("Une erreur est survenue:", str(e))
        t.RollBack()
        return 0, False


def show_results(reset_count, total_count, success):
    if not success:
        show_taskdialog(
            title="Erreur",
            main_instruction="Une erreur est survenue lors de la réinitialisation.",
            main_content="Veuillez réessayer ou contacter l'équipe BIM & Data."
        )
        return

    if reset_count == total_count:
        message = 'Le paramètre "_POIDS_CARBONE" de tous les éléments ont été effacé avec succès !'
    elif reset_count == 0:
        message = 'Tous les éléments avaient déjà le paramètre "_POIDS_CARBONE" à 0.'
    else:
        plural = "s" if reset_count > 1 else ""
        message = (f'Le paramètre "_POIDS_CARBONE" de {reset_count} objet{plural} '
                   f'a été effacé avec succès.\n'
                   f'Le reste des objets était déjà à 0.')

    show_taskdialog(
        title="Réinitialisation terminée",
        main_instruction="La réinitialisation des valeurs de poids carbone est terminée.",
        main_content=message
    )


def main():
    filtered_result = get_filtered_elements(uidoc)

    if not filtered_result.success:
        show_taskdialog(
            title="Erreur",
            main_instruction="Erreur lors de la récupération des éléments",
            main_content=filtered_result.error.message if hasattr(filtered_result, 'error') else "Erreur inconnue"
        )
        return

    filtered_elements = filtered_result.data

    if not filtered_elements:
        show_taskdialog(
            title="Aucun élément",
            main_instruction="Aucun élément trouvé",
            main_content="Aucun élément valide n'a été trouvé pour la réinitialisation."
        )
        return

    user_choice = show_taskdialog(
        title="Confirmation de réinitialisation",
        main_instruction='Souhaitez-vous réinitialiser le paramètre "_POIDS_CARBONE" des éléments ?',
        main_content=f"Cela effacera les valeurs de poids carbone pour {len(filtered_elements)} élément(s). Êtes-vous sûr de vouloir continuer ?",
        buttons=['Yes', 'No']
    )

    if user_choice == TaskDialogResult.Yes:
        reset_count, success = reset_carbon_weight(filtered_elements, doc)
        show_results(reset_count, len(filtered_elements), success)


if __name__ == "__main__":
    main()
