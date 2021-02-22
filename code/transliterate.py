#!/usr/bin/env python3

import argparse
import re
import sys
import unicodedata


class TransNode(object):
    def __init__(self):
        self.reads = dict()
        self.writes = set()

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        return id(self) == id(other)

    def add_entry(self, read, write):
        curr = self
        for c in read:
            if c not in curr.reads:
                curr.reads[c] = TransNode()
            curr = curr.reads[c]
        curr.writes.add(write)

    def transduce(self, read, target=None, break_tie=None):
        if not target:
            target = lambda c: True
        if not break_tie:
            break_tie = break_tie_manually
        states = {(self, '')} # invariant: self is always in states
        for i, c in enumerate(read):
            if not target(c):
                states = {
                    (self, out+c)
                    for (node, out) in states
                    if node == self
                }
            else:
                new_states = {
                    (node.reads[c], out)
                    for (node, out) in states
                    if c in node.reads
                }
                if not new_states:
                    expected = ''.join(sorted({
                        r
                        for (node, out) in states
                        for r in node.reads
                    }))
                    if len(expected) > 20:
                        expected = expected[:5] + f" ({len(expected)} total)"
                    try:
                        name = unicodedata.name(c)
                    except:
                        name = hex(ord(c))
                    raise Exception(f"Could not transliterate '{c}' ({name}) after '{read[:i][-5:]}', expected {expected}")
                states = new_states | {
                    (self, out+write)
                    for (node, out) in new_states
                    for write in node.writes
                }
            min_len = min(len(out) for (node, out) in states)
            prefixes = {out[:min_len] for (node, out) in states}
            if len(prefixes) > 1:
                prefix_groups = {
                    prefix: [
                        out
                        for (node, out) in states
                        if out.startswith(prefix)
                    ]
                    for prefix in prefixes
                }
                chosen_prefix = break_tie(
                    [
                        prefix
                        for _, prefix in sorted([
                            (-len(group), longest_common_prefix(group))
                            for group in prefix_groups.values()
                        ])
                    ],
                    read[i+1:]
                )
                states = {
                    (node, out)
                    for (node, out) in states
                    if out.startswith(chosen_prefix)
                }
        final_outputs = {
            out
            for (node, out) in states
            if node == self
        }
        if len(final_outputs) > 1:
            return break_tie(sorted(final_outputs), '')
        else:
            return next(iter(final_outputs))


def break_tie_manually(candidates, future):
    candidates = list(candidates)
    max_len = min(10, min(map(len, candidates)))
    for i, candidate in enumerate(candidates):
        print(i, candidate[-max_len:].split('\n')[-1], future[:10].split('\n')[0])
    while True:
        choice = input('> ')
        if choice == 'exit':
            sys.exit(1)
        try:
            return candidates[int(choice)]
        except:
            print('Not a valid choice: ', choice)
            pass


def longest_common_prefix(strings):
    strings = list(strings)
    i = 0
    while True:
        if any(i == len(s) or strings[0][i] != s[i] for s in strings):
            return strings[0][:i]
        i += 1


def load_dictionary(lines):
    dictionary = TransNode()
    for line in lines:
        if line.startswith('#'):
            continue
        read, write, _ = line.split(' ', 2)
        dictionary.add_entry(read, write)
    return dictionary


dictionaries = {
    'cmn-Hans': 'data/cc-cedict.txt',
}

target_functions = {
    'cmn-Hans': re.compile('[\u3005-\u3007\u3021-\u3029\u3031-\u3035\u3038-\u303C\u3220-\u3229\u3248-\u324F\u3251-\u325F\u3280-\u3289\u32B1-\u32BF\u3400-\u4DB5\u4E00-\u9FEA\uF900-\uFA6D\uFA70-\uFAD9\U00020000-\U0002A6D6\U0002A700-\U0002B734\U0002B740-\U0002B81D\U0002B820-\U0002CEA1\U0002CEB0-\U0002EBE0\U0002F800-\U0002FA1D]').fullmatch, # CJK according to https://stackoverflow.com/a/48673340
}


def main(argv):
    parser = argparse.ArgumentParser(
        description='Transliteration tool')
    parser.add_argument('target')
    parser.add_argument('input')
    parser.add_argument('output')
    args = parser.parse_args(argv[1:])
    with open(dictionaries[args.target]) as f:
        dictionary = load_dictionary(f)

    with open(args.input) as f:
        read = f.read()

    target = target_functions.get(args.target)
    # do a test run first
    dictionary.transduce(read, target=target, break_tie=lambda candidates, _: candidates[0])
    # repeat with manual control
    write = dictionary.transduce(read, target=target)

    with open(args.output, 'w') as f:
        f.write(write)


if __name__ == '__main__':
    main(sys.argv)
