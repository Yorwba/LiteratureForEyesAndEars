#!/usr/bin/env python3

import json
from librivox_json import get_books
import sys


if __name__ == '__main__':
    result = {'books': {}}
    for arg in sys.argv[1:]:
        for book in get_books(arg):
            result['books'][book['id']] = book

    json.dump(result, sys.stdout, sort_keys=True)
