#!/usr/bin/env python3

import json
from librivox_json import get_books
import os.path
import sys


if __name__ == '__main__':
    for book in get_books(sys.argv[1]):
        if book['language'] == 'Multilingual':
            print(book['id'])
