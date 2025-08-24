import requests
from bs4 import BeautifulSoup, ResultSet
import weasyprint
from pypdf import PdfWriter, PdfReader
import io
from time import sleep

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
        # Read the PDF from bytes
        for pdf in pdfs:
            pdf_reader = PdfReader(io.BytesIO(pdf))

            # Add all pages from this PDF
            for page in pdf_reader.pages:
                pdf_writer.add_page(page)

    pdf_writer.write(f"{title}.pdf")

def make_slides(search: str) -> list[bytes]:
    # Request the web page
    url = f"https://www.biblegateway.com/passage/?search={search.replace(" ", "%20")}&version=CSB"
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
        for sup_tag in specific_div.find_all(lambda tag: tag.name == 'sup' and tag.get('class') != ['versenum']):
            sup_tag.decompose()
        p_tags: ResultSet = specific_div.find_all('p')
        for text in process_text_length(p_tags):
            slides.append(make_html(search, text))
    except Exception as e:
        print("Response Unsuccessful")
        print(f"Error: {e}")
    return slides

def process_text_length(text: ResultSet) -> list[str]:
    processed_text = []  # pages
    current_page = ''
    available_lines = 10

    for p in text:
        # Calculate lines needed for this paragraph
        lines_needed = 1 + len(p.text) // 100

        if lines_needed <= available_lines:
            # Paragraph fits in current page
            current_page += str(p)
            available_lines -= lines_needed

            # If page is full, start a new one
            if available_lines == 0:
                processed_text.append(current_page)
                current_page = ''
                available_lines = 10
        else:
            # Paragraph doesn't fit, start new page
            if current_page:  # Only append if current_page has content
                processed_text.append(current_page)

            current_page = str(p)
            available_lines = 10 - lines_needed

            # Handle case where single paragraph exceeds page limit
            if available_lines < 0:
                available_lines = 0

    # Add final page if it has content
    if current_page:
        processed_text.append(current_page)

    return processed_text

def make_html(title: str, text: str) -> bytes:
    html_str = f"""
        <html>
        <head>
            <link rel="preconnect" href="https://fonts.googleapis.com">
            <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
            <link href="https://fonts.googleapis.com/css2?family=Josefin+Sans:ital,wght@0,100..700;1,100..700&display=swap" rel="stylesheet">
        <style>
            @page {{
                size: 20in 11.25in;
                /*margin: 0.75in;*/
                background-image: url("./slide_background.png");
                background-repeat: no-repeat;
                background-size: cover;
                background-position: center;
                background-attachment: fixed;
                
                @top-center {{
                    content: "{title}";
                    font-family: "Josefin Sans", sans-serif;
                    font-size: 40pt;
                    color: #C3D5E9FF;
                    border-bottom: 1px solid #d4d4d4;
                    margin-top: 15px;
                    padding-bottom: 15px;
                    padding-top: 15px;
                }}
            }}
            
            body {{
                font-family: "Josefin Sans", sans-serif;
                font-optical-sizing: auto;
                font-weight: 400;
                font-style: normal;                
                font-size: 38pt;
                line-height: 1.8;
                color: #2c3e50;
                margin: 0;
                /*padding: 20px;*/
                background-image: url("./slide_background.png");
                background-size: cover;
                background-repeat: no-repeat;
                background-position: center;
                background-attachment: fixed;
            }}
            
            /* Main container */
            .passage-content {{
                /*padding: 40px;*/
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
                border-left: 5px solid #3498db;
                position: relative;
            }}
            
            
            /* Prologue heading */
            h3 {{
                font-family: 'Crimson Text', serif;
                font-size: 38pt;
                font-weight: 600;
                color: #2c3e50;
                text-align: center;
                margin: 0 0 30px 0;
                padding: 15px 0;
                border-bottom: 2px solid #3498db;
                text-transform: uppercase;
                letter-spacing: 3px;
            }}
            
            /* Paragraph styling */
            p {{
                margin: 0 0 20px 0;
                text-align: justify;
                text-indent: 0;
            }}
            
            /* Verse text spans */
            .text {{
                position: relative;
            }}
            
            
            /* Hide elements marked as hidden */
            .hidden {{
                display: block !important;
            }}
            
            
            /* Responsive adjustments for print */
            @media print {{
                body {{
                    font-size: 30pt;
                    color: #c3d5e9;
                }}
            }}
        </style>
        </head>
        <body>
        """

    html_str += text

    html_str += "</body></html>"

    pdf = weasyprint.HTML(string=html_str,  base_url='base_url').write_pdf()
    return pdf

if __name__ == "__main__":
    main("Passages/test.txt", 5)