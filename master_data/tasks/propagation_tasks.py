"""
Celery tasks for background string propagation processing.
"""

import uuid
import logging
from typing import List, Dict, Any, Optional
from celery import shared_task
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model

from ..models import (
    StringDetail, String, Workspace, 
    PropagationJob, PropagationError
)
from ..services.propagation_service import PropagationService, PropagationError as PropagationServiceError

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_large_propagation(
    self,
    string_detail_updates: List[Dict[str, Any]],
    workspace_id: int,
    user_id: Optional[int] = None,
    options: Optional[Dict[str, Any]] = None,
    job_id: Optional[str] = None
):
    """
    Process large string propagation operations in the background.
    
    Args:
        string_detail_updates: List of StringDetail updates to process
        workspace_id: ID of the workspace
        user_id: ID of the user who triggered the operation
        options: Additional processing options
        job_id: Existing job ID to update (optional)
    
    Returns:
        Dict with processing results
    """
    options = options or {}
    batch_id = uuid.UUID(job_id) if job_id else uuid.uuid4()
    
    logger.info(f"Starting background propagation task: {batch_id}")
    
    try:
        # Get workspace and user
        workspace = Workspace.objects.get(id=workspace_id)
        user = User.objects.get(id=user_id) if user_id else None
        
        # Get or create job record
        job, created = PropagationJob.objects.get_or_create(
            batch_id=batch_id,
            defaults={
                'workspace': workspace,
                'triggered_by': user,
                'status': 'running',
                'processing_method': 'background',
                'metadata': {
                    'task_id': self.request.id,
                    'updates': string_detail_updates,
                    'options': options
                }
            }
        )
        
        if not created:
            job.status = 'running'
            job.started_at = timezone.now()
            job.save()
        else:
            job.mark_started()
        
        # Process the propagation
        result = _process_propagation_with_progress(
            self, job, string_detail_updates, workspace, user, options
        )
        
        # Update job with final results
        job.total_strings = result['total_affected']
        job.processed_strings = result['successful']
        job.failed_strings = result['failed']
        job.mark_completed(success=result['failed'] == 0)
        
        logger.info(f"Background propagation completed: {batch_id}")
        
        return {
            'job_id': str(batch_id),
            'status': 'completed',
            'total_affected': result['total_affected'],
            'successful': result['successful'],
            'failed': result['failed'],
            'processing_time': result.get('processing_time', 0)
        }
        
    except Exception as exc:
        logger.error(f"Background propagation failed: {batch_id} - {str(exc)}")
        
        # Update job status
        try:
            job.add_error(str(exc))
        except:
            pass
        
        # Retry logic
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying propagation task: {batch_id} (attempt {self.request.retries + 1})")
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
        
        return {
            'job_id': str(batch_id),
            'status': 'failed',
            'error': str(exc)
        }


