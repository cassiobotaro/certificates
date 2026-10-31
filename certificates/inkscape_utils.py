import re
import subprocess

# Example: "Inkscape 1.2.2 (732a01da63, 2022-12-09)"
_VERSION_PATTERN = re.compile(r'Inkscape\s+(\d+)\.(\d+)')


def _get_inkscape_version():
    """Returns the version as a (major, minor) tuple or None if not found.

    A tuple is used instead of a float so that e.g. 1.10 compares greater
    than 1.2 (as a float, 1.10 == 1.1 < 1.2).
    """
    try:
        result = subprocess.run(
            ['inkscape', '--version'],
            capture_output=True,
            text=True,
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None

    match = _VERSION_PATTERN.search(result.stdout)
    if match is None:
        return None
    return int(match[1]), int(match[2])


def convert_svg_to_png(svg_file, output_file, width=None):
    # ensure svg_file and output_file are strings if Path is used
    svg_file = str(svg_file)
    output_file = str(output_file)

    version = _get_inkscape_version()

    if version is None:
        raise RuntimeError(
            'Could not determine Inkscape version.'
            ' Make sure Inkscape is installed.'
        )

    print('Detected Inkscape version: {}.{}'.format(*version))

    if version >= (1, 0):
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
        raise RuntimeError(f'Inkscape command failed: {e}') from e


if __name__ == '__main__':
    convert_svg_to_png('example.svg', 'output.png', width=1024)
