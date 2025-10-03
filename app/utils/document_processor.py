"""
Document Processing Utility

Enhanced document processing for KYC submissions including:
- File validation and security checks
- OCR processing for document text extraction
- Document type detection and verification
- Metadata extraction
"""

import os
import hashlib
import mimetypes
from typing import Dict, Any, Optional, List
from fastapi import UploadFile, HTTPException
import logging
from datetime import datetime, timezone
import json

# For OCR processing (optional - requires additional dependencies)
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    

# For PDF processing (optional)
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    


class DocumentProcessor:
    """Enhanced document processing for KYC submissions"""
    
    def __init__(self):
        self.allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.tiff']
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.ocr_available = OCR_AVAILABLE
        self.pdf_available = PDF_AVAILABLE
    
    def validate_document(self, file: UploadFile, document_type: str) -> Dict[str, Any]:
        """Validate and process uploaded document"""
        try:
            # Basic validation
            validation_result = self._basic_validation(file)
            if not validation_result["valid"]:
                return validation_result
            
            # Security validation
            security_result = self._security_validation(file)
            if not security_result["valid"]:
                return security_result
            
            # Document type specific validation
            type_result = self._document_type_validation(file, document_type)
            if not type_result["valid"]:
                return type_result
            
            # Process document
            processing_result = self._process_document(file, document_type)
            
            return {
                "valid": True,
                "file_info": {
                    "filename": file.filename,
                    "content_type": file.content_type,
                    "size": file.size,
                    "document_type": document_type,
                    "uploaded_at": datetime.now(timezone.utc).isoformat(),
                    "file_hash": self._calculate_file_hash(file),
                    "metadata": processing_result.get("metadata", {})
                },
                "processing_result": processing_result
            }
            
        except Exception as e:
            
            return {
                "valid": False,
                "error": "Document validation failed",
                "details": str(e)
            }
    
    def _basic_validation(self, file: UploadFile) -> Dict[str, Any]:
        """Basic file validation"""
        try:
            # Check file size
            if file.size and file.size > self.max_file_size:
                return {
                    "valid": False,
                    "error": "File too large",
                    "details": f"Maximum file size is {self.max_file_size / (1024*1024)}MB"
                }
            
            # Check file extension
            if file.filename:
                file_ext = os.path.splitext(file.filename.lower())[1]
                if file_ext not in self.allowed_extensions:
                    return {
                        "valid": False,
                        "error": "Invalid file type",
                        "details": f"Allowed extensions: {', '.join(self.allowed_extensions)}"
                    }
            
            # Check content type - make it more flexible
            if file.content_type:
                allowed_mimes = [
                    'application/pdf',
                    'image/jpeg',
                    'image/jpg',
                    'image/png',
                    'image/tiff',
                    'image/tif'
                ]
                # Also allow any content type that starts with 'image/' for flexibility
                if file.content_type not in allowed_mimes and not file.content_type.startswith('image/'):
                    return {
                        "valid": False,
                        "error": "Invalid content type",
                        "details": f"Allowed content types: {', '.join(allowed_mimes)} or any image type"
                    }
            
            return {"valid": True}
            
        except Exception as e:
            return {
                "valid": False,
                "error": "Basic validation failed",
                "details": str(e)
            }
    
    def _security_validation(self, file: UploadFile) -> Dict[str, Any]:
        """Security validation for uploaded files"""
        try:
            # Check for malicious file patterns
            if file.filename:
                dangerous_patterns = [
                    '.exe', '.bat', '.cmd', '.com', '.pif', '.scr',
                    '.vbs', '.js', '.jar', '.app', '.dmg'
                ]
                
                filename_lower = file.filename.lower()
                for pattern in dangerous_patterns:
                    if pattern in filename_lower:
                        return {
                            "valid": False,
                            "error": "Potentially dangerous file type",
                            "details": "File type not allowed for security reasons"
                        }
            
            # Check file header/magic bytes (basic implementation)
            if file.file:
                # Read first few bytes to check file signature
                file.file.seek(0)
                header = file.file.read(8)
                file.file.seek(0)  # Reset position
                
                # Check for common file signatures
                if file.content_type == 'application/pdf' and not header.startswith(b'%PDF'):
                    return {
                        "valid": False,
                        "error": "Invalid PDF file",
                        "details": "File does not appear to be a valid PDF"
                    }
                
                if file.content_type.startswith('image/'):
                    image_signatures = [
                        b'\xff\xd8\xff',  # JPEG
                        b'\x89PNG\r\n\x1a\n',  # PNG
                        b'II*\x00',  # TIFF (little endian)
                        b'MM\x00*'   # TIFF (big endian)
                    ]
                    
                    if not any(header.startswith(sig) for sig in image_signatures):
                        return {
                            "valid": False,
                            "error": "Invalid image file",
                            "details": "File does not appear to be a valid image"
                        }
            
            return {"valid": True}
            
        except Exception as e:
            return {
                "valid": False,
                "error": "Security validation failed",
                "details": str(e)
            }
    
    def _document_type_validation(self, file: UploadFile, document_type: str) -> Dict[str, Any]:
        """Validate document based on its type"""
        try:
            # Document type specific requirements
            requirements = {
                "articles_of_incorporation": {
                    "required_keywords": ["articles", "incorporation", "corporation", "inc", "llc"],
                    "description": "Articles of Incorporation document"
                },
                "tax_exempt_letter": {
                    "required_keywords": ["irs", "tax", "exempt", "501", "determination"],
                    "description": "IRS Tax Exempt Determination Letter"
                },
                "irs_letter": {
                    "required_keywords": ["irs", "tax", "exempt", "501", "determination"],
                    "description": "IRS Tax Exempt Determination Letter"
                },
                "bank_statement": {
                    "required_keywords": ["bank", "statement", "account", "balance"],
                    "description": "Bank statement document"
                },
                "board_resolution": {
                    "required_keywords": ["resolution", "board", "directors", "authorized"],
                    "description": "Board resolution document"
                }
            }
            
            if document_type not in requirements:
                return {
                    "valid": False,
                    "error": "Unknown document type",
                    "details": f"Unknown document type: {document_type}. Supported types: {', '.join(requirements.keys())}"
                }
            
            # For now, we'll do basic validation
            # In a production environment, you might want to use OCR to extract text
            # and validate against required keywords
            
            return {"valid": True}
            
        except Exception as e:
            return {
                "valid": False,
                "error": "Document type validation failed",
                "details": str(e)
            }
    
    def _process_document(self, file: UploadFile, document_type: str) -> Dict[str, Any]:
        """Process document and extract metadata"""
        try:
            metadata = {
                "document_type": document_type,
                "processing_timestamp": datetime.now(timezone.utc).isoformat(),
                "file_hash": self._calculate_file_hash(file),
                "extracted_text": None,
                "page_count": None,
                "ocr_processed": False
            }
            
            # Extract text if OCR is available
            if self.ocr_available and file.content_type.startswith('image/'):
                try:
                    text = self._extract_text_from_image(file)
                    metadata["extracted_text"] = text
                    metadata["ocr_processed"] = True
                except Exception as e:
                    pass
                    
            
            # Extract text from PDF if available
            elif self.pdf_available and file.content_type == 'application/pdf':
                try:
                    text, page_count = self._extract_text_from_pdf(file)
                    metadata["extracted_text"] = text
                    metadata["page_count"] = page_count
                except Exception as e:
                    pass
                    
            
            return {"metadata": metadata}
            
        except Exception as e:
            
            return {"metadata": {}}
    
    def _calculate_file_hash(self, file: UploadFile) -> str:
        """Calculate SHA-256 hash of file"""
        try:
            if file.file:
                file.file.seek(0)
                file_hash = hashlib.sha256()
                chunk = file.file.read(8192)
                while chunk:
                    file_hash.update(chunk)
                    chunk = file.file.read(8192)
                file.file.seek(0)  # Reset position
                return file_hash.hexdigest()
        except Exception as e:
            pass
            
        return ""
    
    def _extract_text_from_image(self, file: UploadFile) -> str:
        """Extract text from image using OCR"""
        if not self.ocr_available:
            return ""
        
        try:
            # Open image
            image = Image.open(file.file)
            
            # Extract text using OCR
            text = pytesseract.image_to_string(image)
            
            return text.strip()
            
        except Exception as e:
            
            return ""
    
    def _extract_text_from_pdf(self, file: UploadFile) -> tuple:
        """Extract text from PDF"""
        if not self.pdf_available:
            return "", None
        
        try:
            # Read PDF
            pdf_reader = PyPDF2.PdfReader(file.file)
            
            # Extract text from all pages
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            return text.strip(), len(pdf_reader.pages)
            
        except Exception as e:
            
            return "", None
    
    def get_document_requirements(self, document_type: str) -> Dict[str, Any]:
        """Get requirements for a specific document type"""
        requirements = {
            "articles_of_incorporation": {
                "description": "Articles of Incorporation",
                "required": True,
                "file_types": ["pdf", "jpg", "jpeg", "png"],
                "max_size_mb": 10,
                "notes": "Official document showing church incorporation status"
            },
            "tax_exempt_letter": {
                "description": "IRS Tax Exempt Determination Letter",
                "required": True,
                "file_types": ["pdf", "jpg", "jpeg", "png"],
                "max_size_mb": 10,
                "notes": "Official IRS letter granting tax-exempt status"
            },
            "bank_statement": {
                "description": "Recent Bank Statement",
                "required": True,
                "file_types": ["pdf", "jpg", "jpeg", "png"],
                "max_size_mb": 10,
                "notes": "Recent bank statement showing account ownership"
            },
            "board_resolution": {
                "description": "Board Resolution",
                "required": True,
                "file_types": ["pdf", "jpg", "jpeg", "png"],
                "max_size_mb": 10,
                "notes": "Board resolution authorizing Manna integration"
            }
        }
        
        return requirements.get(document_type, {
            "description": "Unknown document type",
            "required": False,
            "file_types": [],
            "max_size_mb": 10,
            "notes": "Unknown document type"
        })


# Global document processor instance
document_processor = DocumentProcessor()
