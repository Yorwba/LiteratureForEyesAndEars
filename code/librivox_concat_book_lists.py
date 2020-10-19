#!/usr/bin/env python3

import json
import sys

if __name__ == '__main__':
    result = {'books': {}}
    for arg in sys.argv[1:]:
        with open(arg) as f: info = json.load(f)
        books = info['books']
        if hasattr(books, 'values'):
            books = books.values()
        for book in books:
            result['books'][book['id']] = book

    json.dump(result, sys.stdout, sort_keys=True)
