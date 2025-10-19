"""Sermon Slides Generator

A tool for generating PDF slides from Bible passages using BibleGateway.
Retrieves scripture text and formats it into presentation slides.
"""

import io
import logging
import sys
import textwrap
from pathlib import Path
from time import sleep
from typing import Optional, List

import requests
from bs4 import BeautifulSoup, Tag
from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader, PdfWriter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
DEFAULT_SLEEP_TIME = 1.0
BIBLE_VERSION = "CSB"
BASE_URL = "https://www.biblegateway.com/passage/"

# Slide dimensions (in inches) and DPI
SLIDE_WIDTH_INCHES = 20
SLIDE_HEIGHT_INCHES = 11.25
DPI = 72

# Layout constants
MARGIN_X = 100
MARGIN_Y = 50
TITLE_Y = 50
SEPARATOR_Y = 120
TEXT_START_Y = 160
LINE_HEIGHT = 50
MAX_LINES_PER_SLIDE = 11
MAX_CHARS_PER_LINE = 75

# Colors
BACKGROUND_COLOR = '#f8f9fa'
TEXT_COLOR = '#2c3e50'
SEPARATOR_COLOR = '#3498db'

# Font settings
TITLE_FONT_SIZE = 48
TEXT_FONT_SIZE = 36

def _get_resource_path(relative_path: str) -> Path:
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = Path(sys._MEIPASS)
    except AttributeError:
        # Running in normal Python environment
        base_path = Path(__file__).parent

    return base_path / relative_path

FONT_FILE = str(_get_resource_path("JosefinSans-Medium.ttf"))

def main(file_path: str = "", sleep_time: float = DEFAULT_SLEEP_TIME) -> None:
    """
    Main function to generate sermon slides PDF from Bible passages.
    
    Args:
        file_path: Path to file containing search terms (one per line).
                  If empty, prompts user for input.
        sleep_time: Delay between API requests to avoid rate limiting.
    """
    try:
        title = input("Sermon Title: ").strip()
        if not title:
            logger.error("No title provided")
            return

        search_terms = _get_search_terms(file_path)
        if not search_terms:
            logger.warning("No search terms provided")
            return

        pdf_writer = PdfWriter()
        total_slides = 0

        for index, search_term in enumerate(search_terms, 1):
            logger.info(f"Processing {index}/{len(search_terms)}: {search_term}")
            
            slide_pdfs = generate_slides_for_passage(search_term)
            
            if slide_pdfs:
                for pdf_bytes in slide_pdfs:
                    _add_pdf_to_writer(pdf_writer, pdf_bytes)
                    total_slides += 1
            else:
                logger.warning(f"No slides generated for: {search_term}")
            
            # Rate limiting between requests
            if index < len(search_terms):
                sleep(sleep_time)

        if total_slides > 0:
            output_file = f"{title}.pdf"
            pdf_writer.write(output_file)
            logger.info(f"Successfully created {output_file} with {total_slides} slides")
        else:
            logger.error("No slides were generated")

    except KeyboardInterrupt:
        logger.info("Generation cancelled by user")
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}")


def _get_search_terms(file_path: str) -> List[str]:
    """
    Get search terms from file or user input.
    
    Args:
        file_path: Path to file containing search terms.
        
    Returns:
        List of search terms.
    """
    search_terms = []
    
    if file_path:
        try:
            path = Path(file_path)
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    search_terms = [line.strip() for line in f if line.strip()]
                logger.info(f"Loaded {len(search_terms)} search terms from {file_path}")
            else:
                logger.error(f"File not found: {file_path}")
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
    else:
        done_keywords = {"d", "done"}
        while True:
            search = input("Enter the search term or type 'done': ").strip()
            if search.lower() in done_keywords:
                break
            if search:
                search_terms.append(search)
    
    return search_terms


def _add_pdf_to_writer(pdf_writer: PdfWriter, pdf_bytes: bytes) -> None:
    """
    Add PDF pages to the writer.
    
    Args:
        pdf_writer: The PDF writer instance.
        pdf_bytes: PDF content as bytes.
    """
    try:
        pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
        for page in pdf_reader.pages:
            pdf_writer.add_page(page)
    except Exception as e:
        logger.error(f"Error adding PDF to writer: {e}")

def generate_slides_for_passage(search_term: str) -> List[bytes]:
    """
    Generate PDF slides for a Bible passage.
    
    Args:
        search_term: Bible reference to search (e.g., "John 3:16", "Psalm 23").
        
    Returns:
        List of PDF bytes for each generated slide.
    """
    slides = []
    
    try:
        passage_text = _fetch_passage_text(search_term)
        if not passage_text:
            return slides
        
        # Split text into slide-sized chunks
        text_chunks = _split_text_for_slides(passage_text)
        
        # Generate PDF for each chunk
        for text_chunk in text_chunks:
            pdf_bytes = _create_slide_pdf(search_term, text_chunk)
            if pdf_bytes:
                slides.append(pdf_bytes)
        
        logger.info(f"Generated {len(slides)} slides for {search_term}")
        
    except Exception as e:
        logger.error(f"Error generating slides for {search_term}: {e}")
    
    return slides