def _process_propagation_with_progress(
    task,
    job: PropagationJob,
    string_detail_updates: List[Dict[str, Any]],
    workspace,
    user: Optional[User],
    options: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Process propagation with progress updates.
    """
    start_time = timezone.now()
    total_affected = 0
    successful = 0
    failed = 0
    
    # Process in chunks for better performance and progress tracking
    chunk_size = options.get('chunk_size', 10)
    error_handling = options.get('error_handling', 'continue')
    
    chunks = [
        string_detail_updates[i:i + chunk_size]
        for i in range(0, len(string_detail_updates), chunk_size)
    ]
    
    logger.info(f"Processing {len(string_detail_updates)} updates in {len(chunks)} chunks")
    
    for chunk_index, chunk in enumerate(chunks):
        try:
            # Update progress
            progress = (chunk_index / len(chunks)) * 100
            task.update_state(
                state='PROGRESS',
                meta={
                    'current_chunk': chunk_index + 1,
                    'total_chunks': len(chunks),
                    'progress': progress,
                    'processed': successful,
                    'failed': failed
                }
            )
            
            # Process chunk
            chunk_result = _process_chunk(
                chunk, workspace, user, job, options
            )
            
            total_affected += chunk_result['total_affected']
            successful += chunk_result['successful']
            failed += chunk_result['failed']
            
            # Update job progress
            job.processed_strings = successful
            job.failed_strings = failed
            job.save(update_fields=['processed_strings', 'failed_strings'])
            
            logger.info(
                f"Chunk {chunk_index + 1}/{len(chunks)} completed: "
                f"{chunk_result['successful']} successful, {chunk_result['failed']} failed"
            )
            
            # Check error handling strategy
            if failed > 0 and error_handling == 'stop':
                logger.warning(f"Stopping processing due to errors (error_handling=stop)")
                break
                
        except Exception as chunk_error:
            logger.error(f"Chunk {chunk_index + 1} failed: {str(chunk_error)}")
            
            # Log chunk-level error
            _log_chunk_error(job, chunk_index, chunk, str(chunk_error))
            
            failed += len(chunk)  # Count all items in failed chunk as failed
            
            if error_handling == 'stop':
                raise chunk_error
            # Continue with next chunk if error_handling is 'continue'
    
    end_time = timezone.now()
    processing_time = (end_time - start_time).total_seconds()
    
    return {
        'total_affected': total_affected,
        'successful': successful,
        'failed': failed,
        'processing_time': processing_time
    }


def _process_chunk(
    chunk: List[Dict[str, Any]],
    workspace,
    user: Optional[User],
    job: PropagationJob,
    options: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Process a single chunk of string detail updates.
    """
    successful = 0
    failed = 0
    total_affected = 0
    
    for update in chunk:
        try:
            with transaction.atomic():
                # Execute single update
                result = PropagationService._execute_single_update(
                    update, workspace, user, job.batch_id, options
                )
                
                successful += 1
                total_affected += result.get('affected_count', 1)
                
        except Exception as update_error:
            logger.error(
                f"Update failed for StringDetail {update.get('string_detail_id')}: "
                f"{str(update_error)}"
            )
            
            # Log individual update error
            _log_update_error(job, update, str(update_error))
            
            failed += 1
    
    return {
        'total_affected': total_affected,
        'successful': successful,
        'failed': failed
    }


def _log_chunk_error(
    job: PropagationJob,
    chunk_index: int,
    chunk: List[Dict[str, Any]],
    error_message: str
) -> None:
    """
    Log errors that occur at the chunk level.
    """
    try:
        PropagationError.objects.create(
            workspace=job.workspace,
            job=job,
            error_type='chunk_processing_error',
            error_message=f"Chunk {chunk_index + 1} failed: {error_message}",
            context_data={
                'chunk_index': chunk_index,
                'chunk_size': len(chunk),
                'string_detail_ids': [u.get('string_detail_id') for u in chunk]
            },
            is_retryable=True
        )
    except Exception as log_error:
        logger.error(f"Failed to log chunk error: {str(log_error)}")


def _log_update_error(
    job: PropagationJob,
    update: Dict[str, Any],
    error_message: str
) -> None:
    """
    Log errors that occur for individual updates.
    """
    try:
        # Try to get the StringDetail and String references
        string_detail = None
        string_obj = None
        
        string_detail_id = update.get('string_detail_id')
        if string_detail_id:
            try:
                string_detail = StringDetail.objects.select_related('string').get(
                    id=string_detail_id
                )
                string_obj = string_detail.string
            except StringDetail.DoesNotExist:
                pass
        
        PropagationError.objects.create(
            workspace=job.workspace,
            job=job,
            string=string_obj,
            string_detail=string_detail,
            error_type='update_processing_error',
            error_message=error_message,
            context_data={
                'update_data': update,
                'string_detail_id': string_detail_id
            },
            is_retryable=True
        )
    except Exception as log_error:
        logger.error(f"Failed to log update error: {str(log_error)}")


@shared_task(bind=True)
def analyze_propagation_impact(
    self,
    string_detail_updates: List[Dict[str, Any]],
    workspace_id: int,
    max_depth: int = 10
):
    """
    Analyze the impact of proposed string detail updates in the background.
    
    Args:
        string_detail_updates: List of updates to analyze
        workspace_id: ID of the workspace
        max_depth: Maximum depth to analyze
    
    Returns:
        Impact analysis results
    """
    logger.info(f"Starting background impact analysis for workspace {workspace_id}")
    
    try:
        workspace = Workspace.objects.get(id=workspace_id)
        
        # Update task progress
        self.update_state(
            state='PROGRESS',
            meta={'status': 'analyzing', 'progress': 25}
        )
        
        # Perform impact analysis
        impact = PropagationService.analyze_impact(
            string_detail_updates, workspace, max_depth
        )
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'status': 'finalizing', 'progress': 90}
        )
        
        logger.info(f"Impact analysis completed: {len(impact['affected_strings'])} strings affected")
        
        return {
            'status': 'completed',
            'impact': impact
        }
        
    except Exception as exc:
        logger.error(f"Impact analysis failed: {str(exc)}")
        
        return {
            'status': 'failed',
            'error': str(exc)
        }


