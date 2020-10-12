#!/usr/bin/env python3

import json
import math
import sys

def num_lines(text, characters_per_line):
    return sum(
        max(1, int(math.ceil(len(line.rstrip())/characters_per_line)))
        for line in text.rstrip().split('\n')
    )

def split_paragraph(paragraph, characters_per_line, lines_per_paragraph):
    if num_lines(paragraph['span'], characters_per_line) <= lines_per_paragraph:
        return [paragraph]
    best_break = None
    best_delta = -1
    text_so_far = ''
    for i, sub in enumerate(paragraph['subalignments']):
        text_so_far += sub['span']
        lines_so_far = num_lines(text_so_far, characters_per_line)
        if lines_so_far > lines_per_paragraph:
            break
        if lines_so_far > lines_per_paragraph/3:
            next_sub = paragraph['subalignments'][i+1]
            delta = next_sub['start_time'] - sub['end_time']
            if delta > best_delta:
                best_delta = delta
                best_break = i
    if best_break is None:
        raise Exception("Paragraph is impossible to break:\n"+str(paragraph))
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

    first_paragraph = True
    for paragraph in alignments:
        for split in split_paragraph(paragraph, characters_per_line, lines_per_paragraph):
            if not first_paragraph:
                print()
            first_paragraph = False
            print(split['span'].rstrip())
