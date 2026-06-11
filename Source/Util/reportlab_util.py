"""!
********************************************************************************
@file   reportlab_util.py
@brief  Utility classes and functions for creating styled PDF files with reportlab.
********************************************************************************
"""

import copy
from io import BytesIO
from typing import Any
from collections.abc import Callable
from PIL import Image as PILImage
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.lib.enums import TA_RIGHT
from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from svglib.svglib import svg2rlg

from Source.Util.app_data import FONT_LIBERATION_SANS_REGULAR, FONT_LIBERATION_SANS_BOLD, \
    FONT_LIBERATION_SANS_ITALIC, FONT_LIBERATION_SANS_BOLD_ITALIC
from Source.Model.data_handler import convert_to_de_amount
from Source.Model.ZUGFeRD.drafthorse_invoice import set_valid_pdf_profile

MARGIN_PADDING = 6  # padding for data write with elements to write in alignment with canvas data
INDENT = "&nbsp;"
TOTAL_TABLE_WIDTH = 480  # maximum table width: used to fill undefined table widths

GHOSTSCRIPT_ENABLED = False


def normalize_list(lst: list[Any] | None, length: int, default: Any) -> list[Any]:
    """!
    @brief Normalize a list to a fixed length by truncating or padding with default values.
    @param lst : list to normalize.
    @param length : fixed list length.
    @param default : default value.
    @return normalized list.
    """
    if lst is None:
        lst = []
    if len(lst) >= length:
        lst = lst[:length]
    else:
        lst = lst + [default] * (length - len(lst))
    return lst


def fill_table_width(lst: list[Any] | None, length: int, default: Any) -> list[int | None] | None:
    """!
    @brief Fill undefined column widths by distributing the remaining table width evenly.
    @param lst : list of column widths to fill.
    @param length : fixed list length.
    @param default : placeholder value for undefined widths.
    @return filled table widths.
    """
    if not lst:
        return lst
    lst = normalize_list(lst, length, default)
    total_width = 0
    empty_count = 0
    for width in lst:
        if width == default:
            empty_count += 1
        else:
            total_width += width
    fill_width = max(((TOTAL_TABLE_WIDTH - total_width) / empty_count), 0) if empty_count > 0 else 0
    for i, width in enumerate(lst):
        if width == default:
            lst[i] = fill_width
    return lst


def convert_to_table_amount(entry: Any) -> str:
    """!
    @brief Convert a value or list of values to German currency format (e.g. '1.234,56 €') with HTML line break support.
    @param entry : single value or list of values to convert.
    @return HTML-formatted German currency string.
    """
    entries = entry if isinstance(entry, list) else [entry]
    return "<br/>".join(f"{convert_to_de_amount(value)} €" for value in entries)


def scale_svg(path: str, max_width: float, max_height: float) -> Any:
    """!
    @brief Load and scale an SVG image to fit within maximum dimensions without upscaling.
    @param path : SVG file path.
    @param max_width : maximum allowed width.
    @param max_height : maximum allowed height.
    @return drawing element.
    """
    # load
    drawing = svg2rlg(path)
    assert drawing is not None
    # scale
    scale = min(max_width / drawing.width, max_height / drawing.height, 1)  # do not scale larger
    drawing.width *= scale
    drawing.height *= scale
    drawing.scale(scale, scale)
    return drawing


def scale_png(path: str, max_width: float, max_height: float) -> tuple[float, float]:
    """!
    @brief Calculate scaled dimensions for a raster image to fit within maximum dimensions without upscaling.
    @param path : image file path.
    @param max_width : maximum allowed width.
    @param max_height : maximum allowed height.
    @return width and height after scaling.
    """
    # load
    if isinstance(path, ImageReader):
        orig_width, orig_height = path.getSize()
    else:
        with PILImage.open(path) as img:
            orig_width, orig_height = img.size
    # scale
    if orig_width == 0 or orig_height == 0:
        return 0.0, 0.0
    scale = min(max_width / orig_width, max_height / orig_height, 1)  # do not scale larger
    scaled_width = orig_width * scale
    scaled_height = orig_height * scale
    return scaled_width, scaled_height


