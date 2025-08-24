from typing import Optional
import requests
from bs4 import BeautifulSoup, ResultSet
from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfWriter
import io
from time import sleep
import textwrap

def main(file="", sleep_time=1):
    title = input("Sermon Title: ")

    pdf_writer = PdfWriter()

    search_terms = []

    if file != "":
        with open(file, "r") as f:
            search_terms = f.read().splitlines()
    else:
        while (search := input("Enter the search term or type 'done': ")) not in ["d", "D", "done", "Done", "DONE"]:
            search_terms.append(search)

    count = 1
    for search in search_terms:
        print(f"Processing {count}/{len(search_terms)}: {search}")
        count += 1
        pdfs = make_slides(search)
        sleep(sleep_time)
        # Add PDFs to writer
        for pdf_bytes in pdfs:
            if pdf_bytes:
                from pypdf import PdfReader
                pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
                for page in pdf_reader.pages:
                    pdf_writer.add_page(page)

    pdf_writer.write(f"{title}.pdf")

def make_slides(search: str) -> list[bytes]:
    # Request the web page
    url = f"https://www.biblegateway.com/passage/?search={search.replace(' ', '%20')}&version=CSB"
    slides = []
    try:
        response = requests.get(url)

        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            return slides

        print("Response Successful")

        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find by CSS selector
        specific_div = soup.select_one('.passage-content')
        if specific_div:
            for sup_tag in specific_div.find_all(lambda tag: tag.name == 'sup' and tag.get('class') != ['versenum']):
                sup_tag.decompose()
            p_tags: ResultSet = specific_div.find_all('p')
            for text in process_text_length(p_tags):
                pdf_bytes = create_slide_pdf(search, text)
                if pdf_bytes:
                    slides.append(pdf_bytes)
    except Exception as e:
        print("Response Unsuccessful")
        print(f"Error: {e}")
    return slides

def process_text_length(text: ResultSet) -> list[str]:
    processed_text = []  # pages
    current_page = ''
    available_lines = 10
    max_chars = 80

    for p in text:
        # Get clean text without HTML tags
        clean_text = p.get_text().strip()
        if not clean_text:
            continue
            
        # Calculate lines needed for this paragraph (estimate)
        lines_needed = 1 + len(clean_text) // max_chars

        if lines_needed <= available_lines:
            # Paragraph fits in current page
            if current_page:
                current_page += '\n\n'
            current_page += clean_text
            available_lines -= lines_needed

            # If page is full, start a new one
            if available_lines <= 0:
                processed_text.append(current_page)
                current_page = ''
                available_lines = 10
        else:
            # Paragraph doesn't fit, start new page
            if current_page:  # Only append if current_page has content
                processed_text.append(current_page)

            current_page = clean_text
            available_lines = 10 - lines_needed

            # Handle case where single paragraph exceeds page limit
            if available_lines < 0:
                available_lines = 0

    # Add final page if it has content
    if current_page:
        processed_text.append(current_page)

    return processed_text

def create_slide_pdf(title: str, text: str) -> Optional[bytes]:
    try:
        # Create image with slide dimensions (20in x 11.25in at 72 DPI)
        width = int(20 * 72)  # 1440 pixels
        height = int(11.25 * 72)  # 810 pixels
        
        # Create image with background color
        img = Image.new('RGB', (width, height), color='#f8f9fa')
        draw = ImageDraw.Draw(img)
        
        # Try to load custom font, fall back to default if not available
        try:
            title_font = ImageFont.truetype("JosefinSans-Medium.ttf", 48)
            text_font = ImageFont.truetype("JosefinSans-Medium.ttf", 36)
        except:
            # Fallback to default font
            title_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
        
        # Draw title at top
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (width - title_width) // 2
        draw.text((title_x, 50), title, fill='#2c3e50', font=title_font)
        
        # Draw separator line
        draw.line([(100, 120), (width - 100, 120)], fill='#3498db', width=2)
        
        # Wrap and draw main text
        wrapped_text = []
        max_width = width - 220  # Leave margins
        
        # Split text into paragraphs and wrap each
        paragraphs = text.split('\n\n')
        for paragraph in paragraphs:
            if paragraph.strip():
                # Estimate characters per line based on font size
                chars_per_line = max_width // 16  # Rough estimate
                wrapped_lines = textwrap.wrap(paragraph.strip(), width=chars_per_line)
                wrapped_text.extend(wrapped_lines)
                wrapped_text.append('')  # Add spacing between paragraphs
        
        # Draw wrapped text
        y_position = 160
        line_height = 50
        
        for line in wrapped_text:
            if y_position > height - 100:  # Stop if we run out of space
                break
            draw.text((100, y_position), line, fill='#2c3e50', font=text_font)
            y_position += line_height
        
        # Save image to bytes buffer
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PDF', quality=95)
        img_buffer.seek(0)
        
        return img_buffer.getvalue()
        
    except Exception as e:
        print(f"Error creating slide: {e}")
        return None

if __name__ == "__main__":
    main("Passages/short.txt", 1)
