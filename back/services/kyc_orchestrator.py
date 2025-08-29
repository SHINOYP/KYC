import logging
from typing import Dict, Any
from .aws_textract import extract_fields
from .aws_rekognition import compare_faces, analyze_face_attributes
from .fraud_rules import run_fraud_checks, validate_document_authenticity
from services.trust_score import calculate_trust_score

logger = logging.getLogger(__name__)

async def run_kyc_pipeline(id_bytes: bytes, selfie_bytes: bytes) -> Dict[str, Any]:
    """
    Orchestrates the full KYC verification process:
    1. Extract fields with Textract
    2. Run fraud rule checks
    3. Validate document authenticity
    4. Match faces with Rekognition
    5. Analyze face attributes
    """

    result = {
        "extracted_fields": {},
        "fraud_checks": {},
        "document_authenticity": {},
        "face_match_score": 0.0,
        "face_attributes": {},
        "final_decision": "pending"
    }

    try:
        # Step 1: Extract fields from ID
        extracted = await extract_fields(id_bytes)
        result["extracted_fields"] = extracted

        # Step 2: Fraud checks (DOB, ID validity, etc.)
        fraud = await run_fraud_checks(extracted)
        result["fraud_checks"] = fraud


        # Step 3: Authenticity validation
        authenticity = await validate_document_authenticity(extracted)
        result["document_authenticity"] = authenticity

        # Step 4: Compare faces (ID photo vs selfie)
        if selfie_bytes:
            match_score = await compare_faces(id_bytes, selfie_bytes)
            result["face_match_score"] = match_score

            attributes = await analyze_face_attributes(selfie_bytes)
            result["face_attributes"] = attributes

        # Step 5: Final decision logic
                # Step 5: Final decision logic
        if fraud["risk_level"] == "high" or not authenticity["authentic"]:
            result["final_decision"] = "rejected"
        elif result["face_match_score"] < 75:
            result["final_decision"] = "rejected"
        else:
            result["final_decision"] = "approved"

        # ✅ Step 6: Trust score calculation
        result["trust_score"] = calculate_trust_score(
            result["extracted_fields"],
            result["face_match_score"],
            result["fraud_checks"]
        )


        logger.info(f"KYC completed with decision: {result['final_decision']}")
        return result

    except Exception as e:
        logger.error(f"KYC pipeline failed: {str(e)}")
        result["final_decision"] = "error"
        result["error"] = str(e)
        return result
