import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class TrustScoreCalculator:
    def __init__(self):
        """Initialize trust score calculator with weights and thresholds"""
        # Component weights (should sum to 100)
        self.weights = {
            'face_match': 35,        # Face comparison confidence
            'document_quality': 25,   # Document extraction quality
            'fraud_flags': 30,        # Fraud detection results
            'consistency': 10         # Data consistency
        }
        
        # Face match thresholds
        self.face_thresholds = {
            'excellent': 95.0,
            'good': 85.0,
            'fair': 75.0,
            'poor': 60.0
        }
        
        # Document quality thresholds
        self.doc_quality_thresholds = {
            'excellent': 95.0,
            'good': 85.0,
            'fair': 70.0,
            'poor': 50.0
        }
    
    def _calculate_face_score(self, face_confidence: float) -> float:
        """Calculate face matching component score"""
        if face_confidence >= self.face_thresholds['excellent']:
            return 100.0
        elif face_confidence >= self.face_thresholds['good']:
            return 90.0
        elif face_confidence >= self.face_thresholds['fair']:
            return 70.0
        elif face_confidence >= self.face_thresholds['poor']:
            return 50.0
        else:
            return max(0.0, face_confidence / self.face_thresholds['poor'] * 50)
    
    def _calculate_document_quality_score(self, extracted_fields: Dict[str, Any]) -> float:
        """Calculate document quality component score"""
        extraction_confidence = extracted_fields.get('extraction_confidence', 0)
        
        # Base score from extraction confidence
        if extraction_confidence >= self.doc_quality_thresholds['excellent']:
            base_score = 100.0
        elif extraction_confidence >= self.doc_quality_thresholds['good']:
            base_score = 90.0
        elif extraction_confidence >= self.doc_quality_thresholds['fair']:
            base_score = 70.0
        elif extraction_confidence >= self.doc_quality_thresholds['poor']:
            base_score = 50.0
        else:
            base_score = max(0.0, extraction_confidence / self.doc_quality_thresholds['poor'] * 50)
        
        # Deductions for missing critical fields
        required_fields = ['name', 'dob', 'id_number']
        missing_count = sum(1 for field in required_fields if not extracted_fields.get(field))
        
        if missing_count > 0:
            base_score -= (missing_count * 25)  # 25 point deduction per missing field
        
        # Bonus for document type identification
        if extracted_fields.get('document_type') != 'unknown':
            base_score += 5
        
        return max(0.0, min(100.0, base_score))
    
    def _calculate_fraud_score(self, fraud_flags: Dict[str, Any]) -> float:
        """Calculate fraud detection component score"""
        if not fraud_flags.get('has_fraud_indicators', False):
            return 100.0
        
        risk_level = fraud_flags.get('risk_level', 'low')
        num_flags = len(fraud_flags.get('flags', []))
        
        # Base score based on risk level
        base_scores = {
            'low': 80.0,
            'medium': 50.0,
            'high': 20.0
        }
        
        base_score = base_scores.get(risk_level, 20.0)
        
        # Additional deductions based on specific high-risk flags
        high_risk_flags = [
            'underage_user', 'expired_document', 'suspicious_name_pattern',
            'suspicious_id_pattern', 'missing_name', 'missing_id_number'
        ]
        
        high_risk_count = sum(1 for flag in fraud_flags.get('flags', []) 
                             if any(hrflag in flag for hrflag in high_risk_flags))
        
        # Deduct 10 points per high-risk flag
        base_score -= (high_risk_count * 10)
        
        # Additional deduction for excessive flags
        if num_flags > 5:
            base_score -= ((num_flags - 5) * 5)
        
        return max(0.0, base_score)
    
    def _calculate_consistency_score(self, extracted_fields: Dict[str, Any], 
                                   fraud_flags: Dict[str, Any]) -> float:
        """Calculate data consistency component score"""
        consistency_issues = fraud_flags.get('details', {}).get('consistency_issues', [])
        
        if not consistency_issues:
            return 100.0
        
        # Deduct points based on number of consistency issues
        base_score = 100.0
        deduction_per_issue = 100.0 / max(len(consistency_issues), 1)
        
        return max(0.0, base_score - (len(consistency_issues) * deduction_per_issue))

trust_calculator = TrustScoreCalculator()

