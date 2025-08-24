import requests
from bs4 import BeautifulSoup
import weasyprint
from pypdf import PdfWriter, PdfReader
import io
from time import sleep

def main():
    title = input("Sermon Title: ")

    pdf_writer = PdfWriter()
    if title == "Test":
        pdf = make_slide("", title)
        pdf_reader = PdfReader(io.BytesIO(pdf))
        for page in pdf_reader.pages:
            pdf_writer.add_page(page)
        pdf_writer.write("Test.pdf")
        return


    search_terms = []
    while (search := input("Enter the search term or type 'done': ")) not in ["d", "D", "done", "Done", "DONE"]:
        search_terms.append(search)

    count = 1
    for search in search_terms:
        print(f"Processing {count}/{len(search_terms)}: {search}")
        count += 1
        pdf = make_slide(search, title)
        sleep(1)
        # Read the PDF from bytes
        pdf_reader = PdfReader(io.BytesIO(pdf))

        # Add all pages from this PDF
        for page in pdf_reader.pages:
            pdf_writer.add_page(page)

    pdf_writer.write(f"{title}.pdf")

def make_slide(search, title):
    html_str = f"""
        <html>
        <head>
            <link rel="preconnect" href="https://fonts.googleapis.com">
            <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
            <link href="https://fonts.googleapis.com/css2?family=Josefin+Sans:ital,wght@0,100..700;1,100..700&display=swap" rel="stylesheet">
        <style>
            @page {{
                size: A4 landscape;
                margin: 0.75in;
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                
                @top-center {{
                    content: "{search}";
                    font-family: "Josefin Sans", sans-serif;
                    font-size: 32pt;
                    color: #5a6c7d;
                    border-bottom: 1px solid #d4d4d4;
                    padding-bottom: 5px;
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
                padding: 20px;
                background: transparent; /* TODO: fix */
            }}
            
            /* Main container */
            .passage-content {{
                /*background: rgba(255, 255, 255, 0.95);*/
                background: black; /* TODO: remove */
                padding: 40px;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
                border-left: 5px solid #3498db;
                position: relative;
            }}
            
            /* Add decorative corner */
            .passage-content::before {{
                content: "✦";
                position: absolute;
                top: 15px;
                right: 20px;
                font-size: 38pt;
                color: #3498db;
                opacity: 0.3;
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
                background: linear-gradient(90deg, #3498db, #2980b9); /* TODO: background */
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                text-transform: uppercase;
                letter-spacing: 3px;
            }}
            
            /* Paragraph styling */
            p {{
                margin: 0 0 20px 0;
                text-align: justify;
                text-indent: 0;
            }}
            
            /* Chapter number */
            .chapternum {{
                font-size: 42pt;
                font-weight: 700;
                color: #3498db;
                float: left;
                line-height: 1;
                margin: -5px 15px -10px 0;
                text-shadow: 2px 2px 4px rgba(52, 152, 219, 0.3);
            }}
            
            /* Verse numbers */
            .versenum {{
                font-size: 20pt;
                font-weight: 600;
                color: #7f8c8d;
                background: #ecf0f1; /* TODO: fix */
                padding: 2px 6px;
                border-radius: 50%;
                margin-right: 8px;
                display: inline-block;
                min-width: 16px;
                text-align: center;
                line-height: 1.2;
            }}
            
            /* Cross references and footnotes */
            .crossreference,
            .footnote {{
                font-size: 8pt;
                color: #95a5a6;
                text-decoration: none;
                vertical-align: super;
                margin-left: 2px;
            }}
            
            .crossreference a,
            .footnote a {{
                color: #95a5a6;
                text-decoration: none;
            }}
            
            .crossreference:hover,
            .footnote:hover {{
                color: #3498db;
            }}
            
            /* Verse text spans */
            .text {{
                position: relative;
            }}
            
            /* Special highlighting for key phrases */
            .text:nth-child(1) {{
                background: linear-gradient(120deg, rgba(52, 152, 219, 0.1) 0%, transparent 100%);
                padding: 2px 4px;
                border-radius: 3px;
            }}
            
            /* Full chapter link */
            .full-chap-link {{
                display: block;
                text-align: center;
                margin: 30px 0 20px 0;
                padding: 12px 24px;
                background: linear-gradient(135deg, #3498db, #2980b9);
                color: white;
                text-decoration: none;
                border-radius: 25px;
                font-weight: 600;
                letter-spacing: 1px;
                text-transform: uppercase;
                font-size: 11pt;
                box-shadow: 0 4px 15px rgba(52, 152, 219, 0.3);
                transition: all 0.3s ease;
            }}
            
            .full-chap-link:hover {{
                background: linear-gradient(135deg, #2980b9, #1abc9c);
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(52, 152, 219, 0.4);
            }}
            
            /* Footnotes section */
            .footnotes {{
                margin-top: 40px;
                padding: 25px;
                background: linear-gradient(135deg, #f8f9fa, #e9ecef);
                border-radius: 10px;
                border-left: 4px solid #1abc9c;
            }}
            
            .footnotes h4 {{
                font-size: 14pt;
                color: #2c3e50;
                margin: 0 0 15px 0;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            
            .footnotes ol {{
                margin: 0;
                padding-left: 20px;
            }}
            
            .footnotes li {{
                margin-bottom: 10px;
                font-size: 11pt;
                line-height: 1.6;
            }}
            
            .footnotes a {{
                color: #3498db;
                text-decoration: none;
                font-weight: 600;
            }}
            
            .footnote-text {{
                color: #5a6c7d;
                font-style: italic;
            }}
            
            /* Cross references section */
            .crossrefs {{
                margin-top: 30px;
                padding: 25px;
                background: linear-gradient(135deg, #fdf2e9, #fdebd0);
                border-radius: 10px;
                border-left: 4px solid #f39c12;
            }}
            
            .crossrefs h4 {{
                font-size: 14pt;
                color: #2c3e50;
                margin: 0 0 15px 0;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            
            .crossrefs ol {{
                margin: 0;
                padding-left: 20px;
            }}
            
            .crossrefs li {{
                margin-bottom: 8px;
                font-size: 11pt;
                line-height: 1.5;
            }}
            
            .crossref-link {{
                color: #e67e22;
                text-decoration: none;
                font-weight: 500;
            }}
            
            /* Hide elements marked as hidden */
            .hidden {{
                display: block !important;
            }}
            
            /* Add some elegant typography touches */
            em {{
                font-style: italic;
                color: #34495e;
            }}
            
            /* Responsive adjustments for print */
            @media print {{
                body {{
                    font-size: 12pt;
                }}
                
                .chapternum {{
                    font-size: 36pt;
                }}
                
                h3 {{
                    font-size: 20pt;
                }}
            }}
        </style>
        </head>
        <body>
        """

    if title != "Test":
        # Request the web page
        url = f"https://www.biblegateway.com/passage/?search={search.replace(" ", "%20")}&version=CSB"
        response = requests.get(url)

        # Check if request was successful
        if response.status_code == 200:
            # Parse the HTML content
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find by CSS selector
            specific_div = soup.select_one('.passage-content')
            for sup_tag in specific_div.find_all(lambda tag: tag.name == 'sup' and tag.get('class') != ['versenum']):
                sup_tag.decompose()
            print(str(specific_div))
            content = specific_div.select('p')
            for p in content:
                html_str += str(p)
    else:
        with open('test.html', 'r') as f:
            html_str += f.read()

    html_str += "</body></html>"

    pdf = weasyprint.HTML(string=html_str).write_pdf()
    return pdf

if __name__ == "__main__":
    main()