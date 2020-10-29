#!/usr/bin/env python3

import json
import os.path


def get_books(path):
    info = get_info(path)
    books = info['books']
    if hasattr(books, 'values'):
        books = list(books.values())
    return books


def get_info(path):
    if os.path.isfile(path):
        with open(path) as f:
            return json.load(f)
    if os.path.isdir(path):
        subpath = os.path.join(path, 'librivox.json')
        if os.path.isfile(subpath):
            return get_info(subpath)
        else:
            up = os.path.dirname(path)
            if up != path:
                return get_info(up)
