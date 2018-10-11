import argparse
from .certificates import make_certificates

parser = argparse.ArgumentParser()
parser.add_argument('participants',
                    help='csv filaname containing participants.')
parser.add_argument('template',
                    help='certificate template in svg format used to build.')
args = parser.parse_args()


def main():
    make_certificates(args)