class PDFCreator:
    """!
    @brief PDF file creator using reportlab with support for embedded fonts, fold marks and page numbers.
    @param file_name_pdf : output PDF file path.
    @param embed_font : True: embed Liberation Sans fonts, False: use Helvetica.
    @param pagesize : page dimensions as (width, height) tuple.
    @param rightMargin : right margin in mm.
    @param leftMargin : left margin in mm.
    @param topMargin : top margin in mm.
    @param bottomMargin : bottom margin in mm.
    """

    def __init__(self, file_name_pdf: str, embed_font: bool = False, pagesize: tuple[float, float] = A4,
                 rightMargin: float = 20, leftMargin: float = 20, topMargin: float = 12, bottomMargin: float = 20) -> None:
        # document
        self.doc = SimpleDocTemplate(file_name_pdf, pagesize=pagesize,
                                     rightMargin=(rightMargin * mm) - MARGIN_PADDING,
                                     leftMargin=(leftMargin * mm) - MARGIN_PADDING,
                                     topMargin=topMargin * mm,
                                     bottomMargin=bottomMargin * mm)
        # settings
        self.file_name_pdf = file_name_pdf
        self.elements: list[Any] = []
        # features
        self.add_page_numbers = False
        self.fold_marks = False
        self.fold_marks_form_a = True  # True: Form A False: Form B
        # meta data
        self.author: str | None = None
        self.title: str | None = None
        self.subject: str | None = None
        self.creator: str | None = None
        # fonts
        self._embed_fonts = embed_font
        if self._embed_fonts:
            self.NORMAL_FONT = "LiberationSans"
            self.BOLD_FONT = "LiberationSans-Bold"
            self.OBLIQUE_FONT = "LiberationSans-Oblique"
            self.BOLD_OBLIQUE_FONT = "LiberationSans-BoldOblique"
            pdfmetrics.registerFont(TTFont(self.NORMAL_FONT, FONT_LIBERATION_SANS_REGULAR))
            pdfmetrics.registerFont(TTFont(self.BOLD_FONT, FONT_LIBERATION_SANS_BOLD))
            pdfmetrics.registerFont(TTFont(self.OBLIQUE_FONT, FONT_LIBERATION_SANS_ITALIC))
            pdfmetrics.registerFont(TTFont(self.BOLD_OBLIQUE_FONT, FONT_LIBERATION_SANS_BOLD_ITALIC))
        else:
            self.NORMAL_FONT = "Helvetica"
            self.BOLD_FONT = "Helvetica-Bold"
            self.OBLIQUE_FONT = "Helvetica-Oblique"
            self.BOLD_OBLIQUE_FONT = "Helvetica-BoldOblique"
        styles = getSampleStyleSheet()
        self.STYLE_NORMAL = ParagraphStyle(name="STYLE_NORMAL", parent=styles["Normal"], fontSize=9, leading=13, leftIndent=0, spaceBefore=0, spaceAfter=0)
        self.STYLE_RIGHT = ParagraphStyle(name="STYLE_RIGHT", parent=self.STYLE_NORMAL, alignment=TA_RIGHT)
        self.STYLE_BOLD = ParagraphStyle(name="STYLE_BOLD", parent=self.STYLE_NORMAL, fontName=self.BOLD_FONT)
        self.STYLE_TITLE = ParagraphStyle(name="STYLE_TITLE", parent=self.STYLE_NORMAL, fontSize=20, leading=24, fontName=self.BOLD_FONT)
        self.STYLE_TABLE_TITLE = ParagraphStyle(name="STYLE_TABLE_TITLE", parent=self.STYLE_NORMAL, fontName=self.BOLD_FONT)
        self.STYLE_TABLE_TITLE_RIGHT = ParagraphStyle(name="STYLE_TABLE_TITLE_RIGHT", parent=self.STYLE_NORMAL, fontName=self.BOLD_FONT, alignment=TA_RIGHT)
        self.STYLE_COMPANY = ParagraphStyle(name="STYLE_COMPANY", parent=self.STYLE_NORMAL, fontSize=12, leading=16, fontName=self.OBLIQUE_FONT)
        self.STYLE_SENDER = ParagraphStyle(name="STYLE_SENDER", parent=self.STYLE_NORMAL, fontSize=7)
        self.STYLE_SENDER_GREY = ParagraphStyle(name="STYLE_SENDER_GREY", parent=self.STYLE_NORMAL, textColor=colors.grey, fontSize=7)
        # local data
        self.MARGIN_TOP = self.doc.topMargin  # pylint: disable=no-member
        self.MARGIN_BOTTOM = self.doc.bottomMargin  # pylint: disable=no-member
        self.MARGIN_LEFT = self.doc.leftMargin + MARGIN_PADDING  # pylint: disable=no-member
        self.MARGIN_RIGHT = self.doc.rightMargin + MARGIN_PADDING  # pylint: disable=no-member
        self.PAGE_WIDTH, self.PAGE_HEIGHT = pagesize
        self.total_pages = 0  # override later if known
        # custom page functions
        self._first_page_func: Callable[..., object] | None = None
        self._later_page_func: Callable[..., object] | None = None

    def add_paragraph(self, text: str, style: ParagraphStyle = None) -> None:
        """!
        @brief Add a styled text paragraph to the document.
        @param text : HTML-formatted text content.
        @param style : paragraph style (default: STYLE_NORMAL).
        """
        if not style:
            style = self.STYLE_NORMAL
        self.elements.append(Paragraph(text, style))

    def add_spacer(self, height: int = 15, width: int = 1) -> None:
        """!
        @brief Add a vertical spacer element to the document.
        @param height : spacer height in points.
        @param width : spacer width in points.
        """
        self.elements.append(Spacer(width, height))

    def add_image(self, image: str | BytesIO) -> None:
        """!
        @brief Add a left-aligned image element to the document.
        @param image : image source (file path or image object).
        """
        img = Image(image)
        img.hAlign = "LEFT"
        self.elements.append(img)

    def add_table(self, table_data: list[list[str]], column_widths: list[int | None] | None = None, right_aligns: list[bool] | None = None,
                  first_row_title: bool = True, small_height: bool = False) -> None:
        """!
        @brief Add a styled table with optional title row highlighting and column alignment.
        @param table_data : 2D list of cell values.
        @param column_widths : list of column widths in points (None entries are auto-filled).
        @param right_aligns : list of booleans for right-aligned columns.
        @param first_row_title : True: first row is title, False: last row is title.
        @param small_height : True: small row padding, False: default row padding.
        """
        if not table_data:
            return
        column_count = len(table_data[0])
        column_widths = fill_table_width(column_widths, column_count, None)
        right_aligns = normalize_list(right_aligns, column_count, False)

        if column_widths is None:
            column_widths = [None] * column_count
        for row_idx, row in enumerate(table_data):
            for col_idx, cell in enumerate(row):
                if first_row_title and (row_idx == 0):  # first row
                    style = self.STYLE_TABLE_TITLE_RIGHT if right_aligns[col_idx] else self.STYLE_TABLE_TITLE
                elif not first_row_title and (row_idx == (len(table_data) - 1)):  # last row
                    style = self.STYLE_TABLE_TITLE_RIGHT if right_aligns[col_idx] else self.STYLE_TABLE_TITLE
                else:
                    style = self.STYLE_RIGHT if right_aligns[col_idx] else self.STYLE_NORMAL
                row[col_idx] = Paragraph(str(cell), style)
        table = Table(table_data, colWidths=column_widths)
        table_style = [
            ("VALIGN", (0, 0), (-1, -1), "TOP"),  # vertical top alignment
            ("LINEABOVE", (0, 0), (-1, 0), 0.5, colors.grey),  # horizontal line above first entry
            ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.grey)  # horizontal line
        ]
        if first_row_title:
            table_style.append(("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey))  # first row grey background
        else:
            table_style.append(("BACKGROUND", (0, -1), (-1, -1), colors.lightgrey))  # last row grey background
        if small_height:
            table_style.append(("TOPPADDING", (0, 0), (-1, -1), 1))  # row space on top
            table_style.append(("BOTTOMPADDING", (0, 0), (-1, -1), 1))  # row space on bottom
        table.setStyle(TableStyle(table_style))
        self.elements.append(table)

    def draw_fold_marks(self, canvas: Canvas) -> None:
        """!
        @brief Draw fold marks and hole mark according to DIN 5008 (Form A or Form B) on the left page edge.
            https://www.wintotal.de/tipp/falzmarken-word/
            | Feld         | Form A     | Form B     |
            | ------------ | ---------- | ---------- |
            | Kopfzeile    | bis 27 mm  | bis 45 mm  |
            | Adressfeld   | ab 33,9 mm | ab 50,8 mm |
            | 1. Falzmarke | 87 mm      | bei 105 mm |
            | 2. Falzmarke | 192 mm     | 210 mm     |
            | Lochmarke    | 148,5 mm   | 148,5 mm   |
        @param canvas : reportlab canvas object.
        """
        line_length = 3 * mm
        line_start = 3 * mm
        canvas.setStrokeColor(colors.black)
        canvas.setLineWidth(0.5)
        # 1st fold mark
        y_fold_mark_1 = 87 if self.fold_marks_form_a else 105
        y_fold_mark_1 = self.PAGE_HEIGHT - (y_fold_mark_1 * mm)
        canvas.line(line_start, y_fold_mark_1, line_start + line_length, y_fold_mark_1)
        # 2nd fold mark
        y_fold_mark_2 = 192 if self.fold_marks_form_a else 210
        y_fold_mark_2 = self.PAGE_HEIGHT - (y_fold_mark_2 * mm)
        canvas.line(line_start, y_fold_mark_2, line_start + line_length, y_fold_mark_2)
        # hole punch mark
        y_hole_mark = self.PAGE_HEIGHT / 2
        canvas.line(line_start, y_hole_mark, line_start + line_length, y_hole_mark)

    def add_page_number(self, canvas: Canvas) -> None:
        """!
        @brief Draw the page number at the bottom right of the current page.
        @param canvas : reportlab canvas object.
        """
        page_num_text = f"Seite {canvas.getPageNumber()}"
        if self.total_pages:
            page_num_text += f" / {self.total_pages}"
        canvas.setFont(self.NORMAL_FONT, 9)
        canvas.setFillColor(colors.black)
        canvas.drawRightString(self.PAGE_WIDTH - self.MARGIN_RIGHT, 25, page_num_text)

    def on_first_page(self, canvas: Canvas, doc: SimpleDocTemplate) -> None:
        """!
        @brief Callback for the first page. Sets PDF metadata, executes custom draw function, draws fold marks and page numbers.
        @param canvas : reportlab canvas object.
        @param doc : document template.
        """
        # set meta data
        if self.author:
            canvas.setAuthor(self.author)
        if self.title:
            canvas.setTitle(self.title)
        if self.subject:
            canvas.setSubject(self.subject)
        if self.creator:
            canvas.setCreator(self.creator)

        if self._first_page_func:
            self._first_page_func(canvas, doc)

        if self.fold_marks:
            self.draw_fold_marks(canvas)
        if self.add_page_numbers:
            self.add_page_number(canvas)

    def on_later_pages(self, canvas: Canvas, doc: SimpleDocTemplate) -> None:
        """!
        @brief Callback for subsequent pages. Executes custom draw function, draws fold marks and page numbers.
        @param canvas : reportlab canvas object.
        @param doc : document template.
        """
        if self._later_page_func:
            self._later_page_func(canvas, doc)
        if self.fold_marks:
            self.draw_fold_marks(canvas)
        if self.add_page_numbers:
            self.add_page_number(canvas)

    def create(self, on_first_page: Callable[..., object] | None = None, on_later_pages: Callable[..., object] | None = None) -> None:
        """!
        @brief Build the PDF document and write it to disk.
        @param on_first_page : custom drawing callback for the first page.
        @param on_later_pages : custom drawing callback for subsequent pages.
        """
        self._first_page_func = on_first_page
        self._later_page_func = on_later_pages
        if self.add_page_numbers:
            # build temporary doc to get maximum page number to set later
            temp_elements = copy.deepcopy(self.elements)
            temp_doc = copy.deepcopy(self.doc)
            temp_doc.build(temp_elements)
            self.total_pages = temp_doc.canv.getPageNumber() - 1
        self.doc.build(self.elements, onFirstPage=self.on_first_page, onLaterPages=self.on_later_pages)
        if GHOSTSCRIPT_ENABLED:
            # convert to valid PDF with ghostscript
            set_valid_pdf_profile(self.file_name_pdf)
