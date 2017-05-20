"""
lecturenotes2pdf: Convert LectureNotes notebooks to PDF format
"""

from __future__ import absolute_import, print_function

import argparse
import logging
import sys

from .notebook import Notebook, NotebooksBoard
from .pdf import notebook2pdf


def list_board(board):
    print('NOTEBOOKS BOARD', board.root)
    for nb in board.all_notebooks():
        list_notebook(nb)

def list_notebook(nb):
    print('NOTEBOOK', nb.root)
    for pg in nb.pages:
        print('"{}"<{}> - bitmaps: {} - text: {} - boxes: {}'
              .format(nb.name, pg.number,
                      len(pg.image_layers),
                      'nY'[pg.text is not None],
                      len(pg.text_boxes)))

def convert_notebook(nb, verbosity):
    pdf_filename = nb.name + '.pdf'
    if verbosity > 0:
        print('Creating', pdf_filename)
    notebook2pdf(nb, pdf_filename)


def convert_board(board, verbosity):
    for nb in board.all_notebooks():
        convert_notebook(nb, verbosity)


arg_parser = argparse.ArgumentParser('lecturenotes2pdf')
arg_parser.add_argument('location', help='location of LectureNotes data')
arg_parser.add_argument('-l', '--list', action='store_true',
                        help='list all notebooks and pages')
arg_parser.add_argument('-v', '--verbose', action='count',
                        help='say what is being done (also: -vv, -vvv)')

args = arg_parser.parse_args()

logger = logging.getLogger('lecturenotes2pdf')
# create console handler and set level to debug
ch = logging.StreamHandler()
# create formatter
formatter = logging.Formatter('[%(levelname)s] %(name)s - %(message)s')
# add formatter to ch
ch.setFormatter(formatter)
# add ch to logger
logger.addHandler(ch)

if args.verbose >= 3:
    logger.setLevel(logging.DEBUG)
    ch.setLevel(logging.DEBUG)
elif args.verbose >= 2:
    logger.setLevel(logging.INFO)
    ch.setLevel(logging.INFO)
else:
    logger.setLevel(logging.WARNING)
    ch.setLevel(logging.WARNING)

try:
    board = NotebooksBoard(args.location)
except ValueError:
    try:
        notebook = Notebook(args.location)
        board = None
    except ValueError:
        print(args.location, 'is neither a notebook nor a notebooks board.',
              file=sys.stderr)

if args.list:
    if board is not None:
        list_board(board)
    else:
        list_notebook(notebook)
elif board is not None:
    convert_board(board, args.verbose)
else:
    convert_notebook(notebook, args.verbose)
