PDF generator for Acadoid LectureNotes
======================================

This program takes data files created by the Android note-taking app
[LectureNotes][LN] by [Acadoid][acadoid] and converts them to PDF. This
functionality is **already provided** by LectureNotes, but sometimes it's
useful to have a PDF backup of your notes generated automatically. The goal
of this package is to make LectureNotes PDF generation scriptable.

## Basic Usage

This tool requires a local copy of LectureNotes' data files. This can be
extracted from a `LectureNotesNotebooksBoard.zip` backup file, or directly
copied from the Android tablet's internal storage. Calling

    lecturenotes2pdf /path/to/lecturenotes/backup/

will generate PDFs for your notebooks and place them in the current working
directory.

To run the tool from the source tree instead of installing it, call
`python -m lecturenotes2pdf` instead of `lecturenotes2pdf`.

## Missing features

This tool is **not complete**, but it should work for many notebooks. Notably:

 - Page background patterns are not supported
 - Changing a notebook's default font (to something other than *sans-serif*)
   has no effect. (Font changes *within* a notebook are used)
 - Underlined text is not underlined

## Requirements

The program requires [Python][py], either version 2.7 or 3.2 (or newer), and the
[ReportLab][rptlab] PDF generation toolkit. ReportLab can be found
[on PyPI][rptlab-pypi] (`pip install reportlab`) and is almost certainly provided
by your Linux distribution.

## Installation

    python setup.py install

## Copyright

This program is distributed under the MIT license as included in the file `COPYING`.


[LN]: https://play.google.com/store/apps/details?id=com.acadoid.lecturenotes
[acadoid]: https://www.acadoid.com/
[py]: https://www.python.org/
[rptlab]: https://www.reportlab.com/opensource/
[rptlab-pypi]: https://pypi.python.org/pypi/reportlab
