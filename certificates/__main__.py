import argparse
import sys

from .certificates import make_certificates


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'participants', help='csv filaname containing participants'
    )
    parser.add_argument(
        'template', help='certificate template in svg format used to build'
    )
    parser.add_argument(
        '--output',
        '-o',
        default='./output',
        help='destination of the generated certificates',
    )
    args = parser.parse_args()
    try:
        make_certificates(args.participants, args.template, args.output)
    except KeyError as missing_column:
        sys.exit(
            f'error while formatting certificate: '
            f'csv is missing {missing_column} column.'
        )


if __name__ == '__main__':
    main()
