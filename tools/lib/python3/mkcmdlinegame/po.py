#!/usr/bin/env python3
# encoding: utf-8
# pylint: disable=unexpected-keyword-arg
"""
   po functions
"""
import re
import os
import sys
from os.path import basename, isfile, join, relpath

try:
    if 'NOPOLIB' not in os.environ:
        from polib import pofile
    else:
        def pofile(fpath):
            """ useless """
            print(f"{relpath(fpath)} ignored")
except ImportError:
    print("\nThis script requires polib >= 1.0.0\n\n"
          "To fix this, run: pip install --upgrade polib\n\n"
          "( If you don't need to parse po files,\n"
          "  use NOPOLIB= environment variable )\n")
    sys.exit(1)

from .utils import get_content, onlyfiles, onlydirs, write
from .build_params import DEFAULT_LANGS, po_perimeter

RE_NOPO_JS = r"\s*('?|\"?)nopo\1\s*:\s*\[(('|\")(text|name)\3,?)+\]\s*"
RE_POREF_JS = r"_\(('|\")([A-Za-z-_0-9]*)\1(,\s*\[.*\])?\)"
RE_POREFITEM_JS = r"new(Item|People|Link|Room)\(('|\")([A-Za-z-_0-9]*)\2\)"


class POLines():
    """ store msgid -> msgstr collection for all lang """
    polines = {}

    def add(self, room, rec=False):
        """ add po file content found in directory """
        for fpath in onlyfiles(room, ext='.po', rec=rec):
            lang = lang_from_fname(fpath)
            if lang not in self.polines:
                self.polines[lang] = gen_po_header(lang)
            po_content = get_po_content(fpath)
            if po_content and po_content[0].strip():
                po_content = ['\n'] + po_content
            self.polines[lang] += po_content

    def get(self):
        """ get list of [lang, {msgid -> msgstr}] """
        return list(self.polines.items())

    def missing(self, typ, name):
        """ get missing msgids for a specific element typ_name """
        pofound = []
        prev = ''   # ensure there is a msgid, and msgstr
        conclude = ''
        for _, polines in self.polines.items():
            for line in polines:
                if len(pofound) == 2:
                    break
                if conclude:
                    if line.strip() or prev:
                        if conclude not in pofound:
                            pofound.append(conclude)
                    prev = ''
                    conclude = ''
                elif prev:
                    conclude = prev
                    if line == 'msgstr ""\n':
                        prev = ''
                elif line == f'msgid "{typ}_{name}"\n':
                    prev = 'name'
                elif line == f'msgid "{typ}_{name}_text"\n':
                    prev = 'text'
        nopo = [f"'{a}'" for a in set(['text', 'name']) - set(pofound)]
        return nopo


def _get_po_comment(entry):
    return (
        "#" + "\n# ".join(entry.comment.split('\n')) + ' ' +
        "\n# ".join(entry.tcomment.split('\n'))
    ) if (entry.comment or entry.tcomment) else ""


def _get_first_po_content_line(lines):
    start = 0
    commentback = 0
    for line in lines:
        poline = " ".join(line.split())
        if poline == 'msgid ""':
            commentback = 0
        elif poline.startswith('msgid "'):
            break
        elif poline.startswith('#'):
            commentback += 1
        start += 1

    return start - commentback


def gen_po_header(lang):
    """ return a po header """
    return ['msgid ""\n',
            'msgstr ""\n',
            '"Content-Type: text/plain; charset=UTF-8\\n"\n',
            f'"Language: {lang}\\n"\n']


def get_po_content(fname):
    """ return content, skip po header """
    lines = get_content(fname)
    start = _get_first_po_content_line(lines)
    return lines[start:]


def _find_nopo(src):
    lines = get_content(src)
    matches = []
    for line in lines:
        matches += [a[3] for a in re.findall(RE_NOPO_JS, line)]
    return matches

def _find_explicit_po_references(src):
    lines = get_content(src)
    matches = []
    for line in lines:
        matches += [a[1] for a in re.findall(RE_POREF_JS, line)]
    return matches


def _find_potential_po_references(src):
    lines = get_content(src)
    matches = []
    for line in lines:
        _matches = re.findall(RE_POREFITEM_JS, line)
        matches += [a[0].lower() + '_' + a[2]
                    for a in _matches]
        matches += [a[0].lower() + '_' + a[2] + '_text'
                    for a in _matches]
    return matches


def find_po_references(path):
    """ returns msgids referenced in a room """
    msgids = []
    if not (
            basename(path).startswith('_') or
            isfile(join(path, '.nopo')) or
            isfile(join(path, 'nopo'))
    ):
        room_id = 'room_' + basename(path).replace('hidden:', '')
        msgids += [room_id, room_id + '_text']
    for fpath in onlyfiles(path, ext='.js'):
        nopo = _find_nopo(fpath)
        msgids += _find_explicit_po_references(fpath)
        msgids += _find_potential_po_references(fpath)
        fname = basename(fpath)
        if ':' in fname:
            if '{' in fname:
                pass
            else:
                po_id = fname[:-3].replace(':', '_')
                if 'name' not in nopo:
                    msgids.append(po_id)
                if 'text' not in nopo:
                    msgids.append(po_id + '_text')
    return msgids


def fetch_langs(room):
    """ get all langs that can be found """
    langs = set([])
    for fpath in onlyfiles(room, ext='.po', rec=True):
        langs.add(lang_from_fname(fpath))
    return list(langs) or DEFAULT_LANGS


