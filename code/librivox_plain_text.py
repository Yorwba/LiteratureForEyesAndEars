#!/usr/bin/env python3

import chardet
from html_to_plain import html_to_plain_text
from io import BytesIO
import json
from librivox_json import get_books
import re
import sys
import urllib.parse
import urllib.request
import zipfile


ARCHIVE_SRC = re.compile(b'<iframe id="playback" src="([^"]*)"')
ENCODING = re.compile(b'\nCharacter set encoding: (.*)\n')
def try_get(url, data=None):
    print('Trying', url, file=sys.stderr)
    if data and isinstance(data, dict):
        data = urllib.parse.urlencode(data).encode()
    request = urllib.request.Request(
        url,
        headers={
            'User-Agent': 'Mozilla/5.0 (not really)',
        },
        data=data,
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
                if not encoding:
                    as_file = BytesIO(text)
                    if zipfile.is_zipfile(as_file):
                        with zipfile.ZipFile(as_file) as z:
                            if 'aozora.gr.jp' in url:
                                text_files = [n for n in z.namelist() if n.endswith('.txt')]
                                if len(text_files) != 1:
                                    raise Exception("Not exactly one .txt in ZIP: "+", ".join(z.namelist()))
                                text = z.read(text_files[0])
                                encoding = 'shift-jis'
                            elif 'runeberg.org' in url:
                                html_files = [n for n in z.namelist() if n.endswith('.html')]
                                text = '\n'.join(html_to_plain_text(z.read(n)) for n in html_files)
                                encoding = 'utf-8'
                                text = text.encode(encoding)
                            else:
                                raise Exception("Didn't expect to get a ZIP file from URL "+url)
                    else:
                        raise Exception("Unknown file type!")
                return '\n'.join(text.decode(encoding).splitlines())
        raise Exception("Couldn't get data at url: "+url)


def gutenberg_id(url):
    split_url = urllib.parse.urlsplit(url)
    if split_url.netloc.endswith('www.gutenberg.org'):
        prefixes = [
            '/ebooks/',
            '/etext/',
        ]
        for prefix in prefixes:
            if split_url.path.startswith(prefix):
                number = split_url.path[len(prefix):]
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


def gutenberg_au_plain_text(url):
    prefix = 'http://gutenberg.net.au/'
    if not url.startswith(prefix):
        raise Exception("Not a gutenberg.net.au URL: "+url)
    if url.endswith('h.html'):
        url = url.replace('h.html', '.txt')
    return try_get(url)


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


def JIS_X_0213_encode(men, ku, ten):
    """
    JIS X 0213 has two planes (men) and each plane consists of a 94x94 grid.
    This function turns a character identified by its position in the grid into
    Unicode, via Shift JIS 2004 as an intermediate encoding.
    """
    # https://en.wikipedia.org/wiki/Shift_JIS#Shift_JISx0213_and_Shift_JIS-2004
    if men == 1:
        if 1 <= ku <= 62:
            s1 = (ku+257)//2
        elif 63 <= ku <= 94:
            s1 = (ku+385)//2
    elif men == 2:
        if ku in (1, 3, 4, 5, 8, 12, 13, 14, 15):
            s1 = (ku+479)//2 - (ku//8) * 3
        elif 78 <= ku <= 94:
            s1 = (ku+411)//2
    if ku & 1 == 1:
        if 1 <= ten <= 63:
            s2 = ten + 63
        elif 64 <= ten <= 94:
            s2 = ten + 64
    else:
        s2 = ten + 158
    return bytes((s1, s2)).decode('sjis_2004')


NUMBER = re.compile(r'\d+')
ZIP_NAME = re.compile(r'files/([^"]+\.zip)"')
JIS_X_ANNOTATION = re.compile(r'※［＃[^］]*([12])-([0-9]{1,2})-([0-9]{1,2})］')
UNICODE_ANNOTATION = re.compile(r'※［＃[^］]*U\+([0-9a-fA-F]+)([^］0-9a-fA-F][^］]*)?］')
FURIGANA = re.compile(
    '｜?(['
        '⺀-⺙⺛-⻳㇀-㇣㐀-䶵一-鿕豈-舘並-龎🈐-🈒🈔-🈻🉀-🉈𠀀-𪛖𪜀-𫜴𫝀-𫠝𫠠-𬺡丽-𪘀' # CJK
        '0-9A-Za-z０-９Ａ-Ｚａ-ｚ々〆※×' # not CJK, but can have furigana
    ']+)《([^》]+)》'
)
def aozora_plain_text(url):
    split_url = urllib.parse.urlsplit(url)
    if not split_url.netloc.endswith('aozora.gr.jp'):
        raise Exception("Not an Aozora Bunko URL: "+url)
    ids = NUMBER.findall(split_url.path)[:2]
    library_card = 'https://www.aozora.gr.jp/cards/{}/card{}.html'.format(*ids)
    library_card = try_get(library_card)
    zip_name = ZIP_NAME.search(library_card).group(1)
    zip_file = 'https://www.aozora.gr.jp/cards/{}/files/{}'.format(ids[0], zip_name)
    text = try_get(zip_file)
    text = JIS_X_ANNOTATION.sub(
        lambda m: JIS_X_0213_encode(*map(int,m.groups())),
        text
    )
    text = UNICODE_ANNOTATION.sub(
        lambda m: chr(int(m.group(1), 16)),
        text
    )
    if 'ruby' in zip_name:
        text = FURIGANA.sub(
            r'[[\1||\2]]',
            text
        )
    return text


BENYEHUDA_DOWNLOAD_FORM = re.compile(
    r'<form id="download_form" action="/([^"]*)" accept-charset="UTF-8" method="post"><input name="utf8" type="hidden" value="&#x2713;" /><input type="hidden" name="authenticity_token" value="([^"]*)" />'
)
def benyehuda_plain_text(url):
    http_prefix = 'http://benyehuda.org/'
    https_prefix = 'https://benyehuda.org/'
    if not any(url.startswith(p) for p in (http_prefix, https_prefix)):
        raise Exception("Not a benyehuda.org URL: "+url)
    html = try_get(url)
    download_form = BENYEHUDA_DOWNLOAD_FORM.search(html)
    action = download_form.group(1)
    authenticity_token = download_form.group(2)
    return try_get(https_prefix+action, data={
        "utf8": "✓",
        "authenticity_token": authenticity_token,
        "format": "txt",
        "os": "UNIX",
        "commit": "הורדה",
    })


def runeberg_plain_text(url):
    split_url = urllib.parse.urlsplit(url)
    if not split_url.netloc.endswith('runeberg.org'):
        raise Exception("Not a Runeberg.org URL: "+url)
    work = split_url.path.split('/')[1]
    zip_file = 'http://runeberg.org/download.pl?mode=html&work='+work
    text = try_get(zip_file)
    return text


if __name__ == '__main__':
    for book in get_books(sys.argv[1]):
        source = urllib.parse.unquote(book['url_text_source'])
        handled = False
        for handler in (
                gutenberg_plain_text,
                gutenberg_au_plain_text,
                azlibru_plain_text,
                wikisource_plain_text,
                aozora_plain_text,
                benyehuda_plain_text,
                runeberg_plain_text,
        ):
            try:
                print(handler(source), end='')
                handled = True
                break
            except Exception as e:
                print(e, file=sys.stderr)
                pass
        if not handled:
            sys.exit(1)
