#!/usr/bin/env python3

import align_json
import csv
from collections import Counter
import json
import librivox_json
import re
import sys


WORD = re.compile('\\w+')


def completed_books_in_language(books, lang):
    for book in books:
        if 'youtube_id' in book:
            if book['language'] == lang:
                yield book
        else:
            for section in book['sections']:
                if 'youtube_id' in section:
                    if section['language'] == lang:
                        yield section


def sentences_from_alignment(paragraphs):
    sentences = []
    unfinished_sentence = False
    blocked = True
    for paragraph in paragraphs:
        if align_json.is_standout(paragraph) or 'librivox' in align_json.span_text(paragraph).lower():
            unfinished_sentence = False
            blocked = True
            continue
        subs = paragraph['subalignments']
        for sub in subs:
            sentence = align_json.span_text(sub)
            first_word = WORD.search(sentence)
            if first_word:
                first_word = first_word.group()
            if unfinished_sentence or ((not blocked) and first_word and (first_word.title() != first_word)):
                if not sentences[-1][-1].isspace():
                    sentences[-1] += ' '
                sentences[-1] += sentence
            else:
                sentences.append(sentence)
            rstripped = sentence.rstrip('\n ()«»—‘’‚“”‹›')
            rstripped_bare = rstripped.rstrip('. ')
            unfinished_sentence = (
                (rstripped[-1] not in '!.?')
                or (not first_word)
                or rstripped_bare[-1].isdigit()
            )
            blocked = False

    return sentences


def clean_formatting(sentence, lang):
    sentence = sentence.strip()

    left, right = {
        'German': (
            '(»‚„›',
            ')«‘“‹',
        ),
    }[lang]

    sentence = sentence.lstrip(right).rstrip(left)

    missing_left = ''
    missing_left_matches = []
    stack = []
    matches = [None] * len(sentence)
    for i, c in enumerate(sentence):
        if c in left:
            stack.append((i, c))
        elif c in right:
            flipped = left[right.index(c)]
            if not stack:
                missing_left = flipped + missing_left
                missing_left_matches = [i] + missing_left_matches
                matches[i] = -len(missing_left)
            else:
                li, lc = stack.pop()
                if lc == flipped:
                    matches[li] = i
                    matches[i] = li
                else:
                    print(f'Mismatch in sentence {repr(sentence)}: {repr(sentence[li:i+1])}', file=sys.stderr)
    missing_right = ''
    missing_right_matches = []
    for i, c in stack:
        matches[i] = len(sentence) + len(missing_right)
        flipped = right[left.index(c)]
        missing_right += flipped
        missing_right_matches.append(i)

    joined = missing_left + sentence + missing_right
    joined_matches = missing_left_matches + matches + missing_right_matches
    drop = 0
    while drop < len(joined):
        if joined_matches[drop] != len(joined) - len(missing_left) - 1 - drop:
            break
        drop += 1
    return joined[drop:len(joined)-drop]


def main(argv):
    lang = argv[2]
    books = completed_books_in_language(
        librivox_json.get_all_books(argv[1]),
        lang
    )

    sentences = []
    for book in books:
        book_text_file = book['lfeae_path']+'.txt'
        book_align_file = book['lfeae_path']+'.align.json'
        with open(book_text_file) as f: book_text = f.read()
        with open(book_align_file) as f: book_align = json.load(f)
        align_text = ''.join(
            align_json.span_ruby(span).rstrip('\n')+'\n\n'
            for span in book_align
        ).rstrip('\n')+'\n\n'

        if book_text != align_text:
            print(f"Text of {book['title']} at {book_text_file} appears to have changed since computing alignment.")
            sys.exit(1)

        sentences += sentences_from_alignment(book_align)

    sentences = sorted(clean_formatting(s, lang) for s in sentences)
    json.dump(sentences, sys.stdout)


if __name__ == '__main__':
    import sys;
    main(sys.argv)

