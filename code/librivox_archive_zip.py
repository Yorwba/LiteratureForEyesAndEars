#!/usr/bin/env python3

import json
from librivox_json import get_books
import sys

if __name__ == '__main__':
    for book in get_books(sys.argv[1]):
        print(book['url_zip_file'])