def po_inject(gamedir, lang, po_source):
    """
        For the current <gamedir>, and all subdirectories :
        Fetch value from poEntry* <po_source>
        for existing msgids in file <lang>.po contained in <gamedir>.
        If a msgid     appears in attributes files,
                   and exists in <po_source>,
                   and not exists in <lang>.po,
                   then it is added.
    """
    if not po_perimeter(gamedir):
        return
    po_refs = find_po_references(gamedir)
    for po_fname in onlyfiles(gamedir, ext=f'{lang}.po'):
        # try:
        po_orig = pofile(po_fname)
        keys = []
        for entry in po_orig:
            keys.append(entry.msgid)
            new_entry = po_source.find(entry.msgid)
            if new_entry and new_entry.msgstr:
                if entry.msgstr != new_entry.msgstr:
                    print(f'{entry.msgid} updated' % entry.msgid)
                    entry.msgstr = new_entry.msgstr

                for attr in ('comment', 'tcomment'):
                    old_comment = getattr(entry, attr)
                    new_comment = getattr(new_entry, attr)
                    if not old_comment and new_comment:
                        print(f'comment added   on {entry.msgid}\n>> {new_comment}')
                        setattr(entry, attr, new_comment)
                    elif old_comment and not new_comment:
                        print(f'comment deleted on {entry.msgid}\n<< {new_comment}')
                        setattr(entry, attr, new_comment)
                    elif old_comment != new_comment:
                        print(f'comment updated on {entry.msgid}\n'
                              f'<< {old_comment}\n>> {new_comment}')
                        setattr(entry, attr, new_comment)

        for msgid in list(set(po_refs) - set(keys)):
            # print(msgid)
            entry_src = po_source.find(msgid)
            if entry_src and entry_src.msgstr:
                print(f'{msgid} added')
                po_orig.append(entry_src)
        po_orig.save()
        # except:
        #     continue

    for subdir in onlydirs(gamedir):
        po_inject(subdir, lang, po_source)


def po_list_msgids(gamedir, langs, with_po_refs=False, rec=False):
    """ list msgids """
    msgids = set([])
    for lang in langs:
        for po_fname in onlyfiles(gamedir, ext=f'{lang}.po', rec=rec):
            po_source = pofile(po_fname)
            msgids |= set(e.msgid for e in po_source)
    if with_po_refs:
        msgids |= set(find_po_references(gamedir))
    ret = list(msgids)
    ret.sort()
    return ret


def po_get(gamedir, lang, msgid, with_file=False):
    """ get po entry in a project directory"""
    for po_fname in onlyfiles(gamedir, ext=f'{lang}.po', rec=True):
        po_source = pofile(po_fname)
        entry = po_source.find(msgid)
        if entry:
            return entry if not with_file else (entry, po_fname)
    return None


def move_po_msgs(room, msgids, langs, tgt=False):
    """
    move po entries for on dir to anothe one
    to call this function with tgt=False is equivalent to call a remove
    """
    for lang in langs:
        fpath = join(room, f'{lang}.po')
        if tgt:
            ftgt = join(tgt, f'{lang}.po')
            if not isfile(ftgt):
                write(ftgt, gen_po_header(lang) + ["\n"])

        entries = pofile(fpath)
        if tgt:
            entriestgt = pofile(ftgt)
        for entry in [entries.find(i)
                      for i in msgids
                      if entries.find(i)]:
            if tgt:
                print(f'move {entry.msgid} to {relpath(ftgt)}')
                entriestgt.append(entry)
            else:
                print(f'remove {entry.msgid} from {relpath(fpath)}')
            entries.remove(entry)
        if tgt:
            entriestgt.save()
        entries.save()


def get_msgid_dbls(gamedir, langs):
    """ list doubles entries """
    occur = {}
    for fpath in onlyfiles(gamedir, ext='.po', rec=True):
        lang = lang_from_fname(fpath)
        if lang not in langs:
            continue
        entries = pofile(fpath)
        if lang not in occur:
            occur[lang] = {}
            for entry in entries:
                if entry.msgid in occur[lang]:
                    occur[lang][entry.msgid].append(relpath(fpath))
                else:
                    occur[lang][entry.msgid] = [relpath(fpath)]
    for lang in langs:
        for msgid in [i for i in occur[lang].keys()
                      if len(occur[lang][i]) == 1]:
            del occur[lang][msgid]
    return occur


def lang_from_fname(fname):
    """ get lang of the po file """
    return re.match(
        r"(.*\.)?([a-z_A-Z]{2,5}).(po|js)$",
        basename(fname)).group(2)


def po2json(orig):
    """ convert po entries in js format """
    lines = []
    entries = pofile(orig)
    if not entries:
        return lines
    lines += [
        "// generated from po file\n",
        "var dialog={"
    ]
    for entry in entries:
        if not entry.msgstr:
            continue
        if len(entry.msgid.split("\n")) > 2:
            msgid = '"' + entry.msgid.replace('"', '\"') + '"'
        else:
            msgid = entry.msgid.replace("\n", "")
            if " " in msgid:
                msgid = '"' + msgid.replace('"', '\\"') + '"'
        msgstr = entry.msgstr.replace(
            '\\', '\\\\').replace(
                '\\"', '\\\\"').replace(
                    "\n", "\\n").replace(
                        '"', '\\"')
        lines.append(str(f'{msgid}:"{msgstr}",\n'))
    lines.append("};\n")
    return lines
