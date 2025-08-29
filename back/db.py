import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import motor.motor_asyncio
from pymongo.errors import DuplicateKeyError, ConnectionFailure
import asyncio

from models.kyc_result import KYCResult, VerificationStats

logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Database configuration and connection management"""
    
    def __init__(self):
        # MongoDB connection settings
        self.mongodb_url = os.getenv('MONGODB_URL', 'mongodb+srv://shinoyshinoo_db_user:ETr0hm5bsg98HXhz@cluster0.ystg5x3.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
        self.database_name = os.getenv('DATABASE_NAME', 'kyc_verification')
        
        # Collection names
        self.kyc_results_collection = 'kyc_results'
        self.verification_logs_collection = 'verification_logs'
        self.audit_logs_collection = 'audit_logs'
        
        # Connection objects
        self.client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
        self.database: Optional[motor.motor_asyncio.AsyncIOMotorDatabase] = None
        
        # Connection status
        self.is_connected = False

    async def connect(self):
        """Establish database connection"""
        try:
            logger.info(f"Connecting to MongoDB at {self.mongodb_url}")
            
            self.client = motor.motor_asyncio.AsyncIOMotorClient(
                self.mongodb_url,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                maxPoolSize=50
            )
            
            # Test connection
            await self.client.admin.command('ping')
            
            self.database = self.client[self.database_name]
            self.is_connected = True
            
            # Create indexes
            await self._create_indexes()
            
            logger.info("Successfully connected to MongoDB")
            
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            self.is_connected = False
            raise
        
        except Exception as e:
            logger.error(f"Database connection error: {str(e)}")
            self.is_connected = False
            raise

    async def disconnect(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            self.is_connected = False
            logger.info("Disconnected from MongoDB")

    async def _create_indexes(self):
        """Create database indexes for optimal performance"""
        try:
            kyc_collection = self.database[self.kyc_results_collection]
            
            # Create indexes
            indexes = [
                ('verification_id', 1),  # Unique index on verification_id
                ('created_at', -1),      # Index for time-based queries
                ('status', 1),           # Index for status filtering
                ('trust_score', -1),     # Index for score-based queries
                ('name', 'text'),        # Text index for name searching
            ]
            
            for field, direction in indexes:
                if field == 'verification_id':
                    await kyc_collection.create_index(
                        [(field, direction)], 
                        unique=True,
                        background=True
                    )
                elif field == 'name':
                    await kyc_collection.create_index(
                        [(field, direction)],
                        background=True
                    )
                else:
                    await kyc_collection.create_index(
                        [(field, direction)],
                        background=True
                    )
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Error creating database indexes: {str(e)}")

    async def health_check(self) -> Dict[str, Any]:
        """Check database health status"""
        try:
            if not self.is_connected or not self.client:
                return {
                    'status': 'disconnected',
                    'error': 'No database connection'
                }
            
            # Ping database
            await self.client.admin.command('ping')
            
            # Get database stats
            stats = await self.database.command('dbStats')
            
            return {
                'status': 'connected',
                'database': self.database_name,
                'collections_count': stats.get('collections', 0),
                'data_size_mb': round(stats.get('dataSize', 0) / (1024 * 1024), 2),
                'storage_size_mb': round(stats.get('storageSize', 0) / (1024 * 1024), 2)
            }
            
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }

# Global database instance
db_config = DatabaseConfig()

async def init_db():
    """Initialize database connection, but app should run even if DB is down"""
    await db_config.connect()
    if not db_config.is_connected:
        logger.warning("⚠️ Running in degraded mode: MongoDB not available")


async def close_db():
    """Close database connection"""
    await db_config.disconnect()

async def save_kyc_result(kyc_result: KYCResult) -> bool:
    """
    Save KYC verification result to database
    
    Args:
        kyc_result: KYC result object to save
    
    Returns:
        Boolean indicating success
    """
    try:
        if not db_config.is_connected:
            logger.error("Database not connected")
            return False
        
        collection = db_config.database[db_config.kyc_results_collection]
        
        # Convert Pydantic model to dict
        result_dict = kyc_result.dict()
        
        # Ensure timestamps are set
        result_dict['updated_at'] = datetime.utcnow()
        
        # Insert document
        await collection.insert_one(result_dict)
        
        logger.info(f"KYC result saved successfully: {kyc_result.verification_id}")
        
        # Log the verification for audit trail
        await log_verification_event(
            kyc_result.verification_id,
            'verification_completed',
            {
                'trust_score': kyc_result.trust_score,
                'status': kyc_result.status,
                'fraud_flags_count': len(kyc_result.fraud_flags.get('flags', []))
            }
        )
        
        return True
        
    except DuplicateKeyError:
        logger.warning(f"KYC result already exists: {kyc_result.verification_id}")
        return await update_kyc_result(kyc_result)
        
    except Exception as e:
        logger.error(f"Failed to save KYC result: {str(e)}")
        return False

async def update_kyc_result(kyc_result: KYCResult) -> bool:
    """
    Update existing KYC verification result
    
    Args:
        kyc_result: Updated KYC result object
    
    Returns:
        Boolean indicating success
    """
    try:
        if not db_config.is_connected:
            logger.error("Database not connected")
            return False
        
        collection = db_config.database[db_config.kyc_results_collection]
        
        # Convert to dict and set update timestamp
        result_dict = kyc_result.dict()
        result_dict['updated_at'] = datetime.utcnow()
        
        # Update document
        result = await collection.update_one(
            {'verification_id': kyc_result.verification_id},
            {'$set': result_dict}
        )
        
        if result.modified_count > 0:
            logger.info(f"KYC result updated successfully: {kyc_result.verification_id}")
            return True
        else:
            logger.warning(f"No KYC result found to update: {kyc_result.verification_id}")
            return False
        
    except Exception as e:
        logger.error(f"Failed to update KYC result: {str(e)}")
        return False

async def get_kyc_result(verification_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve KYC result by verification ID
    
    Args:
        verification_id: Unique verification identifier
    
    Returns:
        KYC result dictionary or None
    """
    try:
        if not db_config.is_connected:
            logger.error("Database not connected")
            return None
        
        collection = db_config.database[db_config.kyc_results_collection]
        
        result = await collection.find_one({'verification_id': verification_id})
        
        if result:
            # Remove MongoDB's _id field
            result.pop('_id', None)
            logger.info(f"Retrieved KYC result: {verification_id}")
            return result
        else:
            logger.info(f"KYC result not found: {verification_id}")
            return None
        
    except Exception as e:
        logger.error(f"Failed to retrieve KYC result: {str(e)}")
        return None

