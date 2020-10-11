#!/usr/bin/env python3

import json
import sys


def gutenberg_plain_text(url):
    prefix = 'http://www.gutenberg.org/ebooks/'
    if url.startswith(prefix):
        number = url[len(prefix):]
        return 'https://www.gutenberg.org/files/'+number+'/'+number+'.txt'
    raise Exception("Can't handle URL: "+url)

if __name__ == '__main__':
    with open(sys.argv[1]) as f: info = json.load(f)

    for book in info['books'].values():
        source = book['url_text_source']
        print(gutenberg_plain_text(source))
