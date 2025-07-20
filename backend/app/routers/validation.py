"""Validation processing router."""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from app.services.supabase_service import supabase_service
from app.services.scraping_service import ScrapingService
from app.scrapers.product_hunt_scraper import ProductHuntScraper
from app.scrapers.google_scraper import GoogleScraper
from app.scrapers.reddit_scraper import RedditScraper
from app.scrapers.google_play_store_scraper import GooglePlayStoreScraper
from app.scrapers.app_store_scraper import AppStoreScraper
from app.scrapers.microsoft_store_scraper import MicrosoftStoreScraper

logger = logging.getLogger(__name__)

router = APIRouter()


class ProcessValidationRequest(BaseModel):
    """Request model for validation processing."""
    validation_id: str = Field(..., description="UUID of the validation to process")


class ProcessValidationResponse(BaseModel):
    """Response model for validation processing."""
    message: str
    validation_id: str
    status: str


async def process_validation_background(validation_id: str) -> None:
    """
    Background task to process validation with scraping and data storage.
    
    Args:
        validation_id: UUID of the validation to process
    """
    try:
        logger.info(f"Starting background processing for validation {validation_id}")
        
        # Update status to processing
        await supabase_service.update_validation_status(
            validation_id, 
            "processing",
            processing_started_at=datetime.utcnow().isoformat()
        )
        
        # Get validation data
        validation = await supabase_service.get_validation(validation_id)
        if not validation:
            logger.error(f"Validation {validation_id} not found")
            await supabase_service.update_validation_status(
                validation_id, 
                "failed",
                error_message="Validation not found"
            )
            return
        
        idea_text = validation.get('idea_text', '')
        if not idea_text:
            logger.error(f"No idea text found for validation {validation_id}")
            await supabase_service.update_validation_status(
                validation_id, 
                "failed",
                error_message="No idea text provided"
            )
            return
        
        # Initialize scraping service
        scraping_service = ScrapingService()
        
        # Register Product Hunt scraper
        product_hunt_scraper = ProductHuntScraper()
        scraping_service.register_scraper(product_hunt_scraper)
        
        # Register Reddit scraper
        reddit_scraper = RedditScraper()
        scraping_service.register_scraper(reddit_scraper)
        
        # Register Google scraper
        google_scraper = GoogleScraper()
        scraping_service.register_scraper(google_scraper)
        
        # Register Google Play Store scraper
        google_play_scraper = GooglePlayStoreScraper()
        scraping_service.register_scraper(google_play_scraper)
        
        # Register iOS App Store scraper
        app_store_scraper = AppStoreScraper()
        scraping_service.register_scraper(app_store_scraper)
        
        # Register Microsoft Store scraper
        microsoft_store_scraper = MicrosoftStoreScraper()
        scraping_service.register_scraper(microsoft_store_scraper)
        
        logger.info(f"Registered scrapers: {scraping_service.get_registered_scrapers()}")
        
        # Perform scraping
        scraping_results = await scraping_service.scrape_all_sources(idea_text, validation_id)
        
        # Store competitors in database
        competitors_stored = 0
        for competitor in scraping_results.get('competitors', []):
            try:
                competitor_id = await supabase_service.create_competitor(
                    validation_id=validation_id,
                    name=competitor.name,
                    description=competitor.description,
                    website=competitor.website,
                    estimated_users=competitor.estimated_users,
                    estimated_revenue=competitor.estimated_revenue,
                    pricing_model=competitor.pricing_model,
                    source=competitor.source,
                    source_url=competitor.source_url,
                    confidence_score=competitor.confidence_score
                )
                if competitor_id:
                    competitors_stored += 1
            except Exception as e:
                logger.warning(f"Failed to store competitor {competitor.name}: {str(e)}")
                continue
        
        # Store feedback in database
        feedback_stored = 0
        for feedback in scraping_results.get('feedback', []):
            try:
                feedback_id = await supabase_service.create_feedback(
                    validation_id=validation_id,
                    text=feedback.text,
                    sentiment=feedback.sentiment,
                    sentiment_score=feedback.sentiment_score,
                    source=feedback.source,
                    source_url=feedback.source_url,
                    author_info=feedback.author_info
                )
                if feedback_id:
                    feedback_stored += 1
            except Exception as e:
                logger.warning(f"Failed to store feedback: {str(e)}")
                continue
        
        # Update validation counts
        await supabase_service.update_validation_counts(validation_id)
        
        # Calculate basic market score (1-10 scale)
        market_score = calculate_market_score(
            competitors_stored, 
            feedback_stored, 
            scraping_results.get('metadata', {})
        )
        
        # Update validation status to completed
        await supabase_service.update_validation_status(
            validation_id,
            "completed",
            market_score=market_score,
            completed_at=datetime.utcnow().isoformat(),
            sources_scraped=scraping_results.get('metadata', {}).get('successful_sources', []),
            processing_metadata=scraping_results.get('metadata', {})
        )
        
        logger.info(f"Completed processing for validation {validation_id}: "
                   f"{competitors_stored} competitors, {feedback_stored} feedback, "
                   f"market score: {market_score}")
        
    except Exception as e:
        logger.error(f"Background processing failed for validation {validation_id}: {str(e)}")
        try:
            await supabase_service.update_validation_status(
                validation_id,
                "failed",
                error_message=str(e),
                failed_at=datetime.utcnow().isoformat()
            )
        except Exception as update_error:
            logger.error(f"Failed to update validation status after error: {str(update_error)}")


