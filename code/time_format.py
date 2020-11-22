#!/usr/bin/env python3


def time_to_seconds(time):
    parts = time.split(':')[::-1]
    factors = [60, 60, 24]
    unit = 1
    seconds = 0
    for part, factor in zip(parts, factors):
        seconds += unit * float(part)
        unit *= factor
    return seconds


def seconds_to_time(seconds):
    factors = [60, 60, 24]
    parts = []
    left = seconds
    for factor in factors:
        parts.append('{:02}'.format(left % factor))
        left //= factor
    if left:
        parts.append(str(left))
    return ':'.join(parts[::-1])
