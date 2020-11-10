#!/usr/bin/env python3

import json
import sys

with open(sys.argv[1]) as f: alignments = json.load(f)

def badness(alignment):
    subbadnesses = [badness(sub) for sub in alignment['subalignments']]
    subbadness = sum(subbadnesses)/len(subbadnesses) if subbadnesses else 0.
    return alignment['average_over_min'] + subbadness

def format_time(t):
    millis = round(t * 1000.)
    seconds = millis // 1000
    minutes = seconds // 60
    hours = minutes // 60
    minutes = minutes % 60
    seconds = seconds % 60
    millis = millis % 1000
    return f'{hours:02d}:{minutes:02d}:{seconds:02d}:{millis:03d}'

for a in sorted(alignments, key=lambda a: -badness(a)):
    print(format_time(a['start_time']), format_time(a['end_time']), a['average_over_min'], badness(a), a['span'])
    try:
        input()
    except:
        break
