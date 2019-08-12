import argparse
from .certificates import make_certificates


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "participants", help="csv filaname containing participants"
    )
    parser.add_argument(
        "template", help="certificate template in svg format used to build"
    )
    parser.add_argument(
        "--output",
        "-o",
        default="./output",
        help="destination of the generated certificates",
    )
    args = parser.parse_args()
    make_certificates(args)


if __name__ == "__main__":
    main()
