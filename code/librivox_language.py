#!/usr/bin/env python3

import json
from librivox_json import get_books
import os.path
import sys


language_codes = {
    'Ancient Greek': 'grc',
    'Dutch': 'nld',
    'English': 'eng',
    'French': 'fra',
    'German': 'deu',
    'Italian': 'ita',
    'Japanese': 'jpn',
    'Latin': 'lat',
    'Polish': 'pol',
    'Portuguese': 'por-br',
    'Russian': 'rus',
    'Spanish': 'spa',
}


if __name__ == '__main__':
    for book in get_books(sys.argv[1]):
        lang = book['language']
        if lang in language_codes:
            lang = language_codes[lang]
        if lang == 'Multilingual' and 'sections' in book:
            for section in book['sections']:
                lang = section['language']
                if lang in language_codes:
                    lang = language_codes[lang]
                print(lang)
        else:
            print(lang)
