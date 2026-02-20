# -*- coding: utf-8 -*-

"""The format needed for a test project with a mur en béton and sol en acier with v3 of the calculette carbon """
components = [
        {
            "component_id": "0",
            "component_name": "doc_title",
            "parent_id": None,
        },
        {
            "component_id": "1",
            "component_name": "phase_nom",
            "parent_id": "0",
        },
        {
            "component_id": "2",
            "component_name": "sous_projet",
            "parent_id": "1",
        },
        {
            "component_id": "3",
            "component_name": "sous_projet",
            "parent_id": "1",
        },
        {
            "component_id": "4",
            "component_name": "categorie",
            "parent_id": "2",
        },
        {
            "component_id": "5",
            "component_name": "categorie",
            "parent_id": "3",
        },
        {
            "component_id": "6",
            "component_name": "element_type",
            "parent_id": "4",
        },
        {
            "component_id": "7",
            "component_name": "element_type",
            "parent_id": "5",
        },
        {
            "component_id": "8",
            "component_name": "béton",
            "parent_id": "6",
            "product_id": "SWFG9KwfPWio8bTjMcmqYC",
            "properties": {
                        "unit": "m3",
                        "quantity": 181.45,
            }
        },
        {
            "component_id": "9",
            "component_name": "acier",
            "parent_id": "7",
            "product_id": "TJWNg5cipJo5hXiX7dc5hy",
            "properties": {
                        "unit": "m3",
                        "quantity": 181.45,
            }
        }
    ]
