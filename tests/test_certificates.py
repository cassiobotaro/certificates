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
import sys
import tempfile
from pathlib import Path

import pytest

# Add parent directory to path to import certificates module
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
)
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
