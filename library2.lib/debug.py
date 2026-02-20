# -*- coding: utf-8 -*-

from pyrevit import EXEC_PARAMS
from datetime import datetime

def debug_print(*args):
    if EXEC_PARAMS.debug_mode:
        print('-' * 80)
        if len(args) == 1 :
            print("[{}]:{}".format(datetime.now().strftime('%Y-%m-%d) %H:%M:%S.%f')[:-3], args[0]))
        else:
            print("[{}]:".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]))
            for arg in args:
                print(arg)


def pretty_format(data, indent=0, separator=False, output=None, init=True):
    """
    A function that arrange a dictionary or a list in a pretty way.

    Examples:
        pretty({'a': ['x', 'y'], 'b': 2})
    Returns:
        a:
            0 : x
            1 : y
        b:
            2
    """
    if isinstance(data, dict):
        items = data.items()
    elif isinstance(data, list):
        items = enumerate(data)
    else:
        return data
    if init:
        output  = []
    for key, value in items:
        new_key = str(key) + ": "
        if isinstance(value, (dict, list)):
            output.append('\t' * indent + new_key)
            pretty_format(value, indent + 1, False, output, False)
            if separator:
                output.append('--------')
        else:
            output.append('\t' * indent + new_key + str(value))

    multiline_output = '\n'.join(output)
    return multiline_output