#!/usr/bin/env python3

import align_json
import json
import math
import sys


def ass_header():
    return '\n'.join((
        '[Script Info]',
        '; Script generated by Literature for Eyes and Ears',
        'PlayResX: 1920',
        'PlayResY: 1080',
        'ScriptType: v4.00+',
        'WrapStyle: 1',
        '',
        '[V4+ Styles]',
        'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding',
        'Style: Default,DejaVu Serif,60,&Hffffff,&H888888,&Hffffff,&H0,0,0,0,0,100,100,0,0,1,2,0,4,90,90,90,0',
        'Style: Standout,Anaktoria,120,&Hffffff,&H888888,&Hffffff,&H0,0,0,0,0,100,100,0,0,1,3,0,5,90,90,90,0',
        '',
        '[Events]',
        'Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text',
    ))


def format_ass_time(time):
    centis = round(time * 100.)
    seconds = centis // 100
    minutes = seconds // 60
    hours = minutes // 60
    return "{}:{:02}:{:02}.{:02}".format(
        hours, minutes % 60, seconds % 60, centis % 100
    )


def ass_karaoke(start, end, sweep):
    start_centis = round(start * 100.)
    end_centis = round(end * 100.)
    delta_centis = end_centis - start_centis
    if delta_centis == 0 and not sweep:
        return ""
    elif (delta_centis == 0 and sweep) or not sweep: # \K0 seems to be buggy
        return "{{\\k{}}}".format(delta_centis)
    else:
        return "{{\\K{}}}".format(delta_centis)


def format_ass_text(text):
    return (
        text.replace("\\", "＼")
            .replace( "{", "｛")
            .replace( "}", "｝")
            .replace("\n", "\\N")
    )


def ass_text(alignment):
    text = ''
    if not alignment['subalignments']:
        text += ass_karaoke(alignment['start_time'], alignment['end_time'], True)
        text += format_ass_text(align_json.span_text(alignment))
    else:
        previous_end = alignment['start_time']
        for subalignment in alignment['subalignments']:
            text += ass_karaoke(previous_end, subalignment['start_time'], False)
            text += ass_text(subalignment)
            previous_end = subalignment['end_time']
        text += ass_karaoke(previous_end, alignment['end_time'], False)
    return text


if __name__ == '__main__':
    with open(sys.argv[1]) as f: alignments = json.load(f)

    print(ass_header())
    for alignment in align_json.vad_pad(alignments):
        style = 'Standout' if align_json.is_standout(alignment) else 'Default'
        print('Dialogue: 0,{},{},{},,0,0,0,,{}'.format(
            format_ass_time(alignment['start_time']),
            format_ass_time(alignment['end_time']),
            style,
            ass_text(alignment),
        ))
