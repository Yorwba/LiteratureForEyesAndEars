#!/usr/bin/env python3

import json
import re
import sys
import urllib.request


ARCHIVE_SRC = re.compile(b'<iframe id="playback" src="([^"]*)"')
ENCODING = re.compile(b'\nCharacter set encoding: (.*)\n')
def try_get(url):
    print('Trying', url, file=sys.stderr)
    with urllib.request.urlopen(url, timeout=5.) as response:
        if 'block.pglaf.org' in response.url:
            return try_get('https://web.archive.org/'+url)
        if response.status == 200:
            text = response.read()
            src = ARCHIVE_SRC.search(text)
            if src:
                return try_get(src.group(1).decode('ascii'))
            else:
                encoding = ENCODING.search(text)
                if encoding:
                    encoding = encoding.group(1).decode('ascii')
                return text.decode(encoding)
        raise Exception("Couldn't get data at url: "+url)


def gutenberg_id(url):
    prefix = 'http://www.gutenberg.org/ebooks/'
    if url.startswith(prefix):
        number = url[len(prefix):]
        return number
    prefix = 'http://www.gutenberg.org/etext/'
    if url.startswith(prefix):
        number = url[len(prefix):]
        return number
    raise Exception("Can't handle URL: "+url)


def gutenberg_plain_text(url):
    number = gutenberg_id(url)
    urls = [
        'http://www.gutenberg.org/files/'+number+'/'+number+'-0.txt',
        'http://www.gutenberg.org/files/'+number+'/'+number+'-8.txt',
        'http://www.gutenberg.org/files/'+number+'/'+number+'.txt',
    ]

    for url in urls:
        try:
            text = try_get(url)
            return text
            break
        except Exception as e:
            print(e, file=sys.stderr)
            pass

    raise Exception('\n - '.join([
        'Gutenberg plain text was at none of the URLs: '
    ]+urls))


if __name__ == '__main__':
    with open(sys.argv[1]) as f: info = json.load(f)

    for book in info['books'].values():
        source = book['url_text_source']
        print(gutenberg_plain_text(source), end='')
