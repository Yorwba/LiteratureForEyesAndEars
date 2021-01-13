#!/usr/bin/env python3

import csv
from collections import defaultdict


def table_to_dicts(table):
    header = table[0]
    return [
        {k: v for k, v in zip(header, row)}
        for row in table[1:]
    ]


def lang(row):
    return row['Video title'].split('|')[1].split(' audiobook')[0].strip()


def stats_per_language(dicts, keys):
    stats = {k: defaultdict(float) for k in keys}
    for row in dicts[1:]:
        for k in keys:
            stats[k][lang(row)] += float(row[k])
    return stats


def ranking(stats):
    for k, s in stats.items():
        print('Top languages by '+k)
        for l, t in sorted(s.items(), key=lambda lt: -lt[1]):
            print(l, t)
        print()


def bottom_line(stats):
    print('Languages watched for more than 15 mins, by number of likes + subscribes:')
    langs = [l for l, t in stats['Watch time (hours)'].items() if t > 15./60.]
    for l in sorted(langs, key=lambda l: -(stats['Likes'][l] + stats['Subscribers'][l])):
        print(l)
    print()


def main(argv):
    with open(argv[1]) as f: table = list(csv.reader(f))
    dicts = table_to_dicts(table)
    stats = stats_per_language(dicts, ['Watch time (hours)', 'Likes', 'Subscribers', 'Views', 'Impressions'])
    ranking(stats)
    bottom_line(stats)
    print('Available stats: '+', '.join(table[0]))


if __name__ == '__main__':
    import sys;
    main(sys.argv)
