"""Test for certificates module.

Tests the following functionality:
- Correct generation of SVG files from participant data
- PNG conversion works properly
- Participant name is used as the filename
- PNG images are created in the output directory
- SVG files are deleted after PNG generation
"""

import csv
import os
import subprocess
import tempfile
from pathlib import Path

import pytest

from certificates import inkscape_utils
from certificates.builder import import_from_csv, make_certificates


@pytest.fixture
def temp_csv_file():
    """Create a temporary CSV file with test participant data"""
    with tempfile.NamedTemporaryFile(
        suffix='.csv', delete=False, mode='w', newline=''
    ) as temp_file:
        writer = csv.DictWriter(temp_file, fieldnames=['name', 'course'])
        writer.writeheader()
        writer.writerow({'name': 'John Doe', 'course': 'Python Programming'})
        writer.writerow({'name': 'Jane Smith', 'course': 'Data Science'})
        csv_path = temp_file.name

    yield csv_path

    # Cleanup after test
    if os.path.exists(csv_path):
        os.remove(csv_path)


@pytest.fixture
def temp_svg_template():
    """Create a temporary SVG template for testing"""
    template_content = """
    <svg xmlns="http://www.w3.org/2000/svg" width="800" height="600">
        <text x="50" y="50">Name: {name}</text>
        <text x="50" y="100">Course: {course}</text>
    </svg>
    """

    with tempfile.NamedTemporaryFile(
        suffix='.svg', delete=False, mode='w'
    ) as temp_file:
        temp_file.write(template_content)
        template_path = temp_file.name

    yield template_path

    # Cleanup after test
    if os.path.exists(template_path):
        os.remove(template_path)


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for certificate output"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


def test_import_from_csv(temp_csv_file):
    """Test that import_from_csv correctly reads CSV data"""
    participants = list(import_from_csv(temp_csv_file))

    assert len(participants) == 2
    assert participants[0]['name'] == 'John Doe'
    assert participants[0]['course'] == 'Python Programming'
    assert participants[1]['name'] == 'Jane Smith'
    assert participants[1]['course'] == 'Data Science'


def test_make_certificates(
    monkeypatch, temp_csv_file, temp_svg_template, temp_output_dir
):
    """Test that make_certificates generates SVG and PNG files correctly"""

    # Mock the convert_svg_to_png function to avoid actual Inkscape dependency
    def mock_convert(svg_path, png_path):
        # Just create an empty file to simulate PNG creation
        Path(png_path).touch()

    monkeypatch.setattr(
        'certificates.builder.convert_svg_to_png', mock_convert
    )

    # Run the function to test
    make_certificates(temp_csv_file, temp_svg_template, temp_output_dir)

    # Check that PNG files were created for each participant
    expected_files = ['John Doe.png', 'Jane Smith.png']

    for filename in expected_files:
        assert os.path.exists(os.path.join(temp_output_dir, filename))


def test_make_certificates_handles_special_chars(
    monkeypatch, temp_svg_template, temp_output_dir
):
    """Test that make_certificates handles special characters"""
    # Create a CSV with special characters
    with tempfile.NamedTemporaryFile(
        suffix='.csv', delete=False, mode='w', newline=''
    ) as temp_file:
        writer = csv.DictWriter(temp_file, fieldnames=['name', 'course'])
        writer.writeheader()
        writer.writerow({'name': 'José García', 'course': 'Python & Data'})
        csv_path = temp_file.name

    # Mock the convert_svg_to_png function
    def mock_convert(svg_path, png_path):
        Path(png_path).touch()

    monkeypatch.setattr(
        'certificates.builder.convert_svg_to_png', mock_convert
    )

    # Run the function to test
    make_certificates(csv_path, temp_svg_template, temp_output_dir)

    # Check that PNG file was created with the special character name
    assert os.path.exists(os.path.join(temp_output_dir, 'José García.png'))

    # Cleanup
    os.remove(csv_path)


def test_make_certificates_removes_svg(
    monkeypatch, temp_csv_file, temp_svg_template, temp_output_dir
):
    """Test that SVG intermediate files are deleted after PNG generation"""

    def mock_convert(svg_path, png_path):
        Path(png_path).touch()

    monkeypatch.setattr(
        'certificates.builder.convert_svg_to_png', mock_convert
    )

    make_certificates(temp_csv_file, temp_svg_template, temp_output_dir)

    svg_files = list(Path(temp_output_dir).glob('*.svg'))
    assert svg_files == [], f'SVG files should be deleted: {svg_files}'


