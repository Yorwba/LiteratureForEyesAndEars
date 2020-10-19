#!/usr/bin/env python3

import json
import math
import sys


def isalphanumeric(c):
    return c.isalpha() or c.isnumeric()


def split_paragraph(paragraph):
    if all(
            isalphanumeric(line[-1])
            for line in paragraph['span'].splitlines()
    ):
        return [paragraph]
    return paragraph['subalignments']


def format_srt_time(time):
    millis = int(time * 1000)
    seconds = millis // 1000
    minutes = seconds // 60
    hours = minutes // 60
    return '{:02}:{:02}:{:02},{:03}'.format(hours, minutes % 60, seconds % 60, millis % 1000)


if __name__ == '__main__':
    with open(sys.argv[1]) as f: alignments = json.load(f)

    sub_index = 0
    for paragraph in alignments:
        for split in split_paragraph(paragraph):
            sub_index += 1
            print(sub_index)
            print('{} --> {}'.format(format_srt_time(split['start_time']), format_srt_time(split['end_time'])))
            print(split['span'].strip())
            print()
