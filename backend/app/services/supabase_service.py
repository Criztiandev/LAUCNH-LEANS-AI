"""Supabase service for database operations."""

from typing import Optional, Dict, Any, List
from supabase import create_client, Client
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class SupabaseService:
    """Service class for Supabase database operations."""
    
    def __init__(self):
        """Initialize Supabase client with service role key."""
        self.client: Client = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key
        )
    
    async def update_validation_status(
        self, 
        validation_id: str, 
        status: str,
        **kwargs
    ) -> bool:
        """
        Update validation status and optional fields.
        
        Args:
            validation_id: UUID of the validation to update
            status: New status ('processing', 'completed', 'failed')
            **kwargs: Additional fields to update (market_score, completed_at, etc.)
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            update_data = {"status": status}
            update_data.update(kwargs)
            
            result = self.client.table("validations").update(update_data).eq("id", validation_id).execute()
            
            if result.data:
                logger.info(f"Updated validation {validation_id} status to {status}")
                return True
            else:
                logger.error(f"Failed to update validation {validation_id}: No data returned")
                return False
                
        except Exception as e:
            logger.error(f"Error updating validation {validation_id}: {str(e)}")
            return False
    
    async def get_validation(self, validation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get validation by ID.
        
        Args:
            validation_id: UUID of the validation
            
        Returns:
            Dict containing validation data or None if not found
        """
        try:
            result = self.client.table("validations").select("*").eq("id", validation_id).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error fetching validation {validation_id}: {str(e)}")
            return None
    
    async def create_competitor(
        self,
        validation_id: str,
        name: str,
        description: Optional[str] = None,
        website: Optional[str] = None,
        estimated_users: Optional[int] = None,
        estimated_revenue: Optional[str] = None,
        pricing_model: Optional[str] = None,
        source: str = "",
        source_url: Optional[str] = None,
        confidence_score: float = 0.0
    ) -> Optional[str]:
        """
        Create a new competitor record.
        
        Args:
            validation_id: UUID of the associated validation
            name: Competitor name
            description: Optional competitor description
            website: Optional competitor website
            estimated_users: Optional estimated user count
            estimated_revenue: Optional estimated revenue
            pricing_model: Optional pricing model description
            source: Source where competitor was found
            source_url: Optional URL of the source
            confidence_score: Confidence score (0.0-1.0)
            
        Returns:
            str: UUID of created competitor or None if failed
        """
        try:
            competitor_data = {
                "validation_id": validation_id,
                "name": name,
                "description": description,
                "website": website,
                "estimated_users": estimated_users,
                "estimated_revenue": estimated_revenue,
                "pricing_model": pricing_model,
                "source": source,
                "source_url": source_url,
                "confidence_score": confidence_score
            }
            
            result = self.client.table("competitors").insert(competitor_data).execute()
            
            if result.data:
                logger.info(f"Created competitor {name} for validation {validation_id}")
                return result.data[0]["id"]
            return None
            
        except Exception as e:
            logger.error(f"Error creating competitor {name}: {str(e)}")
            return None
    
    async def create_feedback(
        self,
        validation_id: str,
        text: str,
        sentiment: str = "neutral",
        sentiment_score: float = 0.0,
        source: str = "",
        source_url: Optional[str] = None,
        author_info: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Create a new feedback record.
        
        Args:
            validation_id: UUID of the associated validation
            text: Feedback text content
            sentiment: Sentiment classification ('positive', 'negative', 'neutral')
            sentiment_score: Sentiment confidence score (0.0-1.0)
            source: Source where feedback was found
            source_url: Optional URL of the source
            author_info: Optional author information as JSON
            
        Returns:
            str: UUID of created feedback or None if failed
        """
        try:
            feedback_data = {
                "validation_id": validation_id,
                "text": text,
                "sentiment": sentiment,
                "sentiment_score": sentiment_score,
                "source": source,
                "source_url": source_url,
                "author_info": author_info or {}
            }
            
            result = self.client.table("feedback").insert(feedback_data).execute()
            
            if result.data:
                logger.info(f"Created feedback for validation {validation_id}")
                return result.data[0]["id"]
            return None
            
        except Exception as e:
            logger.error(f"Error creating feedback: {str(e)}")
            return None
    
    async def update_validation_counts(self, validation_id: str) -> bool:
        """
        Update competitor and feedback counts for a validation.
        
        Args:
            validation_id: UUID of the validation
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            # Get competitor count
            competitor_result = self.client.table("competitors").select("id", count="exact").eq("validation_id", validation_id).execute()
            competitor_count = competitor_result.count or 0
            
            # Get feedback count
            feedback_result = self.client.table("feedback").select("id", count="exact").eq("validation_id", validation_id).execute()
            feedback_count = feedback_result.count or 0
            
            # Update validation with counts
            update_result = self.client.table("validations").update({
                "competitor_count": competitor_count,
                "feedback_count": feedback_count
            }).eq("id", validation_id).execute()
            
            if update_result.data:
                logger.info(f"Updated counts for validation {validation_id}: {competitor_count} competitors, {feedback_count} feedback")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error updating validation counts {validation_id}: {str(e)}")
            return False
    
    async def health_check(self) -> bool:
        """
        Check if Supabase connection is healthy.
        
        Returns:
            bool: True if connection is healthy, False otherwise
        """
        try:
            # Simple query to test connection
            result = self.client.table("validations").select("id").limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Supabase health check failed: {str(e)}")
            return False


# Global service instance
supabase_service = SupabaseService()