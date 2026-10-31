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
from pathlib import Path
from xml.sax.saxutils import escape

from .inkscape_utils import Inkscape

# Besides &, < and >, also escape quotes so values are safe inside
# attributes (e.g. <text aria-label="{name}">), not only in text nodes.
_XML_QUOTE_ENTITIES = {'"': '&quot;', "'": '&apos;'}


def import_from_csv(csv_filename):
    with open(csv_filename) as file:
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
    output_directory.mkdir(exist_ok=True)

    for participant in participants:
        new_svg = base_svg.read_text(encoding='utf-8').format(
            **_xml_escape_values(participant)
        )
        output_filename = output_directory / f'{participant["name"]}.svg'
        output_svg = Path(output_filename)
        output_svg.write_text(new_svg, encoding='utf-8')
        png_filename = output_filename.with_suffix('.png')
        converter.export_png(output_filename, png_filename)
        output_svg.unlink()
