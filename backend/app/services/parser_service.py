"""
Document Parser Service.

Extracts plain text from different file formats:
- PDF  → PyPDF2 (fast) with pdfplumber fallback (handles complex layouts)
- DOCX → python-docx (reads Word documents)
- TXT  → Direct read with encoding detection
- MD   → Strip markdown syntax, keep plain text

WHY SEPARATE PARSERS?
Each file format stores text differently:
- PDF: Text is positioned on a canvas (x, y coordinates)
- DOCX: Text is in XML nodes inside a ZIP file
- TXT: Raw text with various encodings (UTF-8, Latin-1, etc.)
- MD: Text with formatting syntax (**, ##, etc.)
"""

import os
import logging

import chardet       # Detects text file encoding
import markdown      # Converts Markdown → HTML
import PyPDF2        # PDF text extraction (fast, basic)
import pdfplumber    # PDF text extraction (slower, better quality)
from docx import Document as DocxDocument  # Renamed to avoid clash with our model

# Set up logging for this module
logger = logging.getLogger(__name__)

# File types we accept
ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "md"}

# Maximum file size: 50MB in bytes
MAX_FILE_SIZE = 50 * 1024 * 1024


def get_file_extension(filename: str) -> str:
    """
    Extract the file extension from a filename.
    
    Examples:
        "report.pdf"       → "pdf"
        "notes.TXT"        → "txt"
        "file.name.docx"   → "docx"
        "no_extension"     → ""
    """
    # os.path.splitext splits "file.pdf" into ("file", ".pdf")
    # [1] gets ".pdf", [1:] removes the dot, .lower() normalizes case
    ext = os.path.splitext(filename)[1][1:].lower()
    return ext


def validate_file(filename: str, file_size: int) -> tuple[bool, str]:
    """
    Validate a file before processing.
    
    Returns:
        (True, "")           if valid
        (False, "reason")    if invalid
    """
    # Check file extension
    ext = get_file_extension(filename)
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"File type '.{ext}' not supported. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
    
    # Check file size
    if file_size > MAX_FILE_SIZE:
        size_mb = file_size / (1024 * 1024)
        return False, f"File too large ({size_mb:.1f}MB). Maximum: 50MB"
    
    # Check filename is not empty
    if not filename or not filename.strip():
        return False, "Filename cannot be empty"
    
    return True, ""


def parse_pdf(file_path: str) -> str:
    """
    Extract text from a PDF file.
    
    Strategy:
    1. Try PyPDF2 first (fast)
    2. If result is too short, fall back to pdfplumber (better extraction)
    
    Why two libraries?
    - PyPDF2 is fast but struggles with scanned PDFs and complex layouts
    - pdfplumber is slower but handles tables and columns better
    """
    text = ""
    
    # Attempt 1: PyPDF2 (fast)
    try:
        with open(file_path, "rb") as f:  # "rb" = read binary (PDFs are binary)
            reader = PyPDF2.PdfReader(f)
            
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    # Add a page marker so we know which page text came from
                    text += f"\n[Page {page_num + 1}]\n{page_text}"
    except Exception as e:
        logger.warning(f"PyPDF2 failed: {e}. Trying pdfplumber...")
    
    # Attempt 2: If PyPDF2 got very little text, try pdfplumber
    if len(text.strip()) < 100:
        try:
            text = ""  # Reset
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += f"\n[Page {page_num + 1}]\n{page_text}"
        except Exception as e:
            logger.error(f"pdfplumber also failed: {e}")
            if not text:
                raise ValueError(f"Could not extract text from PDF: {e}")
    
    return text.strip()


def parse_docx(file_path: str) -> str:
    """
    Extract text from a Word (.docx) file.
    
    How DOCX works:
    - A .docx file is actually a ZIP archive
    - Inside is XML that describes the document
    - python-docx reads the XML and gives us paragraph objects
    """
    try:
        doc = DocxDocument(file_path)
        
        # Extract text from each paragraph
        paragraphs = []
        for para in doc.paragraphs:
            if para.text.strip():  # Skip empty paragraphs
                paragraphs.append(para.text)
        
        return "\n\n".join(paragraphs)
    
    except Exception as e:
        raise ValueError(f"Could not parse DOCX file: {e}")


def parse_txt(file_path: str) -> str:
    """
    Read a plain text file with automatic encoding detection.
    
    WHY ENCODING DETECTION?
    Text files can be encoded in many formats:
    - UTF-8: Modern standard (handles all languages)
    - Latin-1: Old Western European encoding
    - ASCII: English-only, 7-bit
    - Windows-1252: Windows default
    
    If you open a Latin-1 file as UTF-8, you get garbled text (mojibake).
    chardet detects the encoding so we can read it correctly.
    """
    try:
        # Step 1: Read raw bytes
        with open(file_path, "rb") as f:
            raw_bytes = f.read()
        
        # Step 2: Detect encoding
        detected = chardet.detect(raw_bytes)
        encoding = detected.get("encoding", "utf-8") or "utf-8"
        
        logger.info(f"Detected encoding: {encoding} (confidence: {detected.get('confidence', 0):.0%})")
        
        # Step 3: Decode bytes → string using detected encoding
        text = raw_bytes.decode(encoding, errors="replace")
        # errors="replace" → replaces undecodable bytes with '�' instead of crashing
        
        return text.strip()
    
    except Exception as e:
        raise ValueError(f"Could not read text file: {e}")


def parse_markdown(file_path: str) -> str:
    """
    Read a Markdown file and strip formatting syntax.
    
    We keep the raw text because:
    - Headings (#, ##) become context markers
    - Lists and bold text carry meaning
    - We want the text, not the HTML
    """
    try:
        # Read the file (Markdown files are always text)
        with open(file_path, "r", encoding="utf-8") as f:
            md_text = f.read()
        
        # Return the raw markdown text (keeping ## headings, etc.)
        # The chunker will handle splitting it properly
        return md_text.strip()
    
    except UnicodeDecodeError:
        # Fall back to encoding detection if UTF-8 fails
        return parse_txt(file_path)


def parse_document(file_path: str, filename: str) -> str:
    """
    Main entry point — routes to the correct parser based on file type.
    
    This is the ONLY function other modules call.
    It hides the complexity of multiple parsers behind one simple interface.
    
    Args:
        file_path: Absolute path to the file on disk
        filename:  Original filename (used to determine type)
    
    Returns:
        Extracted text content as a string
    
    Raises:
        ValueError: If the file type is unsupported or parsing fails
    """
    ext = get_file_extension(filename)
    
    logger.info(f"Parsing document: {filename} (type: {ext})")
    
    # Route to the correct parser
    if ext == "pdf":
        text = parse_pdf(file_path)
    elif ext == "docx":
        text = parse_docx(file_path)
    elif ext == "txt":
        text = parse_txt(file_path)
    elif ext == "md":
        text = parse_markdown(file_path)
    else:
        raise ValueError(f"Unsupported file type: .{ext}")
    
    # Log the result
    logger.info(f"Extracted {len(text)} characters from {filename}")
    
    if not text.strip():
        raise ValueError(f"No text content could be extracted from {filename}")
    
    return text