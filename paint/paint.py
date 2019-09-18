
import os
import random
import types

from PySide2.QtCore import (QCoreApplication, QMetaObject, QObject, QRect, QRunnable, QSize,  Qt, QThreadPool, QTimer, Signal, Slot)
from PySide2.QtGui import (QBrush, QColor, QFont, QIcon, QImage, QPainter, QPalette, QPen, QPixmap)
from PySide2.QtWidgets import (QAction, QApplication, QButtonGroup, QComboBox, QFontComboBox, QFormLayout, QGridLayout, QHBoxLayout, QLabel, QLayout, QLineEdit, QMainWindow, QMenu, QMenuBar, QMessageBox, QPushButton, QSizePolicy, QSlider, QSpacerItem, QStatusBar, QToolBar, QVBoxLayout, QWidget)


BRUSH_MULT = 3
SPRAY_PAINT_MULT = 5
SPRAY_PAINT_N = 100

COLORS = [
    '#000000', '#82817f', '#820300', '#868417', '#007e03', '#037e7b', '#040079',
    '#81067a', '#7f7e45', '#05403c', '#0a7cf6', '#093c7e', '#7e07f9', '#7c4002',

    '#ffffff', '#c1c1c1', '#f70406', '#fffd00', '#08fb01', '#0bf8ee', '#0000fa',
    '#b92fc2', '#fffc91', '#00fd83', '#87f9f9', '#8481c4', '#dc137d', '#fb803c',
]

FONT_SIZES = [7, 8, 9, 10, 11, 12, 13, 14, 18, 24, 36, 48, 64, 72, 96, 144, 288]

MODES = [
    'selectpoly', 'selectrect',
    'eraser', 'fill',
    'dropper', 'stamp',
    'pen', 'brush',
    'spray', 'text',
    'line', 'polyline',
    'rect', 'polygon',
    'ellipse', 'roundrect'
]

CANVAS_DIMENSIONS = 600, 400

STAMP_DIR = './stamps'
STAMPS = [os.path.join(STAMP_DIR, f) for f in os.listdir(STAMP_DIR)]

SELECTION_PEN = QPen(QColor(0xff, 0xff, 0xff), 1, Qt.DashLine)
PREVIEW_PEN = QPen(QColor(0xff, 0xff, 0xff), 1, Qt.SolidLine)


def build_font(config):
    """
    Construct a complete font from the configuration options
    :param self:
    :param config:
    :return: QFont
    """
    font = config['font']
    font.setPointSize(config['fontsize'])
    font.setBold(config['bold'])
    font.setItalic(config['italic'])
    font.setUnderline(config['underline'])
    return font


