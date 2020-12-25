#!/usr/bin/env python3

import json
import unicodedata


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


def text_speech_factors(text, speech):
    prefix_len = max(i for i in range(1+min(len(text), len(speech))) if text[:i] == speech[:i])
    prefix = text[:prefix_len]
    text = text[prefix_len:]
    speech = speech[prefix_len:]
    suffix_len = max(i for i in range(1+min(len(text), len(speech))) if text[len(text)-i:] == speech[len(speech)-i:])
    suffix = text[len(text)-suffix_len:]
    text = text[:len(text)-suffix_len]
    speech = speech[:len(speech)-suffix_len]
    return (prefix, text, speech, suffix)


def span_ruby(alignment):
    if alignment['subalignments']:
        return ''.join(map(span_ruby, alignment['subalignments']))
    text = alignment['span']
    if isinstance(text, str):
        return text
    else:
        text, speech = text['text'], text['speech']
        if text == speech:
            return text
        prefix, text, speech, suffix = text_speech_factors(text, speech)
        sep = ''
        while True:
            left = '['+sep+'['
            middle = '|'+sep+'|'
            right = ']'+sep+']'
            if any(x in y for x in (left, middle, right) for y in (text, speech)):
                sep += '='
                continue
            return ''.join((prefix, left, text, middle, speech, right, suffix))


def unicode_last_base(s):
    """The last character, but ignoring modifiers."""
    return next(c for c in s[::-1] if unicodedata.category(c)[0] != 'M')


def is_standout(paragraph):
    return all(
        unicode_last_base(line).isalnum()
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
