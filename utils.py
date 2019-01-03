#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import os

# Defining the abs path of this file, so calls can refer to relative paths (might worth rethink as this is not the best approach)
script_dir = os.path.dirname(__file__)  # <-- absolute dir the script is in


def json_save(x, filepath):
    """
    saves an object into a json file
    :param x: the object to save
    :param filepath: the relative filepath to save the json file to (relative from this module)
    :return: does not return anything
    """
    with open(os.path.join(script_dir, filepath), 'w') as outfile:
        json.dump(x, outfile, sort_keys=True, indent=4, separators=(',', ': '))


def json_load(filepath):
    """
    loads a json file from the relative path given
    :param filepath: the file path to load the json file from (relative path to this module file)
    :return: the loaded json data structure
    """
    with open(os.path.join(script_dir, filepath), 'r') as infile:
        return_dict = json.load(infile)
    return return_dict