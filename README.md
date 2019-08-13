#  Certificates

Generate event certificates easily.

## Requirements

* Inkscape (`apt install inkscape`)

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install certificates.

```bash
pip install certificates
```

## Usage

`certificates participants.csv template.svg`

```
usage: certificates [-h] [--output OUTPUT] participants template

positional arguments:
  participants          csv filaname containing participants
  template              certificate template in svg format used to build

optional arguments:
  -h, --help            show this help message and exit
  --output OUTPUT, -o OUTPUT
                        destination of the generated certificates
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[Apache 2.0](https://choosealicense.com/licenses/apache-2.0/)
