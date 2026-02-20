#! python3
# -*- coding: utf-8 -*-

from System.Collections.Generic import List

from extraction import get_filtered_elements
from forms import show_taskdialog
from misc import process_and_export_to_excel

uidoc = __revit__.ActiveUIDocument


def main():
    filtered_result = get_filtered_elements(uidoc)

    if not filtered_result.success:
        show_taskdialog(
            title="Erreur",
            main_instruction="Erreur lors de la récupération des éléments",
            main_content=filtered_result.error.message if hasattr(filtered_result, 'error') else "Erreur inconnue"
        )
        return

    process_and_export_to_excel(uidoc, filtered_result.data, show_results=True, create_view=True)


if __name__ == "__main__":
    main()
