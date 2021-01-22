#!/usr/bin/env python3

import align_json
import argparse
from collections import defaultdict
import json
import math
import sys


def num_lines(text, characters_per_line):
    return sum(
        max(1, int(math.ceil(len(line.rstrip())/characters_per_line)))
        for line in text.rstrip().split('\n')
    )


def split_paragraph(paragraph, language=None):
    characters_per_line, lines_per_paragraph = defaultdict(
        lambda: (35, 8),
        cmn=(19, 7),
        jpn=(19, 5),
        kor=(26, 7),
        yue=(19, 7),
    )[language]

    if num_lines(align_json.span_text(paragraph), characters_per_line) <= lines_per_paragraph:
        return [paragraph]

    subs = paragraph['subalignments']

    if len(subs) == 1:
        split_single = split_paragraph(subs[0], language=language)
        new_paragraph = {
            'start_time': paragraph['start_time'],
            'end_time': paragraph['end_time'],
            'span': paragraph['span'],
            'subalignments': split_single,
        }
        return split_paragraph(new_paragraph, language=language)

    # dynamic programming to find the collection of breaks with minimal badness
    break_before = [dict(predecessor=None, badness=0.)] # always break before 0
    previous_end = None
    for i, isub in enumerate(subs):
        if any(c.isalnum() for c in align_json.span_text(isub)) or not previous_end:
            previous_end = isub['end_time']

        if i+1 == len(subs):
            badness = 0.
        else:
            next_sub = subs[i+1]
            delta = next_sub['start_time'] - previous_end
            badness = 1./(delta + 0.001)

        best_break = i
        for j in range(i, -1, -1):
            text_from_j_to_i = ''.join(align_json.span_text(jsub) for jsub in subs[j:i+1])
            lines_from_j_to_i = num_lines(text_from_j_to_i, characters_per_line)
            if lines_from_j_to_i > lines_per_paragraph:
                break
            if break_before[j]['badness'] < break_before[best_break]['badness']:
                best_break = j

        break_before.append(dict(
            predecessor=best_break,
            badness=badness + break_before[best_break]['badness'],
        ))

    breaks = [len(subs)] # always break at the end
    while break_before[breaks[-1]]['predecessor'] is not None:
        breaks.append(break_before[breaks[-1]]['predecessor'])
    breaks = breaks[::-1]

    broken = []
    for start, end in zip(breaks, breaks[1:]):
        paragraph_between_breaks = {
            'start_time': (paragraph if start == 0 else subs[start])['start_time'],
            'end_time': (paragraph if end == len(subs) else subs[end-1])['end_time'],
            'span': ''.join(align_json.span_text(sub) for sub in subs[start:end]),
            'subalignments': subs[start:end],
        }
        broken += split_paragraph(paragraph_between_breaks, language=language)

    return broken


def main(argv):
    parser = argparse.ArgumentParser(
        description='Find points to split overly long paragraphs')
    parser.add_argument('alignment')
    parser.add_argument('output')
    parser.add_argument('--language', type=str)
    args = parser.parse_args(argv[1:])
    with open(args.alignment) as f: alignments = json.load(f)

    paragraphs = []
    for paragraph in alignments:
        splits = split_paragraph(paragraph, language=args.language)
        for split in splits:
            paragraphs.append(align_json.span_ruby(split).rstrip()+'\n\n')

    new_text = ''.join(paragraphs).rstrip()+'\n\n'

    with open(args.output, 'r') as f: old_text = f.read()

    if new_text != old_text:
        with open(args.output, 'w') as f:
            f.write(new_text)


if __name__ == '__main__':
    main(sys.argv)
