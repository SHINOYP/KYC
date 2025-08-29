import boto3
import logging
from typing import Dict, Any, Optional
import re
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class TextractService:
    def __init__(self):
        """Initialize AWS Textract client"""
        self.client = boto3.client(
            'textract',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
    
    def _parse_key_value_pairs(self, response: Dict) -> Dict[str, str]:
        """Extract key-value pairs from Textract response"""
        key_map = {}
        value_map = {}
        block_map = {}
        
        # Build maps of blocks
        for block in response['Blocks']:
            block_id = block['Id']
            block_map[block_id] = block
            
            if block['BlockType'] == "KEY_VALUE_SET":
                if 'KEY' in block['EntityTypes']:
                    key_map[block_id] = block
                else:
                    value_map[block_id] = block
        
        # Extract key-value pairs
        kvs = {}
        for key_block_id, key_block in key_map.items():
            value_block = self._find_value_block(key_block, value_map)
            key = self._get_text(key_block, block_map)
            val = self._get_text(value_block, block_map) if value_block else ""
            kvs[key] = val
        
        return kvs
    
    def _find_value_block(self, key_block: Dict, value_map: Dict) -> Optional[Dict]:
        """Find the value block associated with a key block"""
        if 'Relationships' not in key_block:
            return None
            
        for relationship in key_block['Relationships']:
            if relationship['Type'] == 'VALUE':
                for value_id in relationship['Ids']:
                    return value_map.get(value_id)
        return None
    
    def _get_text(self, block: Dict, block_map: Dict) -> str:
        """Extract text from a block"""
        text = ""
        if 'Relationships' not in block:
            return text
            
        for relationship in block['Relationships']:
            if relationship['Type'] == 'CHILD':
                for child_id in relationship['Ids']:
                    child_block = block_map.get(child_id)
                    if child_block and child_block['BlockType'] == 'WORD':
                        text += child_block['Text'] + " "
        
        return text.strip()
    
    def _extract_specific_fields(self, all_text: str, kvs: Dict[str, str]) -> Dict[str, str]:
        """Extract specific fields using patterns and key-value pairs"""
        extracted = {
            'name': '',
            'dob': '',
            'id_number': '',
            'document_type': '',
            'expiry_date': '',
            'issue_date': ''
        }
        
        # Common patterns for different document types
        name_patterns = [
            r'Name[:\s]+([A-Za-z\s]+)',
            r'Full Name[:\s]+([A-Za-z\s]+)',
            r'Given Name[:\s]+([A-Za-z\s]+)',
        ]
        
        dob_patterns = [
            r'DOB[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'Date of Birth[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'Born[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})'  # General date pattern
        ]
        
        id_patterns = [
            r'ID[:\s]+([A-Z0-9]+)',
            r'License[:\s]+([A-Z0-9]+)',
            r'Number[:\s]+([A-Z0-9]+)',
            r'([A-Z]{1,3}\d{6,12})'  # Common ID pattern
        ]
        
        # Extract from key-value pairs first (more reliable)
        for key, value in kvs.items():
            key_lower = key.lower().strip()
            
            if any(term in key_lower for term in ['name', 'given', 'first', 'last']):
                if not extracted['name'] and value.strip():
                    extracted['name'] = value.strip()
            
            elif any(term in key_lower for term in ['dob', 'birth', 'born']):
                if not extracted['dob'] and value.strip():
                    extracted['dob'] = self._normalize_date(value.strip())
            
            elif any(term in key_lower for term in ['id', 'license', 'number']):
                if not extracted['id_number'] and value.strip():
                    extracted['id_number'] = value.strip()
            
            elif any(term in key_lower for term in ['expiry', 'expires', 'valid']):
                if not extracted['expiry_date'] and value.strip():
                    extracted['expiry_date'] = self._normalize_date(value.strip())
        
        # Fallback to pattern matching on full text
        if not extracted['name']:
            for pattern in name_patterns:
                match = re.search(pattern, all_text, re.IGNORECASE)
                if match:
                    extracted['name'] = match.group(1).strip()
                    break
        
        if not extracted['dob']:
            for pattern in dob_patterns:
                match = re.search(pattern, all_text, re.IGNORECASE)
                if match:
                    extracted['dob'] = self._normalize_date(match.group(1).strip())
                    break
        
        if not extracted['id_number']:
            for pattern in id_patterns:
                match = re.search(pattern, all_text, re.IGNORECASE)
                if match:
                    extracted['id_number'] = match.group(1).strip()
                    break
        
        # Detect document type
        text_lower = all_text.lower()
        if 'driver' in text_lower or 'license' in text_lower:
            extracted['document_type'] = 'drivers_license'
        elif 'passport' in text_lower:
            extracted['document_type'] = 'passport'
        elif 'id card' in text_lower or 'identity' in text_lower:
            extracted['document_type'] = 'national_id'
        else:
            extracted['document_type'] = 'unknown'
        
        return extracted
    
    def _normalize_date(self, date_str: str) -> str:
        """Normalize date to YYYY-MM-DD format"""
        if not date_str:
            return ""
        
        # Common date formats
        formats = [
            '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d',
            '%m-%d-%Y', '%d-%m-%Y', '%Y/%m/%d'
        ]
        
        for fmt in formats:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        return date_str  # Return original if can't parse

textract_service = TextractService()

async def extract_fields(id_bytes: bytes) -> Dict[str, Any]:
    """
    Extract fields from ID document using AWS Textract
    
    Args:
        id_bytes: Image bytes of the ID document
    
    Returns:
        Dict containing extracted fields (name, dob, id_number, etc.)
    """
    try:
        logger.info("Starting Textract field extraction...")
        
        # Call Textract to analyze document
        response = textract_service.client.analyze_document(
            Document={'Bytes': id_bytes},
            FeatureTypes=['FORMS', 'TABLES']
        )
        
        # Extract all text for pattern matching
        all_text = ""
        for block in response['Blocks']:
            if block['BlockType'] == 'LINE':
                all_text += block['Text'] + " "
        
        # Extract key-value pairs
        kvs = textract_service._parse_key_value_pairs(response)
        
        # Extract specific fields
        extracted_fields = textract_service._extract_specific_fields(all_text, kvs)
        
        # Add confidence scores
       # Compute confidence score from blocks
        confidences = [block.get("Confidence", 0) for block in response.get("Blocks", []) if "Confidence" in block]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0

        # Add page count + average confidence
        extracted_fields['page_count'] = response.get('DocumentMetadata', {}).get('Pages', 0)
        extracted_fields['extraction_confidence'] = avg_confidence

        logger.info(f"Successfully extracted fields: {list(extracted_fields.keys())}")
        return extracted_fields
        
    except Exception as e:
        logger.error(f"Textract extraction failed: {str(e)}")
        # Return empty fields on error
        return {
            'name': '',
            'dob': '',
            'id_number': '',
            'document_type': 'unknown',
            'extraction_confidence': 0,
            'error': str(e)
        }