async def get_kyc_results_by_status(status: str, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get KYC results filtered by status
    
    Args:
        status: Verification status to filter by
        limit: Maximum number of results to return
    
    Returns:
        List of KYC result dictionaries
    """
    try:
        if not db_config.is_connected:
            return []
        
        collection = db_config.database[db_config.kyc_results_collection]
        
        cursor = collection.find({'status': status}).limit(limit).sort('created_at', -1)
        results = []
        
        async for doc in cursor:
            doc.pop('_id', None)
            results.append(doc)
        
        logger.info(f"Retrieved {len(results)} KYC results with status: {status}")
        return results
        
    except Exception as e:
        logger.error(f"Failed to retrieve KYC results by status: {str(e)}")
        return []

async def get_verification_stats(days: int = 30) -> VerificationStats:
    """
    Get verification statistics for the specified period
    
    Args:
        days: Number of days to look back for statistics
    
    Returns:
        VerificationStats object
    """
    try:
        if not db_config.is_connected:
            return VerificationStats()
        
        collection = db_config.database[db_config.kyc_results_collection]
        
        # Calculate date range
        from_date = datetime.utcnow() - timedelta(days=days)
        
        # Aggregation pipeline for statistics
        pipeline = [
            {'$match': {'created_at': {'$gte': from_date}}},
            {'$group': {
                '_id': None,
                'total': {'$sum': 1},
                'successful': {'$sum': {'$cond': [{'$eq': ['$status', 'completed']}, 1, 0]}},
                'failed': {'$sum': {'$cond': [{'$eq': ['$status', 'failed']}, 1, 0]}},
                'pending': {'$sum': {'$cond': [{'$eq': ['$status', 'manual_review']}, 1, 0]}},
                'avg_trust_score': {'$avg': '$trust_score'}
            }}
        ]
        
        result = await collection.aggregate(pipeline).to_list(length=1)
        
        if result:
            stats_data = result[0]
            return VerificationStats(
                total_verifications=stats_data.get('total', 0),
                successful_verifications=stats_data.get('successful', 0),
                failed_verifications=stats_data.get('failed', 0),
                pending_reviews=stats_data.get('pending', 0),
                average_trust_score=round(stats_data.get('avg_trust_score', 0.0), 2)
            )
        else:
            return VerificationStats()
        
    except Exception as e:
        logger.error(f"Failed to get verification stats: {str(e)}")
        return VerificationStats()

async def log_verification_event(verification_id: str, event_type: str, metadata: Dict[str, Any] = None):
    """
    Log verification event for audit trail
    
    Args:
        verification_id: Verification ID
        event_type: Type of event (e.g., 'verification_started', 'verification_completed')
        metadata: Additional event metadata
    """
    try:
        if not db_config.is_connected:
            return
        
        collection = db_config.database[db_config.verification_logs_collection]
        
        log_entry = {
            'verification_id': verification_id,
            'event_type': event_type,
            'timestamp': datetime.utcnow(),
            'metadata': metadata or {}
        }
        
        await collection.insert_one(log_entry)
        
    except Exception as e:
        logger.error(f"Failed to log verification event: {str(e)}")

# Import required for datetime operations
from datetime import timedelta