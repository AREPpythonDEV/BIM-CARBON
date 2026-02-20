# -*- coding: utf-8 -*-
import datetime

from Autodesk.Revit.DB import (
    Transaction,
    TransactionGroup,
    FilteredElementCollector,
    FillPatternElement,
    OverrideGraphicSettings,
    Color,
    FamilyInstance,
    PhaseFilter, View3D, ElementTypeGroup, CategoryType, ElementId, BuiltInCategory
)
from Autodesk.Revit.UI import TaskDialog

uidoc = __revit__.ActiveUIDocument
doc = uidoc.Document

from import_utils import inject_carbon_results_by_type, sum_carbon_weight_by_type
from views import generate_dynamic_thresholds, create_3d_view, delete_existing_templates, create_carbon_template
from retrieval import elements_with_material_volume


def apply_colour_by_carbon_weight(doc, template=None, target_view=None):
    """
    Colore toute la maquette en gris, sauf les éléments dont le poids carbone
    a été calculé, qui reçoivent une couleur selon leur catégorie d'émission.
    """

    # Cherche le motif de remplissage solide
    solid = next(
        (
            p for p in FilteredElementCollector(doc)
        .OfClass(FillPatternElement)
        .ToElements()
            if p.GetFillPattern().IsSolidFill
        ),
        None
    )
    if not solid:
        TaskDialog.Show("Erreur", "Aucun motif de remplissage solide trouvé.")
        return

    filter_colors = {
        "Très émetteur": Color(197, 66, 58),
        "Émetteur modéré": Color(197, 128, 58),
        "Émission moyenne": Color(197, 193, 58),
        "Faible émission": Color(169, 197, 58),
        "Très faible émission": Color(80, 197, 58),
    }

   
    instances = (
        FilteredElementCollector(doc)
        .OfClass(FamilyInstance)
        .WhereElementIsNotElementType()
        .ToElements()
    )

    
    weight_by_type = sum_carbon_weight_by_type(instances)
    calcules = set(weight_by_type.keys())

    total_carbon = sum(w for (_, w) in weight_by_type.values())
    thresholds = generate_dynamic_thresholds(total_carbon)

    categories = [
        "Très émetteur",
        "Émetteur modéré",
        "Émission moyenne",
        "Faible émission",
        "Très faible émission"
    ]

 
    if template is not None:
        t_temp = Transaction(doc, "Coloration Template")
        t_temp.Start()
        for filt_id in template.GetFilters():
            name = doc.GetElement(filt_id).Name
            if name in filter_colors:
                ogs = OverrideGraphicSettings()
                ogs_gray.SetProjectionLineColor(Color(0, 0, 0))  # noir

                ogs.SetSurfaceForegroundPatternId(solid.Id)
                template.SetFilterOverrides(filt_id, ogs)
        t_temp.Commit()

   
   
    active_view = target_view or doc.ActiveView
    t_inst = Transaction(doc, "Coloration Instances Carbone")
    t_inst.Start()

    for inst in instances:
        if inst.GetTypeId() not in calcules:
            continue

        _, total_w = weight_by_type[inst.GetTypeId()]
        
        for idx, seuil in enumerate(thresholds):
            if total_w >= seuil:
                category = categories[idx]
                break
        else:
            category = categories[-1]

        couleur = filter_colors.get(category, Color(128, 128, 128))
        ogs = OverrideGraphicSettings()
        ogs.SetProjectionLineColor(couleur)
        ogs.SetSurfaceForegroundPatternColor(couleur)
        ogs.SetSurfaceForegroundPatternId(solid.Id)

        active_view.SetElementOverrides(inst.Id, ogs)


    t_inst.Commit()


def main():
    if not inject_carbon_results_by_type():
        TaskDialog.Show("Info", "Le script s'est arrêté avant le filtre.")
        return

    filter_phase_selected = "Afficher tout"
    tg = TransactionGroup(doc, "Importer valeurs et coloration carbone")
    phase_filters = FilteredElementCollector(doc).OfClass(PhaseFilter).ToElements()
    tg.Start()

    total_weight = sum(w for (_, w) in sum_carbon_weight_by_type(elements_with_material_volume).values())

    if total_weight == 0:
        TaskDialog.Show("Alerte", "Aucun poids carbone valide trouvé pour les éléments.")
        tg.RollBack()
        return
    default_3d_view = create_3d_view(doc)

    delete_existing_templates(doc, "CLC_CARBON_")
    template = create_carbon_template(doc, default_3d_view)

    hide_annotations_and_set_phase(doc, template, phase_filters, "Afficher tout")
    create_named_3d_view(doc, template, "Afficher tout")

    apply_colour_by_carbon_weight(doc)

    tg.Assimilate()


if __name__ == "__main__":
    main()


def create_named_3d_view(document, template, selected_phase):
    current_datetime = datetime.datetime.now().strftime("%y%m%d_%H.%M.%S")

    t = Transaction(document, "Duplicate and Activate 3D View")
    t.Start()
    new_view = View3D.CreatePerspective(document, document.GetDefaultElementTypeId(ElementTypeGroup.ViewType3D))
    new_view.Name = "CALCUL_CARBON_{}".format(current_datetime)
    new_view.ViewTemplateId = template.Id
    new_view.CropBoxActive = False
    new_view.CropBoxVisible = False
    t.Commit()

    uidoc.ActiveView = new_view


def hide_annotations_and_set_phase(document, template, phase_filters, selected_phase):
    t = Transaction(document, "Hide annotation")
    t.Start()
    for cat in document.Settings.Categories:
        if cat.CategoryType == CategoryType.Annotation or cat.Name == "Liens RVT":
            try:
                template.SetCategoryHidden(cat.Id, True)
            except:
                pass
    template.SetCategoryHidden(ElementId(BuiltInCategory.OST_Lines), True)
    for param in template.Parameters:
        if str(param.Definition.Name) == "Filtre des phases":
            for pf in phase_filters:
                if pf.Name == selected_phase:
                    param.Set(pf.Id)
    t.Commit()
