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
        split_first = split_paragraph(paragraph['subalignments'][0], characters_per_line, lines_per_paragraph)
        new_paragraph = {
            'start_time': paragraph['start_time'],
            'end_time': paragraph['end_time'],
            'span': paragraph['span'],
            'subalignments': split_first + paragraph['subalignments'][1:],
        }
        return split_paragraph(new_paragraph, characters_per_line, lines_per_paragraph)
    paragraph_before_break = {
        'start_time': paragraph['start_time'],
        'end_time': paragraph['subalignments'][best_break]['end_time'],
        'span': ''.join(sub['span'] for sub in paragraph['subalignments'][:best_break+1]),
        'subalignments': paragraph['subalignments'][:best_break+1],
    }
    paragraph_after_break = {
        'start_time': paragraph['subalignments'][best_break+1]['start_time'],
        'end_time': paragraph['end_time'],
        'span': ''.join(sub['span'] for sub in paragraph['subalignments'][best_break+1:]),
        'subalignments': paragraph['subalignments'][best_break+1:],
    }
    return [paragraph_before_break] + split_paragraph(paragraph_after_break, characters_per_line, lines_per_paragraph)


if __name__ == '__main__':
    characters_per_line = int(sys.argv[1])
    lines_per_paragraph = int(sys.argv[2])
    with open(sys.argv[3]) as f: alignments = json.load(f)

    paragraphs = []
    for paragraph in alignments:
        splits = split_paragraph(paragraph, characters_per_line, lines_per_paragraph)
        for split in splits:
            paragraphs.append(split['span'].rstrip()+'\n\n')

    new_text = ''.join(paragraphs).rstrip()+'\n\n'

    with open(sys.argv[4], 'r') as f: old_text = f.read()

    if new_text != old_text:
        with open(sys.argv[4], 'w') as f:
            f.write(new_text)
