"""
lecturenotes2pdf.notebook

Interface to LectureNotes notebooks
"""

from collections import namedtuple
import os
import os.path
import xml.etree.ElementTree as ET


class NotebooksBoard(object):
    def __init__(self, path):
        if path.endswith('settings.xml') and os.path.exists(path):
            path = os.path.dirname(path)
        elif not (os.path.isdir(path) and 'settings.xml' in os.listdir(path)):
            raise ValueError('{} is not the the location of a notebooks board')

        self.root = path

    def children(self):
        for child_file in os.listdir(self.root):
            child_path = os.path.join(self.root, child_file)
            if os.path.isdir(child_path):
                grandchildren = os.listdir(child_path)
                if 'notebook.xml' in grandchildren:
                    yield Notebook(child_path)
                elif 'folder.xml' in grandchildren:
                    yield Folder(child_path)

    def all_notebooks(self):
        for child in self.children():
            if isinstance(child, Notebook):
                yield child
            elif isinstance(child, Folder):
                for descendant in NotebooksBoard.all_notebooks(child):
                    yield descendant


class Folder(object):
    def __init__(self, path):
        if path.endswith('folder.xml') and os.path.exists(path):
            path = os.path.dirname(path)
        elif not (os.path.isdir(path) and 'folder.xml' in os.listdir(path)):
            raise ValueError('{} is not the the location of a notebook folder')

        self.root = path

    def children(self):
        for child_file in os.listdir(self.root):
            child_path = os.path.join(self.root, child_file)
            if os.path.isdir(child_path):
                grandchildren = os.listdir(child_path)
                if 'notebook.xml' in grandchildren:
                    yield Notebook(child_path)
                elif 'folder.xml' in grandchildren:
                    yield Folder(child_path)


class Notebook(object):
    def __init__(self, path):
        if path.endswith('notebook.xml') and os.path.exists(path):
            path = os.path.dirname(path)
        elif not (os.path.isdir(path) and 'notebook.xml' in os.listdir(path)):
            raise ValueError('{} is not the the location of a notebook')

        self.root = path
        self.name = os.path.basename(path)

        i = 1
        self.pages = []
        while True:
            try:
                self.pages.append(Page(self, i))
                i += 1
            except ValueError:
                break

        self._notebook_xml = ET.parse(os.path.join(self.root, 'notebook.xml'))
        root = self._notebook_xml.getroot()

        self.paper_width = float(root.find('paperwidth').text)
        self.paper_height = float(root.find('paperheight').text)
        self.paper_color = parse_color(root.find('papercolor').text)
        # ignore pattern

        # ignore textlayersettings
        self.text_font_family = int(root.find('textlayerfontfamily').text) # ??
        self.text_font_style = int(root.find('textlayerfontstyle').text)
        self.text_font_size = float(root.find('textlayerfontsize').text)
        self.text_font_color = parse_color(root.find('textlayerfontcolor').text)
        self.text_margin_left = float(root.find('textlayerleftmargin').text)
        self.text_margin_top = float(root.find('textlayertopmargin').text)
        self.text_margin_right = float(root.find('textlayerrightmargin').text)
        self.text_margin_bottom = float(root.find('textlayerbottommargin').text)

        self.layers = int(root.find('layers').text)
        self.displayed_layers = int(root.find('displayedlayers').text)
        self.text_layer = int(root.find('textlayer').text)
        self.display_text = bool(int(root.find('displaytextlayer').text))

        # ignore paper scale and fit

        # Check if there is a text layer!
        self.have_text_layer = any(p.text is not None or p.text_boxes
                                   for p in self.pages)


class Page(object):
    def __init__(self, notebook, number):
        self.notebook = notebook
        self.root = notebook.root
        self.number = number

        # Collect image layers
        bg_1 = os.path.join(self.root, 'page{}.png'.format(number))
        if not os.path.exists(bg_1):
            raise ValueError("No such page: {}".format(number))

        self.image_layers = [bg_1]
        i = 2
        while True:
            path = os.path.join(self.root, 'page{}_{}.png'.format(number, i))
            if os.path.exists(path):
                self.image_layers.append(path)
                i += 1
            else:
                break

        # Collect text layer and boxes
        textpath_base = os.path.join(self.root, 'text{}'.format(self.number))
        if os.path.exists(textpath_base + '.txt'):
            self.text = Text(textpath_base)
        else:
            self.text = None

        self.text_boxes = []
        i = 1
        while True:
            box_base = '{}_{}'.format(textpath_base, i)
            if os.path.exists(box_base + '.txt'):
                self.text_boxes.append(box_base)
                i += 1
            else:
                break

        # Are there keywords?
        key_path = os.path.join(self.root, 'key{}.txt'.format(number))
        if os.path.exists(key_path):
            with open(key_path, 'r') as fp:
                self.keywords = [l.strip() for l in fp]
        else:
            self.keywords = []

class Text(object):
    def __init__(self, filename_base):
        txt_file = filename_base + '.txt'
        box_file = filename_base + '.box'
        style_file = filename_base + '.style'

        with open(txt_file, 'r') as fp:
            self.content = fp.read()

        if os.path.exists(box_file):
            self._read_box(box_file)

        if os.path.exists(style_file):
            self._read_style(style_file)
        else:
            self.style = None

    def _read_box(self, box_file):
        with open(box_file, 'r') as fp:
            self.x = float(fp.readline().strip())
            self.y = float(fp.readline().strip())
            self.w = float(fp.readline().strip())
            self.h = float(fp.readline().strip())

    def _read_style(self, style_file):
        self.style = []
        with open(style_file, 'r') as fp:
            for line in fp:
                command, arg, from_idx, to_idx, foo = line.strip().split()
                self.style.append(TextStyleCommand(
                    command, arg, int(from_idx), int(to_idx), foo))


TextStyleCommand = namedtuple('TextStyleCommand',
                              ['command', 'argument',
                               'from_index', 'to_index',
                               'unknown1'])

def parse_color(ln_color):
    """
    Take the int32 represetation of a color and turn it into an
    (r,g,b) tuple of floats
    """
    ARGB_long = (int(ln_color) + (1 << 32)) & 0xffffffff

    B = (ARGB_long >> 0) & 0xff
    G = (ARGB_long >> 8) & 0xff
    R = (ARGB_long >> 16) & 0xff
    # A = (ARGB_long >> 24) & 0xff

    return (R/255., G/255., B/255.)
