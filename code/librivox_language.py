#!/usr/bin/env python3

import json
from librivox_json import get_books
import os.path
import sys


language_codes = {
    'English': 'eng',
    'German': 'deu',
    'Spanish': 'spa',
    'French': 'fra',
    'Dutch': 'nld',
    'Portuguese': 'por-br',
    'Italian': 'ita',
    'Russian': 'rus',
}


if __name__ == '__main__':
    for book in get_books(sys.argv[1]):
        lang = book['language']
        if lang in language_codes:
            lang = language_codes[lang]
        print(lang)
