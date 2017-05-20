"""
lecturenotes2pdf.pdf

PDF generation
"""

from __future__ import print_function, absolute_import

import logging

from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import inch

from .notebook import TextingMachine

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
        canvas = Canvas(self.pdf_filename, pagesize=(self.width, self.height))
        canvas.setTitle(self.notebook.name)

        for page in self.notebook.pages:
            _log.info('{}: drawing page {}'.format(self.notebook.name, page.number))
            self.draw_page(canvas, page)
            canvas.showPage()

        canvas.save()

    def draw_page(self, canvas, page):
        # Draw the background
        canvas.setFillColorRGB(*self.notebook.paper_color)
        canvas.rect(0, 0, self.width, self.height, stroke=0, fill=1)

        # Draw the layers
        layer = 1
        img_layer = 1
        while layer <= self.notebook.displayed_layers:
            if self.notebook.have_text_layer and self.notebook.text_layer == layer:
                self.draw_text_layer(canvas, page)
            else:
                self.draw_image_layer(canvas, page, img_layer)
                # note the image layer counter does not increment when
                # we draw a text layer
                img_layer += 1
            layer += 1

    def draw_text_layer(self, canvas, page):
        if page.text is not None:
            _log.debug('{}: page {}: drawing main text layer'.format(
                self.notebook.name, page.number))
            txtmachine = PDFTextingMachine(canvas, self, page.text)
            txtmachine.run()

        for i, box_text in enumerate(page.text_boxes):
            _log.debug('{}: page {}: drawing text box {}'.format(
                self.notebook.name, page.number, i))
            txtmachine = PDFTextingMachine(canvas, self, box_text)
            txtmachine.run()

    def draw_image_layer(self, canvas, page, layer):
        _log.debug('{}: page {}: drawing image layer {}'.format(
            self.notebook.name, page.number, layer))
        # Note the layers are 1-indexed
        canvas.drawImage(page.image_layers[layer-1],
                         0, 0, self.width, self.height,
                         mask='auto')


class PDFTextingMachine(TextingMachine):
    def __init__(self, canvas, generaor, text):
        super(PDFTextingMachine, self).__init__(text)
        self.canvas = canvas
        self.pdf_generator = generaor
        self.base_font = 'Helvetica'
        self.is_bold = False
        self.is_italic = False
        self.font_size = 10

    def run(self):
        self.textobject = self.canvas.beginText()
        super(PDFTextingMachine, self).run()
        self.canvas.drawText(self.textobject)

    def __update_font(self):
        def set_font(font, size):
            _log.debug('setting PDF font to {}, {}'.format(font, size))
            self.textobject.setFont(font, size)
        if self.base_font == 'Helvetica':
            if self.is_bold and self.is_italic:
                set_font('Helvetica-BoldOblique', self.font_size)
            elif self.is_bold:
                set_font('Helvetica-Bold', self.font_size)
            elif self.is_italic:
                set_font('Helvetica-Oblique', self.font_size)
            else:
                set_font('Helvetica', self.font_size)
        elif self.base_font == 'Times':
            if self.is_bold and self.is_italic:
                set_font('Times-BoldItalic', self.font_size)
            elif self.is_bold:
                set_font('Times-Bold', self.font_size)
            elif self.is_italic:
                set_font('Times-Italic', self.font_size)
            else:
                set_font('Times-Roman', self.font_size)
        elif self.base_font == 'Courier':
            if self.is_bold and self.is_italic:
                set_font('Courier-BoldOblique', self.font_size)
            elif self.is_bold:
                set_font('Courier-Bold', self.font_size)
            elif self.is_italic:
                set_font('Courier-Oblique', self.font_size)
            else:
                set_font('Courier', self.font_size)

    def set_bold(self, bold):
        self.is_bold = bold
        self.__update_font()

    def set_italic(self, italic):
        self.is_italic = italic
        self.__update_font()

    def set_underline(self, underline):
        # TODO - underline not implemented! (text object does not support
        #        it out of the box)
        pass

    def set_color(self, r, g, b):
        self.textobject.setFillColorRGB(r, g, b)

    def set_size(self, pixelsize):
        self.font_size = pixelsize * self.pdf_generator.pixel
        self.__update_font()

    def set_typeface(self, typeface):
        self.base_font = {
            'sans-serif': 'Helvetica',
            'serif': 'Times',
            'monospace': 'Courier'
        }[typeface]
        self.__update_font()

    def translate(self, px_x, px_y):
        dx = px_x * self.pdf_generator.pixel
        dy = px_y * self.pdf_generator.pixel
        dx += self.textobject.getX()
        self.textobject.moveCursor(dx, dy)

    def goto(self, rel_x, rel_y):
        x = rel_x * self.pdf_generator.width
        y = self.pdf_generator.height - rel_y * self.pdf_generator.height
        self.textobject.setTextOrigin(x, y)
        # Positions appear to be defined as bottom-of-line in reportlab,
        # but top-of-line in LectureNotes. Or something like that.
        self.textobject.textLine()

    def write_text(self, s):
        lines = s.split('\n')
        self.textobject.textLines(lines[:-1])
        self.textobject.textOut(lines[-1])


def notebook2pdf(notebook, pdf_filename):
    PDFGenerator(notebook, pdf_filename).run()
