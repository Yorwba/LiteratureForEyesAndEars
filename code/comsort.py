#!/usr/bin/env python3

# Utility for sorting lines in a file by frequency, while also keeping shared
# prefixes close to each other. This is useful for identifying and fixing common
# misspellings.

from collections import defaultdict
import sys


class Ptree(object):
    def __init__(self):
        self.count = 0
        self.total = 0
        self.children = defaultdict(Ptree)

    def add(self, s):
        current = self
        current.total += 1
        for c in s:
            current = current.children[c]
            current.total += 1
        current.count += 1

    def add_all(self, f):
        for line in f.readlines():
            self.add(line.strip())

    def iter(self, prefix=''):
        if self.count > 0:
            yield prefix
        for child in sorted(self.children.items(), key=lambda child: -child[1].total):
            yield from child[1].iter(prefix+child[0])


def main(argv):
    ptree = Ptree()
    if len(argv) == 1:
        ptree.add_all(sys.stdin)
    else:
        with open(argv[1]) as f:
            ptree.add_all(f)

    for line in ptree.iter():
        print(line)


if __name__ == '__main__':
    main(sys.argv)
