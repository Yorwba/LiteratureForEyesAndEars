#!/usr/bin/env python3

from collections import defaultdict
import json
from librivox_json import get_books
import os.path
import sys


def seconds_to_time(seconds):
    factors = [60, 60, 24]
    parts = []
    left = seconds
    for factor in factors:
        parts.append('{:02}'.format(left % factor))
        left //= factor
    if left:
        parts.append(str(left))
    return ':'.join(parts[::-1])


if __name__ == '__main__':
    totaltime = defaultdict(lambda: 0)
    for book in get_books(sys.argv[1]):
        lang = book['language']
        if lang == 'Multilingual' and 'sections' in book:
            for section in book['sections']:
                lang = section['language']
                totaltime[lang] += int(section['playtime'])
        else:
            totaltime[lang] += int(book['totaltimesecs'])
    table = [
        (lang, seconds_to_time(playtime))
        for lang, playtime 
        in sorted(totaltime.items(), key=lambda lp: lp[1])
    ]
    langlen = max(len(lang) for lang, playtime in table)
    timelen = max(len(playtime) for lang, playtime in table)
    for lang, playtime in table:
        langpad = ' ' * (langlen - len(lang))
        timepad = ' ' * (timelen - len(playtime))
        print(lang+langpad, timepad+playtime)
