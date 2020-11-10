#!/usr/bin/env python3

import json
import math
import sys


def span_text(alignment):
    text = alignment['span']
    if isinstance(text, str):
        return text
    else:
        return text['text']


def split_paragraph(paragraph):
    if all(
            line[-1].isalnum()
            for line in span_text(paragraph).splitlines()
    ):
        return [paragraph]
    return paragraph['subalignments']


def vad_pad(items, extend_before=1., extend_after=1.):
    extension = extend_after + extend_before
    items = iter(items)
    current = next(items).copy()
    current['start_time'] = max(0.0, current['start_time'] - extend_before)
    for item in items:
        item = item.copy()
        end = item['start_time']
        delta = end - current['end_time']
        assert delta >= 0.0
        if delta >= extension:
            current['end_time'] += extend_after
        else:
            scale = delta / extension
            current['end_time'] += scale * extend_after
            item['start_time'] -= scale * extend_before
        yield current
        current = item
    current['end_time'] += extend_after
    yield current


def format_srt_time(time):
    millis = int(time * 1000)
    seconds = millis // 1000
    minutes = seconds // 60
    hours = minutes // 60
    return '{:02}:{:02}:{:02},{:03}'.format(hours, minutes % 60, seconds % 60, millis % 1000)


if __name__ == '__main__':
    with open(sys.argv[1]) as f: alignments = json.load(f)

    sub_index = 0
    for split in vad_pad(
            split
            for paragraph in alignments
            for split in split_paragraph(paragraph)
    ):
        sub_index += 1
        print(sub_index)
        print('{} --> {}'.format(format_srt_time(split['start_time']), format_srt_time(split['end_time'])))
        print(span_text(split).strip())
        print()
