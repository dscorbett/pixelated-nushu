#!/usr/bin/env python

import binascii
import fileinput
import os
import re
import sys


def binary_to_hex(b):
  return '%0*X' % ((len(b) + 3) // 4, int(b, 2))


def print_glyph(glyph):
  print(binary_to_hex(re.sub(r'[^1]', '0', glyph.replace('#', '1'))))


def parse(source):
  if source == sys.stdin:
    glyph = ''.join(line for line in source)
    sys.stdout.write('TODO:')
    print_glyph(glyph)
  else:
    for fn in os.listdir(source):
      if fn.endswith('.glyph'):
        cp = fn[:-6]
        with open(os.path.join(source, fn), 'r') as f:
          glyph = f.read()
        glyph = glyph.replace('\n', '')
        if len(glyph) % (8 * 16) == 0:
          sys.stdout.write(cp + ':')
          print_glyph(glyph)
        else:
          sys.stderr.write('bad glyph: {}\n'.format(cp))


def byte_to_binary(n):
    return ''.join(str((n & (1 << i)) and 1) for i in reversed(range(8)))


def hex_to_binary(h):
    return ''.join(byte_to_binary(ord(b)) for b in binascii.unhexlify(h))


def draw(source, output):
  for line in source:
    fields = line.strip().split(':')
    cp = fields[0]
    glyph = hex_to_binary(fields[1])
    width = len(glyph) / 16
    #if os.path.exists(os.path.join(output, cp + '.glyph')):
    #  continue
    with open(os.path.join(output, cp + '.glyph'), 'a') as f:
      for i, bit in enumerate(glyph):
        if bit == '1':
          f.write('#')
        elif i % 4 == 3:
          f.write('|')
        elif i / width % 4 == 3:
          f.write('_')
        else:
          f.write(' ')
        if i % width == width - 1:
          f.write('\n')


def usage():
    raise Exception('Usage: {} command directory'.format(sys.argv[0]))

if __name__ == '__main__':
  if len(sys.argv) >= 2:
    command = sys.argv[1]
  else:
    usage()
  if len(sys.argv) == 3:
    directory = sys.argv[2]
  elif command == 'parse' and len(sys.argv) == 2:
    directory = None
  else:
    usage()
  if directory:
    if not os.path.isdir(directory):
      if os.path.exists(directory):
        raise Exception('not a directory: ' + directory)
      os.mkdir(directory)
  if command == 'parse':
    parse(directory or sys.stdin)
  elif command == 'draw':
    source = fileinput.input(sys.argv[3:4])
    draw(source, directory)
  else:
    raise Exception('unknown command: ' + command)

