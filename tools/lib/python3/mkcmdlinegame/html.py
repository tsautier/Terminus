#!/usr/bin/env python3
# encoding: utf-8
"""
HTML tools :
 - to extract infos from html files
 - to produce html file
"""
from html.parser import HTMLParser
from os.path import isfile, join, dirname, realpath
import re
from .utils import get_content
from .logging import print_err, print_info


class HTMLParserExtracter(HTMLParser):
    """ parse html to get related js and css files """
    list_src = []
    list_css = []

    def error(self, message):
        """ print error """
        print(str(message))

    def handle_starttag(self, tag, attrs):
        """ handle tag start """
        if tag == 'script':
            self.list_src += [val for (key, val) in attrs if key == 'src']
        elif tag == 'link':
            self.list_css += [val for (key, val) in attrs
                              if key == 'href' and val.endswith('.css')]


def _fetch_in_html(htmlfile, encoding):
    if isfile(htmlfile):
        with open(htmlfile, "r", encoding=encoding) as buf:
            ret = "\n".join(buf.readlines())
            parser = HTMLParserExtracter()
            parser.feed(ret)
            return parser
    else:
        print_err(f"{htmlfile} not found")
    return None


def fetch_javascript_src(htmlfile, encoding="utf-8"):
    """ get list of path of js files referenced in html file """
    parser = _fetch_in_html(htmlfile, encoding)
    if parser:
        path = dirname(realpath(htmlfile))
        return [join(path, fpath) for fpath in parser.list_src]
    return []


def fetch_css_src(htmlfile, encoding="utf-8"):
    """ get list of path of css files referenced in html file """
    parser = _fetch_in_html(htmlfile, encoding)
    if parser:
        path = dirname(realpath(htmlfile))
        return [join(path, fpath) for fpath in parser.list_css]
    return []


def inject(htmlfile, cssfile, jsfile, targetfile, encoding="utf-8"):
    """ put js and css content in html file """
    print_info("%14s > %s", 'Inject all in html', targetfile)

    js_injected = False
    css_injected = False

    css_txt = "<style>%s</style>" % get_content(cssfile, join_sep="\n")
    js_txt = "<script>%s</script>" % get_content(jsfile, join_sep="\n")
    html_lines = get_content(htmlfile)

    with open(targetfile, "w", encoding=encoding) as buf:
        lines = [line.strip() for line in html_lines
                 if not re.match(r"\s*<!--.*-->\s*", line)]
        for line in lines:
            if re.match(r"<script.*src=.*</script>", line):
                if not js_injected:
                    buf.write(js_txt)
                    js_injected = True
            elif re.match(r"<link.*rel=\"stylesheet\".*/>", line):
                if not css_injected:
                    buf.write(css_txt)
                    css_injected = True
            else:
                buf.write(line)
