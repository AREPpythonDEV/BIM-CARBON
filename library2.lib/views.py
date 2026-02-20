# -*- coding: utf-8 -*-

from System.Collections.Generic import List as List
from collections import OrderedDict
from System import Int64
from datetime import datetime

from Autodesk.Revit.UI import TaskDialog
from Autodesk.Revit.DB import Color, Transaction, FilteredElementCollector, ParameterFilterElement, \
    ElementParameterFilter, ParameterFilterRuleFactory, OverrideGraphicSettings, ElementId, LogicalOrFilter, \
    InstanceBinding, TypeBinding, ElementTypeGroup, View3D, FilterRule, StorageType, FillPatternElement, CategoryType, \
    BuiltInCategory, PhaseFilter, FilterElement

from debug import debug_print
from forms import show_taskdialog
from retrieval import POIDS_CARBON_PARAMETER_ID

filter_names_and_colors = OrderedDict([
    ("C_05_Très émetteur", Color(197, 66, 58)),
    ("C_04_Émetteur modéré", Color(197, 128, 58)),
    ("C_03_Émission moyenne", Color(197, 193, 58)),
    ("C_02_Faible émission", Color(169, 197, 58)),
    ("C_01_Très faible émission", Color(80, 197, 58)),
    ("C_00_Non calculé", Color(220, 220, 220))
])


def calculate_total_carbon_weight(elements):
    total_weight = 0.0
    for el in elements:
        carbon_parameter = el.LookupParameter("_POIDS_CARBONE")
        if carbon_parameter and carbon_parameter.HasValue and carbon_parameter.StorageType == StorageType.Double:
            total_weight += carbon_parameter.AsDouble()
    return total_weight


def generate_dynamic_thresholds(total_weight):
    percentages = [0.01, 0.003, 0.0015, 0.0001, 0.0, 0.0]
    valeur = [(round(total_weight * p, 2)) for p in percentages]
    return valeur


def delete_view_filter(document, filter_id):
    t = Transaction(document, "Delete Filters")
    t.Start()
    document.Delete(filter_id)
    t.Commit()


def create_view_filters(document, target_view, category_ilist, total_weight):
    existing_filters = FilteredElementCollector(document).OfClass(ParameterFilterElement).ToElements()
    for existing_filter in existing_filters:
        if existing_filter.Name in filter_names_and_colors:
            delete_view_filter(document, existing_filter.Id)


    if POIDS_CARBON_PARAMETER_ID is None:
        show_taskdialog("Erreur",
                        "Paramètre '_POIDS_CARBONE' introuvable.",
                        icon='Warning')
        return

    thresholds = generate_dynamic_thresholds(total_weight)

    t = Transaction(document, "Create Filters")
    t.Start()
    for i, (filter_name, filter_color) in enumerate(filter_names_and_colors.items()):
        min_val = thresholds[i]
        max_val = thresholds[i - 1]
        if max_val == 0.0:
            max_val = None
        rules = List[FilterRule]()

        if max_val is not None:
            rule_max = ParameterFilterRuleFactory.CreateLessOrEqualRule(POIDS_CARBON_PARAMETER_ID, max_val, False)  # no need for bool, bool are for case sensitive strings
            rules.Add(rule_max)

        if "00" in filter_name:
            has_no_value_rule = ElementParameterFilter(
                ParameterFilterRuleFactory.CreateHasNoValueParameterRule(POIDS_CARBON_PARAMETER_ID))
            equal_to_zero_rule = ElementParameterFilter(
                ParameterFilterRuleFactory.CreateEqualsRule(POIDS_CARBON_PARAMETER_ID, 0.0, False))
            poids_carbon_compatible_categories_ilist = get_poids_carbon_compatible_categories(document)
            no_carbon_or_filter = LogicalOrFilter(has_no_value_rule, equal_to_zero_rule)
            view_filter = ParameterFilterElement.Create(document, filter_name, poids_carbon_compatible_categories_ilist, no_carbon_or_filter)

        else:
            rule_min = ParameterFilterRuleFactory.CreateGreaterRule(POIDS_CARBON_PARAMETER_ID, min_val, False)
            rules.Add(rule_min)
            combined_filters_ilist = ElementParameterFilter(rules)
            view_filter = ParameterFilterElement.Create(document, filter_name, category_ilist, combined_filters_ilist)

        if target_view:

            ogs = OverrideGraphicSettings()
            if filter_name in filter_names_and_colors:
                ogs.SetProjectionLineColor(filter_color)

            if not target_view.GetFilters().Contains(view_filter.Id):
                target_view.AddFilter(view_filter.Id)
            target_view.SetFilterOverrides(view_filter.Id, ogs)
            target_view.SetFilterVisibility(view_filter.Id, True)

    t.Commit()


