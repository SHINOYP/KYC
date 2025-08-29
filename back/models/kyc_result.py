from pydantic import BaseModel, Field, validator
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

class DocumentType(str, Enum):
    """Supported document types"""
    DRIVERS_LICENSE = "drivers_license"
    PASSPORT = "passport"
    NATIONAL_ID = "national_id"
    AADHAAR = "aadhaar"
    PAN = "pan"
    VOTER_ID = "voter_id"
    UNKNOWN = "unknown"




class RiskLevel(str, Enum):
    """Risk assessment levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class VerificationStatus(str, Enum):
    """Verification status options"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    MANUAL_REVIEW = "manual_review"

class KYCResult(BaseModel):
    """
    Complete KYC verification result model for database storage
    """
    # Unique identifiers
    verification_id: str = Field(..., description="Unique verification ID")
    
    # Extracted personal information
    name: str = Field(default="", description="Extracted full name")
    dob: str = Field(default="", description="Date of birth (YYYY-MM-DD)")
    id_number: str = Field(default="", description="Government ID number")
    document_type: str = Field(default="unknown", description="Type of document processed")
    
    # Verification scores and confidence
    face_confidence: float = Field(default=0.0, ge=0.0, le=100.0, description="Face matching confidence score")
    trust_score: float = Field(default=0.0, ge=0.0, le=100.0, description="Overall trust score")
    extraction_confidence: float = Field(default=0.0, ge=0.0, le=100.0, description="Document extraction confidence")
    
    # Fraud detection results
    fraud_flags: Dict[str, Any] = Field(default_factory=dict, description="Fraud detection results")
    
    # AI-generated summary
    summary: str = Field(default="", description="AI-generated compliance summary")
    
    # Additional data
    extracted_fields: Dict[str, Any] = Field(default_factory=dict, description="All extracted document fields")
    verification_metadata: Dict[str, Any] = Field(default_factory=dict, description="Processing metadata")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    # Status
    status: str = Field(default="completed", description="Verification status")
    
    @validator('trust_score', 'face_confidence', 'extraction_confidence')
    def validate_scores(cls, v):
        """Ensure scores are within valid range"""
        return max(0.0, min(100.0, float(v)))
    
    @validator('dob')
    def validate_dob_format(cls, v):
        """Validate date of birth format"""
        if v and v != "":
            # Try to parse the date to ensure it's valid
            try:
                datetime.strptime(v, '%Y-%m-%d')
            except ValueError:
                # If parsing fails, return as-is but log warning
                pass
        return v
    
    class Config:
        """Pydantic configuration"""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class KYCResponse(BaseModel):
    """
    API response model for KYC verification endpoint
    """
    # Request identifiers
    verification_id: str = Field(..., description="Unique verification ID")
    success: bool = Field(..., description="Whether verification was successful")
    
    # Core verification results
    trust_score: float = Field(..., ge=0.0, le=100.0, description="Overall trust score")
    
    # Extracted information
    name: str = Field(default="", description="Extracted name")
    dob: str = Field(default="", description="Date of birth")
    id_number: str = Field(default="", description="ID number")
    document_type: str = Field(default="unknown", description="Document type")
    
    # Confidence scores
    face_confidence: float = Field(default=0.0, ge=0.0, le=100.0, description="Face matching confidence")
    
    # Fraud detection
    fraud_flags: Dict[str, Any] = Field(default_factory=dict, description="Fraud detection results")
    
    # AI summary
    summary: str = Field(default="", description="Compliance summary")
    
    # Processing metadata
    status: str = Field(default="completed", description="Processing status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    
    # Optional additional details for debugging/audit
    processing_time_ms: Optional[int] = Field(default=None, description="Processing time in milliseconds")
    
    class Config:
        """Pydantic configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class KYCRequest(BaseModel):
    """
    Request model for additional KYC operations
    """
    verification_id: Optional[str] = Field(default=None, description="Verification ID for existing record")
    customer_id: Optional[str] = Field(default=None, description="Customer identifier")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional request metadata")

class FraudFlag(BaseModel):
    """
    Individual fraud flag model
    """
    flag_type: str = Field(..., description="Type of fraud flag")
    severity: str = Field(default="medium", description="Severity level (low/medium/high)")
    description: str = Field(default="", description="Human-readable description")
    confidence: float = Field(default=0.0, ge=0.0, le=100.0, description="Detection confidence")

class DocumentQuality(BaseModel):
    """
    Document quality assessment model
    """
    overall_score: float = Field(..., ge=0.0, le=100.0, description="Overall quality score")
    image_clarity: float = Field(default=0.0, ge=0.0, le=100.0, description="Image clarity score")
    text_readability: float = Field(default=0.0, ge=0.0, le=100.0, description="Text readability score")
    document_completeness: float = Field(default=0.0, ge=0.0, le=100.0, description="Document completeness score")
    issues: List[str] = Field(default_factory=list, description="Quality issues detected")

class BiometricAnalysis(BaseModel):
    """
    Biometric analysis results model
    """
    face_detected: bool = Field(default=False, description="Whether face was detected")
    face_quality_score: float = Field(default=0.0, ge=0.0, le=100.0, description="Face quality score")
    liveness_score: float = Field(default=0.0, ge=0.0, le=100.0, description="Liveness detection score")
    multiple_faces: bool = Field(default=False, description="Multiple faces detected")
    face_attributes: Dict[str, Any] = Field(default_factory=dict, description="Detected face attributes")

class ComplianceReport(BaseModel):
    """
    Detailed compliance report model
    """
    verification_id: str = Field(..., description="Verification ID")
    customer_info: Dict[str, str] = Field(default_factory=dict, description="Customer information")
    document_analysis: DocumentQuality = Field(..., description="Document quality analysis")
    biometric_analysis: BiometricAnalysis = Field(..., description="Biometric analysis results")
    fraud_assessment: Dict[str, Any] = Field(default_factory=dict, description="Fraud assessment results")
    regulatory_notes: str = Field(default="", description="Regulatory compliance notes")
    final_recommendation: str = Field(..., description="Final verification recommendation")
    risk_score: float = Field(..., ge=0.0, le=100.0, description="Overall risk score")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Report generation time")
    
    class Config:
        """Pydantic configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class VerificationStats(BaseModel):
    """
    Verification statistics model
    """
    total_verifications: int = Field(default=0, description="Total number of verifications")
    successful_verifications: int = Field(default=0, description="Number of successful verifications")
    failed_verifications: int = Field(default=0, description="Number of failed verifications")
    pending_reviews: int = Field(default=0, description="Number of pending manual reviews")
    average_trust_score: float = Field(default=0.0, description="Average trust score")
    common_fraud_flags: List[str] = Field(default_factory=list, description="Most common fraud flags")
    processing_time_avg: float = Field(default=0.0, description="Average processing time in seconds")
    
    @validator('successful_verifications', 'failed_verifications', 'pending_reviews')
    def validate_counts(cls, v, values):
        """Ensure counts are non-negative"""
        return max(0, v)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_verifications == 0:
            return 0.0
        return round((self.successful_verifications / self.total_verifications) * 100, 2)

# Export all models
__all__ = [
    'KYCResult',
    'KYCResponse', 
    'KYCRequest',
    'FraudFlag',
    'DocumentQuality',
    'BiometricAnalysis',
    'ComplianceReport',
    'VerificationStats',
    'DocumentType',
    'RiskLevel',
    'VerificationStatus'
]