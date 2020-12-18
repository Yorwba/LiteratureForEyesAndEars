#!/usr/bin/env python3

import json
from librivox_json import get_books
import os.path
import sys


language_codes = {
    'Ancient Greek': 'grc',
    'Cantonese Chinese': 'yue',
    'Chinese': 'cmn', # assume Mandarin
    'Danish': 'dan',
    'Dutch': 'nld',
    'English': 'eng',
    'Finnish': 'fin',
    'French': 'fra',
    'German': 'deu',
    'Greek': 'ell',
    'Hebrew': 'heb',
    'Hungarian': 'hun',
    'Italian': 'ita',
    'Japanese': 'jpn',
    'Latin': 'lat',
    'Polish': 'pol',
    'Portuguese': 'por-br',
    'Romanian': 'ron',
    'Russian': 'rus',
    'Spanish': 'spa',
    'Swedish': 'swe',
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
