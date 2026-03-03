"""
PDF Verification Ribbon Utilities

This module provides functionality to embed interactive verification ribbons
into PDF certificates, similar to WPS Office upgrade prompts.
"""

import fitz  # PyMuPDF
import json
import os
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

from verification_metadata import VerificationMetadata
from ribbon_styling import RibbonStyle
from pdf_javascript_templates import JavaScriptTemplates
from ribbon_error_handling import RibbonErrorHandler


class VerificationRibbon:
    """
    Main class for embedding interactive verification ribbons into PDF certificates.
    """
    
    def __init__(self, verification_data: VerificationMetadata, styling: Optional[RibbonStyle] = None):
        """
        Initialize the verification ribbon with metadata and styling.
        
        Args:
            verification_data: Structured verification information
            styling: Optional custom styling configuration
        """
        self.verification_data = verification_data
        self.styling = styling or RibbonStyle()
        self.error_handler = RibbonErrorHandler()
        self.js_templates = JavaScriptTemplates()
    
    def embed_ribbon(self, pdf_path: str, output_path: str) -> bool:
        """
        Embeds interactive verification ribbon into PDF certificate.
        
        Args:
            pdf_path: Path to input PDF file
            output_path: Path for output PDF with ribbon
            
        Returns:
            bool: True if ribbon was successfully embedded, False otherwise
        """
        try:
            # Open the PDF document
            doc = fitz.open(pdf_path)
            
            if len(doc) == 0:
                print("ERROR: PDF has no pages")
                return False
            
            # Get the first page for ribbon placement
            page = doc[0]
            page_rect = page.rect
            
            # Calculate ribbon position and dimensions
            ribbon_rect = self._calculate_ribbon_position(page_rect)
            
            # Create the ribbon annotation
            ribbon_annotation = self._create_ribbon_annotation(page, ribbon_rect)
            
            # Embed verification metadata
            self._embed_verification_metadata(doc, self.verification_data)
            
            # Add interactive JavaScript if supported
            if self.styling.enable_javascript:
                self._add_interactive_javascript(doc, ribbon_annotation)
            
            # Save the modified PDF
            doc.save(output_path, garbage=4, deflate=True)
            doc.close()
            
            print(f"✓ Successfully embedded verification ribbon in {output_path}")
            return True
            
        except Exception as e:
            return self.error_handler.handle_embedding_error(e, pdf_path, output_path)
    
    def _calculate_ribbon_position(self, page_rect: fitz.Rect) -> fitz.Rect:
        """
        Calculate the position and size of the verification ribbon.
        
        Args:
            page_rect: Rectangle representing the page dimensions
            
        Returns:
            fitz.Rect: Rectangle for ribbon placement
        """
        # Position ribbon at the top of the page with some margin
        margin = 10
        ribbon_height = self.styling.height
        
        ribbon_rect = fitz.Rect(
            margin,  # left
            margin,  # top
            page_rect.width - margin,  # right
            margin + ribbon_height  # bottom
        )
        
        return ribbon_rect
    
    def _create_ribbon_annotation(self, page: fitz.Page, ribbon_rect: fitz.Rect) -> fitz.Annot:
        """
        Create the visual ribbon annotation on the PDF page.
        
        Args:
            page: PDF page object
            ribbon_rect: Rectangle for ribbon placement
            
        Returns:
            fitz.Annot: The created ribbon annotation
        """
        # Create a widget annotation (button-like)
        annot = page.add_widget(
            fitz.PDF_WIDGET_TYPE_BUTTON,
            ribbon_rect
        )
        
        # Set ribbon appearance
        annot.set_colors(
            stroke=fitz.utils.getColor(self.styling.border_color),
            fill=fitz.utils.getColor(self.styling.background_color)
        )
        
        # Set ribbon text
        status_text = "🔒 VERIFIED" if self.verification_data.is_verified else "⚠️ UNVERIFIED"
        annot.set_info(
            title="EduCerts Verification",
            content=f"{status_text} - Click for details"
        )
        
        # Configure appearance
        annot.set_border(width=1, style="solid")
        annot.set_flags(fitz.PDF_ANNOT_XF_PRINT)  # Make it printable
        
        # Add custom appearance stream for better styling
        self._customize_ribbon_appearance(annot, ribbon_rect, status_text)
        
        annot.update()
        return annot
    
    def _customize_ribbon_appearance(self, annot: fitz.Annot, rect: fitz.Rect, text: str):
        """
        Customize the visual appearance of the ribbon annotation.
        
        Args:
            annot: The annotation to customize
            rect: Rectangle dimensions
            text: Text to display on ribbon
        """
        # Create custom appearance stream
        ap_stream = f"""
        q
        {self.styling.background_color_rgb} rg
        {rect.x0} {rect.y0} {rect.width} {rect.height} re
        f
        
        BT
        /{self.styling.font_name} {self.styling.font_size} Tf
        {self.styling.text_color_rgb} rg
        {rect.x0 + 10} {rect.y0 + (rect.height/2) - 4} Td
        ({text}) Tj
        ET
        Q
        """
        
        # Set the appearance stream
        annot.set_ap(ap_stream)
    
    def _embed_verification_metadata(self, doc: fitz.Document, metadata: VerificationMetadata):
        """
        Embed verification metadata into PDF for offline access.
        
        Args:
            doc: PDF document object
            metadata: Verification metadata to embed
        """
        # Convert metadata to JSON
        metadata_json = json.dumps(asdict(metadata), indent=2)
        
        # Store in PDF metadata
        current_metadata = doc.metadata
        current_metadata["verification_data"] = metadata_json
        current_metadata["verification_ribbon"] = "true"
        current_metadata["ribbon_version"] = "1.0"
        
        doc.set_metadata(current_metadata)
    
    def _add_interactive_javascript(self, doc: fitz.Document, ribbon_annotation: fitz.Annot):
        """
        Add JavaScript for interactive popup functionality.
        
        Args:
            doc: PDF document object
            ribbon_annotation: The ribbon annotation to make interactive
        """
        try:
            # Generate JavaScript for popup functionality
            popup_js = self.js_templates.generate_popup_javascript(self.verification_data)
            
            # Add JavaScript to the document
            doc.add_javascript("ribbonPopup", popup_js)
            
            # Set the annotation action to trigger JavaScript
            ribbon_annotation.set_action({
                "type": "javascript",
                "js": "showVerificationPopup();"
            })
            
            print("✓ Added interactive JavaScript to ribbon")
            
        except Exception as e:
            print(f"WARNING: Failed to add JavaScript interactivity: {e}")
            # Continue without JavaScript - ribbon will still be visible
    
    def create_verification_popup_html(self) -> str:
        """
        Generate HTML content for the verification popup.
        
        Returns:
            str: HTML content for popup display
        """
        return self.js_templates.generate_popup_html(self.verification_data, self.styling)
    
    @staticmethod
    def extract_verification_data(pdf_path: str) -> Optional[VerificationMetadata]:
        """
        Extract verification metadata from a PDF with embedded ribbon.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            VerificationMetadata or None if not found
        """
        try:
            doc = fitz.open(pdf_path)
            metadata = doc.metadata
            
            if "verification_data" in metadata:
                verification_json = metadata["verification_data"]
                verification_dict = json.loads(verification_json)
                return VerificationMetadata(**verification_dict)
            
            return None
            
        except Exception as e:
            print(f"ERROR: Failed to extract verification data: {e}")
            return None
    
    @staticmethod
    def has_verification_ribbon(pdf_path: str) -> bool:
        """
        Check if a PDF already has a verification ribbon.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            bool: True if ribbon exists, False otherwise
        """
        try:
            doc = fitz.open(pdf_path)
            metadata = doc.metadata
            return metadata.get("verification_ribbon") == "true"
        except:
            return False


