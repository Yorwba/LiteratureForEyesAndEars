#!/usr/bin/env python3

import json
import sys
import urllib.parse


def good_source(url):
    # Being a bit picky here
    good_sources = [
        'aozora.gr.jp',
        'archive.org',
        'gutenberg.net.au',
        'gutenberg.org',
        'wikisource.org',
        'az.lib.ru',
        'rvb.ru',
    ]
    bad_sources = ['projekt-gutenberg.org']
    return url \
        and any(source in url for source in good_sources)\
        and not any(source in url for source in bad_sources)


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
    ]

    matches_from_good_source = [
        book
        for book in matches
        if good_source(book['url_text_source'])
    ]

    if not matches:
        print("No books in: "+language)
    elif not matches_from_good_source:
        print("No matches from good source in: "+language)
        print("Most common sources:")
        from collections import Counter
        sources = [urllib.parse.urlsplit(book['url_text_source']).netloc for book in matches]
        for source, count in Counter(sources).most_common():
            print(source+': '+str(count))
    else:
        for book in sorted(matches_from_good_source, key=lambda b: b['totaltimesecs']):
            print(seconds_to_time(book['totaltimesecs']), book['url_librivox'])
