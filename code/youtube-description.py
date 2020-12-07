#!/usr/bin/env python3

from html_to_plain import html_to_plain_text
from librivox_json import get_books
import re
import sys


PAREN = re.compile(r'(.*)\([^)]*\)')
def deparen(text):
    old_text = text
    while True:
        new_text = old_text.strip()
        match = PAREN.fullmatch(new_text)
        if match:
            new_text = match.group(1)
        if new_text == old_text:
            return new_text
        old_text = new_text


def by_people(people):
    people = [(p['first_name']+' '+p['last_name']).strip() for p in people]
    people = [p for p in people if p and not p.lower() == 'anonymous']
    people = people[:-2] + [' and '.join(people[-2:])]
    people = ', '.join(people)
    if people:
        return ' by '+people
    return people


def title(book):
    title = deparen(book['title'])
    by_authors = by_people(book['authors'])
    language = book['language']
    return f'{title}{by_authors} | {language} audiobook | Literature for Eyes and Ears'


def intro(book):
    title = deparen(book['title'])
    by_authors = by_people(book['authors'])
    language = book['language']
    return f'Practice and perfect your {language} spelling and pronunciation with this ' \
        f'audiobook of {title}{by_authors}. Read and listen at the same time. ' \
        f'Use the translated captions if you need help with difficult vocabulary. ' \
        f"But don't rely on them too much."


def description(book):
    return html_to_plain_text(book['description'])


WORD = re.compile(r'\w+')
def hashtags(book):
    language = book['language']
    words = [
        ''.join(WORD.findall(tag))
        for tag in ['Learn '+language] + [g['name'] for g in book['genres']]
    ]
    tags = []
    seen = set()
    for w in words:
        tag = '#'+w.lower()
        if tag not in seen:
            tags.append(tag)
            seen.add(tag)
    return ' '.join(tags)


def timestamp(seconds):
    minutes = seconds // 60
    hours = minutes // 60
    return '{:02}:{:02}:{:02}'.format(hours, minutes % 60, seconds % 60)


def sections(book):
    sections = sorted(book['sections'], key=lambda s: int(s['section_number']))
    if len(sections) < 2:
        return ''
    playtime = 0
    lines = ['Sections:']
    for s in sections:
        title = s['title']
        lines.append(f'[{timestamp(playtime)}] → {title}')
        playtime += int(s['playtime'])
    return '\n'.join(lines)


def links(book):
    lines = [
        'Original text: ' + book['url_text_source'],
        'Original audio: ' + book['url_librivox'],
        'Internet archive: ' + book['url_iarchive'],
    ]
    return '\n'.join(lines)


def readers(book):
    lines = ['Read by:']
    seen = set()
    for section in book['sections']:
        for reader in section['readers']:
            display_name = reader['display_name']
            reader_id = reader['reader_id']
            line = f'→ {display_name} https://librivox.org/reader/{reader_id}'
            if line not in seen:
                lines.append(line)
                seen.add(line)
    return '\n'.join(lines)


def donations(book):
    lines = [
        'Ways to give back:',
        '→ Thank a reader: https://librivox.org/pages/thank-a-reader/',
        '→ Help record a new book: https://librivox.org/pages/volunteer-for-librivox/',
        '→ Donate to LibriVox: https://librivox.org/pages/how-to-donate/',
        '→ Proofread scanned books for Project Gutenberg: https://www.pgdp.net/c/',
        '→ Donate to Project Gutenberg: https://gutenberg.org/donate/',
        '',
        'Support this channel:',
        '→ Donate via Liberapay: https://liberapay.com/LiteratureForEyesAndEars',
        '→ Donate via Patreon: https://www.patreon.com/LiteratureForEyesAndEars',
        '→ Tell your friends!',
    ]
    return '\n'.join(lines)


if __name__ == '__main__':
    for book in get_books(sys.argv[1]):
        print(title(book))
        print()
        print()
        print(intro(book))
        print()
        print(description(book))
        print(hashtags(book))
        print()
        print(sections(book))
        print()
        print(links(book))
        print()
        print(readers(book))
        print()
        print(donations(book))
