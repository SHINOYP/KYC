import logging
from typing import Dict, Any, List
from datetime import datetime, date
import re

logger = logging.getLogger(__name__)

class FraudDetectionService:
    def __init__(self):
        """Initialize fraud detection service with rules and patterns"""
        self.min_age = 18  # Minimum age for KYC
        self.max_age = 120  # Maximum reasonable age
        
        # Common patterns for fake/test IDs
        self.fake_id_patterns = [
            r'FAKE',
            r'TEST',
            r'SAMPLE',
            r'SPECIMEN',
            r'000000',
            r'123456',
            r'111111'
        ]
        
        # Suspicious name patterns
        self.suspicious_name_patterns = [
            r'^[A-Z]+$',  # All uppercase
            r'^\d+$',     # All numbers
            r'^.{1,2}$',  # Too short
            r'TEST',
            r'SAMPLE',
            r'FAKE'
        ]
    
    def _validate_date_format(self, date_str: str) -> bool:
        """Validate if date string is in proper format"""
        if not date_str:
            return False
        
        # Try common date formats
        formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%m-%d-%Y']
        
        for fmt in formats:
            try:
                datetime.strptime(date_str, fmt)
                return True
            except ValueError:
                continue
        
        return False
    
    def _parse_date(self, date_str: str) -> date:
        """Parse date string to date object"""
        formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%m-%d-%Y']
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        
        raise ValueError(f"Unable to parse date: {date_str}")
    
    def _check_age_validation(self, dob_str: str) -> Dict[str, Any]:
        """Check if age is within valid range"""
        result = {
            'underage': False,
            'overage': False,
            'invalid_dob': False,
            'age': None
        }
        
        if not dob_str or not self._validate_date_format(dob_str):
            result['invalid_dob'] = True
            return result
        
        try:
            dob = self._parse_date(dob_str)
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            
            result['age'] = age
            result['underage'] = age < self.min_age
            result['overage'] = age > self.max_age
            
        except Exception as e:
            logger.error(f"Date parsing error: {str(e)}")
            result['invalid_dob'] = True
        
        return result
    
    def _check_document_expiry(self, expiry_str: str) -> Dict[str, Any]:
        """Check if document is expired"""
        result = {
            'expired': False,
            'expires_soon': False,
            'invalid_expiry': False
        }
        
        if not expiry_str or not self._validate_date_format(expiry_str):
            result['invalid_expiry'] = True
            return result
        
        try:
            expiry_date = self._parse_date(expiry_str)
            today = date.today()
            days_until_expiry = (expiry_date - today).days
            
            result['expired'] = expiry_date < today
            result['expires_soon'] = 0 <= days_until_expiry <= 30
            
        except Exception as e:
            logger.error(f"Expiry date parsing error: {str(e)}")
            result['invalid_expiry'] = True
        
        return result
    
    def _check_name_validity(self, name: str) -> Dict[str, Any]:
        """Check if name appears valid"""
        result = {
            'suspicious_name': False,
            'empty_name': False,
            'invalid_characters': False
        }
        
        if not name or not name.strip():
            result['empty_name'] = True
            return result
        
        name = name.strip()
        
        # Check against suspicious patterns
        for pattern in self.suspicious_name_patterns:
            if re.search(pattern, name, re.IGNORECASE):
                result['suspicious_name'] = True
                break
        
        # Check for invalid characters (should only contain letters, spaces, hyphens, apostrophes)
        if not re.match(r"^[A-Za-z\s\-'\.]+$", name):
            result['invalid_characters'] = True
        
        return result
    
    def _check_id_number_validity(self, id_number: str) -> Dict[str, Any]:
        """Check if ID number appears valid"""
        result = {
            'suspicious_id': False,
            'empty_id': False,
            'invalid_format': False
        }
        
        if not id_number or not id_number.strip():
            result['empty_id'] = True
            return result
        
        id_number = id_number.strip()
        
        # Check against fake ID patterns
        for pattern in self.fake_id_patterns:
            if re.search(pattern, id_number, re.IGNORECASE):
                result['suspicious_id'] = True
                break
        
        # Basic format validation (should have reasonable length and contain alphanumeric)
        if len(id_number) < 5 or len(id_number) > 20:
            result['invalid_format'] = True
        
        if not re.match(r"^[A-Za-z0-9]+$", id_number):
            result['invalid_format'] = True
        
        return result
    
    def _check_data_consistency(self, extracted_fields: Dict[str, Any]) -> List[str]:
        """Check for data consistency issues"""
        inconsistencies = []
        
        # Check if all required fields are present
        required_fields = ['name', 'dob', 'id_number']
        for field in required_fields:
            if not extracted_fields.get(field):
                inconsistencies.append(f"Missing required field: {field}")
        
        # Check extraction confidence
        extraction_confidence = extracted_fields.get('extraction_confidence', 0)
        if extraction_confidence < 80:
            inconsistencies.append("Low document extraction confidence")
        
        # Check document type detection
        doc_type = extracted_fields.get('document_type', 'unknown')
        if doc_type == 'unknown':
            inconsistencies.append("Document type could not be determined")
        
        return inconsistencies

fraud_service = FraudDetectionService()

