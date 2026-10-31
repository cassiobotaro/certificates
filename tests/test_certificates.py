"""Test for certificates module.

Tests the following functionality:
- Correct generation of SVG files from participant data
- PNG conversion works properly
- Participant name is used as the filename
- PNG images are created in the output directory
- SVG files are deleted after PNG generation
"""

import csv
import subprocess
from pathlib import Path
from xml.etree import ElementTree

import pytest

from certificates import inkscape_utils
from certificates.builder import (
    _safe_filename,
    import_from_csv,
    make_certificates,
)
from certificates.inkscape_utils import Inkscape


class FakeConverter:
    """Stand-in for Inkscape: creates an empty PNG and records the calls.

    The SVG content is captured at export time because make_certificates
    deletes the intermediate SVG right after converting it.
    """

    def __init__(self):
        self.calls = []
        self.svgs = {}

    def export_png(self, svg_path, png_path):
        self.calls.append((Path(svg_path), Path(png_path)))
        self.svgs[Path(png_path).name] = Path(svg_path).read_text(
            encoding='utf-8'
        )
        Path(png_path).touch()


@pytest.fixture
def fake_converter():
    return FakeConverter()


def _write_csv(path, rows):
    """Write `rows` (dicts sharing the same keys) to `path` as CSV."""
    with path.open('w', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return path


@pytest.fixture
def csv_file(tmp_path):
    """CSV file with two participants"""
    return _write_csv(
        tmp_path / 'participants.csv',
        [
            {'name': 'John Doe', 'course': 'Python Programming'},
            {'name': 'Jane Smith', 'course': 'Data Science'},
        ],
    )


@pytest.fixture
def svg_template(tmp_path):
    """SVG template using the `name` and `course` columns"""
    template = tmp_path / 'template.svg'
    template.write_text(
        """
    <svg xmlns="http://www.w3.org/2000/svg" width="800" height="600">
        <text x="50" y="50">Name: {name}</text>
        <text x="50" y="100">Course: {course}</text>
    </svg>
    """,
        encoding='utf-8',
    )
    return template


@pytest.fixture
def output_dir(tmp_path):
    """Output directory path; make_certificates is expected to create it"""
    return tmp_path / 'output'


def test_import_from_csv(csv_file):
    """Test that import_from_csv correctly reads CSV data"""
    participants = list(import_from_csv(csv_file))

    assert participants == [
        {'name': 'John Doe', 'course': 'Python Programming'},
        {'name': 'Jane Smith', 'course': 'Data Science'},
    ]


def test_make_certificates(fake_converter, csv_file, svg_template, output_dir):
    """Test that make_certificates generates SVG and PNG files correctly"""
    make_certificates(
        csv_file, svg_template, output_dir, converter=fake_converter
    )

    assert sorted(p.name for p in output_dir.iterdir()) == [
        'Jane Smith.png',
        'John Doe.png',
    ]


def test_make_certificates_handles_special_chars(
    fake_converter, svg_template, output_dir, tmp_path
):
    """Test that make_certificates handles special characters"""
    csv_path = _write_csv(
        tmp_path / 'p.csv',
        [{'name': 'José García', 'course': 'Python & Data <2026> "A\'s"'}],
    )

    make_certificates(
        csv_path, svg_template, output_dir, converter=fake_converter
    )

    # Check that PNG file was created with the special character name
    assert (output_dir / 'José García.png').exists()

    # The generated SVG must be well-formed XML and, once parsed, carry the
    # original (unescaped) values
    root = ElementTree.fromstring(fake_converter.svgs['José García.png'])
    texts = [
        node.text for node in root.iter('{http://www.w3.org/2000/svg}text')
    ]
    assert texts == [
        'Name: José García',
        'Course: Python & Data <2026> "A\'s"',
    ]


def test_make_certificates_removes_svg(
    fake_converter, csv_file, svg_template, output_dir
):
    """Test that SVG intermediate files are deleted after PNG generation"""
    make_certificates(
        csv_file, svg_template, output_dir, converter=fake_converter
    )

    svg_files = list(output_dir.glob('*.svg'))
    assert svg_files == [], f'SVG files should be deleted: {svg_files}'


def test_make_certificates_missing_column(
    fake_converter, svg_template, output_dir, tmp_path
):
    """Test that make_certificates raises KeyError for missing CSV column"""
    csv_path = _write_csv(tmp_path / 'p.csv', [{'name': 'John Doe'}])

    with pytest.raises(KeyError):
        make_certificates(
            csv_path, svg_template, output_dir, converter=fake_converter
        )


def _fake_inkscape(monkeypatch, version_stdout):
    """Make `inkscape --version` return `version_stdout`; record all calls."""
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        if cmd[:2] == ['inkscape', '--version']:
            return subprocess.CompletedProcess(cmd, 0, stdout=version_stdout)
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(inkscape_utils.subprocess, 'run', fake_run)
    return calls


def test_make_certificates_detects_inkscape_once(
    monkeypatch, csv_file, svg_template, output_dir
):
    """Test that `inkscape --version` runs once, not once per participant"""
    calls = _fake_inkscape(monkeypatch, 'Inkscape 1.2.2 (x, y)\n')

    make_certificates(csv_file, svg_template, output_dir)

    version_calls = [c for c in calls if c[:2] == ['inkscape', '--version']]
    export_calls = [c for c in calls if '--export-type=png' in c]
    assert len(version_calls) == 1
    assert len(export_calls) == 2


def test_detect_inkscape_not_installed(monkeypatch):
    """Test that a missing Inkscape binary raises a friendly RuntimeError"""

    def fake_run(*args, **kwargs):
        raise FileNotFoundError(2, 'No such file or directory', 'inkscape')

    monkeypatch.setattr(inkscape_utils.subprocess, 'run', fake_run)

    with pytest.raises(RuntimeError, match='Make sure Inkscape is installed'):
        Inkscape.detect()


@pytest.mark.parametrize(
    ('stdout', 'expected'),
    [
        ('Inkscape 1.2.2 (732a01da63, 2022-12-09)\n', (1, 2)),
        ('Inkscape 1.4.3 (0d15f75042, 2025-12-25)\n', (1, 4)),
        ('Inkscape 0.92.4 (5da689c313, 2019-01-14)\n', (0, 92)),
        ('Inkscape 1.10 (abc, 2030-01-01)\n', (1, 10)),
        ('Inkscape 1.0 (4035a4fb49, 2020-05-01)\n', (1, 0)),
    ],
)
def test_detect_inkscape_version(monkeypatch, stdout, expected):
    """Test that the Inkscape version is parsed as a (major, minor) tuple"""
    _fake_inkscape(monkeypatch, stdout)

    assert Inkscape.detect().version == expected


@pytest.mark.parametrize('stdout', ['', 'garbage output\n'])
def test_detect_inkscape_unexpected_output(monkeypatch, stdout):
    """Test that unparseable `--version` output raises RuntimeError"""
    _fake_inkscape(monkeypatch, stdout)

    with pytest.raises(RuntimeError, match='Unexpected output'):
        Inkscape.detect()


def test_detect_inkscape_version_orders_correctly(monkeypatch):
    """Test that 1.10 is considered newer than 1.2 (float would say older)"""
    _fake_inkscape(monkeypatch, 'Inkscape 1.10 (abc, 2030-01-01)\n')

    assert Inkscape.detect().version > (1, 2)


def test_export_png_modern_cli(monkeypatch):
    """Test that Inkscape >= 1.0 uses the --export-* syntax"""
    calls = _fake_inkscape(monkeypatch, '')

    Inkscape((1, 2)).export_png('in.svg', 'out.png', width=1024)

    assert calls == [
        [
            'inkscape',
            'in.svg',
            '--export-type=png',
            '--export-filename=out.png',
            '--export-width=1024',
        ]
    ]


def test_export_png_legacy_cli(monkeypatch):
    """Test that Inkscape < 1.0 uses the -z -e legacy syntax"""
    calls = _fake_inkscape(monkeypatch, '')

    Inkscape((0, 92)).export_png('in.svg', 'out.png', width=1024)

    assert calls == [
        ['inkscape', '-z', '-e', 'out.png', '-w', '1024', 'in.svg']
    ]


def test_export_png_failure(monkeypatch):
    """Test that a failing export is reported as RuntimeError"""

    def fake_run(cmd, **kwargs):
        raise subprocess.CalledProcessError(1, cmd)

    monkeypatch.setattr(inkscape_utils.subprocess, 'run', fake_run)

    with pytest.raises(RuntimeError, match='Inkscape command failed'):
        Inkscape((1, 2)).export_png('in.svg', 'out.png')


def test_import_from_csv_multiline_field(tmp_path):
    """Test that quoted fields with embedded newlines are read intact"""
    csv_path = tmp_path / 'participants.csv'
    csv_path.write_text(
        'name,course\r\n"John Doe","Python\r\nProgramming"\r\n',
        encoding='utf-8',
    )

    participants = list(import_from_csv(csv_path))

    assert participants == [
        {'name': 'John Doe', 'course': 'Python\r\nProgramming'}
    ]


def test_make_certificates_creates_nested_output_dir(
    fake_converter, csv_file, svg_template, tmp_path
):
    """Test that a nested, non-existent output path is created"""
    output_dir = tmp_path / 'events' / '2026' / 'certificates'

    make_certificates(
        csv_file, svg_template, output_dir, converter=fake_converter
    )

    assert (output_dir / 'John Doe.png').exists()


@pytest.mark.parametrize(
    ('name', 'expected'),
    [
        ('John Doe', 'John Doe'),
        ('José García', 'José García'),
        ('a/b\\c:d*e?f"g<h>i|j', 'a_b_c_d_e_f_g_h_i_j'),
        ('tab\there', 'tab_here'),
        ('  padded.  ', 'padded'),
        ('', 'participant'),
        ('...', 'participant'),
    ],
)
def test_safe_filename(name, expected):
    """Test that unsafe chars are replaced and empty names get a default"""
    assert _safe_filename(name) == expected


def test_make_certificates_name_with_slash(
    fake_converter, svg_template, tmp_path
):
    """Test that a '/' in the name does not create a subdirectory"""
    csv_path = _write_csv(
        tmp_path / 'p.csv', [{'name': 'Ana/Maria', 'course': 'Python'}]
    )
    output_dir = tmp_path / 'out'

    make_certificates(
        csv_path, svg_template, output_dir, converter=fake_converter
    )

    assert sorted(p.name for p in output_dir.iterdir()) == ['Ana_Maria.png']
    # the SVG content still carries the original name
    assert 'Name: Ana/Maria' in fake_converter.svgs['Ana_Maria.png']


def test_make_certificates_duplicate_names(
    fake_converter, svg_template, tmp_path, capsys
):
    """Test that repeated names get a numeric suffix instead of overwriting"""
    csv_path = _write_csv(
        tmp_path / 'p.csv',
        [
            {'name': name, 'course': 'Python'}
            for name in ['João Silva', 'João Silva', 'João Silva (2)']
        ],
    )
    output_dir = tmp_path / 'out'

    make_certificates(
        csv_path, svg_template, output_dir, converter=fake_converter
    )

    assert sorted(p.name for p in output_dir.iterdir()) == [
        'João Silva (2) (2).png',
        'João Silva (2).png',
        'João Silva.png',
    ]
    assert len(fake_converter.calls) == 3
    assert 'warning: duplicate name' in capsys.readouterr().out
