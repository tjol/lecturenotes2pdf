"""
lecturenotes2pdf.notebook

Interface to LectureNotes notebooks
"""

from collections import namedtuple
import logging
import os
import os.path
import xml.etree.ElementTree as ET

_log = logging.getLogger(__name__)

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
            self.text = Text(self, textpath_base)
        else:
            self.text = None

        self.text_boxes = []
        i = 1
        while True:
            box_base = '{}_{}'.format(textpath_base, i)
            if os.path.exists(box_base + '.txt'):
                self.text_boxes.append(Text(self, box_base))
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
    def __init__(self, page, filename_base):
        self.page = page

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

BOLD = 0b01
ITALIC = 0b10

class TextingMachine(object):
    """
    Base class providing support for rendering Text objects.

    This reads through the text and style and calls a number of methods
    to add plain text or change style.

    Subclasses must implement these methods:

     - set_bold
     - set_italic
     - set_underline
     - set_color
     - set_size
     - set_typeface
     - translate
     - goto
     - write_text
    """

    def __init__(self, text):
        self.text = text

        self._style = -1


    def run(self):
        current_idx = 0
        for new_idx, method, args in self._internal_command_queue():
            if new_idx > current_idx:
                s = self.text.content[current_idx:new_idx]
                _log.debug('calling write_text ({})'.format(repr(s)))
                self.write_text(s)
                current_idx = new_idx
            _log.debug('Calling {} {}'.format(method.__name__, args))
            method(*args)

        if current_idx < len(self.text.content):
            self.write_text(self.text.content[current_idx:])


    def _internal_command_queue(self):
        """
        Convert the LectureNotes command queue into something we can use.

        Basically, this method takes all the instructions (which have start and
        end points), and turns them into do and undo instructions which run()
        then executes in order.
        """
        # Create a list of commands (index, callable, args)
        q = []

        nb = self.text.page.notebook

        # Use the default text formats
        style = nb.text_font_style
        # No idea why, but it appears that the font size is off by a factor of
        # 4/3.
        pixelsize = nb.text_font_size * 3 / 4.0
        underline = False
        color = nb.text_font_color
        # This should be taken from config! TODO
        typeface = 'sans-serif'

        # Setup commands - will prepend them to the final queue!
        q.append((0, self._set_style, (style,)))
        q.append((0, self.set_size, (pixelsize,)))
        q.append((0, self.set_color, color))
        q.append((0, self.set_typeface, (typeface,)))
        if hasattr(self.text, 'x'):
            q.append((0, self.goto, (self.text.x, self.text.y)))
        else:
            q.append((0, self.goto, (nb.text_margin_left,
                                     nb.text_margin_top)))

        style_commands = self.text.style or []
        style_commands = style_commands[:]

        def insert_command(index, command, arg):
            """
            add undo command to the script
            """
            if index < 0:
                return
            cmd_tuple = (command, arg, index, -1, None)
            for i in range(len(style_commands)):
                cmd, arg, from_idx, to_idx, foo = style_commands[i]
                if from_idx >= index:
                    style_commands.insert(i, cmd_tuple)
                    break
            else:
                style_commands.append(cmd_tuple)

        for cmd, arg, from_idx, to_idx, foo in style_commands:
            if cmd == 'typeface':
                q.append((from_idx, self.set_typeface, (arg,)))
                insert_command(to_idx, 'typeface', typeface)
                typeface = arg
            elif cmd == 'styleset':
                q.append((from_idx, self._set_style, (int(arg),)))
                insert_command(to_idx, 'styleset', style)
                style = int(arg)
            elif cmd == 'stylexor':
                stylebits = int(arg)
                q.append((from_idx, self._set_style, (style ^ stylebits,)))
                insert_command(to_idx, 'stylexor', arg)
                style ^= stylebits
            elif cmd == 'underline':
                q.append((from_idx, self.set_underline, (True,)))
                insert_command(to_idx, 'UNDO underline', None)
                underline = True
            elif cmd == 'UNDO underline':
                q.append((from_idx, self.set_underline, (False,)))
                underline = False
            elif cmd == 'underlinexor':
                bit = bool(int(arg))
                q.append((from_idx, self.set_underline, (underline ^ bit,)))
                insert_command(to_idx, 'underlinexor', arg)
                underline ^= bit
            elif cmd == 'foregroundcolor':
                q.append((from_idx, self.set_color, parse_color(arg)))
                insert_command(to_idx, 'foregroundcolor', color)
                color = parse_color(arg)
            elif cmd == 'relativesize':
                newsize = pixelsize * float(arg)
                q.append((from_idx, self.set_size, (newsize,)))
                insert_command(to_idx, 'relativesize', 1 / float(arg))
                pixelsize = newsize
            elif cmd == 'subscript':
                dy = 0.5 * pixelsize
                q.append((from_idx, self.translate, (0, dy)))
                insert_command(to_idx, 'superscript', None)
            elif cmd == 'superscript':
                dy = - 0.5 * pixelsize
                q.append((from_idx, self.translate, (0, dy)))
                insert_command(to_idx, 'subscript', None)
            else:
                raise ValueError('Unknown style command {}'.format(cmd))

        return q


    def _set_style(self, style):
        if self._style < 0:
            # initial set
            self._style = style
            self.set_bold((style & BOLD) != 0)
            self.set_italic((style & ITALIC) != 0)
        else:
            change = self._style ^ style
            if (change & BOLD) != 0:
                self.set_bold((style & BOLD) != 0)
            if (change & ITALIC) != 0:
                self.set_italic((style & ITALIC) != 0)

            self._style = style

    def set_bold(self, bold):
        raise NotImplementedError

    def set_italic(self, italic):
        raise NotImplementedError

    def set_underline(self, underline):
        raise NotImplementedError

    def set_color(self, r, g, b):
        raise NotImplementedError

    def set_size(self, pixelsize):
        raise NotImplementedError

    def set_typeface(self, typeface):
        raise NotImplementedError

    def translate(self, px_x, px_y):
        raise NotImplementedError

    def goto(self, rel_x, rel_y):
        raise NotImplementedError

    def write_text(self, s):
        raise NotImplementedError


def parse_color(ln_color):
    """
    Take the int32 represetation of a color and turn it into an
    (r,g,b) tuple of floats
    """
    if isinstance(ln_color, tuple) and len(ln_color) == 3:
        return ln_color

    ARGB_long = (int(ln_color) + (1 << 32)) & 0xffffffff

    B = (ARGB_long >> 0) & 0xff
    G = (ARGB_long >> 8) & 0xff
    R = (ARGB_long >> 16) & 0xff
    # A = (ARGB_long >> 24) & 0xff

    return (R/255., G/255., B/255.)