def calculate_trust_score(extracted_fields: Dict[str, Any], 
                         face_confidence: float, 
                         fraud_flags: Dict[str, Any]) -> float:
    """
    Calculate overall trust score based on all verification components
    
    Args:
        extracted_fields: Extracted document fields
        face_confidence: Face matching confidence (0-100)
        fraud_flags: Fraud detection results
    
    Returns:
        Overall trust score (0-100)
    """
    try:
        logger.info("Calculating trust score...")
        
        # Calculate component scores
        face_score = trust_calculator._calculate_face_score(face_confidence)
        doc_quality_score = trust_calculator._calculate_document_quality_score(extracted_fields)
        fraud_score = trust_calculator._calculate_fraud_score(fraud_flags)
        consistency_score = trust_calculator._calculate_consistency_score(extracted_fields, fraud_flags)
        
        # Calculate weighted total
        weighted_total = (
            (face_score * trust_calculator.weights['face_match']) +
            (doc_quality_score * trust_calculator.weights['document_quality']) +
            (fraud_score * trust_calculator.weights['fraud_flags']) +
            (consistency_score * trust_calculator.weights['consistency'])
        ) / 100.0
        
        # Round to 1 decimal place
        final_score = round(weighted_total, 1)
        
        logger.info(f"Trust score calculated: {final_score}")
        logger.info(f"Component scores - Face: {face_score:.1f}, Doc Quality: {doc_quality_score:.1f}, "
                   f"Fraud: {fraud_score:.1f}, Consistency: {consistency_score:.1f}")
        
        return final_score
        
    except Exception as e:
        logger.error(f"Trust score calculation failed: {str(e)}")
        return 0.0

def get_trust_score_breakdown(extracted_fields: Dict[str, Any], 
                             face_confidence: float, 
                             fraud_flags: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get detailed breakdown of trust score calculation
    
    Args:
        extracted_fields: Extracted document fields
        face_confidence: Face matching confidence (0-100)
        fraud_flags: Fraud detection results
    
    Returns:
        Detailed breakdown of trust score components
    """
    try:
        # Calculate component scores
        face_score = trust_calculator._calculate_face_score(face_confidence)
        doc_quality_score = trust_calculator._calculate_document_quality_score(extracted_fields)
        fraud_score = trust_calculator._calculate_fraud_score(fraud_flags)
        consistency_score = trust_calculator._calculate_consistency_score(extracted_fields, fraud_flags)
        
        # Calculate final score
        final_score = calculate_trust_score(extracted_fields, face_confidence, fraud_flags)
        
        # Determine risk level based on final score
        if final_score >= 80:
            risk_level = "Low Risk"
            recommendation = "Approve"
        elif final_score >= 60:
            risk_level = "Medium Risk"
            recommendation = "Manual Review"
        else:
            risk_level = "High Risk"
            recommendation = "Reject"
        
        breakdown = {
            'final_score': final_score,
            'risk_level': risk_level,
            'recommendation': recommendation,
            'components': {
                'face_matching': {
                    'score': face_score,
                    'weight': trust_calculator.weights['face_match'],
                    'weighted_contribution': round(face_score * trust_calculator.weights['face_match'] / 100, 1),
                    'input_confidence': face_confidence
                },
                'document_quality': {
                    'score': doc_quality_score,
                    'weight': trust_calculator.weights['document_quality'],
                    'weighted_contribution': round(doc_quality_score * trust_calculator.weights['document_quality'] / 100, 1),
                    'extraction_confidence': extracted_fields.get('extraction_confidence', 0)
                },
                'fraud_detection': {
                    'score': fraud_score,
                    'weight': trust_calculator.weights['fraud_flags'],
                    'weighted_contribution': round(fraud_score * trust_calculator.weights['fraud_flags'] / 100, 1),
                    'risk_level': fraud_flags.get('risk_level', 'unknown'),
                    'flags_count': len(fraud_flags.get('flags', []))
                },
                'data_consistency': {
                    'score': consistency_score,
                    'weight': trust_calculator.weights['consistency'],
                    'weighted_contribution': round(consistency_score * trust_calculator.weights['consistency'] / 100, 1),
                    'issues_count': len(fraud_flags.get('details', {}).get('consistency_issues', []))
                }
            }
        }
        
        return breakdown
        
    except Exception as e:
        logger.error(f"Trust score breakdown calculation failed: {str(e)}")
        return {
            'final_score': 0.0,
            'risk_level': "High Risk",
            'recommendation': "Reject - System Error",
            'error': str(e)
        }