async def run_fraud_checks(extracted_fields: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run comprehensive fraud checks on extracted fields
    
    Args:
        extracted_fields: Dictionary containing extracted document fields
    
    Returns:
        Dictionary containing fraud flags and details
    """
    try:
        logger.info("Running fraud detection checks...")
        
        fraud_flags = {
            'has_fraud_indicators': False,
            'risk_level': 'low',  # low, medium, high
            'flags': [],
            'details': {}
        }
        
        # Extract fields
        name = extracted_fields.get('name', '')
        dob = extracted_fields.get('dob', '')
        id_number = extracted_fields.get('id_number', '')
        expiry_date = extracted_fields.get('expiry_date', '')
        
        # 1. Age validation
        age_check = fraud_service._check_age_validation(dob)
        fraud_flags['details']['age_validation'] = age_check
        
        if age_check['underage']:
            fraud_flags['flags'].append('underage_user')
        if age_check['overage']:
            fraud_flags['flags'].append('unrealistic_age')
        if age_check['invalid_dob']:
            fraud_flags['flags'].append('invalid_date_of_birth')
        
        # 2. Document expiry check
        expiry_check = fraud_service._check_document_expiry(expiry_date)
        fraud_flags['details']['expiry_validation'] = expiry_check
        
        if expiry_check['expired']:
            fraud_flags['flags'].append('expired_document')
        if expiry_check['expires_soon']:
            fraud_flags['flags'].append('document_expires_soon')
        if expiry_check['invalid_expiry']:
            fraud_flags['flags'].append('invalid_expiry_date')
        
        # 3. Name validity check
        name_check = fraud_service._check_name_validity(name)
        fraud_flags['details']['name_validation'] = name_check
        
        if name_check['suspicious_name']:
            fraud_flags['flags'].append('suspicious_name_pattern')
        if name_check['empty_name']:
            fraud_flags['flags'].append('missing_name')
        if name_check['invalid_characters']:
            fraud_flags['flags'].append('invalid_name_characters')
        
        # 4. ID number validity check
        id_check = fraud_service._check_id_number_validity(id_number)
        fraud_flags['details']['id_validation'] = id_check
        
        if id_check['suspicious_id']:
            fraud_flags['flags'].append('suspicious_id_pattern')
        if id_check['empty_id']:
            fraud_flags['flags'].append('missing_id_number')
        if id_check['invalid_format']:
            fraud_flags['flags'].append('invalid_id_format')
        
        # 5. Data consistency checks
        consistency_issues = fraud_service._check_data_consistency(extracted_fields)
        fraud_flags['details']['consistency_issues'] = consistency_issues
        
        for issue in consistency_issues:
            fraud_flags['flags'].append(f"consistency_issue: {issue}")
        
        # 6. Determine overall risk level
        high_risk_flags = [
            'underage_user', 'expired_document', 'suspicious_name_pattern',
            'suspicious_id_pattern', 'missing_name', 'missing_id_number'
        ]
        
        medium_risk_flags = [
            'document_expires_soon', 'invalid_name_characters', 'invalid_id_format',
            'unrealistic_age'
        ]
        
        if any(flag in fraud_flags['flags'] for flag in high_risk_flags):
            fraud_flags['risk_level'] = 'high'
        elif any(flag in fraud_flags['flags'] for flag in medium_risk_flags):
            fraud_flags['risk_level'] = 'medium'
        elif len(fraud_flags['flags']) > 0:
            fraud_flags['risk_level'] = 'medium'
        else:
            fraud_flags['risk_level'] = 'low'
        
        # Set has_fraud_indicators flag
        fraud_flags['has_fraud_indicators'] = len(fraud_flags['flags']) > 0
        
        # 7. Generate summary
        fraud_flags['summary'] = f"Risk Level: {fraud_flags['risk_level'].upper()}"
        if fraud_flags['flags']:
            fraud_flags['summary'] += f" - {len(fraud_flags['flags'])} issues detected"
        else:
            fraud_flags['summary'] += " - No fraud indicators detected"
        
        logger.info(f"Fraud check completed. Risk level: {fraud_flags['risk_level']}, Flags: {len(fraud_flags['flags'])}")
        
        return fraud_flags
        
    except Exception as e:
        logger.error(f"Fraud checks failed: {str(e)}")
        return {
            'has_fraud_indicators': True,
            'risk_level': 'high',
            'flags': ['fraud_check_error'],
            'details': {'error': str(e)},
            'summary': 'Fraud detection system error'
        }

async def validate_document_authenticity(extracted_fields: Dict[str, Any]) -> Dict[str, Any]:
    """
    Additional document authenticity checks
    
    Args:
        extracted_fields: Dictionary containing extracted document fields
    
    Returns:
        Dictionary containing authenticity assessment
    """
    try:
        logger.info("Running document authenticity checks...")
        
        authenticity = {
            'authentic': True,
            'confidence': 100.0,
            'issues': []
        }
        
        # Check extraction confidence
        extraction_conf = extracted_fields.get('extraction_confidence', 0)
        if extraction_conf < 70:
            authenticity['issues'].append('Low text extraction quality - possible poor image or tampered document')
            authenticity['confidence'] -= 20
        
        # Check for complete field extraction
        required_fields = ['name', 'dob', 'id_number']
        missing_fields = [f for f in required_fields if not extracted_fields.get(f)]
        
        if missing_fields:
            authenticity['issues'].append(f'Failed to extract critical fields: {", ".join(missing_fields)}')
            authenticity['confidence'] -= 15 * len(missing_fields)
        
        # Check document type detection
        if extracted_fields.get('document_type') == 'unknown':
            authenticity['issues'].append('Document type could not be identified')
            authenticity['confidence'] -= 10
        
        # Final assessment
        if authenticity['confidence'] < 60:
            authenticity['authentic'] = False
        
        authenticity['confidence'] = max(0, authenticity['confidence'])
        
        logger.info(f"Document authenticity check completed. Confidence: {authenticity['confidence']:.1f}%")
        
        return authenticity
        
    except Exception as e:
        logger.error(f"Document authenticity check failed: {str(e)}")
        return {
            'authentic': False,
            'confidence': 0.0,
            'issues': ['Authenticity check system error'],
            'error': str(e)
        }