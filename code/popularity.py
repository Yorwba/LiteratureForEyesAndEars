#!/usr/bin/env python3

import csv
from collections import defaultdict
import librivox_json


def table_to_dicts(table):
    header = table[0]
    return [
        {k: v for k, v in zip(header, row)}
        for row in table[2:]
    ]


def lang(row):
    return row['Video title'].split('|')[1].split(' audiobook')[0].strip()


def stats_per_language(dicts, keys):
    stats = {k: defaultdict(float) for k in keys}
    for row in dicts:
        for k in keys:
            stats[k][lang(row)] += float(row[k] or 0)
    return stats


def stats_per_video_in_language(language, dicts, keys):
    stats = {k: defaultdict(float) for k in keys}
    for row in dicts:
        if lang(row) != language: continue
        for k in keys:
            stats[k][row['Video title']] += float(row[k] or 0)
    return stats


def ranking(stats):
    for k, s in stats.items():
        print('Top by '+k)
        for l, t in sorted(s.items(), key=lambda lt: -lt[1]):
            print(l, t)
        print()


def playtime_per_youtube_id(books):
    playtime = defaultdict(int)
    for book in books:
        book_youtube_id = book.get('youtube_id', None)
        for section in book['sections']:
            section_youtube_id = section.get('youtube_id', None)
            youtube_id = book_youtube_id or section_youtube_id
            if isinstance(youtube_id, list):
                for y in youtube_id:
                    playtime[y] += int(section['playtime'])
            elif isinstance(youtube_id, str):
                playtime[youtube_id] += int(section['playtime'])
    return dict(playtime)


def add_playtime_to_dicts(dicts, playtime):
    for d in dicts:
        if 'Video' in d:
            video = d['Video']
        else:
            video = d['Content']
        d['Available time (hours)'] = playtime[video.strip()] / (60. * 60.)


def bottom_line(stats):
    print('Watched by watched ratio, with watch time, available time, number of likes and subscribes:')
    langs = [l for l, t in stats['Watch time (hours)'].items()]
    for l in sorted(langs, key=lambda l: -stats['Watch ratio'][l]):
        print(l, f"{stats['Watch ratio'][l]:.02}", f"{stats['Watch time (hours)'][l]:.02}", f"{stats['Available time (hours)'][l]:.02}", int(stats['Likes'][l]), int(stats['Subscribers'][l]))
    print()


def main(argv):
    with open(argv[2]) as f: table = list(csv.reader(f))
    dicts = table_to_dicts(table)
    add_playtime_to_dicts(
        dicts,
        playtime_per_youtube_id(librivox_json.get_all_books(argv[1]))
    )
    if len(argv) > 3:
        stats = stats_per_video_in_language(argv[3], dicts, ['Watch time (hours)', 'Available time (hours)', 'Likes', 'Subscribers', 'Views', 'Impressions'])
    else:
        stats = stats_per_language(dicts, ['Watch time (hours)', 'Available time (hours)', 'Likes', 'Subscribers', 'Views', 'Impressions'])
    stats['Watch ratio'] = {
        l:  stats['Watch time (hours)'][l] / stats['Available time (hours)'][l]
        for l in stats['Watch time (hours)']
    }
    ranking(stats)
    bottom_line(stats)
    print('Available stats: '+', '.join(table[0]))


if __name__ == '__main__':
    import sys;
    main(sys.argv)