def embed_ribbon_in_pdf(
    pdf_path: str, 
    output_path: str, 
    verification_data: VerificationMetadata,
    styling: Optional[RibbonStyle] = None
) -> bool:
    """
    Convenience function to embed verification ribbon in PDF.
    
    Args:
        pdf_path: Input PDF path
        output_path: Output PDF path
        verification_data: Verification metadata
        styling: Optional custom styling
        
    Returns:
        bool: Success status
    """
    ribbon = VerificationRibbon(verification_data, styling)
    return ribbon.embed_ribbon(pdf_path, output_path)


def batch_embed_ribbons(
    pdf_paths: list, 
    output_dir: str,
    verification_data_list: list,
    styling: Optional[RibbonStyle] = None
) -> Dict[str, bool]:
    """
    Embed verification ribbons in multiple PDFs.
    
    Args:
        pdf_paths: List of input PDF paths
        output_dir: Directory for output PDFs
        verification_data_list: List of verification metadata
        styling: Optional custom styling
        
    Returns:
        Dict mapping PDF paths to success status
    """
    results = {}
    
    for i, pdf_path in enumerate(pdf_paths):
        try:
            filename = os.path.basename(pdf_path)
            output_path = os.path.join(output_dir, f"ribbon_{filename}")
            
            verification_data = verification_data_list[i] if i < len(verification_data_list) else None
            if not verification_data:
                results[pdf_path] = False
                continue
            
            success = embed_ribbon_in_pdf(pdf_path, output_path, verification_data, styling)
            results[pdf_path] = success
            
        except Exception as e:
            print(f"ERROR: Failed to process {pdf_path}: {e}")
            results[pdf_path] = False
    
    return results