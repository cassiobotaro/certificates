#!/usr/bin/env python
"""
usage: certificates [-h] [--output OUTPUT] participants template

positional arguments:
  participants          csv filaname containing participants
  template              certificate template in svg format used to build

optional arguments:
  -h, --help            show this help message and exit
  --output OUTPUT, -o OUTPUT
                        destination of the generated certificates
"""

import csv
from pathlib import Path

from .inkscape_utils import convert_svg_to_png


def import_from_csv(csv_filename):
    with open(csv_filename) as file:
        table = csv.DictReader(file)
        yield from table


def make_certificates(participants_path, template_path, output_path):
    # svg used as template
    base_svg = Path(template_path)
    # retrieve participants list
    participants = import_from_csv(participants_path)
    # Create output directory if not exists
    output_directory = Path(output_path)
    output_directory.mkdir(exist_ok=True)

    for participant in participants:
        new_svg = base_svg.read_text(encoding='utf-8').format(**participant)
        output_filename = output_directory / f'{participant["name"]}.svg'
        output_svg = Path(output_filename)
        output_svg.write_text(new_svg)
        png_filename = str(output_filename).replace('svg', 'png')
        convert_svg_to_png(output_filename, png_filename)
        output_svg.unlink()
