import boto3
import logging
from typing import Dict, Any, Optional
import os

logger = logging.getLogger(__name__)

class RekognitionService:
    def __init__(self):
        """Initialize AWS Rekognition client"""
        self.client = boto3.client(
            'rekognition',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        
        # Confidence thresholds
        self.MIN_FACE_CONFIDENCE = 80.0  # Minimum confidence for face detection
        self.MIN_MATCH_CONFIDENCE = 75.0  # Minimum confidence for face matching
    
    def _detect_faces(self, image_bytes: bytes) -> Dict[str, Any]:
        """Detect faces in an image and return face details"""
        try:
            response = self.client.detect_faces(
                Image={'Bytes': image_bytes},
                Attributes=['ALL']  # Get all face attributes
            )
            
            return {
                'faces_detected': len(response['FaceDetails']),
                'face_details': response['FaceDetails'],
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Face detection failed: {str(e)}")
            return {
                'faces_detected': 0,
                'face_details': [],
                'success': False,
                'error': str(e)
            }
    
    def _validate_face_quality(self, face_details: list) -> Dict[str, Any]:
        """Validate face quality for KYC purposes"""
        if not face_details:
            return {
                'valid': False,
                'issues': ['No face detected'],
                'quality_score': 0
            }
        
        if len(face_details) > 1:
            return {
                'valid': False,
                'issues': ['Multiple faces detected'],
                'quality_score': 0
            }
        
        face = face_details[0]
        issues = []
        quality_score = face['Confidence']
        
        # Check face confidence
        if face['Confidence'] < self.MIN_FACE_CONFIDENCE:
            issues.append('Low face detection confidence')
        
        # Check face quality attributes
        quality_attrs = face.get('Quality', {})
        if quality_attrs.get('Brightness', 100) < 30:
            issues.append('Image too dark')
        if quality_attrs.get('Brightness', 0) > 95:
            issues.append('Image too bright')
        if quality_attrs.get('Sharpness', 100) < 30:
            issues.append('Image too blurry')
        
        # Check pose (ensure face is reasonably straight)
        pose = face.get('Pose', {})
        if abs(pose.get('Yaw', 0)) > 30:
            issues.append('Face turned too far sideways')
        if abs(pose.get('Pitch', 0)) > 30:
            issues.append('Face tilted too much up/down')
        if abs(pose.get('Roll', 0)) > 30:
            issues.append('Head tilted too much')
        
        # Check if eyes are open
        landmarks = face.get('Landmarks', [])
        left_eye_open = any(l for l in landmarks if l.get('Type') == 'eyeLeft' and l.get('Confidence', 0) > 50)
        right_eye_open = any(l for l in landmarks if l.get('Type') == 'eyeRight' and l.get('Confidence', 0) > 50)
        
        if not (left_eye_open and right_eye_open):
            issues.append('Eyes may be closed or not clearly visible')
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'quality_score': quality_score
        }

rekognition_service = RekognitionService()

async def compare_faces(id_bytes: bytes, selfie_bytes: bytes) -> float:
    try:
        response = rekognition_service.client.compare_faces(
            SourceImage={'Bytes': id_bytes},
            TargetImage={'Bytes': selfie_bytes},
            SimilarityThreshold=rekognition_service.MIN_MATCH_CONFIDENCE
        )

        if not response['FaceMatches']:
            logger.info("No face matches found")
            return 0.0

        best_match = max(response['FaceMatches'], key=lambda x: x['Similarity'])
        confidence = best_match['Similarity']

        logger.info(f"Face comparison completed. Confidence: {confidence:.2f}%")
        return round(confidence, 2)

    except Exception as e:
        logger.error(f"Face comparison failed: {str(e)}")
        return 0.0

    """
    Compare faces between ID document and selfie using AWS Rekognition
    
    Args:
        id_bytes: Image bytes of the ID document
        selfie_bytes: Image bytes of the selfie
    
    Returns:
        Confidence score (0-100) for face match
    """
    try:
        logger.info("Starting face comparison with Rekognition...")
        
        # Step 1: Detect faces in both images
        id_face_detection = rekognition_service._detect_faces(id_bytes)
        selfie_face_detection = rekognition_service._detect_faces(selfie_bytes)
        
        # Step 2: Validate face quality in both images
        id_quality = rekognition_service._validate_face_quality(id_face_detection['face_details'])
        selfie_quality = rekognition_service._validate_face_quality(selfie_face_detection['face_details'])
        
        if not id_quality['valid']:
            logger.warning(f"ID face quality issues: {id_quality['issues']}")
            return 0.0
        
        if not selfie_quality['valid']:
            logger.warning(f"Selfie quality issues: {selfie_quality['issues']}")
            return 0.0
        
        # Step 3: Compare faces using Rekognition
        response = rekognition_service.client.compare_faces(
            SourceImage={'Bytes': id_bytes},
            TargetImage={'Bytes': selfie_bytes},
            SimilarityThreshold=rekognition_service.MIN_MATCH_CONFIDENCE
        )
        
        # Step 4: Process results
        if not response['FaceMatches']:
            logger.info("No face matches found")
            return 0.0
        
        # Get the highest confidence match
        best_match = max(response['FaceMatches'], key=lambda x: x['Similarity'])
        confidence = best_match['Similarity']
        
        logger.info(f"Face comparison completed. Confidence: {confidence:.2f}%")
        
        # Apply quality adjustment to confidence
        quality_factor = min(id_quality['quality_score'], selfie_quality['quality_score']) / 100
        adjusted_confidence = confidence * quality_factor
        
        return round(adjusted_confidence, 2)
        
    except Exception as e:
        logger.error(f"Face comparison failed: {str(e)}")
        return 0.0

async def analyze_face_attributes(image_bytes: bytes) -> Dict[str, Any]:
    """
    Analyze face attributes for additional fraud detection
    
    Args:
        image_bytes: Image bytes to analyze
    
    Returns:
        Dict containing face attributes analysis
    """
    try:
        logger.info("Analyzing face attributes...")
        
        detection_result = rekognition_service._detect_faces(image_bytes)
        
        if not detection_result['success'] or not detection_result['face_details']:
            return {
                'success': False,
                'attributes': {},
                'fraud_indicators': ['No face detected']
            }
        
        face = detection_result['face_details'][0]
        
        # Extract relevant attributes
        attributes = {
            'age_range': face.get('AgeRange', {}),
            'gender': face.get('Gender', {}),
            'emotions': face.get('Emotions', []),
            'sunglasses': face.get('Sunglasses', {}),
            'eyeglasses': face.get('Eyeglasses', {}),
            'smile': face.get('Smile', {}),
            'beard': face.get('Beard', {}),
            'mustache': face.get('Mustache', {})
        }
        
        # Identify potential fraud indicators
        fraud_indicators = []
        
        # Check for sunglasses (can hide identity)
        if attributes['sunglasses'].get('Value', False) and attributes['sunglasses'].get('Confidence', 0) > 80:
            fraud_indicators.append('Sunglasses detected - may obscure identity')
        
        # Check for very low or high emotions (may indicate fake/manipulated image)
        emotions = attributes.get('emotions', [])
        for emotion in emotions:
            if emotion['Type'] == 'SURPRISED' and emotion['Confidence'] > 90:
                fraud_indicators.append('Unusual facial expression detected')
        
        return {
            'success': True,
            'attributes': attributes,
            'fraud_indicators': fraud_indicators
        }
        
    except Exception as e:
        logger.error(f"Face attributes analysis failed: {str(e)}")
        return {
            'success': False,
            'attributes': {},
            'fraud_indicators': ['Face analysis failed'],
            'error': str(e)
        }