#!/usr/bin/env python3

import argparse
from librivox_json import get_books
import sys
from time_format import time_to_seconds, seconds_to_time
import urllib.parse


def good_source(url):
    # Being a bit picky here
    good_sources = [
        'aozora.gr.jp',
        'archive.org',
        'benyehuda.org',
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


def main(argv):
    parser = argparse.ArgumentParser(
        description='Recommend books in a given language')
    parser.add_argument('--all', action='store_true', default=False)
    parser.add_argument('language', nargs='?', type=str, default='')
    parser.add_argument('mintime', nargs='?', type=str, default='-inf')
    parser.add_argument('maxtime', nargs='?', type=str, default='inf')
    args = parser.parse_args(argv[1:])

    books = []
    for book in get_books('books/librivox.org/all_with_multilingual_sections.json'):
        if book['language'] == 'Multilingual' and 'sections' in book:
            for section in book['sections']:
                section['totaltimesecs'] = int(section['playtime'])
                section.setdefault('url_text_source', book['url_text_source'])
                section.setdefault('url_librivox', book['url_librivox'])
                books.append(section)
        else:
            books.append(book)

    language = args.language
    mintime = time_to_seconds(args.mintime)
    maxtime = time_to_seconds(args.maxtime)

    matches = [
        book
        for book in books
        if language in book['language']
        and mintime < book['totaltimesecs'] < maxtime
    ]

    matches_from_good_source = [
        book
        for book in matches
        if args.all or good_source(book['url_text_source'])
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


if __name__ == '__main__':
    main(sys.argv)
