#!/usr/bin/env python3

import json
import os.path
import sys


language_codes = {
    'English': 'eng',
    'German': 'deu',
    'Spanish': 'spa',
}


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


if __name__ == '__main__':
    info = get_info(sys.argv[1])

    for book in info['books'].values():
        lang = book['language']
        if lang in language_codes:
            lang = language_codes[lang]
        print(lang)
