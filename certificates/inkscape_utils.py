import subprocess
import sys


def _get_inkscape_version():
    """Returns the version number as a float or None if not found."""
    try:
        result = subprocess.run(
            ['inkscape', '--version'],
            capture_output=True,
            text=True,
            check=True,
        )
        version_line = result.stdout.strip()
        # Example: "Inkscape 1.2.2 (732a01da63, 2022-12-09)"
        version_str = version_line.split()[1]
        major_minor = version_str.split('.')[:2]
        return float('.'.join(major_minor))
    except (subprocess.CalledProcessError, IndexError, ValueError):
        return None


def convert_svg_to_png(svg_file, output_file, width=None):
    # ensure svg_file and output_file are strings if Path is used
    svg_file = str(svg_file)
    output_file = str(output_file)

    version = _get_inkscape_version()

    if version is None:
        print(
            'Could not determine Inkscape version.'
            ' Make sure Inkscape is installed.'
        )
        sys.exit(1)

    print(f'Detected Inkscape version: {version}')

    if version >= 1.0:
        # Use modern CLI syntax
        cmd = [
            'inkscape',
            svg_file,
            '--export-type=png',
            f'--export-filename={output_file}',
        ]
        if width:
            cmd.append(f'--export-width={width}')
    else:
        # Use legacy syntax
        cmd = ['inkscape', '-z', '-e', output_file]
        if width:
            cmd += ['-w', str(width)]
        cmd.append(svg_file)

    print('Running command:', ' '.join(cmd))
    try:
        subprocess.run(cmd, check=True)
        print('Export successful!')
    except subprocess.CalledProcessError as e:
        print('Inkscape command failed:', e)


if __name__ == '__main__':
    convert_svg_to_png('example.svg', 'output.png', width=1024)
