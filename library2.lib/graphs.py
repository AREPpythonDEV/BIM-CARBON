#! python3
# -*- coding: utf-8 -*-

import datetime
import os

import plotly
import plotly.graph_objs as go
from plotly.subplots import make_subplots


def process_data(list_of_results, element_quantity_dict):
    total = 0
    sous_projet_totals = {}
    material_totals = {}
    material_par_sp = {}

    for result in list_of_results:
        total_value = float(result["Impact sur le changement climatique (kgCO2e)"])
        total += total_value

        mcrcom = result["Macro-composant de niveau 3"]
        prod = result["Produit"].replace(" - BIM & Carbone", "")
        impact = round(total_value, 3)

        if mcrcom not in sous_projet_totals:
            sous_projet_totals[mcrcom] = impact
        else:
            sous_projet_totals[mcrcom] += impact

        if prod not in material_totals:
            material_totals[prod] = impact
        else:
            material_totals[prod] += impact

        if mcrcom not in material_par_sp:
            material_par_sp[mcrcom] = {prod: impact}
        else:
            material_par_sp[mcrcom][prod] = impact

    moyen_poids_carbone_par_element = "{:,.0f}".format(total / len(element_quantity_dict))

    return total, sous_projet_totals, material_totals, material_par_sp, moyen_poids_carbone_par_element


material_colors = {}


def get_color(material):
    """Retourne une couleur unique parmi 7 couleurs fixes pour chaque matériau."""
    color_palette = [

        "rgb(37, 80, 90)",  # Sarcelle foncée (Dark Slate Gray)
        "rgb(91, 119, 109)",  # Gris ardoise (Slate Gray)
        "rgb(105, 57, 208)",  # Indigo électrique (Electric Indigo)
        "rgb(206, 48, 46)",  # Rouge brique (Brick Red)
        "rgb(34, 31, 32)",  # Noir charbon (Rich Black)
        "rgb(244, 241, 149)",  # Jaune pâle (Pale Yellow)
        "rgb(106, 77, 70)"  # Marron terre (Earth Brown)
    ]

    if material not in material_colors:
        index = len(material_colors) % len(color_palette)
        material_colors[material] = color_palette[index]

    return material_colors[material]


def create_pie_chart(labels, values, title):
    """Crée un camembert pour afficher la répartition des matériaux les plus carbonés."""

    colors = [get_color(label) for label in labels]

    fig = go.Figure(data=[
        go.Pie(labels=labels, values=values, hole=0.3, marker=dict(colors=colors))
    ])

    fig.update_layout(title_text=title)
    return fig


def create_stacked_bar_chart_for_subproject(data, title, x_label, legend_title):
    """
    Crée un graphique en barres empilées pour les sous-projets,
    triés par ordre décroissant selon la somme des valeurs (KgCO₂eq).
    """
    # Calculer la somme des valeurs pour chaque sous-projet
    totals = {sp: sum(materials.values()) for sp, materials in data.items()}
    # Trier les sous-projets par ordre décroissant
    sorted_subprojects = sorted(totals, key=lambda sp: totals[sp], reverse=True)

    fig = go.Figure()
    material_seen = set()

    # Itérer sur les sous-projets dans l'ordre trié
    for sp in sorted_subprojects:
        materials = data[sp]
        for material, value in materials.items():
            # Afficher la légende une seule fois par matériau
            show_legend = material not in material_seen
            fig.add_trace(go.Bar(
                x=[sp],
                y=[value],
                name=material,
                text=[material],
                textposition='auto',
                legendgroup=material,
                showlegend=show_legend,
                marker=dict(color=get_color(material))
            ))
            material_seen.add(material)

    fig.update_layout(
        barmode='stack',
        title=title,
        xaxis=dict(title=x_label, tickangle=-45),
        yaxis=dict(title="KgCO₂eq"),
        legend=dict(title=legend_title)
    )

    return fig


def format_number(value):
    if isinstance(value, float) and value % 1 != 0:
        return "{:,.3f}".format(value).replace(",", " ").replace(".", ",")
    else:
        return "{:,.0f}".format(value).replace(",", ".")


def plot_data(total, sous_projet_totals, material_totals, material_par_sp, category_quantity_dict, doc, path,
              moyen_poids_carbone_par_element, element_quantity_dict):
    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=(
            "Par lot",
            "Par classe de matériau",
            "Matériaux par lot",
            "Par catégorie Revit",
        ),
    )

    fig.add_trace(
        go.Bar(
            x=list([x.replace(" ", "<br>") for x in sous_projet_totals.keys()]),
            y=list(sous_projet_totals.values()),
            name="Par lot",
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Bar(
            x=list(material_totals.keys()),
            y=list(material_totals.values()),
            name="Par classe de matériau",
        ),
        row=1,
        col=2,
    )

    fig.add_trace(
        go.Bar(
            x=list([x.replace(" ", "<br>") for x in category_quantity_dict.keys()]),
            y=list(category_quantity_dict.values()),
            name="Par catégorie Revit",
        ),
        row=2,
        col=1,
    )

    for sp, material_data in material_par_sp.items():
        fig.add_trace(
            go.Bar(
                x=list(material_data.keys()),
                y=list(material_data.values()),
                name="{}".format(sp),
            ),
            row=2,
            col=2,
        )

    fig.update_yaxes(title_text="Impact climat[kgCO2e]", row=1, col=1)
    fig.update_yaxes(title_text="Impact climat[kgCO2e]", row=1, col=2)
    fig.update_yaxes(title_text="Impact climat[kgCO2e]", row=2, col=1)
    fig.update_yaxes(title_text="Impact climat[kgCO2e]", row=2, col=2)

    fig.update_xaxes(title_text="Par lot", row=1, col=1, title_font=dict(size=16))
    fig.update_xaxes(title_text="Par classe de matériau", row=1, col=2, title_font=dict(size=16))
    fig.update_xaxes(title_text="Par catégorie Revit", row=2, col=1, title_font=dict(size=16))
    fig.update_xaxes(title_text="Matériaux par lot", row=2, col=2, title_font=dict(size=16))

    title_text = "Projet: {}".format(doc.Title)

    sub_title_text = [
        "Résultats poids carbone(kgCO2e): {:,.3f}".format(total),
        "Nombre d'éléments calculés: {:,.0f}".format(len(element_quantity_dict)),
        "Moyen poids carbone par élément(kgCO2e): {}".format(moyen_poids_carbone_par_element)
    ]

    fig.update_layout(
        barmode="group",
        title=dict(
            x=0,
            y=1,
            text=title_text
        ),
        annotations=[
            dict(
                x=0.05,
                y=1.11,
                xref="paper",
                yref="paper",
                text=sub_title_text[0],
                showarrow=False,
                font=dict(size=14),
                xanchor='left',
                yanchor='top'
            ),
            dict(
                x=0.05,
                y=1.08,
                xref="paper",
                yref="paper",
                text=sub_title_text[1],
                showarrow=False,
                font=dict(size=14),
                xanchor='left',
                yanchor='top'
            ),
            dict(
                x=0.05,
                y=1.05,
                xref="paper",
                yref="paper",
                text=sub_title_text[2],
                showarrow=False,
                font=dict(size=14),
                xanchor='left',
                yanchor='top'
            )
        ])

    # Save the plot to an HTML file
    current_datetime = datetime.datetime.now().strftime("%y%m%d %Hh%M")
    html_file = "carbon_data {}.html".format(current_datetime)
    fichier = os.path.join(path, html_file)
    with open(fichier, "w", encoding="utf-8") as file:
        file.write(fig.to_html())
    return fichier