def calculate_market_score(competitor_count: int, feedback_count: int, metadata: Dict[str, Any]) -> float:
    """
    Calculate market score based on competition and feedback data.
    
    Args:
        competitor_count: Number of competitors found
        feedback_count: Number of feedback items found
        metadata: Scraping metadata
        
    Returns:
        Market score from 1.0 to 10.0
    """
    try:
        # Base score starts at 5.0 (neutral)
        score = 5.0
        
        # Adjust based on competition (fewer competitors = higher score)
        if competitor_count == 0:
            score += 2.0  # No direct competition is good
        elif competitor_count <= 3:
            score += 1.0  # Low competition
        elif competitor_count <= 7:
            score += 0.0  # Moderate competition
        elif competitor_count <= 15:
            score -= 1.0  # High competition
        else:
            score -= 2.0  # Very high competition
        
        # Adjust based on feedback availability (more feedback = better validation)
        if feedback_count >= 20:
            score += 1.0  # Lots of user feedback available
        elif feedback_count >= 10:
            score += 0.5  # Good amount of feedback
        elif feedback_count >= 5:
            score += 0.0  # Some feedback
        else:
            score -= 0.5  # Limited feedback available
        
        # Adjust based on scraping success rate
        sources_attempted = metadata.get('sources_attempted', 1)
        sources_successful = metadata.get('sources_successful', 0)
        success_rate = sources_successful / sources_attempted if sources_attempted > 0 else 0
        
        if success_rate >= 0.8:
            score += 0.5  # High data quality
        elif success_rate >= 0.5:
            score += 0.0  # Moderate data quality
        else:
            score -= 0.5  # Low data quality
        
        # Ensure score is within bounds
        score = max(1.0, min(10.0, score))
        
        return round(score, 1)
        
    except Exception as e:
        logger.warning(f"Error calculating market score: {str(e)}")
        return 5.0  # Default neutral score


@router.post("/process-validation", response_model=ProcessValidationResponse)
async def process_validation(
    request: ProcessValidationRequest,
    background_tasks: BackgroundTasks
) -> ProcessValidationResponse:
    """
    Trigger validation processing for a given validation ID.
    
    Args:
        request: ProcessValidationRequest containing validation_id
        background_tasks: FastAPI background tasks
        
    Returns:
        ProcessValidationResponse with processing status
    """
    try:
        validation_id = request.validation_id
        
        # Validate that the validation exists and is in the right state
        validation = await supabase_service.get_validation(validation_id)
        if not validation:
            raise HTTPException(
                status_code=404,
                detail=f"Validation {validation_id} not found"
            )
        
        current_status = validation.get('status', '')
        if current_status == 'completed':
            raise HTTPException(
                status_code=400,
                detail=f"Validation {validation_id} is already completed"
            )
        
        if current_status == 'processing':
            raise HTTPException(
                status_code=400,
                detail=f"Validation {validation_id} is already being processed"
            )
        
        # Add background task for processing
        background_tasks.add_task(process_validation_background, validation_id)
        
        logger.info(f"Queued validation {validation_id} for background processing")
        
        return ProcessValidationResponse(
            message="Validation processing started",
            validation_id=validation_id,
            status="processing"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start validation processing: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start validation processing: {str(e)}"
        )