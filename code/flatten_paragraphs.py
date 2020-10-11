#!/usr/bin/env python3

import sys

if __name__ == '__main__':
    with open(sys.argv[1]) as f:
        paragraph = []
        for line in f.readlines():
            line = line.strip()
            if not line:
                if paragraph:
                    print(' '.join(paragraph))
                    print()
                paragraph = []
            else:
                paragraph.append(line)
        if paragraph:
            print(' '.join(paragraph))