def _fetch_passage_text(search_term: str) -> List[str]:
    """
    Fetch Bible passage text from BibleGateway.
    
    Args:
        search_term: Bible reference to search.
        
    Returns:
        List of paragraph texts from the passage.
    """
    import urllib.parse
    
    url = f"{BASE_URL}?search={urllib.parse.quote(search_term)}&version={BIBLE_VERSION}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        passage_div = soup.select_one('.passage-content')
        
        if not passage_div:
            logger.warning(f"No passage content found for: {search_term}")
            return []
        
        # Remove footnote markers (but keep verse numbers)
        _remove_footnotes(passage_div)
        
        # Replace <br> tags with spaces for poetry formatting
        for br in passage_div.find_all('br'):
            br.replace_with(' ')
        
        # Extract paragraph texts
        paragraphs = []
        for p_tag in passage_div.find_all('p'):
            text = p_tag.get_text().strip()
            if text:
                # Clean up multiple spaces that might result from br replacements
                text = ' '.join(text.split())
                paragraphs.append(text)
        
        return paragraphs
        
    except requests.RequestException as e:
        logger.error(f"Error fetching passage {search_term}: {e}")
        return []


def _remove_footnotes(element: Tag) -> None:
    """
    Remove footnote markers from passage, keeping verse numbers.
    
    Args:
        element: BeautifulSoup element to clean.
    """
    for sup_tag in element.find_all('sup'):
        # Keep verse numbers, remove other superscript elements
        if sup_tag.get('class') != ['versenum']:
            sup_tag.decompose()

def _split_text_for_slides(paragraphs: List[str]) -> List[str]:
    """
    Split text into slide-sized chunks based on line and character limits.
    
    Args:
        paragraphs: List of paragraph texts.
        
    Returns:
        List of text chunks, each fitting on one slide.
    """
    slides = []
    current_slide = ''
    available_lines = MAX_LINES_PER_SLIDE
    
    for paragraph in paragraphs:
        if not paragraph:
            continue
        
        # Estimate lines needed for this paragraph
        lines_needed = _estimate_lines(paragraph, MAX_CHARS_PER_LINE)
        
        if lines_needed <= available_lines:
            # Paragraph fits on current slide
            if current_slide:
                current_slide += '\n\n'
                available_lines -= 1  # Account for paragraph break
            
            current_slide += paragraph
            available_lines -= lines_needed
            
            # Check if slide is full
            if available_lines <= 1:
                slides.append(current_slide)
                current_slide = ''
                available_lines = MAX_LINES_PER_SLIDE
        else:
            # Paragraph doesn't fit, start new slide
            if current_slide:
                slides.append(current_slide)
            
            # Handle long paragraphs that exceed single slide
            if lines_needed > MAX_LINES_PER_SLIDE:
                # Split paragraph across multiple slides
                split_paragraphs = _split_long_paragraph(paragraph, MAX_CHARS_PER_LINE, MAX_LINES_PER_SLIDE)
                slides.extend(split_paragraphs[:-1])  # Add complete slides
                current_slide = split_paragraphs[-1]  # Keep last chunk for current slide
                available_lines = MAX_LINES_PER_SLIDE - _estimate_lines(current_slide, MAX_CHARS_PER_LINE)
            else:
                current_slide = paragraph
                available_lines = MAX_LINES_PER_SLIDE - lines_needed
    
    # Add final slide if it has content
    if current_slide:
        slides.append(current_slide)
    
    return slides


def _estimate_lines(text: str, max_chars_per_line: int) -> int:
    """
    Estimate number of lines needed for text.
    
    Args:
        text: Text to estimate.
        max_chars_per_line: Maximum characters per line.
        
    Returns:
        Estimated number of lines.
    """
    if not text:
        return 0
    return 1 + len(text) // max_chars_per_line


def _split_long_paragraph(text: str, max_chars_per_line: int, max_lines: int) -> List[str]:
    """
    Split a long paragraph into multiple slide-sized chunks.
    
    Args:
        text: Text to split.
        max_chars_per_line: Maximum characters per line.
        max_lines: Maximum lines per slide.
        
    Returns:
        List of text chunks.
    """
    max_chars_per_slide = max_chars_per_line * max_lines
    chunks = []
    
    # Split at sentence boundaries when possible
    sentences = text.replace('. ', '.\n').split('\n')
    current_chunk = ''
    
    for sentence in sentences:
        if not sentence:
            continue
            
        if len(current_chunk) + len(sentence) + 1 <= max_chars_per_slide:
            if current_chunk:
                current_chunk += ' '
            current_chunk += sentence
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = sentence
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks if chunks else [text[:max_chars_per_slide]]

