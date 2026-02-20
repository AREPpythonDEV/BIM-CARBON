from Autodesk.Revit.DB import HostObjAttributes, Solid, Options
from misc import convert_to_cubic_meters

def get_compound_structure_data(element, document, sous_projet, all_subcategories, filtered_ws_mapping,known_materials,material_mapping):
    """Retourne une liste de dicos contenant les infos pour chaque couche d’un élément multicouche"""
    result = []
    try:
        if not isinstance(element, HostObjAttributes):
            return result

        structure = element.GetCompoundStructure()
        if not structure:
            return result

        # Calcul de la surface totale approximative
        options = Options()
        geom_elem = element.get_Geometry(options)
        surface_area = 0.0
        for geom in geom_elem:
            if isinstance(geom, Solid) and geom.Faces.Size > 0:
                for face in geom.Faces:
                    surface_area += face.Area
                break

        for layer in structure.GetLayers():
            mat_id = layer.MaterialId
            revit_mat = document.GetElement(mat_id)
            if revit_mat is None:
                continue

            material_name = revit_mat.Name
            material_class = revit_mat.MaterialClass

            if material_name.upper().startswith("ESPACE"):
                continue

            thickness = layer.Width
            volume_m3 = convert_to_cubic_meters(thickness * surface_area)

            known_class = None
            for kmc, possibles in known_materials.items():
                if material_class and material_class.lower() in possibles:
                    known_class = kmc
                    break
            if known_class is None:
                continue

            component_id, density = material_mapping[known_class]
            quantity = round(volume_m3 * density, 3)

            if sous_projet in filtered_ws_mapping:
                result.append({
                    "sous-projet": filtered_ws_mapping[sous_projet],
                    "lot": "N/A",
                    "volume": round(volume_m3, 3),
                    "unit": "kg",
                    "component_id": str(component_id),
                    "material": known_class,
                    "element_id": str(element.Id.IntegerValue),
                    "category": element.Category.Name,
                    "quantity": quantity,
                    "sub_category": element.LookupParameter("Subcategory").AsValueString() if element.LookupParameter("Subcategory") else None,
                    "sub_categories_available": all_subcategories.get(element.Category.Name, [])
                })
    except Exception as e:
        print(f"Erreur dans get_compound_structure_data pour élément {element.Id}: {e}")

    return result
