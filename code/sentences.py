#!/usr/bin/env python3

import align_json
import csv
from collections import Counter
import json
import librivox_json
from pqdict import maxpq
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


def homogenize(sentence):
    words = list(w.lower() for w in WORD.findall(sentence))
    words.append('') # ensure every word is followed by a space
    return ' '.join(words)


class Tokenizer(object):
    """Inspired by https://en.wikipedia.org/wiki/Re-Pair """

    def __init__(self, sentences):
        self.sentences = sorted(set(sentences))
        self.sentence_id = {s: i for i, s in enumerate(self.sentences)}
        self.end_at = [[None] * (len(s) - 1) for i, s in enumerate(sentences)]
        self.seq_prev = [[None] * (len(s) - 1) for i, s in enumerate(sentences)]
        self.seq_next = [[None] * (len(s) - 1) for i, s in enumerate(sentences)]
        self.same_prev = [[None] * (len(s) - 1) for i, s in enumerate(sentences)]
        self.same_next = [[None] * (len(s) - 1) for i, s in enumerate(sentences)]
        self.pair_parts = dict()
        self.pair_counts = Counter()
        self.pair_first = dict()
        self.pair_last = dict()

        prev_i, prev_j = None, None
        for i, s in enumerate(sentences):
            for j in range(len(s) - 1):
                if prev_i is not None:
                    self.seq_prev[i][j] = (prev_i, prev_j)
                    self.seq_next[prev_i][prev_j] = (i, j)
                self.end_at[i][j] = j+2
                pair = s[j:j+2]
                self.pair_parts[pair] = tuple(pair)
                self.pair_counts[pair] += 1
                if pair not in self.pair_first:
                    self.pair_first[pair] = (i, j)
                    self.pair_last[pair] = (i, j)
                else:
                    last_i, last_j = self.pair_last[pair]
                    self.same_prev[i][j] = (last_i, last_j)
                    self.same_next[last_i][last_j] = (i, j)
                    self.pair_last[pair] = (i, j)
                prev_i, prev_j = (i, j)

        self.pair_counts = maxpq(self.pair_counts)

        while True:
            common_pair, common_count = self.pair_counts.topitem()
            if common_count <= 1:
                break
            self.join_pair(common_pair)

    def _remove_pair_at(self, i, j):
        end = self.end_at[i][j]
        text = self.sentences[i][j:end]
        prev = self.seq_prev[i][j]
        next = self.seq_next[i][j]
        same_prev = self.same_prev[i][j]
        same_next = self.same_next[i][j]
        if prev:
            prev_i, prev_j = prev
            self.seq_next[prev_i][prev_j] = next
        if next:
            next_i, next_j = next
            self.seq_prev[next_i][next_j] = prev
        if same_prev:
            same_prev_i, same_prev_j = same_prev
            self.same_next[same_prev_i][same_prev_j] = same_next
        if same_next:
            same_next_i, same_next_j = same_next
            self.same_prev[same_next_i][same_next_j] = same_prev

        self.end_at[i][j] = None
        self.seq_prev[i][j] = None
        self.seq_next[i][j] = None
        self.same_prev[i][j] = None
        self.same_next[i][j] = None
        self.pair_counts[text] -= 1
        if self.pair_counts[text] == 0:
            del self.pair_counts[text]
        if self.pair_first.get(text) == (i, j):
            self.pair_first[text] = same_next
        if self.pair_last.get(text) == (i, j):
            self.pair_last[text] = same_prev

    def _replace_pair_at(self, old_i, old_j, new_i, new_j, old_end, new_end):
        prev = self.seq_prev[old_i][old_j]
        next = self.seq_next[old_i][old_j]
        self._remove_pair_at(old_i, old_j)

        if prev:
            prev_i, prev_j = prev
            self.seq_prev[new_i][new_j] = prev
            self.seq_next[prev_i][prev_j] = (new_i, new_j)
        if next:
            next_i, next_j = next
            self.seq_prev[next_i][next_j] = (new_i, new_j)
            self.seq_next[new_i][new_j] = next

        self.end_at[new_i][new_j] = new_end
        sentence = self.sentences[new_i]
        text = sentence[new_j:new_end]
        self.pair_parts[text] = sentence[new_j:old_end], sentence[old_end:new_end]
        self.pair_counts[text] = self.pair_counts.get(text, 0) + 1
        if self.pair_first.get(text) is None:
            self.pair_first[text] = (new_i, new_j)
            self.pair_last[text] = (new_i, new_j)
        else:
            last_i, last_j = self.pair_last[text]
            self.same_prev[new_i][new_j] = (last_i, last_j)
            self.same_next[last_i][last_j] = (new_i, new_j)
            self.pair_last[text] = (new_i, new_j)

    def join_pair(self, pair):
        position = self.pair_first.get(pair)
        while position:
            i, j = position
            end = self.end_at[i][j]
            prev = self.seq_prev[i][j]
            next = self.seq_next[i][j]
            position = self.same_next[i][j]
            if position and position[0] == i and position == next:
                # if the next pair is the same and overlaps, it will be invalidated, so skip
                position = self.same_next[position[0]][position[1]]
            self._remove_pair_at(i, j)
            if prev and prev[0] == i:
                prev_i, prev_j = prev
                prev_end = self.end_at[prev_i][prev_j]
                self._replace_pair_at(prev_i, prev_j, prev_i, prev_j, j, end)
            if next and next[0] == i:
                next_i, next_j = next
                next_end = self.end_at[next_i][next_j]
                self._replace_pair_at(next_i, next_j, i, j, end, next_end)

    def tokens(self, sentence):
        i = start_i = self.sentence_id[sentence]
        j = 0
        while i == start_i:
            end = self.end_at[i][j]
            if end is None: # no pair
                assert j == 0
                yield sentence
                return
            text = sentence[j:end]
            first, second = self.pair_parts[text]
            if j == 0:
                yield first
            yield second
            next = self.seq_next[i][j]
            if next is None:
                break
            i, j = next

    def tokentree(self, sentence):
        def tree(token):
            return (token, tuple(map(tree, self.pair_parts.get(token, ()))))
        for token in self.tokens(sentence):
            yield tree(token)


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
            print(f"Text of {book['title']} at {book_text_file} appears to have changed since computing alignment.", file=sys.stderr)
            sys.exit(1)

        sentences += sentences_from_alignment(book_align)

    sentences = sorted(clean_formatting(s, lang) for s in sentences)
    homogenized_sentences = sorted(set(map(homogenize, sentences)))
    tokenizer = Tokenizer(homogenized_sentences)
    for s in sentences:
        print(json.dumps({
            'text': s,
            'tokens': list(tokenizer.tokens(homogenize(s))),
            'tokentree': list(tokenizer.tokentree(homogenize(s))),
        }))


if __name__ == '__main__':
    import sys;
    main(sys.argv)

