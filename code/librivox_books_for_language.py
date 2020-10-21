#!/usr/bin/env python3

import json
import sys


def good_source(url):
    # Being a bit picky here
    return url and 'gutenberg.org' in url and 'projekt-gutenberg.org' not in url


def time_to_seconds(time):
    parts = time.split(':')[::-1]
    factors = [60, 60, 24]
    unit = 1
    seconds = 0
    for part, factor in zip(parts, factors):
        seconds += unit * float(part)
        unit *= factor
    return seconds


def seconds_to_time(seconds):
    factors = [60, 60, 24]
    parts = []
    left = seconds
    for factor in factors:
        parts.append('{:02}'.format(left % factor))
        left //= factor
    return ':'.join(parts[::-1])


if __name__ == '__main__':
    with open('books/librivox.org/all.json') as f: info = json.load(f)
    books = list(info['books'].values())

    argvdict = dict(enumerate(sys.argv))

    language = argvdict.get(1, '')
    mintime = time_to_seconds(argvdict.get(2, '-inf'))
    maxtime = time_to_seconds(argvdict.get(3,  'inf'))

    matches = [
        book
        for book in books
        if language in book['language']
        and mintime < book['totaltimesecs'] < maxtime
        and good_source(book['url_text_source'])
    ]

    for book in sorted(matches, key=lambda b: b['totaltimesecs']):
        print(seconds_to_time(book['totaltimesecs']), book['url_librivox'])
