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
        lambda: (60, 14),
        jpn=(25, 7),
    )[language]
    if num_lines(align_json.span_text(paragraph), characters_per_line) <= lines_per_paragraph:
        return [paragraph]
    best_break = None
    best_delta = -1
    text_so_far = ''
    previous_end = None
    for i, sub in enumerate(paragraph['subalignments']):
        text_so_far += align_json.span_text(sub)
        lines_so_far = num_lines(text_so_far, characters_per_line)
        if lines_so_far > lines_per_paragraph:
            break
        if any(c.isalnum() for c in align_json.span_text(sub)) or not previous_end:
            previous_end = sub['end_time']
        next_sub = paragraph['subalignments'][i+1]
        delta = next_sub['start_time'] - previous_end
        if delta >= best_delta:
            best_delta = delta
            best_break = i
    if best_break is None:
        split_first = split_paragraph(paragraph['subalignments'][0], language=language)
        new_paragraph = {
            'start_time': paragraph['start_time'],
            'end_time': paragraph['end_time'],
            'span': paragraph['span'],
            'subalignments': split_first + paragraph['subalignments'][1:],
        }
        return split_paragraph(new_paragraph, language=language)
    paragraph_before_break = {
        'start_time': paragraph['start_time'],
        'end_time': paragraph['subalignments'][best_break]['end_time'],
        'span': ''.join(align_json.span_text(sub) for sub in paragraph['subalignments'][:best_break+1]),
        'subalignments': paragraph['subalignments'][:best_break+1],
    }
    paragraph_after_break = {
        'start_time': paragraph['subalignments'][best_break+1]['start_time'],
        'end_time': paragraph['end_time'],
        'span': ''.join(align_json.span_text(sub) for sub in paragraph['subalignments'][best_break+1:]),
        'subalignments': paragraph['subalignments'][best_break+1:],
    }
    return [paragraph_before_break] + split_paragraph(paragraph_after_break, language=language)

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
