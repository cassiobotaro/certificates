#!/usr/bin/env python
"""
usage: certificates [-h] [--output OUTPUT] participants template

positional arguments:
  participants          csv filename containing participants
  template              certificate template in svg format used to build

optional arguments:
  -h, --help            show this help message and exit
  --output OUTPUT, -o OUTPUT
                        destination of the generated certificates
"""

import csv
import re
from pathlib import Path
from xml.sax.saxutils import escape

from .inkscape_utils import Inkscape

# Besides &, < and >, also escape quotes so values are safe inside
# attributes (e.g. <text aria-label="{name}">), not only in text nodes.
_XML_QUOTE_ENTITIES = {'"': '&quot;', "'": '&apos;'}

# Characters forbidden in file names on Windows (a superset of POSIX's),
# plus ASCII control characters.
_UNSAFE_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|\x00-\x1f]')


def _safe_filename(name):
    """Turn a participant name into a name usable as a file stem."""
    safe = _UNSAFE_FILENAME_CHARS.sub('_', name).strip(' .')
    return safe or 'participant'


def _unique_stem(name, used):
    """Return a file stem for `name` not yet in `used`, and record it.

    Repeated names get a ' (2)', ' (3)', ... suffix instead of silently
    overwriting the previous participant's certificate.
    """
    base = stem = _safe_filename(name)
    counter = 1
    while stem in used:
        counter += 1
        stem = f'{base} ({counter})'
    used.add(stem)
    if stem != base:
        print(f'warning: duplicate name {name!r}, saving as {stem!r}')
    return stem


def import_from_csv(csv_filename):
    with open(csv_filename, encoding='utf-8', newline='') as file:
        table = csv.DictReader(file)
        yield from table


def _xml_escape_values(row):
    """Escape every value of a CSV row so it can be placed inside an SVG."""
    return {
        key: escape(value, _XML_QUOTE_ENTITIES) for key, value in row.items()
    }


def make_certificates(
    participants_path, template_path, output_path, converter=None
):
    """Generate one PNG certificate per participant.

    `converter` is any object with an `export_png(svg, png)` method;
    by default the installed Inkscape is detected once and reused.
    """
    if converter is None:
        converter = Inkscape.detect()
    # svg used as template
    base_svg = Path(template_path)
    # retrieve participants list
    participants = import_from_csv(participants_path)
    # Create output directory if not exists
    output_directory = Path(output_path)
    output_directory.mkdir(parents=True, exist_ok=True)

    used_stems = set()
    for participant in participants:
        new_svg = base_svg.read_text(encoding='utf-8').format(
            **_xml_escape_values(participant)
        )
        stem = _unique_stem(participant['name'], used_stems)
        output_svg = output_directory / f'{stem}.svg'
        output_svg.write_text(new_svg, encoding='utf-8')
        png_filename = output_svg.with_suffix('.png')
        converter.export_png(output_svg, png_filename)
        output_svg.unlink()
