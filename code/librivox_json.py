#!/usr/bin/env python3

import json
import os.path


def get_books(path):
    info = get_info(path)
    books = info['books']
    if hasattr(books, 'values'):
        books = list(books.values())
    if not path.endswith('.json'):
        filename = path.split('/')[-1].split('.')[0]
        if filename:
            sections = [
                s
                for b in books
                for s in b.get('sections', [])
                if filename in (s['file_name'] or '')
            ]
            if sections:
                return sections
    return books


def get_info(path):
    if os.path.isfile(path):
        if path.endswith('.json'):
            with open(path) as f:
                return json.load(f)
        else:
            up = os.path.dirname(path)
            return get_info(up)
    if os.path.isdir(path):
        subpath = os.path.join(path, 'librivox.json')
        if os.path.isfile(subpath):
            return get_info(subpath)
        else:
            up = os.path.dirname(path)
            if up != path:
                return get_info(up)
