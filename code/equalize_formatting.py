#!/usr/bin/env python3

import argparse
import re
import sys

WORD = re.compile(r'\w+')


def print_windows(wordlists, start, window_size=10):
    windows = [[''] + [str(i+1) for i in range(window_size)]] + [
        [chr(i+ord('a'))+':'] + [w.group() for w in wordlist[start:start+window_size]]
        for i, wordlist in enumerate(wordlists)
    ]
    for window in windows:
        if len(window) < window_size+1:
            window.extend(('',) * (window_size + 1 - len(window)))
    maxlens = [
        max(len(window[i]) for window in windows)
        for i in range(window_size+1)
    ]
    for i, window in enumerate(windows):
        print(' '.join(
            ' ' * (maxlen - len(w)) + w
            for maxlen, w in zip(maxlens, window)
        ))


def find_divergence(wordlists, previous=0):
    lens = list(map(len, wordlists))
    min_len = min(lens)

    min_bound, max_bound = previous, min_len

    step = 0
    while True:
        guess = min(min_bound + step, (min_bound + max_bound)//2)
        step += step + 1
        while guess < max_bound and len(set(wordlist[guess].group() for wordlist in wordlists)) <= 1:
            guess = guess + 1
        if guess >= max_bound:
            return guess

        print_windows(wordlists, guess)
        while True:
            choice = input('Match? [y/n] > ')
            if choice == 'exit':
                sys.exit(1)
            elif choice == 'y':
                min_bound = guess + 1
            elif choice == 'n':
                max_bound = guess
            else:
                try:
                    choice = int(choice)
                    if choice > 1:
                        min_bound = guess + choice - 1
                    max_bound = guess + choice - 1
                except:
                    print('Not a valid choice: ', choice)
                    continue
            break


def equalize_wordcounts(texts):
    div = 0
    while True:
        wordlists = [list(WORD.finditer(text)) for text in texts]
        lens = list(map(len, wordlists))
        div = find_divergence(wordlists, div)
        if all(l <= div for l in lens):
            return texts

        print_windows(wordlists, div)
        while True:
            choice = input('[cat <count> <row> || rm <count> <row> || cp <count> <from_row> <to_row> ] > ').split()
            if choice == ['exit']:
                sys.exit(1)
            elif len(choice) == 3 and choice[0] == 'cat':
                count = int(choice[1])
                row = ord(choice[2])-ord('a')
                cat_start = wordlists[row][div].start()
                cat_end   = wordlists[row][div+count-1].end()
                cat_text = ''.join(w.group() for w in wordlists[row][div:div+count])
                texts[row] = texts[row][:cat_start] + cat_text + texts[row][cat_end:]
            elif len(choice) == 3 and choice[0] == 'rm':
                count = int(choice[1])
                row = ord(choice[2])-ord('a')
                rm_start = wordlists[row][div].start()
                rm_end   = wordlists[row][div+count-1].end()
                texts[row] = texts[row][:rm_start] + texts[row][rm_end:]
            elif len(choice) == 4 and choice[0] == 'cp':
                count = int(choice[1])
                from_row = ord(choice[2])-ord('a')
                to_row   = ord(choice[3])-ord('a')
                from_start = wordlists[from_row][div].start()
                from_end   = wordlists[from_row][div+count].start() if div+count < len(wordlists[from_row]) else wordlists[from_row][div:div+count][-1].end()
                to_start   = wordlists[  to_row][div].start() if div < len(wordlists[to_row]) else len(texts[to_row])
                texts[to_row] = texts[to_row][:to_start] + texts[from_row][from_start:from_end] + texts[to_row][to_start:]
            else:
                print('Not a valid choice: ', choice)
                continue
            break


def equalize_formatting(texts, files):
    texts = equalize_wordcounts(texts)
    wordlists = [list(WORD.finditer(text)) for text in texts]
    for i, filename in enumerate(files):
        print(chr(i+ord('a'))+':', filename)

    while True:
        choice = input("Choose which file's formatting to use > ")
        if choice == 'exit':
            sys.exit(1)
        elif len(choice) == 1:
            row = ord(choice)-ord('a')
        else:
            print('Not a valid choice: ', choice)
            continue
        break

    formatting = []
    previous_end = 0
    for word in wordlists[row]:
        formatting.append(texts[row][previous_end:word.start()])
        previous_end = word.end()
    formatting.append(texts[row][previous_end:])

    texts = [
        ''.join(
            f+w for f, w in zip(formatting, [w.group() for w in wordlist] + [''])
        )
        for wordlist in wordlists
    ]

    return texts


def main(argv):
    parser = argparse.ArgumentParser(
        description='Line up the formatting of different versions of the same text for easy comparison with vimdiff')
    parser.add_argument('files', nargs='+')
    args = parser.parse_args(argv[1:])

    texts = []
    for filename in args.files:
        with open(filename) as f:
            texts.append(f.read())

    new_texts = equalize_formatting(texts, args.files)

    for filename, text, new_text in zip(args.files, texts, new_texts):
        if text != new_text:
            with open(filename, 'w') as f:
                f.write(new_text)


if __name__ == '__main__':
    main(sys.argv)
