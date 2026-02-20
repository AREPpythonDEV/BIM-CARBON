# -*- coding: utf-8 -*-
"""
IronPython library for extracting data from a compressed dictionary.
This function was removed from extraction.py because of the use of python 3.
"""

import copy
from collections import OrderedDict


def create_element_id_dict(compressed_dico):
    element_quantity_dict = {}
    category_quantity_dict = {}
    for item in compressed_dico:
        elements = item["elements"]
        individual_quantities = item["individual_quantities"]
        categories = item["category"]
        for element_id, quantity, category in zip(elements, individual_quantities, categories):
            element_id = str(element_id)

            if element_id in element_quantity_dict:
                element_quantity_dict[element_id] += quantity
            else:
                element_quantity_dict[element_id] = quantity
            if category in category_quantity_dict:
                category_quantity_dict[category] += quantity
            else:
                category_quantity_dict[category] = quantity
    element_quantity_dict = OrderedDict(sorted(element_quantity_dict.items()))
    element_quantity_dict_copy = copy.copy(element_quantity_dict)
    # TODO : vérifier si on enlève les éléments avec quantité < 1
    # for key, value in element_quantity_dict_copy.items():
    #     if value < 1:
    #         lst.append({value: key})
    #         del element_quantity_dict[key]

    return element_quantity_dict_copy, category_quantity_dict
