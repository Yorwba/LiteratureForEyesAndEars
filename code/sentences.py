#!/usr/bin/env python3

import align_json
import csv
from collections import defaultdict, Counter
import hashlib
import json
import librivox_json
from pqdict import maxpq, minpq
import re
import sys


def stable_hash(string):
    h = hashlib.md5()
    h.update(string.encode('utf-8'))
    return h.digest()


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
            words = WORD.findall(sentence)
            if words:
                first_word = words[0]
                last_word = words[-1]
            short = len(words) < 2
            punctuation_to_strip = '\n ()«»—‘’‚“”‹›'
            rstripped = sentence.rstrip(punctuation_to_strip)
            lrstripped = rstripped.lstrip(punctuation_to_strip)
            if (
                    unfinished_sentence
                    or ((not blocked) and words and (first_word.title() != first_word))
                    or (short and lrstripped == rstripped)
            ):
                if not sentences[-1]['text'][-1].isspace():
                    sentences[-1]['text'] += ' '
                sentences[-1]['text'] += sentence
                sentences[-1]['end_time'] = sub['end_time']
            else:
                sentences.append({
                    'text': sentence,
                    'start_time': sub['start_time'],
                    'end_time': sub['end_time'],
                })
            unfinished_sentence = (
                (rstripped[-1] not in '!.?')
                or (short and lrstripped != rstripped)
                or last_word[-1].isdigit()
                or (len(last_word) < 2)
                or (not any(vowel in last_word.lower() for vowel in 'aeiouäöü'))
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
    words = [w.lower() for w in WORD.findall(sentence)]
    return ['['+w+']' for w in words]


class Tokenizer(object):
    """Inspired by https://en.wikipedia.org/wiki/Re-Pair """

    def __init__(self, strings, confidence):
        self.string_counts = Counter(strings)
        self.strings = sorted(self.string_counts)
        self.string_counts = [self.string_counts[s] for s in self.strings]
        self.string_id = {s: i for i, s in enumerate(self.strings)}
        self.end_at = [[None] * (len(s) - 1) for i, s in enumerate(self.strings)]
        self.seq_prev = [[None] * (len(s) - 1) for i, s in enumerate(self.strings)]
        self.seq_next = [[None] * (len(s) - 1) for i, s in enumerate(self.strings)]
        self.same_prev = [[None] * (len(s) - 1) for i, s in enumerate(self.strings)]
        self.same_next = [[None] * (len(s) - 1) for i, s in enumerate(self.strings)]
        self.token_counts = Counter()
        self.total_tokens = 0
        self.token_pairs = defaultdict(set)
        self.pair_parts = dict()
        self.pair_counts = Counter()
        self.pair_first = dict()
        self.pair_last = dict()

        prev_i, prev_j = None, None
        for i, s in enumerate(self.strings):
            count = self.string_counts[i]
            for c in s:
                self.token_counts[c] += count
            self.total_tokens += len(s) * count
            for j in range(len(s) - 1):
                if prev_i is not None:
                    self.seq_prev[i][j] = (prev_i, prev_j)
                    self.seq_next[prev_i][prev_j] = (i, j)
                self.end_at[i][j] = j+2
                pair = s[j:j+2]
                for token in pair:
                    self.token_pairs[token].add(pair)
                self.pair_parts[pair] = tuple(pair)
                self.pair_counts[pair] += count
                if pair not in self.pair_first:
                    self.pair_first[pair] = (i, j)
                    self.pair_last[pair] = (i, j)
                else:
                    last_i, last_j = self.pair_last[pair]
                    self.same_prev[i][j] = (last_i, last_j)
                    self.same_next[last_i][last_j] = (i, j)
                    self.pair_last[pair] = (i, j)
                prev_i, prev_j = (i, j)

        self.touched_tokens = set(self.token_counts)
        self.pair_scores = maxpq()

        while True:
            touched_pairs = set()
            for token in self.touched_tokens:
                touched_pairs.update(self.token_pairs[token])
            self.touched_tokens = set()
            for pair in touched_pairs:
                left, right = self.pair_parts[pair]
                count = self.pair_counts[pair]
                left_count = self.token_counts[left]
                right_count = self.token_counts[right]
                # Following http://arxiv.org/abs/1406.6312 , score pairs using
                # the t-statistic for deviation from independent pairing, with
                # the variance approximated by the observed count. (Valid for
                # total_tokens >> count)
                self.pair_scores[pair] = (
                    (count - left_count*right_count/self.total_tokens)/(count ** 0.5),
                    stable_hash(pair), # tiebreaker
                )
                # In theory, all scores should be recalculated as total_tokens
                # decreases, but invalidating only pairs whose token_counts
                # changed seems reasonable enough.

            best_pair, (best_score, _pair_hash) = self.pair_scores.topitem()
            if best_score <= confidence:
                break
            self.join_pair(best_pair)

    def _remove_pair_at(self, i, j):
        end = self.end_at[i][j]
        text = self.strings[i][j:end]
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
        self.pair_counts[text] -= self.string_counts[i]
        if self.pair_counts[text] == 0:
            for token in set(self.pair_parts[text]):
                self.token_pairs[token].remove(text)
            del self.pair_counts[text]
            if text in self.pair_scores:
                # The check is necessary because the pair might've been created
                # in a merge just now, which means it won't have been scored yet.
                del self.pair_scores[text]
        if self.pair_first.get(text) == (i, j):
            self.pair_first[text] = same_next
        if self.pair_last.get(text) == (i, j):
            self.pair_last[text] = same_prev

    def _replace_pair_at(self, i, old_j, new_j, old_end, new_end):
        prev = self.seq_prev[i][old_j]
        next = self.seq_next[i][old_j]
        self._remove_pair_at(i, old_j)

        if prev:
            prev_i, prev_j = prev
            self.seq_prev[i][new_j] = prev
            self.seq_next[prev_i][prev_j] = (i, new_j)
        if next:
            next_i, next_j = next
            self.seq_prev[next_i][next_j] = (i, new_j)
            self.seq_next[i][new_j] = next

        self.end_at[i][new_j] = new_end
        string = self.strings[i]
        text = string[new_j:new_end]
        tokens = string[new_j:old_end], string[old_end:new_end]
        for token in tokens:
            self.token_pairs[token].add(text)
        self.pair_parts[text] = tokens
        self.pair_counts[text] += self.string_counts[i]
        if self.pair_first.get(text) is None:
            self.pair_first[text] = (i, new_j)
            self.pair_last[text] = (i, new_j)
        else:
            last_i, last_j = self.pair_last[text]
            self.same_prev[i][new_j] = (last_i, last_j)
            self.same_next[last_i][last_j] = (i, new_j)
            self.pair_last[text] = (i, new_j)

    def join_pair(self, pair):
        left, right = self.pair_parts[pair]
        count = 0
        position = self.pair_first.get(pair)
        while position:
            i, j = position
            count += self.string_counts[i]
            end = self.end_at[i][j]
            prev = self.seq_prev[i][j]
            next = self.seq_next[i][j]
            position = self.same_next[i][j]
            if position and position[0] == i and position == next:
                # if the next pair is the same and overlaps, it will be invalidated, so skip
                position = self.same_next[position[0]][position[1]]
            self._remove_pair_at(i, j)
            if prev and prev[0] == i:
                prev_j = prev[1]
                prev_end = self.end_at[i][prev_j]
                self._replace_pair_at(i, prev_j, prev_j, j, end)
            if next and next[0] == i:
                next_j = next[1]
                next_end = self.end_at[i][next_j]
                self._replace_pair_at(i, next_j, j, end, next_end)
        for token in left, right:
            self.token_counts[token] -= count
            if self.token_counts[token] == 0:
                del self.token_counts[token]
                del self.token_pairs[token]
            else:
                self.touched_tokens.add(token)
        self.token_counts[pair] += count
        self.touched_tokens.add(pair)
        self.total_tokens -= count

    def tokens(self, string):
        i = start_i = self.string_id[string]
        j = 0
        while i == start_i:
            end = self.end_at[i][j]
            if end is None: # no pair
                assert j == 0
                yield string
                return
            text = string[j:end]
            first, second = self.pair_parts[text]
            if j == 0:
                yield first
            yield second
            next = self.seq_next[i][j]
            if next is None:
                break
            i, j = next

    def tokentree(self, string):
        def tree(token):
            return (token, tuple(map(tree, self.pair_parts.get(token, ()))))
        for token in self.tokens(string):
            yield tree(token)


def curriculum(sentences):
    sentences = list(sentences)
    vocabulary = set()
    chosen = []
    token_count = Counter(t for s in sentences for t in s['tokens'])

    def nonempty_token_len(sentence):
        return sum(any(c not in '[]' for c in t) for t in sentence['tokens'])

    sentences = [s for s in sentences if nonempty_token_len(s) >= 3] # discard short sentences
    length_count = Counter(nonempty_token_len(s) for s in sentences)
    token_sentences = defaultdict(set)
    for i, s in enumerate(sentences):
        for t in s['tokens']:
            token_sentences[t].add(i)

    def sentence_key(sentence):
        new_tokens = set(sentence['tokens']) - vocabulary
        if not new_tokens:
            return None
        token_keys = sorted(
            (token_count[t], stable_hash(t), t) # smallest count first, break ties
            for t in new_tokens
        )
        return (
            [-c for c, h, t in token_keys], # biggest smallest count first
            [(h, t) for c, h, t in token_keys], # break ties when number and counts of unknown tokens are the same
            -length_count[nonempty_token_len(sentence)], # if unknown tokens are the same, pick something with a more common length
            stable_hash(sentence['text']), # final tiebreaker
        )

    learnq = minpq()
    for i, s in enumerate(sentences):
        learnq[i] = sentence_key(s)

    while learnq:
        i, key = learnq.topitem()
        if key[0][0] >= -1: # stop at the first hapax legomenon
            break
        s = sentences[i]
        chosen.append(s)
        new_tokens = set(s['tokens']) - vocabulary
        vocabulary.update(new_tokens)
        touched_sentences = set(ti for t in new_tokens for ti in token_sentences[t])
        for ti in touched_sentences:
            ts = sentences[ti]
            k = sentence_key(ts)
            if k is None:
                for t in set(ts['tokens']):
                    token_sentences[t].remove(ti)
                del learnq[ti]
            else:
                learnq[ti] = k

    return chosen


def main(argv):
    lang = argv[2]
    books = completed_books_in_language(
        librivox_json.get_all_books(argv[1]),
        lang
    )

    sentences = []
    for book in books:
        book_audio_file = book['lfeae_path']+'.mp3'
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

        book_sentences = sentences_from_alignment(book_align)
        for s in book_sentences:
            s['audio_path'] = book_audio_file
        sentences += book_sentences

    for s in sentences:
        s['text'] = clean_formatting(s['text'], lang)
    sentences = sorted(sentences, key=lambda s: s['text'])
    homogenized_words = sorted(w for s in sentences for w in homogenize(s['text']))
    tokenizer = Tokenizer(homogenized_words, confidence=2)

    for s in sentences:
        s['tokens'] = list(t for w in homogenize(s['text']) for t in tokenizer.tokens(w))
    chosen_sentences = curriculum(sentences)
    for s in chosen_sentences:
        print(json.dumps(s))


if __name__ == '__main__':
    import sys;
    main(sys.argv)

