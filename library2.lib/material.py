# -*- coding: utf-8 -*-

class Material:
    # Constructeur qui initialise les matériaux
    def __init__(self):
        self.material_mapping = {
            "acier":                        ("nxHZ7zxGUghg5mXmYv6RS4", 7850),
            "acier_non_structurel":         ("LoNxZDMDkjP4sdurKhSJSS", 7250),
            "air":                          ("Rm63sm3zWPDJJGksn8XpvW", 0), # normalement 1 mais à ignorer
            "aluminium":                    ("a56Zz8CHRgcWEdyX8QRL95", 2710),
            "autres_materiaux":             ("HnLgsV5a42ztT6WysdAfx3", 0), # 2000 mais à ignorer contient les CCD, caoutchouc, lino et textils
            "autres_metaux":                ("AGUFGLX9zzHhVzgNEgpBmL", 7800),
            "beton":                        ("aJrbbWGEPxNgEbRSKt9YDR", 2407),
            "beton_bas_carbone":            ("7JzL8bFP4Zhd5VeavQMrhc", 2407),
            "beton_chanvre":                ("nprQd2QHRhEnDwbBNXjHx5", 600),
            "beton_leger_ciment":           ("ane2oeWrPb7Ddy5c4xvL28", 2000),
            "bitume":                       ("bfPE4g3Baj7hdFXYCNmmNo", 2350),
            "bois":                         ("Ac489R6BYsxswScw5ptVUM", 500),
            "brique_creuse":                ("gAY3bMH7LEJbDyKx9EEf5Q", 900),
            "brique_perforee":              ("c2Cd58ineh7gcDEpQQLrkR", 1350),
            "brique_pleine_ceramique":      ("7x8UKeQGHe44Qa3PcDhTeN", 1900),
            "granulats":                    ("nKSeQWifkRsr8CxD9qvXLU", 1840),
            "isolants_biosources":          ("6ruaanXvQeA949PNX3tLeE", 100),
            "laines_minerales":             ("mdnyL8jE8jrCtRqzjBfYqU", 200),
            "peinture":                     ("RL7WZdiQSskMQSbAH56q59", 1200),
            "pierre":                       ("4AserSz3kJ4KsCrrqdZ2aD", 2700),
            "plastiques":                   ("AfRMYn8YmmezhNeEkqa5b4", 1400),
            "platre":                       ("eKTdoAMBud4QkJURvh5MKK", 1120),
            "terre":                        ("QU3AAosYiLqtJGHzx66DFa", 1400),
            "terre_crue":                   ("kcyJ5RLENKL7oJ5BTtkgjk", 2000),
            "vegetal":                      ("SAwRC8KCaQMrTkLiUNBqBP", 150),
            "verre":                        ("a7Q7YHJeDQcPyCvYKpqMZW", 2180)
        }

        self.known_materials = {
            "acier": ["acier", "steel"],
            "acier_non_structurel": ["acier_non_structurel", "non_structural_steel", "Métal"],
            "air": ["air", "gaz", "gas"],
            "aluminium": ["aluminium", "aluminum"],
            "autres_materiaux": ["autres_materiaux", "ccd", "caoutchouc", "lino", "textile", "divers"],
            "autres_metaux": ["autres_metaux", "autres_métaux", "other_metals"],
            "beton": ["beton", "béton", "concreto", "concrete", "hormigón"],
            "beton_bas_carbone": ["beton_bas_carbone"],
            "beton_chanvre_cellulaire": ["beton_chanvre_cellulaire"],
            "beton_leger_ciment": ["beton_leger_ciment"],
            "bitume": ["bitume", "bitumeux", "bituminous"],
            "bois": ["bois", "madera", "wood"],
            "brique_creuse": ["brique_creuse", "brique alvéolée", "hollow_brick"],
            "brique_perforee": ["brique_perforee", "brique perforée", "perforated_brick"],
            "brique_pleine_ceramique": [
                "brique_pleine_ceramique",
                "céramique",
                "ceramic",
                "cerámica",
                "ceràmica",
                "maconnerie",
                "maçonnerie",
                "masonry"
            ],
            "isolants_biosources": ["isolants_biosources", "isolation_bio", "bio_insulation"],
            "laines_minerales": ["laines_minerales", "laine_minerale", "mineral_wool"],
            "peinture": ["peinture", "peinture/revêtement", "paint/coating", "peindre"],
            "pierre": ["pierre", "stone", "roche", "rock"],
            "plastiques": ["plastiques", "plastique", "plastic", "plástico", "plstico"],
            "platre": ["platre", "plâtre", "gypsum"],
            "sable_granulats_roches": [
                "sable_granulats_roches",
                "granulat",
                "gravel",
                "aggregate",
                "sable",
                "sand"
            ],
            "terre": ["terre", "soil", "terreno"],
            "terre_crue": ["terre_crue", "raw_earth", "earth"],
            "vegetal": ["vegetal", "vegetaux", "vegetation", "plant"],
            "verre": ["verre", "glass", "cristal", "vidrio"]
        }

        self.unknown_materials = [
            "Pas d'attribution",
            "Lot 11",
            "Lot 09",
            "Lot 07",
            "Lot 04",
            "Générique",
            "Divers",
            "Textile",
            "System",
            "Système",
            "Generic",
            "Miscellaneous",
            "Non attribuée",
            "Unassigned",
            "Genérico",
            "Sin asignar",
            "Sistema",
            "Varios"
        ]

    def get_material_info(self, material_name):
        """Get material info from material mapping"""
        return self.material_mapping.get(material_name, "Matériau non trouvé")

    def is_known_material(self, material_name):
        """Check if a material name exists in any of the known materials lists"""
        return any(material_name.lower() in [m.lower() for m in materials]
                  for materials in self.known_materials.values())

    def filter_by_category(self, category):
        return self.known_materials.get(category, "Catégorie non trouvée")

    def is_unknown_material(self, material_name):
        """Check if a material is unknown"""
        return material_name in self.unknown_materials

    def display_all_materials(self, all_materials=True, category=None):
        """Display all materials or materials from a specific category"""
        if all_materials:
            for material, details in self.material_mapping.items():
                print("Matériau: {}, Code produit: {}, Densité: {} kg/m3".format(material, details[0], details[1]))
        elif category:
            for material, details in self.filter_by_category(category):
                print("Matériau: {}, Code produit: {}, Densité: {} kg/m3".format(material, details[0], details[1]))
        else:
            print("Veuillez spécifier une catégorie de matériau à afficher")


materiaux = Material()
material_mapping = materiaux.material_mapping
known_materials = materiaux.known_materials
unknown_materials = materiaux.unknown_materials
