#!/usr/bin/env python3

import json
import os.path


def get_books(path):
    info = get_info(path)
    books = info['books']
    if hasattr(books, 'values'):
        books = list(books.values())
    if not path.endswith('.json'):
        filename = path.split('/')[-1].split('.')[0]
        if filename:
            sections = []
            for b in books:
                for s in b.get('sections', []):
                    if filename in (s['file_name'] or ''):
                        s = s.copy()
                        s['sections'] = [s]
                        for k, v in b.items():
                            if k not in s:
                                s[k] = v
                        sections.append(s)
            if sections:
                return sections
    return books


def get_info(path):
    if os.path.isdir(path):
        subpath = os.path.join(path, 'librivox.json')
        if os.path.isfile(subpath):
            return get_info(subpath)
        else:
            up = os.path.dirname(path)
            if up != path:
                return get_info(up)
            else:
                return None
    else:
        if path.endswith('.json'):
            with open(path) as f:
                return json.load(f)
        else:
            up = os.path.dirname(path)
            if up != path:
                return get_info(up)
            else:
                return None


def main(argv):
    for name in argv[1:]:
        with open(name) as f: text = f.read()
        pretty = json.dumps(json.loads(text), sort_keys=True, indent=2)
        if pretty != text:
            with open(name, 'w') as f: f.write(pretty)


if __name__ == '__main__':
    import sys
    main(sys.argv)
