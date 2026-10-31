import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Self

# Example: "Inkscape 1.2.2 (732a01da63, 2022-12-09)"
_VERSION_PATTERN = re.compile(r'Inkscape\s+(\d+)\.(\d+)')


@dataclass(frozen=True)
class Inkscape:
    """A detected Inkscape installation able to export SVG files to PNG.

    The version is resolved once, in `detect()`, and reused for every
    export; the CLI syntax changed in 1.0, so it decides which flags to use.
    The version is a (major, minor) tuple rather than a float so that e.g.
    1.10 compares greater than 1.2.
    """

    version: tuple[int, int]

    @classmethod
    def detect(cls) -> Self:
        """Run `inkscape --version` and build an instance from its output.

        Raises RuntimeError if Inkscape is not installed or its version
        cannot be determined.
        """
        try:
            result = subprocess.run(
                ['inkscape', '--version'],
                capture_output=True,
                text=True,
                check=True,
            )
        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            raise RuntimeError(
                'Could not determine Inkscape version.'
                ' Make sure Inkscape is installed.'
            ) from e

        match = _VERSION_PATTERN.search(result.stdout)
        if match is None:
            raise RuntimeError(
                'Could not determine Inkscape version.'
                f' Unexpected output: {result.stdout!r}'
            )

        inkscape = cls((int(match[1]), int(match[2])))
        print('Detected Inkscape version: {}.{}'.format(*inkscape.version))
        return inkscape

    def export_png(
        self,
        svg_file: str | Path,
        output_file: str | Path,
        width: int | None = None,
    ) -> None:
        """Export `svg_file` to `output_file` as PNG."""
        svg_file = str(svg_file)
        output_file = str(output_file)

        if self.version >= (1, 0):
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
