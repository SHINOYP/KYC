import os
import logging
import aiohttp
import asyncio
import json
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class HuggingFaceService:
    def __init__(self):
        """Initialize Hugging Face LLM service"""
        self.api_key = os.getenv("HF_API_KEY", "hf_jYyQaEDFIXXYPUAfGRCmDdvRJQvFdnvmEOx")
        self.model_id = os.getenv("HF_MODEL_ID", "deepseek-ai/DeepSeek-R1")

        # Generation parameters
        self.max_tokens = 500
        self.temperature = 0.3
        self.top_p = 0.9

    async def _call_hf_api(self, prompt: str, max_tokens: int = None) -> Optional[str]:
        """Call Hugging Face Inference API"""
        if not self.api_key:
            logger.warning("Hugging Face API key not configured")
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": max_tokens or self.max_tokens,
                "temperature": self.temperature,
                "top_p": self.top_p,
                "return_full_text": False,
            }
        }

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                url = f"https://api-inference.huggingface.co/models/{self.model_id}"
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        # HF usually returns a list of dicts with "generated_text"
                        if isinstance(result, list) and len(result) > 0 and "generated_text" in result[0]:
                            return result[0]["generated_text"].strip()
                        else:
                            logger.error(f"Unexpected Hugging Face response: {result}")
                            return None
                    else:
                        error_text = await response.text()
                        logger.error(f"Hugging Face API error {response.status}: {error_text}")
                        return None
        except asyncio.TimeoutError:
            logger.error("Hugging Face API request timed out")
            return None
        except Exception as e:
            logger.error(f"Error calling Hugging Face API: {str(e)}")
            return None

    def _create_compliance_prompt(self, extracted_fields: Dict[str, Any], 
                                trust_score: float, 
                                fraud_flags: Dict[str, Any]) -> str:
        """Create compliance summary prompt for Hugging Face"""
        prompt = f"""
Generate a professional KYC compliance summary based on the following information:

Document Details:
- Name: {extracted_fields.get('name', 'N/A')}
- Document Type: {extracted_fields.get('document_type', 'N/A')}
- ID Number: {extracted_fields.get('id_number', 'N/A')}
- Date of Birth: {extracted_fields.get('dob', 'N/A')}
- Expiry Date: {extracted_fields.get('expiry_date', 'N/A')}

Verification Results:
- Trust Score: {trust_score}/100
- Risk Level: {fraud_flags.get('risk_level', 'unknown')}
- Fraud Flags: {fraud_flags.get('flag_count', 0)}

Please provide a concise compliance summary including verification outcome and recommendation.
"""
        return prompt

    def _create_risk_assessment_prompt(self, extracted_fields: Dict[str, Any], 
                                     fraud_flags: Dict[str, Any]) -> str:
        """Create risk assessment prompt for Hugging Face"""
        prompt = f"""
Generate a structured risk assessment for KYC verification:

Document Information:
- Document Type: {extracted_fields.get('document_type', 'N/A')}
- Extraction Confidence: {extracted_fields.get('extraction_confidence', 0)}%

Fraud Detection:
- Risk Level: {fraud_flags.get('risk_level', 'unknown')}
- Flag Count: {fraud_flags.get('flag_count', 0)}
- Detected Issues: {', '.join(fraud_flags.get('flags', []))}

Please provide:
RISK_SCORE: [1-10 scale]
TOP_RISKS: [comma-separated list of main risks]
MITIGATION: [recommended actions]
REVIEW_TIME: [estimated time needed]
"""
        return prompt

    def _determine_recommendation(self, trust_score: float, fraud_flags: Dict[str, Any]) -> str:
        """Determine verification recommendation"""
        if trust_score >= 80:
            return "APPROVED"
        elif trust_score >= 60:
            return "MANUAL_REVIEW"
        elif trust_score >= 40:
            return "ADDITIONAL_VERIFICATION"
        else:
            return "REJECTED"

    def _generate_fallback_summary(self, extracted_fields: Dict[str, Any], 
                                 trust_score: float, 
                                 fraud_flags: Dict[str, Any]) -> str:
        """Generate fallback summary when API fails"""
        recommendation = self._determine_recommendation(trust_score, fraud_flags)
        
        summary = f"KYC verification completed for {extracted_fields.get('document_type', 'document')}. "
        summary += f"Trust score: {trust_score}/100. "
        summary += f"Risk level: {fraud_flags.get('risk_level', 'medium')} "
        summary += f"with {fraud_flags.get('flag_count', 0)} fraud flags detected. "
        summary += f"Verification outcome: {recommendation}."
        
        return summary

    def _generate_fallback_risk_assessment(self, extracted_fields: Dict[str, Any], 
                                         fraud_flags: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback risk assessment when API fails"""
        risk_level = fraud_flags.get('risk_level', 'medium')
        flag_count = fraud_flags.get('flag_count', 0)
        
        # Simple rule-based risk scoring
        if risk_level == 'high' or flag_count >= 5:
            risk_score = 8
            review_time = "60 minutes"
        elif risk_level == 'medium' or flag_count >= 3:
            risk_score = 5
            review_time = "30 minutes"
        else:
            risk_score = 2
            review_time = "15 minutes"

        return {
            'risk_score': risk_score,
            'top_risks': fraud_flags.get('flags', ['Document quality issues']),
            'mitigation_actions': 'Standard verification process with manual review',
            'estimated_review_time': review_time,
            'assessment_method': 'fallback'
        }

    def _parse_risk_assessment(self, llm_response: str) -> Dict[str, Any]:
        """Parse structured LLM response into risk assessment dictionary"""
        try:
            lines = llm_response.split('\n')
            assessment = {
                'risk_score': 5,
                'top_risks': [],
                'mitigation_actions': 'Standard review process',
                'estimated_review_time': '30 minutes'
            }
            
            for line in lines:
                line = line.strip()
                if line.startswith('RISK_SCORE:'):
                    try:
                        score = int(line.split(':', 1)[1].strip().split()[0])
                        assessment['risk_score'] = max(1, min(10, score))
                    except (ValueError, IndexError):
                        pass
                
                elif line.startswith('TOP_RISKS:'):
                    risks_text = line.split(':', 1)[1].strip()
                    # Simple parsing - split by common delimiters
                    risks = [risk.strip() for risk in risks_text.replace(',', '|').replace(';', '|').split('|') if risk.strip()]
                    assessment['top_risks'] = risks[:3]  # Keep top 3
                
                elif line.startswith('MITIGATION:'):
                    mitigation = line.split(':', 1)[1].strip()
                    if mitigation:
                        assessment['mitigation_actions'] = mitigation
                
                elif line.startswith('REVIEW_TIME:'):
                    review_time = line.split(':', 1)[1].strip()
                    if review_time:
                        assessment['estimated_review_time'] = review_time
            
            return assessment

        except Exception as e:
            logger.warning(f"Failed to parse LLM risk assessment: {str(e)}")
            return self._generate_fallback_risk_assessment({}, {})


# Create a global instance using HuggingFace (renamed for compatibility)
granite_service = HuggingFaceService()


async def generate_summary(extracted_fields: Dict[str, Any], 
                          trust_score: float, 
                          fraud_flags: Dict[str, Any]) -> str:
    """
    Generate compliance summary using Hugging Face LLM
    
    Args:
        extracted_fields: Extracted document fields
        trust_score: Calculated trust score (0-100)
        fraud_flags: Fraud detection results
    
    Returns:
        Professional compliance summary text
    """
    try:
        logger.info("Generating compliance summary with Hugging Face...")
        
        # Create compliance prompt
        prompt = granite_service._create_compliance_prompt(
            extracted_fields, trust_score, fraud_flags
        )
        
        # Try to get LLM-generated summary
        llm_summary = await granite_service._call_hf_api(prompt, max_tokens=200)
        
        if llm_summary:
            # Clean up the response
            summary = llm_summary.replace('\n', ' ').strip()
            
            # Ensure it includes recommendation if not present
            recommendation = granite_service._determine_recommendation(trust_score, fraud_flags)
            if recommendation not in summary:
                summary += f" Verification outcome: {recommendation}."
            
            logger.info("Successfully generated LLM compliance summary")
            return summary
        
        else:
            # Fallback to template-based summary
            logger.info("Using fallback summary generation")
            return granite_service._generate_fallback_summary(
                extracted_fields, trust_score, fraud_flags
            )
    
    except Exception as e:
        logger.error(f"Summary generation failed: {str(e)}")
        # Return basic fallback summary
        return granite_service._generate_fallback_summary(
            extracted_fields, trust_score, fraud_flags
        )


async def generate_risk_assessment(extracted_fields: Dict[str, Any], 
                                  fraud_flags: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate detailed risk assessment using Hugging Face
    
    Args:
        extracted_fields: Extracted document fields  
        fraud_flags: Fraud detection results
    
    Returns:
        Dictionary containing risk assessment details
    """
    try:
        logger.info("Generating risk assessment with Hugging Face...")
        
        # Create risk assessment prompt
        risk_prompt = granite_service._create_risk_assessment_prompt(
            extracted_fields, fraud_flags
        )
        
        # Try to get LLM-generated risk assessment
        llm_assessment = await granite_service._call_hf_api(risk_prompt, max_tokens=300)
        
        if llm_assessment:
            # Parse structured response
            assessment = granite_service._parse_risk_assessment(llm_assessment)
            assessment['assessment_method'] = 'llm'
            
            logger.info("Successfully generated LLM risk assessment")
            return assessment
        
        else:
            # Fallback to rule-based assessment
            logger.info("Using fallback risk assessment")
            return granite_service._generate_fallback_risk_assessment(
                extracted_fields, fraud_flags
            )
    
    except Exception as e:
        logger.error(f"Risk assessment generation failed: {str(e)}")
        # Return basic fallback assessment
        return granite_service._generate_fallback_risk_assessment(
            extracted_fields, fraud_flags
        )