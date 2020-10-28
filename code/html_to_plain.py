#!/usr/bin/env python3

import html.parser


class HtmlToPlain(html.parser.HTMLParser):
    def __init__(self):
        super(HtmlToPlain, self).__init__()
        self.chunks = []

    def handle_data(self, data):
        self.chunks.append(data)

    def text(self):
        return ''.join(self.chunks)


def html_to_plain_text(html):
    html_to_plain = HtmlToPlain()
    html_to_plain.feed(html)
    html_to_plain.close()
    return html_to_plain.text()