def test_make_certificates_missing_column(
    monkeypatch, temp_svg_template, temp_output_dir
):
    """Test that make_certificates raises KeyError for missing CSV column"""
    with tempfile.NamedTemporaryFile(
        suffix='.csv', delete=False, mode='w', newline=''
    ) as temp_file:
        writer = csv.DictWriter(temp_file, fieldnames=['name'])
        writer.writeheader()
        writer.writerow({'name': 'John Doe'})
        csv_path = temp_file.name

    def mock_convert(svg_path, png_path):
        Path(png_path).touch()

    monkeypatch.setattr(
        'certificates.builder.convert_svg_to_png', mock_convert
    )

    with pytest.raises(KeyError):
        make_certificates(csv_path, temp_svg_template, temp_output_dir)

    os.remove(csv_path)


def test_convert_svg_to_png_inkscape_not_installed(monkeypatch, tmp_path):
    """Test that a missing Inkscape binary raises a friendly RuntimeError"""

    def fake_run(*args, **kwargs):
        raise FileNotFoundError(2, 'No such file or directory', 'inkscape')

    monkeypatch.setattr(inkscape_utils.subprocess, 'run', fake_run)

    with pytest.raises(RuntimeError, match='Make sure Inkscape is installed'):
        inkscape_utils.convert_svg_to_png(
            tmp_path / 'in.svg', tmp_path / 'out.png'
        )


def _fake_inkscape_version(monkeypatch, stdout):
    """Make `inkscape --version` return `stdout`; record other commands."""
    calls = []

    def fake_run(cmd, **kwargs):
        if cmd[:2] == ['inkscape', '--version']:
            return subprocess.CompletedProcess(cmd, 0, stdout=stdout)
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(inkscape_utils.subprocess, 'run', fake_run)
    return calls


@pytest.mark.parametrize(
    ('stdout', 'expected'),
    [
        ('Inkscape 1.2.2 (732a01da63, 2022-12-09)\n', (1, 2)),
        ('Inkscape 1.4.3 (0d15f75042, 2025-12-25)\n', (1, 4)),
        ('Inkscape 0.92.4 (5da689c313, 2019-01-14)\n', (0, 92)),
        ('Inkscape 1.10 (abc, 2030-01-01)\n', (1, 10)),
        ('Inkscape 1.0 (4035a4fb49, 2020-05-01)\n', (1, 0)),
        ('', None),
        ('garbage output\n', None),
    ],
)
def test_get_inkscape_version(monkeypatch, stdout, expected):
    """Test that the Inkscape version is parsed as a (major, minor) tuple"""
    _fake_inkscape_version(monkeypatch, stdout)

    assert inkscape_utils._get_inkscape_version() == expected


def test_get_inkscape_version_orders_correctly(monkeypatch):
    """Test that 1.10 is considered newer than 1.2 (float would say older)"""
    _fake_inkscape_version(monkeypatch, 'Inkscape 1.10 (abc, 2030-01-01)\n')

    assert inkscape_utils._get_inkscape_version() > (1, 2)


def test_convert_svg_to_png_modern_cli(monkeypatch):
    """Test that Inkscape >= 1.0 uses the --export-* syntax"""
    calls = _fake_inkscape_version(monkeypatch, 'Inkscape 1.2.2 (x, y)\n')

    inkscape_utils.convert_svg_to_png('in.svg', 'out.png', width=1024)

    assert calls == [
        [
            'inkscape',
            'in.svg',
            '--export-type=png',
            '--export-filename=out.png',
            '--export-width=1024',
        ]
    ]


def test_convert_svg_to_png_legacy_cli(monkeypatch):
    """Test that Inkscape < 1.0 uses the -z -e legacy syntax"""
    calls = _fake_inkscape_version(monkeypatch, 'Inkscape 0.92.4 (x, y)\n')

    inkscape_utils.convert_svg_to_png('in.svg', 'out.png', width=1024)

    assert calls == [
        ['inkscape', '-z', '-e', 'out.png', '-w', '1024', 'in.svg']
    ]
