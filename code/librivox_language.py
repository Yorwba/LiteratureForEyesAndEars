#!/usr/bin/env python3

import json
import sys

language_codes = {
    'English': 'eng',
    'German': 'deu',
}

if __name__ == '__main__':
    with open(sys.argv[1]) as f: info = json.load(f)

    for book in info['books'].values():
        lang = book['language']
        if lang in language_codes:
            lang = language_codes[lang]
        print(lang)
