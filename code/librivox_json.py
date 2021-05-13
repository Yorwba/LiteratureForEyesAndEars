#!/usr/bin/env python3

import json
import os.path


def get_books(path):
    info = get_info(path)
    books = info['books']
    if hasattr(books, 'values'):
        books = list(books.values())

    # normalize language data
    for b in books:
        blang = b['language']
        slangs = set()
        for s in b.get('sections', []):
            slang = s.get('language', blang)
            if slang == 'English' and blang != 'Multilingual':
                slang = blang
            if slang == 'Chinese':
                stitle = s['title'] or ''
                chinese_varieties = {
                    'Cantonese Chinese': {'Cantonese', 'Canonese'},
                    'Chengdu dialect': set(),
                    'Hainanese': set(),
                    'Hakka Chinese': {'Hakka'},
                    'Hokkien': set(),
                    'Hunanese - Changsha': set(),
                    'Hunanese - Linwu': set(),
                    'Hunanese - Taoyuan': set(),
                    'Sichuanese': set(),
                    '(Shandong)': set(),
                    'Taishanese': set(),
                    'Taiwanese': set(),
                    'Teochow': set(),
                }
                for tlang, aliases in chinese_varieties.items():
                    if any(a in stitle for a in aliases | {tlang}):
                        slang = tlang
            s['language'] = slang
            slangs.add(slang)
        if len(slangs) > 1:
            b['language'] = 'Multilingual'

    # find section matching file name
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


def get_all_librivox_json(path):
    if os.path.isdir(path):
        for name in os.listdir(path):
            subpath = os.path.join(path, name)
            if name == 'librivox.json':
                yield subpath
            else:
                yield from get_all_librivox_json(subpath)


def get_all_books(path):
    books = []
    for filename in get_all_librivox_json(path):
        books += get_books(filename)
    return books


def fix_bitrate(obj):
    if obj is None:
        return obj
    if isinstance(obj, int):
        return obj
    if isinstance(obj, str):
        return obj.replace('_128kb.mp3', '_64kb.mp3')
    if isinstance(obj, list):
        return list(map(fix_bitrate, obj))
    if isinstance(obj, dict):
        return {
            k: fix_bitrate(v)
            for k, v in obj.items()
        }
    raise NotImplementedError("Fixing bitrate of: "+repr(obj))


def main(argv):
    for name in argv[1:]:
        with open(name) as f: text = f.read()
        pretty = json.dumps(
            fix_bitrate(json.loads(text)),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )+'\n'
        if pretty != text:
            with open(name, 'w') as f: f.write(pretty)


if __name__ == '__main__':
    import sys
    main(sys.argv)
