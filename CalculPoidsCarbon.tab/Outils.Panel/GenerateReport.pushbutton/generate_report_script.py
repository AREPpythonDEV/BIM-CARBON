#! python3
# -*- coding: utf-8 -*-
import datetime
import os

from Autodesk.Revit.DB import FilteredElementCollector, BuiltInParameter
import Autodesk.Revit.UI as UI

from debug import debug_print
from forms import show_taskdialog
from graphs import create_stacked_bar_chart_for_subproject, format_number, create_pie_chart
from paths import D_MODEL_DIRECTORY_PATH
from retrieval import extracted_data, impact_data
from views import generate_dynamic_thresholds, filter_names_and_colors

# Import du template HTML
from html_template import (
    get_css_content,
    generate_html_header,
    generate_page_header,
    generate_stats_cards,
    generate_intro_section,
    generate_table_section,
    generate_chart_section,
    generate_scroll_buttons_and_scripts
)

uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document
doc_title = doc.Title


def calculate_total_weight_and_average(category_element_carbon):
    """Retourne le poids total, le nombre d'éléments et la moyenne par élément."""
    weights = []
    for elements in category_element_carbon.values():
        for weight in elements.values():
            weights.append(weight)

    total_weight = sum(weights)
    total_elements = len(weights)
    average_weight = total_weight / total_elements if total_elements > 0 else 0

    return total_weight, total_elements, average_weight


def get_top_10_material(impact_data):
    """Récupère les 10 matériaux les plus carbonés."""
    material_weight_dict = {}
    tableau = []

    for _, materials in impact_data.items():
        for material, weight in materials.items():
            if material in material_weight_dict:
                material_weight_dict[material] += weight
            else:
                material_weight_dict[material] = weight

    total_weight = sum(material_weight_dict.values())

    if total_weight == 0:
        return []

    for material, weight in material_weight_dict.items():
        pourcentage = (weight / total_weight) * 100
        tableau.append((material, pourcentage, weight))
    top_10_material = sorted(tableau, key=lambda x: x[2], reverse=True)[:10]

    return top_10_material


def get_top_10_elements(category_element_carbon):
    """Récupère les 10 éléments les plus carbonés en ignorant les catégories."""
    element_list = []
    total_weight_global = sum(
        weight for elements in category_element_carbon.values() for weight in elements.values()
    )

    if total_weight_global == 0:
        return []

    for category, elements in category_element_carbon.items():
        for element, weight in elements.items():
            pourcentage = (weight / total_weight_global) * 100
            element_list.append((category, element, pourcentage, weight))

    top_10_elements = sorted(element_list, key=lambda x: x[3], reverse=True)[:10]
    return top_10_elements


def get_top_10_categories(impact_data):
    """Récupère les 10 catégories les plus carbonées."""
    categorie_list = {}
    total_weight_global = sum(
        weight for elements in impact_data.values() for weight in elements.values()
    )

    if total_weight_global == 0:
        return []

    for category, elements in impact_data.items():
        categorie_list[category] = sum(elements.values())

    pourcentage_list = [
        (category, (weight / total_weight_global) * 100, weight) for category, weight in categorie_list.items()
    ]

    top_10_categorie = sorted(pourcentage_list, key=lambda x: x[2], reverse=True)
    debug_print("get_top_10_categories")
    for i in top_10_categorie:
        debug_print(i)
    return top_10_categorie


def get_element_name(element):
    """Récupère un nom d'élément de manière sécurisée."""
    try:
        if hasattr(element, "Name") and isinstance(element.Name, str):
            return element.Name
        name_param = element.LookupParameter(element.Name)
        if name_param and name_param.HasValue:
            return name_param.AsString()
        mark_param = element.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)
        if mark_param and mark_param.HasValue:
            return mark_param.AsString()
    except Exception as e:
        debug_print(f"Erreur lors de la récupération du nom de l'élément {element.Id}: {e}")

    return "Nom inconnu"


def collect_carbon_data(doc):
    """Récupère les données carbone par catégorie, famille et élément."""
    collector = FilteredElementCollector(doc).WhereElementIsNotElementType()

    category_element_carbon = {}

    for element in collector:
        param = element.LookupParameter("_POIDS_CARBONE")
        category = element.Category.Name if element.Category else "Non classé"

        element_name = get_element_name(element)

        if param and param.HasValue:
            try:
                poids_carbone = param.AsDouble()

                category_element_carbon.setdefault(category, {}).setdefault(element_name, 0)
                category_element_carbon[category][element_name] += poids_carbone


            except Exception as e:
                print(f"Erreur lors de la récupération de `_POIDS_CARBONE` pour {element_name}: {e}")

    return category_element_carbon


def rgb_to_hex(color):
    return "#{:02x}{:02x}{:02x}".format(color.Red, color.Green, color.Blue)