@shared_task
def cleanup_old_propagation_jobs(days_old: int = 30):
    """
    Clean up old completed propagation jobs and their errors.
    
    Args:
        days_old: Number of days after which to clean up jobs
    """
    from datetime import timedelta
    
    cutoff_date = timezone.now() - timedelta(days=days_old)
    
    logger.info(f"Cleaning up propagation jobs older than {cutoff_date}")
    
    # Delete old completed jobs and their related errors
    old_jobs = PropagationJob.objects.filter(
        status__in=['completed', 'failed'],
        completed_at__lt=cutoff_date
    )
    
    job_count = old_jobs.count()
    
    # Delete related errors first (due to foreign key constraints)
    error_count = PropagationError.objects.filter(
        job__in=old_jobs
    ).count()
    
    PropagationError.objects.filter(job__in=old_jobs).delete()
    old_jobs.delete()
    
    logger.info(f"Cleaned up {job_count} old jobs and {error_count} related errors")
    
    return {
        'deleted_jobs': job_count,
        'deleted_errors': error_count
    }


@shared_task
def retry_failed_propagation_updates(job_id: str, max_retries: int = 3):
    """
    Retry failed updates from a propagation job.
    
    Args:
        job_id: UUID of the propagation job
        max_retries: Maximum number of retries per update
    """
    logger.info(f"Retrying failed updates for job {job_id}")
    
    try:
        job = PropagationJob.objects.get(batch_id=job_id)
        
        # Get retryable errors
        retryable_errors = job.errors.filter(
            is_retryable=True,
            resolved=False,
            retry_count__lt=max_retries
        ).select_related('string_detail')
        
        retry_count = 0
        success_count = 0
        
        for error in retryable_errors:
            try:
                # Increment retry count
                error.increment_retry_count()
                
                # Attempt to retry the operation
                if error.string_detail:
                    # Reconstruct the update from context data
                    context = error.context_data
                    update_data = context.get('update_data', {})
                    
                    if update_data:
                        # Re-execute the update
                        PropagationService._execute_single_update(
                            update_data, job.workspace, job.triggered_by, job.batch_id, {}
                        )
                        
                        # Mark error as resolved
                        error.mark_resolved()
                        success_count += 1
                        
                retry_count += 1
                
            except Exception as retry_error:
                logger.error(f"Retry failed for error {error.id}: {str(retry_error)}")
                
                # Update error with retry failure info
                if error.retry_count >= max_retries:
                    error.is_retryable = False
                    error.save(update_fields=['is_retryable'])
        
        logger.info(f"Retry completed: {success_count}/{retry_count} successful")
        
        return {
            'job_id': job_id,
            'attempted_retries': retry_count,
            'successful_retries': success_count,
            'failed_retries': retry_count - success_count
        }
        
    except PropagationJob.DoesNotExist:
        logger.error(f"Job {job_id} not found for retry")
        return {
            'error': f'Job {job_id} not found'
        }
    except Exception as exc:
        logger.error(f"Retry operation failed: {str(exc)}")
        return {
            'error': str(exc)
        }


@shared_task
def generate_propagation_report(workspace_id: int, start_date: str, end_date: str):
    """
    Generate a comprehensive propagation report for a workspace.
    
    Args:
        workspace_id: ID of the workspace
        start_date: Start date for the report (ISO format)
        end_date: End date for the report (ISO format)
    """
    from datetime import datetime
    
    logger.info(f"Generating propagation report for workspace {workspace_id}")
    
    try:
        workspace = Workspace.objects.get(id=workspace_id)
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        
        # Get jobs in date range
        jobs = PropagationJob.objects.filter(
            workspace=workspace,
            created__range=[start_dt, end_dt]
        ).select_related('triggered_by')
        
        # Calculate statistics
        total_jobs = jobs.count()
        completed_jobs = jobs.filter(status='completed').count()
        failed_jobs = jobs.filter(status='failed').count()
        
        # Get error statistics
        errors = PropagationError.objects.filter(
            job__in=jobs
        ).values('error_type').annotate(
            count=models.Count('id')
        ).order_by('-count')
        
        # Calculate average processing time
        completed_with_duration = jobs.filter(
            status='completed',
            started_at__isnull=False,
            completed_at__isnull=False
        )
        
        avg_duration = None
        if completed_with_duration.exists():
            durations = [
                (job.completed_at - job.started_at).total_seconds()
                for job in completed_with_duration
            ]
            avg_duration = sum(durations) / len(durations)
        
        # Generate report
        report = {
            'workspace_id': workspace_id,
            'workspace_name': workspace.name,
            'report_period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'summary': {
                'total_jobs': total_jobs,
                'completed_jobs': completed_jobs,
                'failed_jobs': failed_jobs,
                'success_rate': (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0,
                'average_duration_seconds': avg_duration
            },
            'error_breakdown': list(errors),
            'generated_at': timezone.now().isoformat()
        }
        
        logger.info(f"Report generated: {total_jobs} jobs analyzed")
        
        return report
        
    except Exception as exc:
        logger.error(f"Report generation failed: {str(exc)}")
        return {
            'error': str(exc)
        }