def _create_slide_pdf(title: str, text: str) -> Optional[bytes]:
    """
    Create a PDF slide with title and text content.
    
    Args:
        title: Slide title (Bible reference).
        text: Main text content for the slide.
        
    Returns:
        PDF content as bytes, or None if creation fails.
    """
    try:
        # Calculate dimensions
        width = int(SLIDE_WIDTH_INCHES * DPI)
        height = int(SLIDE_HEIGHT_INCHES * DPI)
        
        # Create image
        img = Image.new('RGB', (width, height), color=BACKGROUND_COLOR)
        draw = ImageDraw.Draw(img)
        
        # Load fonts
        title_font, text_font = _load_fonts()
        
        # Draw title
        _draw_title(draw, title, title_font, width)
        
        # Draw separator
        _draw_separator(draw, width)
        
        # Draw main text
        _draw_text_content(draw, text, text_font, width, height)
        
        # Convert to PDF
        return _image_to_pdf(img)
        
    except Exception as e:
        logger.error(f"Error creating slide for '{title}': {e}")
        return None


def _load_fonts() -> tuple[ImageFont.FreeTypeFont, ImageFont.FreeTypeFont]:
    """
    Load fonts with fallback to default.
    
    Returns:
        Tuple of (title_font, text_font).
    """
    try:
        title_font = ImageFont.truetype(FONT_FILE, TITLE_FONT_SIZE)
        text_font = ImageFont.truetype(FONT_FILE, TEXT_FONT_SIZE)
    except (IOError, OSError):
        logger.warning(f"Custom font '{FONT_FILE}' not found, using default")
        # Create larger default fonts
        title_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
    
    return title_font, text_font


def _draw_title(draw: ImageDraw.ImageDraw, title: str, font: ImageFont.FreeTypeFont, width: int) -> None:
    """
    Draw centered title on slide.
    
    Args:
        draw: ImageDraw instance.
        title: Title text.
        font: Font to use.
        width: Slide width.
    """
    bbox = draw.textbbox((0, 0), title, font=font)
    title_width = bbox[2] - bbox[0]
    title_x = (width - title_width) // 2
    draw.text((title_x, TITLE_Y), title, fill=TEXT_COLOR, font=font)


def _draw_separator(draw: ImageDraw.ImageDraw, width: int) -> None:
    """
    Draw horizontal separator line.
    
    Args:
        draw: ImageDraw instance.
        width: Slide width.
    """
    draw.line(
        [(MARGIN_X, SEPARATOR_Y), (width - MARGIN_X, SEPARATOR_Y)],
        fill=SEPARATOR_COLOR,
        width=2
    )


def _draw_text_content(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, 
                      width: int, height: int) -> None:
    """
    Draw wrapped text content on slide.
    
    Args:
        draw: ImageDraw instance.
        text: Text to draw.
        font: Font to use.
        width: Slide width.
        height: Slide height.
    """
    # Calculate available width for text
    text_width = width - MARGIN_X
    chars_per_line = text_width // (TEXT_FONT_SIZE // 2)  # Better estimate
    
    # Wrap text
    wrapped_lines = []
    paragraphs = text.split('\n\n')
    
    for paragraph in paragraphs:
        if paragraph.strip():
            lines = textwrap.wrap(paragraph.strip(), width=chars_per_line)
            wrapped_lines.extend(lines)
            if paragraphs.index(paragraph) < len(paragraphs) - 1:
                wrapped_lines.append('')  # Add spacing between paragraphs
    
    # Draw lines
    y_position = TEXT_START_Y
    max_y = height - MARGIN_Y
    
    for line in wrapped_lines:
        if y_position > max_y:
            break
        if line == '':
            y_position += LINE_HEIGHT * 0.3
            continue
        draw.text((MARGIN_X, y_position), line, fill=TEXT_COLOR, font=font)
        y_position += LINE_HEIGHT


def _image_to_pdf(img: Image.Image) -> bytes:
    """
    Convert PIL Image to PDF bytes.
    
    Args:
        img: PIL Image.
        
    Returns:
        PDF content as bytes.
    """
    buffer = io.BytesIO()
    img.save(buffer, format='PDF', quality=95, resolution=DPI)
    buffer.seek(0)
    return buffer.getvalue()

if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    file_path = sys.argv[1] if len(sys.argv) > 1 else "Passages/short.txt"
    sleep_time = float(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_SLEEP_TIME
    
    main(file_path, sleep_time)
