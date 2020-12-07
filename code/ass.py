#!/usr/bin/env python3

import align_json
import argparse
from collections import defaultdict
import json
import math
import subprocess
import sys


def ass_header(language=None, use_template=False):
    styles = defaultdict(
        lambda: {
            "Default": "DejaVu Serif,100",
            "Standout": "Anaktoria,150",
        },
        cmn={
            "Default": "Noto Serif CJK TC,120",
            "Standout": "Noto Serif CJK TC,180",
        },
        cmn_Hans={
            "Default": "Noto Serif CJK SC,120",
            "Standout": "Noto Serif CJK SC,180",
        },
        jpn={
            "Default": "Noto Serif CJK JP,90",
            "Standout": "Noto Serif CJK JP,180",
        },
        yue={
            "Default": "Noto Serif CJK TC,120", # should be HK, but that's only Sans
            "Standout": "Noto Serif CJK TC,180",
        },
    )[language]
    karaoke_template = (
        'Comment: 0,0:00:00.00,0:00:00.00,Default,,0,0,0,template syl furi,{\pos($x,$y)\k!syl.start_time/10!\!syl.tag!$kdur}',
        'Comment: 0,0:00:00.00,0:00:00.00,Standout,,0,0,0,template syl furi,{\pos($x,$y)\k!syl.start_time/10!\!syl.tag!$kdur}',
    ) if use_template else ()
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
        f'Style: Default,{styles["Default"]},&Hffffff,&H888888,&Hffffff,&H0,0,0,0,0,100,100,0,0,1,2,0,4,90,90,90,0',
        f'Style: Standout,{styles["Standout"]},&Hffffff,&H888888,&Hffffff,&H0,0,0,0,0,100,100,0,0,1,3,0,5,90,90,90,0',
        '',
        '[Events]',
        'Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text',
    ) + karaoke_template)


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


def ass_text(alignment, furigana=False):
    text = ''
    if not alignment['subalignments']:
        span_text = align_json.span_text(alignment)
        span_speech = align_json.span_speech(alignment)
        if furigana and span_text != span_speech:
            prefix, span_text, span_speech, suffix = align_json.text_speech_factors(span_text, span_speech)
            total_duration = alignment['end_time']-alignment['start_time']
            total_len = len(prefix+span_speech+suffix)
            start_time = alignment['start_time']
            if prefix:
                end_time = start_time + total_duration * len(prefix) / total_len
                text += ass_karaoke(start_time, end_time, True)
                text += format_ass_text(prefix)
                start_time = end_time
            if span_text or span_speech:
                end_time = start_time + total_duration * len(span_speech) / total_len
                text += ass_karaoke(start_time, end_time, True)
                text += format_ass_text(span_text) + '|<' + span_speech
                start_time = end_time
            if suffix:
                end_time = start_time + total_duration * len(suffix) / total_len
                text += ass_karaoke(start_time, end_time, True)
                text += format_ass_text(suffix)
        else:
            text += ass_karaoke(alignment['start_time'], alignment['end_time'], True)
            text += format_ass_text(span_text)
    else:
        previous_end = alignment['start_time']
        for subalignment in alignment['subalignments']:
            text += ass_karaoke(previous_end, subalignment['start_time'], False)
            text += ass_text(subalignment, furigana=furigana)
            previous_end = subalignment['end_time']
        text += ass_karaoke(previous_end, alignment['end_time'], False)
    return text


def main(argv):
    parser = argparse.ArgumentParser(
        description='ASS file generator')
    parser.add_argument('alignment')
    parser.add_argument('output')
    parser.add_argument('--language', type=str)
    parser.add_argument('--furigana', dest='furigana', action='store_true')
    parser.add_argument('--no-furigana', dest='furigana', action='store_false')
    parser.set_defaults(furigana=False)
    args = parser.parse_args(argv[1:])
    with open(args.alignment) as f: alignments = json.load(f)

    use_template = args.furigana or args.language in {'cmn', 'jpn', 'yue'}

    if args.language == 'cmn' and 'cmn-Hans' in args.output:
        args.language = 'cmn_Hans'

    with open(args.output, 'w') as out:
        print(ass_header(language=args.language, use_template=use_template), file=out)
        for alignment in align_json.vad_pad(alignments):
            style = 'Standout' if align_json.is_standout(alignment) else 'Default'
            print(
                'Dialogue: 0,{},{},{},,0,0,0,,{}'.format(
                    format_ass_time(alignment['start_time']),
                    format_ass_time(alignment['end_time']),
                    style,
                    ass_text(alignment, furigana=args.furigana),
                ),
                file=out
            )
    if use_template:
        print("Press 'Automation' > 'Apply karaoke template'")
        subprocess.run(['aegisub', args.output], check=True)

if __name__ == '__main__':
    main(sys.argv)
