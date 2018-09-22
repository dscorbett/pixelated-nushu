#!/usr/bin/env python3.7

import argparse
import os
from pathlib import Path
import subprocess

from pyforms import BaseWidget
from pyforms import start_app
from pyforms.controls import *

# For some inexplicable reason, images must be square or in landscape
# orientation to be centered properly. Images in portrait orientation
# have their left center placed at the widget's top center.

ROOT_DIR = Path(__file__).parent
AUTO_DIR = ROOT_DIR / 'auto'
INPUT_PNG_PATTERN = str(AUTO_DIR  / 'input' / '{}.png')
OUTPUT_GLYPH_PATTERN = str(AUTO_DIR / 'glyphs' / '{}.glyph')
OUTPUT_PARAMS_PATTERN = str(AUTO_DIR / 'params' / '{}.png')
OUTPUT_PNG_PATTERN = str(AUTO_DIR / 'output' / '{}.png')
MANUAL_GLYPH_PATTERN = str(ROOT_DIR / 'glyphs' / '{}.glyph')
B_INPUT = str(ROOT_DIR / 'temp_b_q.png')
B_OUTPUT = str(ROOT_DIR / 'temp_b_output.png')
SCALE_FACTOR = 233
EXTRA_BORDER = 50

BYTES = ['{:08b}'.format(x).replace('0', '\x00').replace('1', '#')[::-1].encode() for x in range(0, 256)]
BYTES_INV = {e: i for i, e in enumerate(BYTES)}

def bytes_or(a, b):
    return bytes(x or y for x, y in zip(a, b)).decode()

def add_border(in_path, out_path):
    """The widget crops all images slightly at the top and bottom, so
    every image needs a temporary display copy with extra borders.
    """
    subprocess.call('magick {} -set option:wd "%[fx:max(w,h+2*{})]" -set option:ht "%[fx:h+2*{}]" -background "#dfdfdf" -gravity center -extent "%[wd]x%[ht]" {}'.format(in_path, EXTRA_BORDER, EXTRA_BORDER, out_path),
        shell=True)

class Pixelator(BaseWidget):
    def __init__(self):
        super(Pixelator, self).__init__('Pixelator')

        self._cp = ControlCombo('Code point')
        self._width = ControlNumber('Width', default=100, minimum=0, maximum=1000)
        self._threshold = ControlNumber('Threshold', default=80, maximum=99)
        self._input_file = ControlImage('Input')
        self._output_file = ControlImage('Output')

        self._cp.changed_event = lambda: self._redraw(self._cp)
        self._width.changed_event = lambda: self._redraw(self._width)
        self._threshold.changed_event = lambda: self._redraw(self._threshold)

        parser = argparse.ArgumentParser(description='Pixelize Nüshu glyphs.')
        parser.add_argument('--view', action='store_true', help='View existing pixelations instead of creating new ones.')
        args = parser.parse_args()
        self._viewer_mode = args.view
        if self._viewer_mode:
            self._width.enabled = False
            self._threshold.enabled = False

        self._cp += '16FE1'
        for cp in range(0x1B170, 0x1B2FB + 1):
            self._cp += hex(cp)[2:].upper()

        self.formset = [
            ('_width', '_threshold'),
            ('_cp', '_input_file', '_output_file'),
        ]

    def _redraw(self, current_control):
        cp = self._cp.text
        output_params_file = OUTPUT_PARAMS_PATTERN.format(cp)
        if current_control == self._cp:
            try:
                with open(output_params_file, 'r') as f:
                    saved_width, saved_threshold = f.read().strip().split()
                    if current_control != self._width:
                        self._width.value = float(saved_width)
                    if current_control != self._threshold:
                        self._threshold.value = float(saved_threshold)
            except IOError:
                pass
        input_file = INPUT_PNG_PATTERN.format(cp)
        add_border(input_file, B_INPUT)
        self._input_file.value = B_INPUT
        self._input_file.repaint()
        if self._viewer_mode:
            self._view(cp)
        else:
            self._pixelate(current_control, cp, output_params_file, input_file)

    def _view(self, cp):
        with open(MANUAL_GLYPH_PATTERN.format(cp), 'rb') as f:
            with open(B_OUTPUT + '.mono', 'w+b') as mono:
                while True:
                    chunk = f.read(8)
                    if not chunk:
                        break
                    mono.write(BYTES_INV[b''.join(b'#' if b == ord(b'#') else b'\x00' for b in chunk)].to_bytes(1, 'little'))
                    chunk = f.read(8)
                    mono.write(BYTES_INV[b''.join(b'#' if b == ord(b'#') else b'\x00' for b in chunk)].to_bytes(1, 'little'))
                    f.read(1)  # newline
        subprocess.call('convert -size 16x16 {}.mono -scale {} {}'.format(B_OUTPUT, SCALE_FACTOR, B_OUTPUT), shell=True)
        add_border(B_OUTPUT, B_OUTPUT)
        self._output_file.value = B_OUTPUT
        self._output_file.repaint()

    def _pixelate(self, current_control, cp, output_params_file, input_file):
        output_file = OUTPUT_PNG_PATTERN.format(cp)
        subprocess.call('''convert {} -negate -morphology Thinning:-1 Skeleton -negate -resize {}%x100% - |
                magick - -set option:wd "%[fx:max(w,h)]" -set option:ht "%[fx:max(w,h)]" -gravity center -extent "%[wd]x%[ht]" - |
                convert - -resize 16x16 +dither '''
                '''-threshold {}% -write {}'''.format(
                    input_file, self._width.value, self._threshold.value, output_file),
            shell=True)
        subprocess.call('convert {} {}.mono'.format(output_file, output_file), shell=True)
        subprocess.call('convert {} -scale {} -density 72 {}'.format(output_file, SCALE_FACTOR, output_file), shell=True)
        add_border(output_file, B_OUTPUT)
        self._output_file.value = B_OUTPUT
        self._output_file.repaint()
        if current_control in [self._width, self._threshold] or not os.path.exists(output_params_file):
            with open(output_params_file, 'w') as f:
                f.write(str(self._width.value) + ' ' + str(self._threshold.value))
        with open(output_file + '.mono', 'rb') as mono:
            with open(OUTPUT_GLYPH_PATTERN.format(cp), 'w') as f:
                line_pair = 0
                while True:
                    try:
                        b1, b2, b3, b4 = mono.read(4)
                    except ValueError:
                        break
                    p = b'   |   |'
                    print(bytes_or(BYTES[b1], p), end='', file=f)
                    print(bytes_or(BYTES[b2], p), file=f)
                    if line_pair % 2:
                        p = b'___|___|'
                    print(bytes_or(BYTES[b3], p), end='', file=f)
                    print(bytes_or(BYTES[b4], p), file=f)
                    line_pair += 1

if __name__ == "__main__":
    Path(OUTPUT_GLYPH_PATTERN).parent.mkdir(exist_ok=True)
    Path(OUTPUT_PARAMS_PATTERN).parent.mkdir(exist_ok=True)
    Path(OUTPUT_PNG_PATTERN).parent.mkdir(exist_ok=True)
    start_app(Pixelator, geometry=(200, 200, 800, 400))
    # TODO: clean up temporary files