def get_poids_carbon_compatible_categories(document):
    param_name = "_POIDS_CARBONE"
    param_categories = []
    bindings = document.ParameterBindings
    iterator = bindings.ForwardIterator()
    iterator.Reset()

    while iterator.MoveNext():
        definition = iterator.Key
        binding = iterator.Current

        if definition.Name == param_name:
            if isinstance(binding, InstanceBinding) or isinstance(binding, TypeBinding):  # Handle both InstanceBinding and TypeBinding
                categories = binding.Categories
                for cat in categories:
                    if cat.Id != ElementId(Int64(-2000011)) and cat.Id != ElementId(Int64(-2000035)):
                        param_categories.append(cat.Id)
    all_categories_for_poids_carbone_ilist = List[ElementId](param_categories)

    return all_categories_for_poids_carbone_ilist


def three_d_and_isolate(ui_document, ilist_elements_to_isolate):
    """Create a 3D view and isolate specified elements."""
    document = ui_document.Document
    typeid_3d = document.GetDefaultElementTypeId(ElementTypeGroup.ViewType3D)

    t = Transaction(document, '3D - Eléments sans matériaux')
    t.Start()
    new_3d_view = View3D.CreateIsometric(document, typeid_3d)
    current_datetime = datetime.now().strftime("%y%m%d_%Hh%M.%S")
    new_3d_view.Name = "CALCUL_CARBON_Eléments sans matériaux {}".format(current_datetime)
    new_3d_view.IsolateElementsTemporary(ilist_elements_to_isolate)
    new_3d_view.ConvertTemporaryHideIsolateToPermanent()
    t.Commit()
    ui_document.ActiveView = new_3d_view
    ui_document.RefreshActiveView()


def create_3d_view(document):
    view_type_id = document.GetDefaultElementTypeId(ElementTypeGroup.ViewType3D)
    t = Transaction(document, "Create view")
    t.Start()
    view = View3D.CreateIsometric(document, view_type_id)
    t.Commit()
    return view


def delete_existing_templates(document, keyword):
    templates = FilteredElementCollector(document).OfClass(View3D).WhereElementIsNotElementType().ToElements()
    t = Transaction(document, "Delete VT")
    t.Start()
    for template in templates:
        if keyword in template.Name:
            document.Delete(template.Id)
    t.Commit()


def apply_color_filters_in_template(document, template):
    all_patterns = FilteredElementCollector(document).OfClass(FillPatternElement).ToElements()
    solid_pattern = [i for i in all_patterns if i.GetFillPattern().IsSolidFill][0]

    for filt_id in template.GetFilters():
        name = document.GetElement(filt_id).Name
        if name in filter_names_and_colors:
            ogs = OverrideGraphicSettings()
            ogs.SetSurfaceForegroundPatternId(solid_pattern.Id)
            if "00" not in name:
                ogs.SetSurfaceForegroundPatternColor(filter_names_and_colors[name])
            else:
                ogs.SetProjectionLineColor(filter_names_and_colors[name])
                ogs.SetSurfaceForegroundPatternColor(Color(255, 255, 255))
            t = Transaction(document, "Apply Color Filter")
            t.Start()
            template.SetFilterOverrides(filt_id, ogs)
            t.Commit()


def hide_annotations_and_lines_in_template(document, template):
    t = Transaction(document, "Hide annotations and lines")
    t.Start()
    for cat in document.Settings.Categories:
        if cat.CategoryType == CategoryType.Annotation:
            try:
                template.SetCategoryHidden(cat.Id, True)
            except:
                pass
    for ost in [BuiltInCategory.OST_Lines, BuiltInCategory.OST_RvtLinks]:
        try:
            template.SetCategoryHidden(ElementId(ost), True)
        except:
            pass
    t.Commit()


def set_filter_phase_in_template(template, phase_filters, selected_filter_phase):
    t = Transaction(template.Document, "Set Phase in Template")
    t.Start()
    for param in template.Parameters:
        if str(param.Definition.Name) == "Filtre des phases":
            for pf in phase_filters:
                if pf.Name == selected_filter_phase:
                    param.Set(pf.Id)
    t.Commit()


def set_view_name_and_template(document, carbon_view, template):
    current_datetime = datetime.now().strftime("%y%m%d_%H.%M.%S")

    t = Transaction(document, 'set name')
    t.Start()
    carbon_view.Name = "CALCUL_CARBON_{}".format(current_datetime)
    carbon_view.ViewTemplateId = template.Id
    carbon_view.CropBoxActive = False
    carbon_view.CropBoxVisible = False
    t.Commit()


def create_carbon_template(document, base_view):
    filter_phase_name = "Afficher tout"
    name = "CLC_CARBON_{}".format(filter_phase_name.upper())
    phase_filters = FilteredElementCollector(document).OfClass(PhaseFilter).ToElements()

    t = Transaction(document, "Create view template")
    t.Start()
    template_id = base_view.CreateViewTemplate().Id
    template = document.GetElement(template_id)
    template.Name = name
    carbon_filter_ids = []
    for f in FilteredElementCollector(document).OfClass(FilterElement):
        if "CARBON" in f.Name:
            carbon_filter_ids.append(f.Id)
    for fid in carbon_filter_ids:
        template.AddFilter(fid)
        template.SetIsFilterEnabled(fid, True)
    t.Commit()

    apply_color_filters_in_template(document, template)
    hide_annotations_and_lines_in_template(document, template)
    set_filter_phase_in_template(template, phase_filters, filter_phase_name)

    return template
