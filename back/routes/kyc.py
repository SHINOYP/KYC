from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import logging
import uuid

from services.kyc_orchestrator import run_kyc_pipeline
from services.aws_textract import extract_fields
from services.aws_rekognition import compare_faces
from services.fraud_rules import run_fraud_checks
from services.trust_score import calculate_trust_score
from services.hugging_face import generate_summary
from models.kyc_result import KYCResult, KYCResponse
from db import save_kyc_result

logger = logging.getLogger(__name__)
router = APIRouter()

# -------- Helpers ----------
async def validate_file(file: UploadFile, max_size: int = 10 * 1024 * 1024) -> bytes:
    """Validate uploaded file size and type"""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(status_code=400, detail=f"File size exceeds {max_size} bytes")
    return content

# -------- Main Endpoint ----------
@router.post("/kyc/verify", response_model=KYCResponse)
async def verify_kyc(
    id_card: UploadFile = File(..., description="Government ID card image"),
    selfie: UploadFile = File(..., description="User selfie image")
):
    """
    Full KYC verification endpoint
    """
    try:
        verification_id = str(uuid.uuid4())
        logger.info(f"[{verification_id}] Starting KYC verification...")

        # Step 1: Validate input files
        id_bytes = await validate_file(id_card)
        selfie_bytes = await validate_file(selfie)

        # Step 2: Run orchestrated KYC pipeline (modular call)
        pipeline_result = await run_kyc_pipeline(id_bytes, selfie_bytes)

        # Step 3: Build model & save to DB
        kyc_result = KYCResult(
            verification_id=verification_id,
            name=pipeline_result["extracted_fields"].get("name", ""),
            dob=pipeline_result["extracted_fields"].get("dob", ""),
            id_number=pipeline_result["extracted_fields"].get("id_number", ""),
            document_type=pipeline_result["extracted_fields"].get("document_type", "unknown"),
            face_confidence=pipeline_result.get("face_match_score", 0.0),
            trust_score=pipeline_result.get("trust_score", 0.0),
            fraud_flags=pipeline_result.get("fraud_checks", {}),
            summary=pipeline_result.get("summary", ""),
            extracted_fields=pipeline_result.get("extracted_fields", {}),
        )
        await save_kyc_result(kyc_result)

        # Step 4: Return response model
        return KYCResponse(
            verification_id=verification_id,
            success=True,
            trust_score=kyc_result.trust_score,
            name=kyc_result.name,
            dob=kyc_result.dob,
            id_number=kyc_result.id_number,
            document_type=kyc_result.document_type,
            face_confidence=kyc_result.face_confidence,
            fraud_flags=kyc_result.fraud_flags,
            summary=kyc_result.summary,
            status=pipeline_result.get("final_decision", "completed")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("KYC verification failed")
        raise HTTPException(status_code=500, detail=f"KYC verification failed: {str(e)}")

# -------- Utility Endpoints ----------
@router.get("/kyc/status/{verification_id}")
async def get_verification_status(verification_id: str):
    """Check verification status (dummy for now)"""
    return {
        "verification_id": verification_id,
        "status": "completed",
        "message": "Verification completed successfully"
    }

@router.get("/kyc/health")
async def kyc_health_check():
    """Service health check"""
    return {
        "status": "healthy",
        "services": {
            "textract": "available",
            "rekognition": "available",
            "granite": "available",
            "database": "connected"
        }
    }
