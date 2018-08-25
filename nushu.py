#!/usr/bin/env python3.7

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
OUTPUT_PARAMS_PATTERN = str(AUTO_DIR / 'params' / '{}.png')
OUTPUT_PNG_PATTERN = str(AUTO_DIR / 'output' / '{}.png')
B_INPUT = str(ROOT_DIR / 'temp_b_q.png')
B_OUTPUT = str(ROOT_DIR / 'temp_b_output.png')
EXTRA_BORDER = 50

def add_border(in_path, out_path):
    """The widget crops all images slightly at the top and bottom, so
    every image needs a temporary display copy with extra borders.
    """
    subprocess.call('magick {} -set option:wd "%[fx:max(w,h+2*{})]" -set option:ht "%[fx:h+2*{}]" -background "#dfdfdf" -gravity center -extent "%[wd]x%[ht]" {}'.format(in_path, EXTRA_BORDER, EXTRA_BORDER, out_path),
        shell=True)

class Pixelator(BaseWidget):
    def __init__(self):
        super(Pixelator, self).__init__('Pixelator')

        #self._width = ControlSlider('Width', default=100, minimum=100, maximum=300)
        #self._threshold = ControlSlider('Threshold', default=80, minimum=50, maximum=99)
        self._cp = ControlCombo('Code point')
        self._width = ControlNumber('Width', default=100, minimum=0, maximum=1000)
        self._threshold = ControlNumber('Threshold', default=80, maximum=99)
        self._input_file = ControlImage('Input')
        self._output_file = ControlImage('Output')

        self._cp.changed_event = lambda: self._redraw(self._cp)
        self._width.changed_event = lambda: self._redraw(self._width)
        self._threshold.changed_event = lambda: self._redraw(self._threshold)

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
        output_file = OUTPUT_PNG_PATTERN.format(cp)
        subprocess.call('''convert {} -negate -morphology Thinning:-1 Skeleton -negate -resize {}%x100% - |
                magick - -set option:wd "%[fx:max(w,h)]" -set option:ht "%[fx:max(w,h)]" -gravity center -extent "%[wd]x%[ht]" - |
                convert - -resize 16x16 +dither '''
                '''-threshold {}% '''
                #'''-posterize 5 '''
                '''-scale 233 -density 72 {}'''.format(
            input_file, self._width.value, self._threshold.value, output_file),
            shell=True)
        add_border(input_file, B_INPUT)
        add_border(output_file, B_OUTPUT)
        self._input_file.value = B_INPUT
        self._output_file.value = B_OUTPUT
        self._input_file.repaint()
        self._output_file.repaint()
        if current_control in [self._width, self._threshold] or not os.path.exists(output_params_file):
            with open(output_params_file, 'w') as f:
                f.write(str(self._width.value) + ' ' + str(self._threshold.value))

if __name__ == "__main__":
    Path(OUTPUT_PARAMS_PATTERN).parent.mkdir(exist_ok=True)
    Path(OUTPUT_PNG_PATTERN).parent.mkdir(exist_ok=True)
    start_app(Pixelator, geometry=(200, 200, 800, 400))
    # TODO: clean up temporary files