def print_project_percentages(total_weight):
    thresholds = generate_dynamic_thresholds(total_weight)

    table_html = "<table border='3' style='border-collapse: collapse;'>"
    table_html += "<thead><tr><th>Filtre</th><th>Valeur Minimum</th><th>Couleur</th></tr></thead><tbody>"

    for (filter_name, filter_color), treshold in zip(filter_names_and_colors.items(), thresholds):
        hex_color = rgb_to_hex(filter_color)
        table_html += (
            f"<tr>"
            f"<td>{filter_name}</td>"
            f"<td>{treshold}</td>"
            f"<td style='background-color: {hex_color}; width: 100px;'>&nbsp;</td>"
            f"</tr>"
        )

    table_html += "</tbody></table>"
    return table_html


def save_to_html(category_element_carbon, model_name):
    """Sauvegarde les histogrammes empilés et les données dans un fichier HTML standalone."""

    # Calcul des totaux et des moyennes
    total_weight, total_elements, moyen_poids_carbone_par_element = calculate_total_weight_and_average(
        category_element_carbon)
    top_10_elements = get_top_10_elements(category_element_carbon)
    top_10_class_material = get_top_10_material(impact_data)
    top_10_categorie = get_top_10_categories(impact_data)
    valeur = print_project_percentages(total_weight)

    # Graphiques
    subproject_material_class_chart = create_stacked_bar_chart_for_subproject(
        extracted_data,
        "Empreinte Carbone par Lots et par Classes de Matériau",
        "Lots",
        "Classe de Matériau"
    )
    material_labels = [material for material, _, _ in top_10_class_material]
    material_values = [weight for _, _, weight in top_10_class_material]
    material_pie_chart = create_pie_chart(
        material_labels,
        material_values,
        "Répartition des Classes de Matériaux les plus Carbonés"
    )

    # Chemin de sauvegarde
    current_datetime = datetime.datetime.now().strftime("%y%m%d_%Hh%M")
    html_file = f"carbon_report_{current_datetime}.html"
    file_path = os.path.join(D_MODEL_DIRECTORY_PATH, html_file)

    # Chemin du fichier CSS (dans le même dossier que le script)
    css_file_path = os.path.join(os.path.dirname(__file__), "arep_carbon_report.css")

    # Lire le contenu du CSS
    css_content = get_css_content(css_file_path)

    # Écriture du fichier HTML standalone
    with open(file_path, "w", encoding="utf-8") as file:
        # 1. Header HTML avec CSS injecté
        file.write(generate_html_header(css_content, f"Rapport Carbone - {model_name}"))

        # 2. Header visuel de la page
        file.write(generate_page_header(model_name))

        # 3. Stats cards
        file.write(generate_stats_cards(total_weight, total_elements, format_number))

        # 4. Introduction
        file.write(generate_intro_section())

        # 5. Tableau répartition par lot
        file.write(generate_table_section(
            "Répartition du Poids Carbone par Lot",
            ["Lots", "Pourcentage", "Poids Carbone (kgCO₂e)"],
            top_10_categorie,
            format_number
        ))

        # 6. Tableau répartition par matériau
        file.write(generate_table_section(
            "Répartition du Poids Carbone par Classe des Matériaux",
            ["Classe de Matériau", "Pourcentage", "Poids Carbone (kgCO₂e)"],
            top_10_class_material,
            format_number
        ))

        # 7. Tableau éléments impactants
        elements_data = [(element, category, pourcentage, weight)
                         for category, element, pourcentage, weight in top_10_elements]
        file.write(generate_table_section(
            "Éléments les plus impactants en termes d'émissions de GES",
            ["Élément", "Catégorie", "Pourcentage", "Poids Carbone (kgCO₂e)"],
            elements_data,
            format_number
        ))

        # 8. Tableau seuils de filtre
        file.write("        <div class='section'>\n")
        file.write("            <h3 class='section-title'>Valeurs des seuils de filtre par couleur</h3>\n")
        file.write("            <div class='table-container color-table'>\n")
        file.write(valeur)
        file.write("            </div>\n")
        file.write("        </div>\n")

        # 9. Graphique barres empilées
        chart_html = subproject_material_class_chart.to_html(full_html=False, include_plotlyjs='cdn')
        file.write(generate_chart_section(
            "Graphique Empreinte Carbone par Lots et Classes",
            chart_html,
            large=False
        ))

        # 10. Graphique camembert (plus grand)
        pie_chart_html = material_pie_chart.to_html(full_html=False, include_plotlyjs='cdn')
        file.write(generate_chart_section(
            "Graphique des Matériaux les plus Carbonés",
            pie_chart_html,
            large=True  # Camembert plus grand
        ))

        # 11. Boutons de scroll et scripts
        file.write(generate_scroll_buttons_and_scripts())

    return file_path


def main():
    """Exécution du script principal."""
    category_element_carbon = collect_carbon_data(doc)

    html_file = save_to_html(category_element_carbon, doc_title)
    res = show_taskdialog("Rapport Carbone",
                          "Le rapport HTML a été généré avec succès.",
                          "Souhaitez-vous ouvrir le fichier maintenant ?",
                          buttons=['Yes', 'No'])
    if res == UI.TaskDialogResult.Yes:
        os.startfile(html_file)


if __name__ == "__main__":
    main()
