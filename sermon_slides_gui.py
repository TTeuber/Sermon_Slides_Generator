"""Sermon Slides Generator GUI

A PyWebView-based GUI application for generating PDF slides from Bible passages.
"""

import json
import logging
import os
import sys
import threading
from pathlib import Path
from typing import Optional, Dict, Any

import webview
from sermon_slides_generator import (
    generate_slides_for_passage,
    _fetch_passage_text,
    create_title_slide_with_qr
)
from pypdf import PdfWriter
import io

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SermonSlidesAPI:
    """API class exposing backend functions to the frontend."""
    
    def __init__(self):
        self.window = None
        self.save_location = str(Path.home())
        self.is_generating = False
        
    def set_window(self, window):
        """Set the webview window reference."""
        self.window = window
        
    def select_save_location(self):
        """Open file dialog to select save location."""
        try:
            result = self.window.create_file_dialog(
                # webview.FOLDER_DIALOG,
                webview.FileDialog.FOLDER,
                directory=self.save_location
            )
            
            if result and len(result) > 0:
                self.save_location = result[0]
                return {
                    'success': True,
                    'location': self.save_location
                }
            
            return {
                'success': False,
                'message': 'No folder selected'
            }
        except Exception as e:
            logger.error(f"Error selecting save location: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def validate_passage(self, passage: str) -> Dict[str, Any]:
        """Validate a single Bible passage reference."""
        try:
            # Try to fetch the passage to validate it exists
            text = _fetch_passage_text(passage.strip())
            if text:
                return {
                    'valid': True,
                    'passage': passage.strip()
                }
            else:
                return {
                    'valid': False,
                    'passage': passage.strip(),
                    'message': 'Passage not found'
                }
        except Exception as e:
            return {
                'valid': False,
                'passage': passage.strip(),
                'message': str(e)
            }
    
    def generate_pdf(self, title: str, passages_text: str, save_location: str = None) -> Dict[str, Any]:
        """Generate PDF slides from the provided passages."""
        if self.is_generating:
            return {
                'success': False,
                'message': 'Generation already in progress'
            }
        
        # Use provided save location or default
        if save_location:
            self.save_location = save_location
            
        # Start generation in a separate thread
        thread = threading.Thread(
            target=self._generate_pdf_thread,
            args=(title, passages_text)
        )
        thread.daemon = True
        thread.start()
        
        return {
            'success': True,
            'message': 'Generation started'
        }
    
    def _generate_pdf_thread(self, title: str, passages_text: str):
        """Generate PDF in a separate thread with progress updates."""
        self.is_generating = True
        
        try:
            # Send initial status
            self._update_progress(0, 'Starting PDF generation...')
            
            # Parse passages
            passages = [p.strip() for p in passages_text.strip().split('\n') if p.strip()]
            
            if not passages:
                self._send_error('No passages provided')
                return
            
            # Validate title
            if not title.strip():
                self._send_error('No title provided')
                return
            
            pdf_writer = PdfWriter()
            total_slides = 0

            # Generate title slide with QR code first
            self._update_progress(0, 'Creating title slide...')
            try:
                title_slide_pdf = create_title_slide_with_qr(title.strip())
                if title_slide_pdf:
                    self._add_pdf_to_writer(pdf_writer, title_slide_pdf)
                    total_slides += 1
                    logger.info("Title slide with QR code created")
                else:
                    logger.warning("Failed to create title slide")
            except Exception as e:
                logger.error(f"Error creating title slide: {e}")
                self._send_warning("Could not create title slide, continuing with passages...")

            for index, passage in enumerate(passages, 1):
                # Update progress
                progress = int((index - 1) / len(passages) * 100)
                self._update_progress(progress, f'Processing {index}/{len(passages)}: {passage}')
                
                # Generate slides for this passage
                try:
                    slide_pdfs = generate_slides_for_passage(passage)
                    
                    if slide_pdfs:
                        for pdf_bytes in slide_pdfs:
                            self._add_pdf_to_writer(pdf_writer, pdf_bytes)
                            total_slides += 1
                    else:
                        logger.warning(f"No slides generated for: {passage}")
                        
                except Exception as e:
                    logger.error(f"Error processing passage {passage}: {e}")
                    self._send_warning(f"Failed to process: {passage}")
            
            if total_slides > 0:
                # Save the PDF
                output_path = Path(self.save_location) / f"{title.strip()}.pdf"
                
                # Ensure directory exists
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, 'wb') as f:
                    pdf_writer.write(f)
                
                self._update_progress(100, f'Successfully created {total_slides} slides')
                self._send_success(str(output_path), total_slides)
            else:
                self._send_error('No slides were generated')
                
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            self._send_error(str(e))
        finally:
            self.is_generating = False
    
    def _add_pdf_to_writer(self, pdf_writer: PdfWriter, pdf_bytes: bytes) -> None:
        """Add PDF pages to the writer."""
        from pypdf import PdfReader
        try:
            pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
            for page in pdf_reader.pages:
                pdf_writer.add_page(page)
        except Exception as e:
            logger.error(f"Error adding PDF to writer: {e}")
    
    def _update_progress(self, percent: int, message: str):
        """Send progress update to frontend."""
        if self.window:
            self.window.evaluate_js(
                f"window.updateProgress({percent}, {json.dumps(message)})"
            )
    
    def _send_success(self, file_path: str, slide_count: int):
        """Send success message to frontend."""
        if self.window:
            self.window.evaluate_js(
                f"window.onGenerationSuccess({json.dumps(file_path)}, {slide_count})"
            )
    
    def _send_error(self, message: str):
        """Send error message to frontend."""
        if self.window:
            self.window.evaluate_js(
                f"window.onGenerationError({json.dumps(message)})"
            )
    
    def _send_warning(self, message: str):
        """Send warning message to frontend."""
        if self.window:
            self.window.evaluate_js(
                f"window.onGenerationWarning({json.dumps(message)})"
            )
    
    def get_default_location(self) -> str:
        """Get the current save location."""
        return self.save_location


def create_app():
    """Create and configure the PyWebView application."""
    api = SermonSlidesAPI()
    
    # Get the directory of this script
    base_dir = Path(__file__).parent
    
    # Read HTML template
    template_path = base_dir / 'templates' / 'index.html'
    
    # Create templates directory if it doesn't exist
    template_path.parent.mkdir(exist_ok=True)
    
    # Create a basic HTML if template doesn't exist yet
    if not template_path.exists():
        # This will be replaced with the actual HTML file
        html_content = "<html><body><h1>Loading...</h1></body></html>"
    else:
        with open(template_path, 'r') as f:
            html_content = f.read()
    
    # Create window
    window = webview.create_window(
        'Sermon Slides Generator',
        html=html_content,
        js_api=api,
        width=800,
        height=700,
        resizable=True,
        min_size=(600, 500)
    )
    
    # Set window reference in API
    api.set_window(window)
    
    return window


def main():
    """Main entry point for the GUI application."""
    try:
        window = create_app()
        webview.start(debug=True if '--debug' in sys.argv else False)
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()