"""
lecturenotes2pdf.pdf

PDF generation
"""

from __future__ import print_function

import logging

from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

_log = logging.getLogger(__name__)

class PDFGenerator(object):
    def __init__(self, notebook, pdf_filename):
        self.notebook = notebook
        self.pdf_filename = pdf_filename

        self.dpi = 300.0
        self.pixel = inch / self.dpi

        self.width = notebook.paper_width * self.pixel
        self.height = notebook.paper_height * self.pixel

    def run(self):
        c = canvas.Canvas(self.pdf_filename, pagesize=(self.width, self.height))
        c.setTitle(self.notebook.name)

        for page in self.notebook.pages:
            _log.info('{}: drawing page {}'.format(self.notebook.name, page.number))
            self.draw_page(c, page)
            c.showPage()

        c.save()

    def draw_page(self, c, page):
        # Draw the background
        c.setFillColorRGB(*self.notebook.paper_color)
        c.rect(0, 0, self.width, self.height, stroke=1, fill=1)

        # Draw the layers
        layer = 1
        img_layer = 1
        while layer <= self.notebook.displayed_layers:
            if self.notebook.have_text_layer and self.notebook.text_layer == layer:
                self.draw_text_layer(c, page)
            else:
                self.draw_image_layer(c, page, img_layer)
                # note the image layer counter does not increment when
                # we draw a text layer
                img_layer += 1
            layer += 1

    def draw_text_layer(self, c, page):
        pass


    def draw_image_layer(self, c, page, layer):
        _log.debug('{}: page {}: drawing image layer {}'.format(
            self.notebook.name, page.number, layer))
        # Note the layers are 1-indexed
        c.drawImage(page.image_layers[layer-1],
                    0, 0, self.width, self.height,
                    mask='auto')


def notebook2pdf(notebook, pdf_filename):
    PDFGenerator(notebook, pdf_filename).run()
