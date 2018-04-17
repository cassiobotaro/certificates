#!/usr/bin/env python
'''
usage: certificates.py [-h] participants template

positional arguments:
  participants  csv filaname containing participants.
  template      certificate template in svg format used to build.

optional arguments:
  -h, --help    show this help message and exit
'''

import argparse
import csv
import os
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('participants',
                    help='csv filaname containing participants.')
parser.add_argument('template',
                    help='certificate template in svg format used to build.')
args = parser.parse_args()


def import_from_csv(csv_filename):
    with open(csv_filename) as file:
        table = csv.DictReader(file)
        for row in table:
            yield row


# svg used as template
base_svg = Path(args.template)
# retrieve participants list
participants = import_from_csv(args.participants)
# Create output directory if not exists
output_directory = Path('./output')
output_directory.mkdir(exist_ok=True)


for participant in participants:
    locals().update(participant)
    new_svg = base_svg.read_text(encoding='utf-8').format(**locals())
    output_filename = output_directory / f'{name}.svg'
    output_svg = Path(output_filename)
    output_svg.write_text(new_svg)
    png_filename = str(output_filename).replace("svg", "png")
    os.system(f'inkscape -z -e "{png_filename}" "{output_filename}"')
    output_svg.unlink()