class Canvas(QLabel):

    mode = 'rectangle'

    primary_color = QColor(Qt.black)
    secondary_color = None

    primary_color_updated = Signal(str)
    secondary_color_updated = Signal(str)

    # Store configuration settings, including pen width, fonts etc.
    config = {
        # Drawing options.
        'size': 1,
        'fill': True,
        # Font options.
        'font': QFont('Times'),
        'fontsize': 12,
        'bold': False,
        'italic': False,
        'underline': False,
    }

    active_color = None
    preview_pen = None

    timer_event = None

    current_stamp = None

    def initialize(self):
        self.background_color = QColor(self.secondary_color) if self.secondary_color else QColor(Qt.white)
        self.eraser_color = QColor(self.secondary_color) if self.secondary_color else QColor(Qt.white)
        self.eraser_color.setAlpha(100)
        self.reset()

    def reset(self):
        # Create the pixmap for display.
        self.setPixmap(QPixmap(*CANVAS_DIMENSIONS))

        # Clear the canvas.
        self.pixmap().fill(self.background_color)

    def set_primary_color(self, hex):
        self.primary_color = QColor(hex)

    def set_secondary_color(self, hex):
        self.secondary_color = QColor(hex)

    def set_config(self, key, value):
        self.config[key] = value

    def set_mode(self, mode):
        # Clean up active timer animations.
        self.timer_cleanup()
        # Reset mode-specific vars (all)
        self.active_shape_fn = None
        self.active_shape_args = ()

        self.origin_pos = None

        self.current_pos = None
        self.last_pos = None

        self.history_pos = None
        self.last_history = []

        self.current_text = ""
        self.last_text = ""

        self.last_config = {}

        self.dash_offset = 0
        self.locked = False
        # Apply the mode
        self.mode = mode

    def reset_mode(self):
        self.set_mode(self.mode)

    def on_timer(self):
        if self.timer_event:
            self.timer_event()

    def timer_cleanup(self):
        if self.timer_event:
            # Stop the timer, then trigger cleanup.
            timer_event = self.timer_event
            self.timer_event = None
            timer_event(final=True)

    # Mouse events.

    def mousePressEvent(self, e):
        fn = getattr(self, "%s_mousePressEvent" % self.mode, None)
        if fn:
            return fn(e)

    def mouseMoveEvent(self, e):
        fn = getattr(self, "%s_mouseMoveEvent" % self.mode, None)
        if fn:
            return fn(e)

    def mouseReleaseEvent(self, e):
        fn = getattr(self, "%s_mouseReleaseEvent" % self.mode, None)
        if fn:
            return fn(e)

    def mouseDoubleClickEvent(self, e):
        fn = getattr(self, "%s_mouseDoubleClickEvent" % self.mode, None)
        if fn:
            return fn(e)

    # Generic events (shared by brush-like tools)

    def generic_mousePressEvent(self, e):
        self.last_pos = e.pos()

        if e.button() == Qt.LeftButton:
            self.active_color = self.primary_color
        else:
            self.active_color = self.secondary_color

    def generic_mouseReleaseEvent(self, e):
        self.last_pos = None

    # Mode-specific events.

    # Select polygon events

    def selectpoly_mousePressEvent(self, e):
        if not self.locked or e.button == Qt.RightButton:
            self.active_shape_fn = 'drawPolygon'
            self.preview_pen = SELECTION_PEN
            self.generic_poly_mousePressEvent(e)

    def selectpoly_timerEvent(self, final=False):
        self.generic_poly_timerEvent(final)

    def selectpoly_mouseMoveEvent(self, e):
        if not self.locked:
            self.generic_poly_mouseMoveEvent(e)

    def selectpoly_mouseDoubleClickEvent(self, e):
        self.current_pos = e.pos()
        self.locked = True

    def selectpoly_copy(self):
        """
        Copy a polygon region from the current image, returning it.

        Create a mask for the selected area, and use it to blank
        out non-selected regions. Then get the bounding rect of the
        selection and crop to produce the smallest possible image.

        :return: QPixmap of the copied region.
        """
        self.timer_cleanup()

        pixmap = self.pixmap().copy()
        bitmap = QBitmap(*CANVAS_DIMENSIONS)
        bitmap.clear()  # Starts with random data visible.

        p = QPainter(bitmap)
        # Construct a mask where the user selected area will be kept, the rest removed from the image is transparent.
        userpoly = QPolygon(self.history_pos + [self.current_pos])
        p.setPen(QPen(Qt.color1))
        p.setBrush(QBrush(Qt.color1))  # Solid color, Qt.color1 == bit on.
        p.drawPolygon(userpoly)
        p.end()

        # Set our created mask on the image.
        pixmap.setMask(bitmap)

        # Calculate the bounding rect and return a copy of that region.
        return pixmap.copy(userpoly.boundingRect())

    # Select rectangle events

    def selectrect_mousePressEvent(self, e):
        self.active_shape_fn = 'drawRect'
        self.preview_pen = SELECTION_PEN
        self.generic_shape_mousePressEvent(e)

    def selectrect_timerEvent(self, final=False):
        self.generic_shape_timerEvent(final)

    def selectrect_mouseMoveEvent(self, e):
        if not self.locked:
            self.current_pos = e.pos()

    def selectrect_mouseReleaseEvent(self, e):
        self.current_pos = e.pos()
        self.locked = True

    def selectrect_copy(self):
        """
        Copy a rectangle region of the current image, returning it.

        :return: QPixmap of the copied region.
        """
        self.timer_cleanup()
        return self.pixmap().copy(QRect(self.origin_pos, self.current_pos))

    # Eraser events

    def eraser_mousePressEvent(self, e):
        self.generic_mousePressEvent(e)

    def eraser_mouseMoveEvent(self, e):
        if self.last_pos:
            p = QPainter(self.pixmap())
            p.setPen(QPen(self.eraser_color, 30, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            p.drawLine(self.last_pos, e.pos())

            self.last_pos = e.pos()
            self.update()

    def eraser_mouseReleaseEvent(self, e):
        self.generic_mouseReleaseEvent(e)

    # Stamp (pie) events

    def stamp_mousePressEvent(self, e):
        p = QPainter(self.pixmap())
        stamp = self.current_stamp
        p.drawPixmap(e.x() - stamp.width() // 2, e.y() - stamp.height() // 2, stamp)
        self.update()

    # Pen events

    def pen_mousePressEvent(self, e):
        self.generic_mousePressEvent(e)

    def pen_mouseMoveEvent(self, e):
        if self.last_pos:
            p = QPainter(self.pixmap())
            p.setPen(QPen(self.active_color, self.config['size'], Qt.SolidLine, Qt.SquareCap, Qt.RoundJoin))
            p.drawLine(self.last_pos, e.pos())

            self.last_pos = e.pos()
            self.update()

    def pen_mouseReleaseEvent(self, e):
        self.generic_mouseReleaseEvent(e)

    # Brush events

    def brush_mousePressEvent(self, e):
        self.generic_mousePressEvent(e)

    def brush_mouseMoveEvent(self, e):
        if self.last_pos:
            p = QPainter(self.pixmap())
            p.setPen(QPen(self.active_color, self.config['size'] * BRUSH_MULT, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            p.drawLine(self.last_pos, e.pos())

            self.last_pos = e.pos()
            self.update()

    def brush_mouseReleaseEvent(self, e):
        self.generic_mouseReleaseEvent(e)

    # Spray events

    def spray_mousePressEvent(self, e):
        self.generic_mousePressEvent(e)

    def spray_mouseMoveEvent(self, e):
        if self.last_pos:
            p = QPainter(self.pixmap())
            p.setPen(QPen(self.active_color, 1))

            for n in range(self.config['size'] * SPRAY_PAINT_N):
                xo = random.gauss(0, self.config['size'] * SPRAY_PAINT_MULT)
                yo = random.gauss(0, self.config['size'] * SPRAY_PAINT_MULT)
                p.drawPoint(e.x() + xo, e.y() + yo)

        self.update()

    def spray_mouseReleaseEvent(self, e):
        self.generic_mouseReleaseEvent(e)

    # Text events

    def keyPressEvent(self, e):
        if self.mode == 'text':
            if e.key() == Qt.Key_Backspace:
                self.current_text = self.current_text[:-1]
            else:
                self.current_text = self.current_text + e.text()

    def text_mousePressEvent(self, e):
        if e.button() == Qt.LeftButton and self.current_pos is None:
            self.current_pos = e.pos()
            self.current_text = ""
            self.timer_event = self.text_timerEvent

        elif e.button() == Qt.LeftButton:

            self.timer_cleanup()
            # Draw the text to the image
            p = QPainter(self.pixmap())
            p.setRenderHints(QPainter.Antialiasing)
            font = build_font(self.config)
            p.setFont(font)
            pen = QPen(self.primary_color, 1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            p.setPen(pen)
            p.drawText(self.current_pos, self.current_text)
            self.update()

            self.reset_mode()

        elif e.button() == Qt.RightButton and self.current_pos:
            self.reset_mode()

    def text_timerEvent(self, final=False):
        p = QPainter(self.pixmap())
        p.setCompositionMode(QPainter.RasterOp_SourceXorDestination)
        pen = PREVIEW_PEN
        p.setPen(pen)
        if self.last_text:
            font = build_font(self.last_config)
            p.setFont(font)
            p.drawText(self.current_pos, self.last_text)

        if not final:
            font = build_font(self.config)
            p.setFont(font)
            p.drawText(self.current_pos, self.current_text)

        self.last_text = self.current_text
        self.last_config = self.config.copy()
        self.update()

    # Fill events

    def fill_mousePressEvent(self, e):

        if e.button() == Qt.LeftButton:
            self.active_color = self.primary_color
        else:
            self.active_color = self.secondary_color

        image = self.pixmap().toImage()
        w, h = image.width(), image.height()
        x, y = e.x(), e.y()

        # Get our target color from origin.
        target_color = image.pixel(x,y)

        have_seen = set()
        queue = [(x, y)]

        def get_cardinal_points(have_seen, center_pos):
            points = []
            cx, cy = center_pos
            for x, y in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
                xx, yy = cx + x, cy + y
                if (xx >= 0 and xx < w and
                    yy >= 0 and yy < h and
                    (xx, yy) not in have_seen):

                    points.append((xx, yy))
                    have_seen.add((xx, yy))

            return points

        # Now perform the search and fill.
        p = QPainter(self.pixmap())
        p.setPen(QPen(self.active_color))

        while queue:
            x, y = queue.pop()
            if image.pixel(x, y) == target_color:
                p.drawPoint(QPoint(x, y))
                queue.extend(get_cardinal_points(have_seen, (x, y)))

        self.update()

    # Dropper events

    def dropper_mousePressEvent(self, e):
        c = self.pixmap().toImage().pixel(e.pos())
        hex = QColor(c).name()

        if e.button() == Qt.LeftButton:
            self.set_primary_color(hex)
            self.primary_color_updated.emit(hex)  # Update UI.

        elif e.button() == Qt.RightButton:
            self.set_secondary_color(hex)
            self.secondary_color_updated.emit(hex)  # Update UI.

    # Generic shape events: Rectangle, Ellipse, Rounded-rect

    def generic_shape_mousePressEvent(self, e):
        self.origin_pos = e.pos()
        self.current_pos = e.pos()
        self.timer_event = self.generic_shape_timerEvent

    def generic_shape_timerEvent(self, final=False):
        p = QPainter(self.pixmap())
        p.setCompositionMode(QPainter.RasterOp_SourceXorDestination)
        pen = self.preview_pen
        pen.setDashOffset(self.dash_offset)
        p.setPen(pen)
        if self.last_pos:
            getattr(p, self.active_shape_fn)(QRect(self.origin_pos, self.last_pos), *self.active_shape_args)

        if not final:
            self.dash_offset -= 1
            pen.setDashOffset(self.dash_offset)
            p.setPen(pen)
            getattr(p, self.active_shape_fn)(QRect(self.origin_pos, self.current_pos), *self.active_shape_args)

        self.update()
        self.last_pos = self.current_pos

    def generic_shape_mouseMoveEvent(self, e):
        self.current_pos = e.pos()

    def generic_shape_mouseReleaseEvent(self, e):
        if self.last_pos:
            # Clear up indicator.
            self.timer_cleanup()

            p = QPainter(self.pixmap())
            p.setPen(QPen(self.primary_color, self.config['size'], Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin))

            if self.config['fill']:
                p.setBrush(QBrush(self.secondary_color))
            getattr(p, self.active_shape_fn)(QRect(self.origin_pos, e.pos()), *self.active_shape_args)
            self.update()

        self.reset_mode()

    # Line events

    def line_mousePressEvent(self, e):
        self.origin_pos = e.pos()
        self.current_pos = e.pos()
        self.preview_pen = PREVIEW_PEN
        self.timer_event = self.line_timerEvent

    def line_timerEvent(self, final=False):
        p = QPainter(self.pixmap())
        p.setCompositionMode(QPainter.RasterOp_SourceXorDestination)
        pen = self.preview_pen
        p.setPen(pen)
        if self.last_pos:
            p.drawLine(self.origin_pos, self.last_pos)

        if not final:
            p.drawLine(self.origin_pos, self.current_pos)

        self.update()
        self.last_pos = self.current_pos

    def line_mouseMoveEvent(self, e):
        self.current_pos = e.pos()

    def line_mouseReleaseEvent(self, e):
        if self.last_pos:
            # Clear up indicator.
            self.timer_cleanup()

            p = QPainter(self.pixmap())
            p.setPen(QPen(self.primary_color, self.config['size'], Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))

            p.drawLine(self.origin_pos, e.pos())
            self.update()

        self.reset_mode()

    # Generic poly events
    def generic_poly_mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            if self.history_pos:
                self.history_pos.append(e.pos())
            else:
                self.history_pos = [e.pos()]
                self.current_pos = e.pos()
                self.timer_event = self.generic_poly_timerEvent

        elif e.button() == Qt.RightButton and self.history_pos:
            # Clean up, we're not drawing
            self.timer_cleanup()
            self.reset_mode()

    def generic_poly_timerEvent(self, final=False):
        p = QPainter(self.pixmap())
        p.setCompositionMode(QPainter.RasterOp_SourceXorDestination)
        pen = self.preview_pen
        pen.setDashOffset(self.dash_offset)
        p.setPen(pen)
        if self.last_history:
            getattr(p, self.active_shape_fn)(*self.last_history)

        if not final:
            self.dash_offset -= 1
            pen.setDashOffset(self.dash_offset)
            p.setPen(pen)
            getattr(p, self.active_shape_fn)(*self.history_pos + [self.current_pos])

        self.update()
        self.last_pos = self.current_pos
        self.last_history = self.history_pos + [self.current_pos]

    def generic_poly_mouseMoveEvent(self, e):
        self.current_pos = e.pos()

    def generic_poly_mouseDoubleClickEvent(self, e):
        self.timer_cleanup()
        p = QPainter(self.pixmap())
        p.setPen(QPen(self.primary_color, self.config['size'], Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))

        # Note the brush is ignored for polylines.
        if self.secondary_color:
            p.setBrush(QBrush(self.secondary_color))

        getattr(p, self.active_shape_fn)(*self.history_pos + [e.pos()])
        self.update()
        self.reset_mode()

    # Polyline events

    def polyline_mousePressEvent(self, e):
        self.active_shape_fn = 'drawPolyline'
        self.preview_pen = PREVIEW_PEN
        self.generic_poly_mousePressEvent(e)

    def polyline_timerEvent(self, final=False):
        self.generic_poly_timerEvent(final)

    def polyline_mouseMoveEvent(self, e):
        self.generic_poly_mouseMoveEvent(e)

    def polyline_mouseDoubleClickEvent(self, e):
        self.generic_poly_mouseDoubleClickEvent(e)

    # Rectangle events

    def rect_mousePressEvent(self, e):
        self.active_shape_fn = 'drawRect'
        self.active_shape_args = ()
        self.preview_pen = PREVIEW_PEN
        self.generic_shape_mousePressEvent(e)

    def rect_timerEvent(self, final=False):
        self.generic_shape_timerEvent(final)

    def rect_mouseMoveEvent(self, e):
        self.generic_shape_mouseMoveEvent(e)

    def rect_mouseReleaseEvent(self, e):
        self.generic_shape_mouseReleaseEvent(e)

    # Polygon events

    def polygon_mousePressEvent(self, e):
        self.active_shape_fn = 'drawPolygon'
        self.preview_pen = PREVIEW_PEN
        self.generic_poly_mousePressEvent(e)

    def polygon_timerEvent(self, final=False):
        self.generic_poly_timerEvent(final)

    def polygon_mouseMoveEvent(self, e):
        self.generic_poly_mouseMoveEvent(e)

    def polygon_mouseDoubleClickEvent(self, e):
        self.generic_poly_mouseDoubleClickEvent(e)

    # Ellipse events

    def ellipse_mousePressEvent(self, e):
        self.active_shape_fn = 'drawEllipse'
        self.active_shape_args = ()
        self.preview_pen = PREVIEW_PEN
        self.generic_shape_mousePressEvent(e)

    def ellipse_timerEvent(self, final=False):
        self.generic_shape_timerEvent(final)

    def ellipse_mouseMoveEvent(self, e):
        self.generic_shape_mouseMoveEvent(e)

    def ellipse_mouseReleaseEvent(self, e):
        self.generic_shape_mouseReleaseEvent(e)

    # Roundedrect events

    def roundrect_mousePressEvent(self, e):
        self.active_shape_fn = 'drawRoundedRect'
        self.active_shape_args = (25, 25)
        self.preview_pen = PREVIEW_PEN
        self.generic_shape_mousePressEvent(e)

    def roundrect_timerEvent(self, final=False):
        self.generic_shape_timerEvent(final)

    def roundrect_mouseMoveEvent(self, e):
        self.generic_shape_mouseMoveEvent(e)

    def roundrect_mouseReleaseEvent(self, e):
        self.generic_shape_mouseReleaseEvent(e)


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)

        # Replace canvas placeholder from QtDesigner.
        self.horizontalLayout.removeWidget(self.canvas)
        self.canvas = Canvas()
        self.canvas.initialize()
        # We need to enable mouse tracking to follow the mouse without the button pressed.
        self.canvas.setMouseTracking(True)
        # Enable focus to capture key inputs.
        self.canvas.setFocusPolicy(Qt.StrongFocus)
        self.horizontalLayout.addWidget(self.canvas)

        # Setup the mode buttons
        mode_group = QButtonGroup(self)
        mode_group.setExclusive(True)

        for mode in MODES:
            btn = getattr(self, '%sButton' % mode)
            btn.pressed.connect(lambda mode=mode: self.canvas.set_mode(mode))
            mode_group.addButton(btn)

        # Setup the color selection buttons.
        self.primaryButton.pressed.connect(lambda: self.choose_color(self.set_primary_color))
        self.secondaryButton.pressed.connect(lambda: self.choose_color(self.set_secondary_color))

        # Initialize button colours.
        for n, hex in enumerate(COLORS, 1):
            btn = getattr(self, 'colorButton_%d' % n)
            btn.setStyleSheet('QPushButton { background-color: %s; }' % hex)
            btn.hex = hex  # For use in the event below

            def patch_mousePressEvent(self_, e):
                if e.button() == Qt.LeftButton:
                    self.set_primary_color(self_.hex)

                elif e.button() == Qt.RightButton:
                    self.set_secondary_color(self_.hex)

            btn.mousePressEvent = types.MethodType(patch_mousePressEvent, btn)

        # Setup up action signals
        self.actionCopy.triggered.connect(self.copy_to_clipboard)

        # Initialize animation timer.
        self.timer = QTimer()
        self.timer.timeout.connect(self.canvas.on_timer)
        self.timer.setInterval(100)
        self.timer.start()

        # Setup to agree with Canvas.
        self.set_primary_color('#000000')
        self.set_secondary_color('#ffffff')

        # Signals for canvas-initiated color changes (dropper).
        self.canvas.primary_color_updated.connect(self.set_primary_color)
        self.canvas.secondary_color_updated.connect(self.set_secondary_color)

        # Setup the stamp state.
        self.current_stamp_n = -1
        self.next_stamp()
        self.stampnextButton.pressed.connect(self.next_stamp)

        # Menu options
        self.actionNewImage.triggered.connect(self.canvas.initialize)
        self.actionOpenImage.triggered.connect(self.open_file)
        self.actionSaveImage.triggered.connect(self.save_file)
        self.actionClearImage.triggered.connect(self.canvas.reset)
        self.actionInvertColors.triggered.connect(self.invert)
        self.actionFlipHorizontal.triggered.connect(self.flip_horizontal)
        self.actionFlipVertical.triggered.connect(self.flip_vertical)

        # Setup the drawing toolbar.
        self.fontselect = QFontComboBox()
        self.fontToolbar.addWidget(self.fontselect)
        self.fontselect.currentFontChanged.connect(lambda f: self.canvas.set_config('font', f))
        self.fontselect.setCurrentFont(QFont('Times'))

        self.fontsize = QComboBox()
        self.fontsize.addItems([str(s) for s in FONT_SIZES])
        self.fontsize.currentTextChanged.connect(lambda f: self.canvas.set_config('fontsize', int(f)))

        # Connect to the signal producing the text of the current selection. Convert the string to float
        # and set as the pointsize. We could also use the index + retrieve from FONT_SIZES.
        self.fontToolbar.addWidget(self.fontsize)

        self.fontToolbar.addAction(self.actionBold)
        self.actionBold.triggered.connect(lambda s: self.canvas.set_config('bold', s))
        self.fontToolbar.addAction(self.actionItalic)
        self.actionItalic.triggered.connect(lambda s: self.canvas.set_config('italic', s))
        self.fontToolbar.addAction(self.actionUnderline)
        self.actionUnderline.triggered.connect(lambda s: self.canvas.set_config('underline', s))

        sizeicon = QLabel()
        sizeicon.setPixmap(QPixmap(os.path.join('images', 'border-weight.png')))
        self.drawingToolbar.addWidget(sizeicon)
        self.sizeselect = QSlider()
        self.sizeselect.setRange(1,20)
        self.sizeselect.setOrientation(Qt.Horizontal)
        self.sizeselect.valueChanged.connect(lambda s: self.canvas.set_config('size', s))
        self.drawingToolbar.addWidget(self.sizeselect)

        self.actionFillShapes.triggered.connect(lambda s: self.canvas.set_config('fill', s))
        self.drawingToolbar.addAction(self.actionFillShapes)
        self.actionFillShapes.setChecked(True)

        self.show()
        
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(549, 452)
        self.centralWidget = QWidget(MainWindow)
        sizePolicy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.centralWidget.sizePolicy().hasHeightForWidth())
        self.centralWidget.setSizePolicy(sizePolicy)
        self.centralWidget.setObjectName("centralWidget")
        self.verticalLayout = QVBoxLayout(self.centralWidget)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setSpacing(6)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.widget = QWidget(self.centralWidget)
        sizePolicy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget.sizePolicy().hasHeightForWidth())
        self.widget.setSizePolicy(sizePolicy)
        self.widget.setObjectName("widget")
        self.gridLayout = QGridLayout(self.widget)
        self.gridLayout.setContentsMargins(11, 11, 11, 11)
        self.gridLayout.setSpacing(15)
        self.gridLayout.setObjectName("gridLayout")
        self.rectButton = QPushButton(self.widget)
        self.rectButton.setMinimumSize(QSize(30, 30))
        self.rectButton.setMaximumSize(QSize(30, 30))
        self.rectButton.setText("")
        icon = QIcon()
        icon.addPixmap(QPixmap("images/layer-shape.png"), QIcon.Normal, QIcon.Off)
        self.rectButton.setIcon(icon)
        self.rectButton.setCheckable(True)
        self.rectButton.setObjectName("rectButton")
        self.gridLayout.addWidget(self.rectButton, 6, 0, 1, 1)
        self.polylineButton = QPushButton(self.widget)
        self.polylineButton.setMinimumSize(QSize(30, 30))
        self.polylineButton.setMaximumSize(QSize(30, 30))
        self.polylineButton.setText("")
        icon1 = QIcon()
        icon1.addPixmap(QPixmap("images/layer-shape-polyline.png"), QIcon.Normal, QIcon.Off)
        self.polylineButton.setIcon(icon1)
        self.polylineButton.setCheckable(True)
        self.polylineButton.setObjectName("polylineButton")
        self.gridLayout.addWidget(self.polylineButton, 5, 1, 1, 1)
        self.selectrectButton = QPushButton(self.widget)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.selectrectButton.sizePolicy().hasHeightForWidth())
        self.selectrectButton.setSizePolicy(sizePolicy)
        self.selectrectButton.setMinimumSize(QSize(30, 30))
        self.selectrectButton.setMaximumSize(QSize(30, 30))
        self.selectrectButton.setText("")
        icon2 = QIcon()
        icon2.addPixmap(QPixmap("images/selection.png"), QIcon.Normal, QIcon.Off)
        self.selectrectButton.setIcon(icon2)
        self.selectrectButton.setCheckable(True)
        self.selectrectButton.setObjectName("selectrectButton")
        self.gridLayout.addWidget(self.selectrectButton, 0, 1, 1, 1)
        self.eraserButton = QPushButton(self.widget)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.eraserButton.sizePolicy().hasHeightForWidth())
        self.eraserButton.setSizePolicy(sizePolicy)
        self.eraserButton.setMinimumSize(QSize(30, 30))
        self.eraserButton.setMaximumSize(QSize(30, 30))
        self.eraserButton.setText("")
        icon3 = QIcon()
        icon3.addPixmap(QPixmap("images/eraser.png"), QIcon.Normal, QIcon.Off)
        self.eraserButton.setIcon(icon3)
        self.eraserButton.setCheckable(True)
        self.eraserButton.setObjectName("eraserButton")
        self.gridLayout.addWidget(self.eraserButton, 1, 0, 1, 1)
        self.stampButton = QPushButton(self.widget)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.stampButton.sizePolicy().hasHeightForWidth())
        self.stampButton.setSizePolicy(sizePolicy)
        self.stampButton.setMinimumSize(QSize(30, 30))
        self.stampButton.setMaximumSize(QSize(30, 30))
        self.stampButton.setText("")
        icon4 = QIcon()
        icon4.addPixmap(QPixmap("images/cake.png"), QIcon.Normal, QIcon.Off)
        self.stampButton.setIcon(icon4)
        self.stampButton.setCheckable(True)
        self.stampButton.setObjectName("stampButton")
        self.gridLayout.addWidget(self.stampButton, 2, 1, 1, 1)
        self.dropperButton = QPushButton(self.widget)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.dropperButton.sizePolicy().hasHeightForWidth())
        self.dropperButton.setSizePolicy(sizePolicy)
        self.dropperButton.setMinimumSize(QSize(30, 30))
        self.dropperButton.setMaximumSize(QSize(30, 30))
        self.dropperButton.setText("")
        icon5 = QIcon()
        icon5.addPixmap(QPixmap("images/pipette.png"), QIcon.Normal, QIcon.Off)
        self.dropperButton.setIcon(icon5)
        self.dropperButton.setCheckable(True)
        self.dropperButton.setObjectName("dropperButton")
        self.gridLayout.addWidget(self.dropperButton, 2, 0, 1, 1)
        self.selectpolyButton = QPushButton(self.widget)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.selectpolyButton.sizePolicy().hasHeightForWidth())
        self.selectpolyButton.setSizePolicy(sizePolicy)
        self.selectpolyButton.setMinimumSize(QSize(30, 30))
        self.selectpolyButton.setMaximumSize(QSize(30, 30))
        self.selectpolyButton.setText("")
        icon6 = QIcon()
        icon6.addPixmap(QPixmap("images/selection-poly.png"), QIcon.Normal, QIcon.Off)
        self.selectpolyButton.setIcon(icon6)
        self.selectpolyButton.setCheckable(True)
        self.selectpolyButton.setObjectName("selectpolyButton")
        self.gridLayout.addWidget(self.selectpolyButton, 0, 0, 1, 1)
        self.brushButton = QPushButton(self.widget)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.brushButton.sizePolicy().hasHeightForWidth())
        self.brushButton.setSizePolicy(sizePolicy)
        self.brushButton.setMinimumSize(QSize(30, 30))
        self.brushButton.setMaximumSize(QSize(30, 30))
        self.brushButton.setText("")
        icon7 = QIcon()
        icon7.addPixmap(QPixmap("images/paint-brush.png"), QIcon.Normal, QIcon.Off)
        self.brushButton.setIcon(icon7)
        self.brushButton.setCheckable(True)
        self.brushButton.setObjectName("brushButton")
        self.gridLayout.addWidget(self.brushButton, 3, 1, 1, 1)
        self.penButton = QPushButton(self.widget)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.penButton.sizePolicy().hasHeightForWidth())
        self.penButton.setSizePolicy(sizePolicy)
        self.penButton.setMinimumSize(QSize(30, 30))
        self.penButton.setMaximumSize(QSize(30, 30))
        self.penButton.setText("")
        icon8 = QIcon()
        icon8.addPixmap(QPixmap("images/pencil.png"), QIcon.Normal, QIcon.Off)
        self.penButton.setIcon(icon8)
        self.penButton.setCheckable(True)
        self.penButton.setObjectName("penButton")
        self.gridLayout.addWidget(self.penButton, 3, 0, 1, 1)
        self.fillButton = QPushButton(self.widget)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.fillButton.sizePolicy().hasHeightForWidth())
        self.fillButton.setSizePolicy(sizePolicy)
        self.fillButton.setMinimumSize(QSize(30, 30))
        self.fillButton.setMaximumSize(QSize(30, 30))
        self.fillButton.setText("")
        icon9 = QIcon()
        icon9.addPixmap(QPixmap("images/paint-can.png"), QIcon.Normal, QIcon.Off)
        self.fillButton.setIcon(icon9)
        self.fillButton.setCheckable(True)
        self.fillButton.setObjectName("fillButton")
        self.gridLayout.addWidget(self.fillButton, 1, 1, 1, 1)
        self.textButton = QPushButton(self.widget)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.textButton.sizePolicy().hasHeightForWidth())
        self.textButton.setSizePolicy(sizePolicy)
        self.textButton.setMinimumSize(QSize(30, 30))
        self.textButton.setMaximumSize(QSize(30, 30))
        self.textButton.setText("")
        icon10 = QIcon()
        icon10.addPixmap(QPixmap("images/edit.png"), QIcon.Normal, QIcon.Off)
        self.textButton.setIcon(icon10)
        self.textButton.setCheckable(True)
        self.textButton.setObjectName("textButton")
        self.gridLayout.addWidget(self.textButton, 4, 1, 1, 1)
        self.polygonButton = QPushButton(self.widget)
        self.polygonButton.setMinimumSize(QSize(30, 30))
        self.polygonButton.setMaximumSize(QSize(30, 30))
        self.polygonButton.setText("")
        icon11 = QIcon()
        icon11.addPixmap(QPixmap("images/layer-shape-polygon.png"), QIcon.Normal, QIcon.Off)
        self.polygonButton.setIcon(icon11)
        self.polygonButton.setCheckable(True)
        self.polygonButton.setObjectName("polygonButton")
        self.gridLayout.addWidget(self.polygonButton, 6, 1, 1, 1)
        self.roundrectButton = QPushButton(self.widget)
        self.roundrectButton.setMinimumSize(QSize(30, 30))
        self.roundrectButton.setMaximumSize(QSize(30, 30))
        self.roundrectButton.setText("")
        icon12 = QIcon()
        icon12.addPixmap(QPixmap("images/layer-shape-round.png"), QIcon.Normal, QIcon.Off)
        self.roundrectButton.setIcon(icon12)
        self.roundrectButton.setCheckable(True)
        self.roundrectButton.setObjectName("roundrectButton")
        self.gridLayout.addWidget(self.roundrectButton, 7, 1, 1, 1)
        self.ellipseButton = QPushButton(self.widget)
        self.ellipseButton.setMinimumSize(QSize(30, 30))
        self.ellipseButton.setMaximumSize(QSize(30, 30))
        self.ellipseButton.setText("")
        icon13 = QIcon()
        icon13.addPixmap(QPixmap("images/layer-shape-ellipse.png"), QIcon.Normal, QIcon.Off)
        self.ellipseButton.setIcon(icon13)
        self.ellipseButton.setCheckable(True)
        self.ellipseButton.setObjectName("ellipseButton")
        self.gridLayout.addWidget(self.ellipseButton, 7, 0, 1, 1)
        self.lineButton = QPushButton(self.widget)
        self.lineButton.setMinimumSize(QSize(30, 30))
        self.lineButton.setMaximumSize(QSize(30, 30))
        self.lineButton.setText("")
        icon14 = QIcon()
        icon14.addPixmap(QPixmap("images/layer-shape-line.png"), QIcon.Normal, QIcon.Off)
        self.lineButton.setIcon(icon14)
        self.lineButton.setCheckable(True)
        self.lineButton.setObjectName("lineButton")
        self.gridLayout.addWidget(self.lineButton, 5, 0, 1, 1)
        self.sprayButton = QPushButton(self.widget)
        sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sprayButton.sizePolicy().hasHeightForWidth())
        self.sprayButton.setSizePolicy(sizePolicy)
        self.sprayButton.setMinimumSize(QSize(30, 30))
        self.sprayButton.setMaximumSize(QSize(30, 30))
        self.sprayButton.setText("")
        icon15 = QIcon()
        icon15.addPixmap(QPixmap("images/spray.png"), QIcon.Normal, QIcon.Off)
        self.sprayButton.setIcon(icon15)
        self.sprayButton.setCheckable(True)
        self.sprayButton.setFlat(False)
        self.sprayButton.setObjectName("sprayButton")
        self.gridLayout.addWidget(self.sprayButton, 4, 0, 1, 1)
        self.verticalLayout_2.addWidget(self.widget)
        spacerItem = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem)
        self.horizontalLayout.addLayout(self.verticalLayout_2)
        self.canvas = QLabel(self.centralWidget)
        sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.canvas.sizePolicy().hasHeightForWidth())
        self.canvas.setSizePolicy(sizePolicy)
        self.canvas.setText("")
        self.canvas.setObjectName("canvas")
        self.horizontalLayout.addWidget(self.canvas)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(6)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.widget_3 = QWidget(self.centralWidget)
        self.widget_3.setMinimumSize(QSize(78, 0))
        self.widget_3.setMaximumSize(QSize(78, 16777215))
        self.widget_3.setObjectName("widget_3")
        self.secondaryButton = QPushButton(self.widget_3)
        self.secondaryButton.setGeometry(QRect(30, 10, 40, 40))
        self.secondaryButton.setMinimumSize(QSize(40, 40))
        self.secondaryButton.setMaximumSize(QSize(40, 40))
        self.secondaryButton.setText("")
        self.secondaryButton.setObjectName("secondaryButton")
        self.primaryButton = QPushButton(self.widget_3)
        self.primaryButton.setGeometry(QRect(10, 0, 40, 40))
        self.primaryButton.setMinimumSize(QSize(40, 40))
        self.primaryButton.setMaximumSize(QSize(40, 40))
        self.primaryButton.setText("")
        self.primaryButton.setObjectName("primaryButton")
        self.horizontalLayout_2.addWidget(self.widget_3)
        self.widget_2 = QWidget(self.centralWidget)
        self.widget_2.setObjectName("widget_2")
        self.gridLayout_2 = QGridLayout(self.widget_2)
        self.gridLayout_2.setContentsMargins(15, 0, 15, 15)
        self.gridLayout_2.setSpacing(15)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.colorButton_11 = QPushButton(self.widget_2)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.colorButton_11.sizePolicy().hasHeightForWidth())
        self.colorButton_11.setSizePolicy(sizePolicy)
        self.colorButton_11.setMinimumSize(QSize(20, 20))
        self.colorButton_11.setMaximumSize(QSize(20, 13))
        self.colorButton_11.setText("")
        self.colorButton_11.setObjectName("colorButton_11")
        self.gridLayout_2.addWidget(self.colorButton_11, 0, 10, 1, 1)
        self.colorButton_7 = QPushButton(self.widget_2)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.colorButton_7.sizePolicy().hasHeightForWidth())
        self.colorButton_7.setSizePolicy(sizePolicy)
        self.colorButton_7.setMinimumSize(QSize(20, 20))
        self.colorButton_7.setMaximumSize(QSize(20, 13))
        self.colorButton_7.setText("")
        self.colorButton_7.setObjectName("colorButton_7")
        self.gridLayout_2.addWidget(self.colorButton_7, 0, 6, 1, 1)
        self.colorButton_9 = QPushButton(self.widget_2)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.colorButton_9.sizePolicy().hasHeightForWidth())
        self.colorButton_9.setSizePolicy(sizePolicy)
        self.colorButton_9.setMinimumSize(QSize(20, 20))
        self.colorButton_9.setMaximumSize(QSize(20, 13))
        self.colorButton_9.setText("")
        self.colorButton_9.setObjectName("colorButton_9")
        self.gridLayout_2.addWidget(self.colorButton_9, 0, 8, 1, 1)
        self.colorButton_10 = QPushButton(self.widget_2)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.colorButton_10.sizePolicy().hasHeightForWidth())
        self.colorButton_10.setSizePolicy(sizePolicy)
        self.colorButton_10.setMinimumSize(QSize(20, 20))
        self.colorButton_10.setMaximumSize(QSize(20, 13))
        self.colorButton_10.setText("")
        self.colorButton_10.setObjectName("colorButton_10")
        self.gridLayout_2.addWidget(self.colorButton_10, 0, 9, 1, 1)
        self.colorButton_23 = QPushButton(self.widget_2)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.colorButton_23.sizePolicy().hasHeightForWidth())
        self.colorButton_23.setSizePolicy(sizePolicy)
        self.colorButton_23.setMinimumSize(QSize(20, 20))
        self.colorButton_23.setMaximumSize(QSize(20, 13))
        self.colorButton_23.setText("")
        self.colorButton_23.setObjectName("colorButton_23")
        self.gridLayout_2.addWidget(self.colorButton_23, 1, 8, 1, 1)
        self.colorButton_18 = QPushButton(self.widget_2)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.colorButton_18.sizePolicy().hasHeightForWidth())
        self.colorButton_18.setSizePolicy(sizePolicy)
        self.colorButton_18.setMinimumSize(QSize(20, 20))
        self.colorButton_18.setMaximumSize(QSize(20, 13))
        self.colorButton_18.setText("")
        self.colorButton_18.setObjectName("colorButton_18")
        self.gridLayout_2.addWidget(self.colorButton_18, 1, 3, 1, 1)
        self.colorButton_20 = QPushButton(self.widget_2)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.colorButton_20.sizePolicy().hasHeightForWidth())
        self.colorButton_20.setSizePolicy(sizePolicy)
        self.colorButton_20.setMinimumSize(QSize(20, 20))
        self.colorButton_20.setMaximumSize(QSize(20, 13))
        self.colorButton_20.setText("")
        self.colorButton_20.setObjectName("colorButton_20")
        self.gridLayout_2.addWidget(self.colorButton_20, 1, 5, 1, 1)
        self.colorButton_6 = QPushButton(self.widget_2)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.colorButton_6.sizePolicy().hasHeightForWidth())
        self.colorButton_6.setSizePolicy(sizePolicy)
        self.colorButton_6.setMinimumSize(QSize(20, 20))
        self.colorButton_6.setMaximumSize(QSize(20, 13))
        self.colorButton_6.setText("")
        self.colorButton_6.setObjectName("colorButton_6")
        self.gridLayout_2.addWidget(self.colorButton_6, 0, 5, 1, 1)
        self.colorButton_3 = QPushButton(self.widget_2)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.colorButton_3.sizePolicy().hasHeightForWidth())
        self.colorButton_3.setSizePolicy(sizePolicy)
        self.colorButton_3.setMinimumSize(QSize(20, 20))
        self.colorButton_3.setMaximumSize(QSize(20, 13))
        self.colorButton_3.setText("")
        self.colorButton_3.setObjectName("colorButton_3")
        self.gridLayout_2.addWidget(self.colorButton_3, 0, 2, 1, 1)
        self.colorButton_24 = QPushButton(self.widget_2)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.colorButton_24.sizePolicy().hasHeightForWidth())
        self.colorButton_24.setSizePolicy(sizePolicy)
        self.colorButton_24.setMinimumSize(QSize(20, 20))
        self.colorButton_24.setMaximumSize(QSize(20, 13))
        self.colorButton_24.setText("")
        self.colorButton_24.setObjectName("colorButton_24")
        self.gridLayout_2.addWidget(self.colorButton_24, 1, 9, 1, 1)
        self.colorButton_17 = QPushButton(self.widget_2)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.colorButton_17.sizePolicy().hasHeightForWidth())
        self.colorButton_17.setSizePolicy(sizePolicy)
        self.colorButton_17.setMinimumSize(QSize(20, 20))
        self.colorButton_17.setMaximumSize(QSize(20, 13))
        self.colorButton_17.setText("")
        self.colorButton_17.setObjectName("colorButton_17")
        self.gridLayout_2.addWidget(self.colorButton_17, 1, 2, 1, 1)
        self.colorButton_1 = QPushButton(self.widget_2)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.colorButton_1.sizePolicy().hasHeightForWidth())
        self.colorButton_1.setSizePolicy(sizePolicy)
        self.colorButton_1.setMinimumSize(QSize(20, 20))
        self.colorButton_1.setMaximumSize(QSize(20, 13))
        self.colorButton_1.setStyleSheet("")
        self.colorButton_1.setText("")
        self.colorButton_1.setObjectName("colorButton_1")
        self.gridLayout_2.addWidget(self.colorButton_1, 0, 0, 1, 1)
        self.colorButton_8 = QPushButton(self.widget_2)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.colorButton_8.sizePolicy().hasHeightForWidth())
        self.colorButton_8.setSizePolicy(sizePolicy)
        self.colorButton_8.setMinimumSize(QSize(20, 20))
        self.colorButton_8.setMaximumSize(QSize(20, 13))
        self.colorButton_8.setText("")
        self.colorButton_8.setObjectName("colorButton_8")
        self.gridLayout_2.addWidget(self.colorButton_8, 0, 7, 1, 1)
        self.colorButton_27 = QPushButton(self.widget_2)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.colorButton_27.sizePolicy().hasHeightForWidth())
        self.colorButton_27.setSizePolicy(sizePolicy)
        self.colorButton_27.setMinimumSize(QSize(20, 20))
        self.colorButton_27.setMaximumSize(QSize(20, 13))
        self.colorButton_27.setText("")
        self.colorButton_27.setObjectName("colorButton_27")
        self.gridLayout_2.addWidget(self.colorButton_27, 1, 12, 1, 1)
        self.colorButton_22 = QPushButton(self.widget_2)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.colorButton_22.sizePolicy().hasHeightForWidth())
        self.colorButton_22.setSizePolicy(sizePolicy)
        self.colorButton_22.setMinimumSize(QSize(20, 20))
        self.colorButton_22.setMaximumSize(QSize(20, 13))
        self.colorButton_22.setText("")
        self.colorButton_22.setObjectName("colorButton_22")
        self.gridLayout_2.addWidget(self.colorButton_22, 1, 7, 1, 1)
        self.colorButton_15 = QPushButton(self.widget_2)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.colorButton_15.sizePolicy().hasHeightForWidth())
        self.colorButton_15.setSizePolicy(sizePolicy)
        self.colorButton_15.setMinimumSize(QSize(20, 20))
        self.colorButton_15.setMaximumSize(QSize(20, 13))
        self.colorButton_15.setText("")
        self.colorButton_15.setObjectName("colorButton_15")
        self.gridLayout_2.addWidget(self.colorButton_15, 1, 0, 1, 1)
        self.colorButton_5 = QPushButton(self.widget_2)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.colorButton_5.sizePolicy().hasHeightForWidth())
        self.colorButton_5.setSizePolicy(sizePolicy)
        self.colorButton_5.setMinimumSize(QSize(20, 20))
        self.colorButton_5.setMaximumSize(QSize(20, 13))
        self.colorButton_5.setText("")
        self.colorButton_5.setObjectName("colorButton_5")
        self.gridLayout_2.addWidget(self.colorButton_5, 0, 4, 1, 1)
        self.colorButton_2 = QPushButton(self.widget_2)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.colorButton_2.sizePolicy().hasHeightForWidth())
        self.colorButton_2.setSizePolicy(sizePolicy)
        self.colorButton_2.setMinimumSize(QSize(20, 20))
        self.colorButton_2.setMaximumSize(QSize(20, 13))
        self.colorButton_2.setText("")
        self.colorButton_2.setObjectName("colorButton_2")
        self.gridLayout_2.addWidget(self.colorButton_2, 0, 1, 1, 1)
        self.colorButton_16 = QPushButton(self.widget_2)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.colorButton_16.sizePolicy().hasHeightForWidth())
        self.colorButton_16.setSizePolicy(sizePolicy)
        self.colorButton_16.setMinimumSize(QSize(20, 20))
        self.colorButton_16.setMaximumSize(QSize(20, 13))
        self.colorButton_16.setText("")
        self.colorButton_16.setObjectName("colorButton_16")
        self.gridLayout_2.addWidget(self.colorButton_16, 1, 1, 1, 1)
        self.colorButton_14 = QPushButton(self.widget_2)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.colorButton_14.sizePolicy().hasHeightForWidth())
        self.colorButton_14.setSizePolicy(sizePolicy)
        self.colorButton_14.setMinimumSize(QSize(20, 20))
        self.colorButton_14.setMaximumSize(QSize(20, 13))
        self.colorButton_14.setText("")
        self.colorButton_14.setObjectName("colorButton_14")
        self.gridLayout_2.addWidget(self.colorButton_14, 0, 13, 1, 1)
        self.colorButton_4 = QPushButton(self.widget_2)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.colorButton_4.sizePolicy().hasHeightForWidth())
        self.colorButton_4.setSizePolicy(sizePolicy)
        self.colorButton_4.setMinimumSize(QSize(20, 20))
        self.colorButton_4.setMaximumSize(QSize(20, 13))
        self.colorButton_4.setText("")
        self.colorButton_4.setObjectName("colorButton_4")
        self.gridLayout_2.addWidget(self.colorButton_4, 0, 3, 1, 1)
        self.colorButton_21 = QPushButton(self.widget_2)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.colorButton_21.sizePolicy().hasHeightForWidth())
        self.colorButton_21.setSizePolicy(sizePolicy)
        self.colorButton_21.setMinimumSize(QSize(20, 20))
        self.colorButton_21.setMaximumSize(QSize(20, 13))
        self.colorButton_21.setText("")
        self.colorButton_21.setObjectName("colorButton_21")
        self.gridLayout_2.addWidget(self.colorButton_21, 1, 6, 1, 1)
        self.colorButton_25 = QPushButton(self.widget_2)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.colorButton_25.sizePolicy().hasHeightForWidth())
        self.colorButton_25.setSizePolicy(sizePolicy)
        self.colorButton_25.setMinimumSize(QSize(20, 20))
        self.colorButton_25.setMaximumSize(QSize(20, 13))
        self.colorButton_25.setText("")
        self.colorButton_25.setObjectName("colorButton_25")
        self.gridLayout_2.addWidget(self.colorButton_25, 1, 10, 1, 1)
        self.colorButton_12 = QPushButton(self.widget_2)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.colorButton_12.sizePolicy().hasHeightForWidth())
        self.colorButton_12.setSizePolicy(sizePolicy)
        self.colorButton_12.setMinimumSize(QSize(20, 20))
        self.colorButton_12.setMaximumSize(QSize(20, 13))
        self.colorButton_12.setText("")
        self.colorButton_12.setObjectName("colorButton_12")
        self.gridLayout_2.addWidget(self.colorButton_12, 0, 11, 1, 1)
        self.colorButton_19 = QPushButton(self.widget_2)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.colorButton_19.sizePolicy().hasHeightForWidth())
        self.colorButton_19.setSizePolicy(sizePolicy)
        self.colorButton_19.setMinimumSize(QSize(20, 20))
        self.colorButton_19.setMaximumSize(QSize(20, 13))
        self.colorButton_19.setText("")
        self.colorButton_19.setObjectName("colorButton_19")
        self.gridLayout_2.addWidget(self.colorButton_19, 1, 4, 1, 1)
        self.colorButton_13 = QPushButton(self.widget_2)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.colorButton_13.sizePolicy().hasHeightForWidth())
        self.colorButton_13.setSizePolicy(sizePolicy)
        self.colorButton_13.setMinimumSize(QSize(20, 20))
        self.colorButton_13.setMaximumSize(QSize(20, 13))
        self.colorButton_13.setText("")
        self.colorButton_13.setObjectName("colorButton_13")
        self.gridLayout_2.addWidget(self.colorButton_13, 0, 12, 1, 1)
        self.colorButton_26 = QPushButton(self.widget_2)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.colorButton_26.sizePolicy().hasHeightForWidth())
        self.colorButton_26.setSizePolicy(sizePolicy)
        self.colorButton_26.setMinimumSize(QSize(20, 20))
        self.colorButton_26.setMaximumSize(QSize(20, 13))
        self.colorButton_26.setText("")
        self.colorButton_26.setObjectName("colorButton_26")
        self.gridLayout_2.addWidget(self.colorButton_26, 1, 11, 1, 1)
        self.colorButton_28 = QPushButton(self.widget_2)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.colorButton_28.sizePolicy().hasHeightForWidth())
        self.colorButton_28.setSizePolicy(sizePolicy)
        self.colorButton_28.setMinimumSize(QSize(20, 20))
        self.colorButton_28.setMaximumSize(QSize(20, 13))
        self.colorButton_28.setText("")
        self.colorButton_28.setObjectName("colorButton_28")
        self.gridLayout_2.addWidget(self.colorButton_28, 1, 13, 1, 1)
        self.horizontalLayout_2.addWidget(self.widget_2)
        self.stampnextButton = QPushButton(self.centralWidget)
        self.stampnextButton.setMinimumSize(QSize(78, 55))
        self.stampnextButton.setMaximumSize(QSize(78, 55))
        self.stampnextButton.setText("")
        self.stampnextButton.setIconSize(QSize(80, 50))
        self.stampnextButton.setObjectName("stampnextButton")
        self.horizontalLayout_2.addWidget(self.stampnextButton)
        spacerItem1 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        MainWindow.setCentralWidget(self.centralWidget)
        self.menuBar = QMenuBar(MainWindow)
        self.menuBar.setGeometry(QRect(0, 0, 549, 22))
        self.menuBar.setObjectName("menuBar")
        self.menuFIle = QMenu(self.menuBar)
        self.menuFIle.setObjectName("menuFIle")
        self.menuEdit = QMenu(self.menuBar)
        self.menuEdit.setObjectName("menuEdit")
        self.menuImage = QMenu(self.menuBar)
        self.menuImage.setObjectName("menuImage")
        self.menuHelp = QMenu(self.menuBar)
        self.menuHelp.setObjectName("menuHelp")
        MainWindow.setMenuBar(self.menuBar)
        self.statusBar = QStatusBar(MainWindow)
        self.statusBar.setObjectName("statusBar")
        MainWindow.setStatusBar(self.statusBar)
        self.fileToolbar = QToolBar(MainWindow)
        self.fileToolbar.setIconSize(QSize(16, 16))
        self.fileToolbar.setObjectName("fileToolbar")
        MainWindow.addToolBar(Qt.TopToolBarArea, self.fileToolbar)
        self.drawingToolbar = QToolBar(MainWindow)
        self.drawingToolbar.setIconSize(QSize(16, 16))
        self.drawingToolbar.setObjectName("drawingToolbar")
        MainWindow.addToolBar(Qt.TopToolBarArea, self.drawingToolbar)
        self.fontToolbar = QToolBar(MainWindow)
        self.fontToolbar.setIconSize(QSize(16, 16))
        self.fontToolbar.setObjectName("fontToolbar")
        MainWindow.addToolBar(Qt.TopToolBarArea, self.fontToolbar)
        self.actionCopy = QAction(MainWindow)
        self.actionCopy.setObjectName("actionCopy")
        self.actionClearImage = QAction(MainWindow)
        self.actionClearImage.setObjectName("actionClearImage")
        self.actionOpenImage = QAction(MainWindow)
        icon16 = QIcon()
        icon16.addPixmap(QPixmap("images/blue-folder-open-image.png"), QIcon.Normal, QIcon.Off)
        self.actionOpenImage.setIcon(icon16)
        self.actionOpenImage.setObjectName("actionOpenImage")
        self.actionSaveImage = QAction(MainWindow)
        icon17 = QIcon()
        icon17.addPixmap(QPixmap("images/disk.png"), QIcon.Normal, QIcon.Off)
        self.actionSaveImage.setIcon(icon17)
        self.actionSaveImage.setObjectName("actionSaveImage")
        self.actionInvertColors = QAction(MainWindow)
        self.actionInvertColors.setObjectName("actionInvertColors")
        self.actionFlipHorizontal = QAction(MainWindow)
        self.actionFlipHorizontal.setObjectName("actionFlipHorizontal")
        self.actionFlipVertical = QAction(MainWindow)
        self.actionFlipVertical.setObjectName("actionFlipVertical")
        self.actionNewImage = QAction(MainWindow)
        icon18 = QIcon()
        icon18.addPixmap(QPixmap("images/document-image.png"), QIcon.Normal, QIcon.Off)
        self.actionNewImage.setIcon(icon18)
        self.actionNewImage.setObjectName("actionNewImage")
        self.actionBold = QAction(MainWindow)
        self.actionBold.setCheckable(True)
        icon19 = QIcon()
        icon19.addPixmap(QPixmap("images/edit-bold.png"), QIcon.Normal, QIcon.Off)
        self.actionBold.setIcon(icon19)
        self.actionBold.setObjectName("actionBold")
        self.actionItalic = QAction(MainWindow)
        self.actionItalic.setCheckable(True)
        icon20 = QIcon()
        icon20.addPixmap(QPixmap("images/edit-italic.png"), QIcon.Normal, QIcon.Off)
        self.actionItalic.setIcon(icon20)
        self.actionItalic.setObjectName("actionItalic")
        self.actionUnderline = QAction(MainWindow)
        self.actionUnderline.setCheckable(True)
        icon21 = QIcon()
        icon21.addPixmap(QPixmap("images/edit-underline.png"), QIcon.Normal, QIcon.Off)
        self.actionUnderline.setIcon(icon21)
        self.actionUnderline.setObjectName("actionUnderline")
        self.actionFillShapes = QAction(MainWindow)
        self.actionFillShapes.setCheckable(True)
        icon22 = QIcon()
        icon22.addPixmap(QPixmap("images/paint-can-color.png"), QIcon.Normal, QIcon.Off)
        self.actionFillShapes.setIcon(icon22)
        self.actionFillShapes.setObjectName("actionFillShapes")
        self.menuFIle.addAction(self.actionNewImage)
        self.menuFIle.addAction(self.actionOpenImage)
        self.menuFIle.addAction(self.actionSaveImage)
        self.menuEdit.addAction(self.actionCopy)
        self.menuEdit.addSeparator()
        self.menuEdit.addAction(self.actionClearImage)
        self.menuImage.addAction(self.actionInvertColors)
        self.menuImage.addSeparator()
        self.menuImage.addAction(self.actionFlipHorizontal)
        self.menuImage.addAction(self.actionFlipVertical)
        self.menuBar.addAction(self.menuFIle.menuAction())
        self.menuBar.addAction(self.menuEdit.menuAction())
        self.menuBar.addAction(self.menuImage.menuAction())
        self.menuBar.addAction(self.menuHelp.menuAction())
        self.fileToolbar.addAction(self.actionNewImage)
        self.fileToolbar.addAction(self.actionOpenImage)
        self.fileToolbar.addAction(self.actionSaveImage)

        self.retranslateUi(MainWindow)
        QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Piecasso"))
        self.menuFIle.setTitle(_translate("MainWindow", "FIle"))
        self.menuEdit.setTitle(_translate("MainWindow", "Edit"))
        self.menuImage.setTitle(_translate("MainWindow", "Image"))
        self.menuHelp.setTitle(_translate("MainWindow", "Help"))
        self.fileToolbar.setWindowTitle(_translate("MainWindow", "toolBar"))
        self.drawingToolbar.setWindowTitle(_translate("MainWindow", "toolBar"))
        self.fontToolbar.setWindowTitle(_translate("MainWindow", "toolBar"))
        self.actionCopy.setText(_translate("MainWindow", "Copy"))
        self.actionCopy.setShortcut(_translate("MainWindow", "Ctrl+C"))
        self.actionClearImage.setText(_translate("MainWindow", "Clear Image"))
        self.actionOpenImage.setText(_translate("MainWindow", "Open Image..."))
        self.actionSaveImage.setText(_translate("MainWindow", "Save Image As..."))
        self.actionInvertColors.setText(_translate("MainWindow", "Invert Colors"))
        self.actionFlipHorizontal.setText(_translate("MainWindow", "Flip Horizontal"))
        self.actionFlipVertical.setText(_translate("MainWindow", "Flip Vertical"))
        self.actionNewImage.setText(_translate("MainWindow", "New Image"))
        self.actionBold.setText(_translate("MainWindow", "Bold"))
        self.actionBold.setShortcut(_translate("MainWindow", "Ctrl+B"))
        self.actionItalic.setText(_translate("MainWindow", "Italic"))
        self.actionItalic.setShortcut(_translate("MainWindow", "Ctrl+I"))
        self.actionUnderline.setText(_translate("MainWindow", "Underline"))
        self.actionFillShapes.setText(_translate("MainWindow", "Fill Shapes?"))

    def choose_color(self, callback):
        dlg = QColorDialog()
        if dlg.exec():
            callback( dlg.selectedColor().name() )

    def set_primary_color(self, hex):
        self.canvas.set_primary_color(hex)
        self.primaryButton.setStyleSheet('QPushButton { background-color: %s; }' % hex)

    def set_secondary_color(self, hex):
        self.canvas.set_secondary_color(hex)
        self.secondaryButton.setStyleSheet('QPushButton { background-color: %s; }' % hex)

    def next_stamp(self):
        self.current_stamp_n += 1
        if self.current_stamp_n >= len(STAMPS):
            self.current_stamp_n = 0

        pixmap = QPixmap(STAMPS[self.current_stamp_n])
        self.stampnextButton.setIcon(QIcon(pixmap))

        self.canvas.current_stamp = pixmap

    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()

        if self.canvas.mode == 'selectrect' and self.canvas.locked:
            clipboard.setPixmap(self.canvas.selectrect_copy())

        elif self.canvas.mode == 'selectpoly' and self.canvas.locked:
            clipboard.setPixmap(self.canvas.selectpoly_copy())

        else:
            clipboard.setPixmap(self.canvas.pixmap())

    def open_file(self):
        """
        Open image file for editing, scaling the smaller dimension and cropping the remainder.
        :return:
        """
        path, _ = QFileDialog.getOpenFileName(self, "Open file", "", "PNG image files (*.png); JPEG image files (*jpg); All files (*.*)")

        if path:
            pixmap = QPixmap()
            pixmap.load(path)

            # We need to crop down to the size of our canvas. Get the size of the loaded image.
            iw = pixmap.width()
            ih = pixmap.height()

            # Get the size of the space we're filling.
            cw, ch = CANVAS_DIMENSIONS

            if iw/cw < ih/ch:  # The height is relatively bigger than the width.
                pixmap = pixmap.scaledToWidth(cw)
                hoff = (pixmap.height() - ch) // 2
                pixmap = pixmap.copy(
                    QRect(QPoint(0, hoff), QPoint(cw, pixmap.height()-hoff))
                )

            elif iw/cw > ih/ch:  # The height is relatively bigger than the width.
                pixmap = pixmap.scaledToHeight(ch)
                woff = (pixmap.width() - cw) // 2
                pixmap = pixmap.copy(
                    QRect(QPoint(woff, 0), QPoint(pixmap.width()-woff, ch))
                )

            self.canvas.setPixmap(pixmap)


    def save_file(self):
        """
        Save active canvas to image file.
        :return:
        """
        path, _ = QFileDialog.getSaveFileName(self, "Save file", "", "PNG Image file (*.png)")

        if path:
            pixmap = self.canvas.pixmap()
            pixmap.save(path, "PNG" )

    def invert(self):
        img = QImage(self.canvas.pixmap())
        img.invertPixels()
        pixmap = QPixmap()
        pixmap.convertFromImage(img)
        self.canvas.setPixmap(pixmap)

    def flip_horizontal(self):
        pixmap = self.canvas.pixmap()
        self.canvas.setPixmap(pixmap.transformed(QTransform().scale(-1, 1)))

    def flip_vertical(self):
        pixmap = self.canvas.pixmap()
        self.canvas.setPixmap(pixmap.transformed(QTransform().scale(1, -1)))



if __name__ == '__main__':

    app = QApplication([])
    window = MainWindow()
    app.exec_()
