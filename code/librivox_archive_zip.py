#!/usr/bin/env python3

import json
import sys

if __name__ == '__main__':
    with open(sys.argv[1]) as f: info = json.load(f)

    for book in info['books'].values():
        print(book['url_zip_file'])
