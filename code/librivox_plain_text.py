#!/usr/bin/env python3

import chardet
from html_to_plain import html_to_plain_text
import json
from librivox_json import get_books
import re
import sys
import urllib.parse
import urllib.request


ARCHIVE_SRC = re.compile(b'<iframe id="playback" src="([^"]*)"')
ENCODING = re.compile(b'\nCharacter set encoding: (.*)\n')
def try_get(url):
    print('Trying', url, file=sys.stderr)
    request = urllib.request.Request(
        url,
        headers={
            'User-Agent': 'Mozilla/5.0 (not really)',
        },
    )
    with urllib.request.urlopen(request, timeout=5.) as response:
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
                else:
                    det = chardet.UniversalDetector()
                    det.feed(text)
                    encoding = det.close()['encoding']
                return '\n'.join(text.decode(encoding).splitlines())
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
    raise Exception("Not a Gutenberg.org URL: "+url)


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


def azlibru_plain_text(url):
    prefix = 'http://az.lib.ru/'
    if not url.startswith(prefix):
        raise Exception("Not an arz.lib.ru URL: "+url)
    html = try_get(url)
    return html_to_plain_text(html)


def wikisource_plain_text(url):
    split_url = urllib.parse.urlsplit(url)
    if not split_url.netloc.endswith('wikisource.org'):
        raise Exception("Not a Wikisource URL: "+url)
    query = urllib.parse.urlencode({
        'lang': split_url.netloc.split('.')[0],
        'page': '/'.join(split_url.path.split('/')[2:]),
        'format': 'txt',
        'fonts': '',
    })

    txt_url = 'https://wsexport.wmflabs.org/book.php?'+query
    return try_get(txt_url)


if __name__ == '__main__':
    for book in get_books(sys.argv[1]):
        source = book['url_text_source']
        handled = False
        for handler in (gutenberg_plain_text, azlibru_plain_text, wikisource_plain_text):
            try:
                print(handler(source), end='')
                handled = True
                break
            except Exception as e:
                print(e, file=sys.stderr)
                pass
        if not handled:
            sys.exit(1)
