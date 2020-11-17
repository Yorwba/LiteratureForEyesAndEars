#!/usr/bin/env python3

import json


def span_text(alignment):
    text = alignment['span']
    if isinstance(text, str):
        return text
    else:
        return text['text']


def span_speech(alignment):
    text = alignment['span']
    if isinstance(text, str):
        return text
    else:
        return text['speech']


def is_standout(paragraph):
    return all(
        line[-1].isalnum()
        for line in span_text(paragraph).splitlines()
    )


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
