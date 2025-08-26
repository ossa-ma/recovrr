"""Scheduler service for running monitoring jobs."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from recovrr.config.settings import settings
from .monitoring_job import MonitoringJob

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service for scheduling and running monitoring jobs."""
    
    def __init__(self):
        """Initialize the scheduler service."""
        self.scheduler = AsyncIOScheduler()
        self.monitoring_job = MonitoringJob()
        self.is_running = False
        
    async def start(self):
        """Start the scheduler service."""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
            
        try:
            # Add the main monitoring job
            self.scheduler.add_job(
                func=self._run_monitoring_cycle,
                trigger=IntervalTrigger(minutes=settings.scrape_interval_minutes),
                id='monitoring_cycle',
                name='Marketplace Monitoring Cycle',
                max_instances=1,  # Prevent overlapping runs
                replace_existing=True
            )
            
            # Add a daily summary job
            self.scheduler.add_job(
                func=self._send_daily_summary,
                trigger=CronTrigger(hour=9, minute=0),  # 9 AM daily
                id='daily_summary',
                name='Daily Summary Report',
                replace_existing=True
            )
            
            # Start the scheduler
            self.scheduler.start()
            self.is_running = True
            
            logger.info(f"Scheduler started - monitoring every {settings.scrape_interval_minutes} minutes")
            
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            raise
            
    async def stop(self):
        """Stop the scheduler service."""
        if not self.is_running:
            return
            
        try:
            self.scheduler.shutdown(wait=True)
            self.is_running = False
            logger.info("Scheduler stopped")
            
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
            
    async def run_once(self) -> dict:
        """Run a single monitoring cycle manually.
        
        Returns:
            Dictionary with cycle results
        """
        logger.info("Running manual monitoring cycle")
        return await self.monitoring_job.run_monitoring_cycle()
        
    async def _run_monitoring_cycle(self):
        """Internal method to run monitoring cycle (called by scheduler)."""
        try:
            result = await self.monitoring_job.run_monitoring_cycle()
            
            # Log summary
            if result['status'] == 'completed':
                logger.info(
                    f"Monitoring cycle completed: "
                    f"{result['new_listings']} new listings, "
                    f"{result['matches_found']} matches, "
                    f"{result['notifications_sent']} notifications sent"
                )
            else:
                logger.error(f"Monitoring cycle failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Error in scheduled monitoring cycle: {e}")
            
    async def _send_daily_summary(self):
        """Send daily summary of monitoring activity."""
        try:
            # This would query the database for daily stats
            # and send a summary email/notification
            logger.info("Sending daily summary (not implemented yet)")
            
        except Exception as e:
            logger.error(f"Error sending daily summary: {e}")
            
    def get_job_status(self) -> dict:
        """Get status of scheduled jobs.
        
        Returns:
            Dictionary with job status information
        """
        if not self.is_running:
            return {'status': 'stopped', 'jobs': []}
            
        jobs = []
        for job in self.scheduler.get_jobs():
            job_info = {
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            }
            jobs.append(job_info)
            
        return {
            'status': 'running',
            'jobs': jobs
        }
        
    async def reschedule_monitoring(self, interval_minutes: int):
        """Reschedule the monitoring job with a new interval.
        
        Args:
            interval_minutes: New interval in minutes
        """
        try:
            self.scheduler.modify_job(
                'monitoring_cycle',
                trigger=IntervalTrigger(minutes=interval_minutes)
            )
            logger.info(f"Monitoring interval updated to {interval_minutes} minutes")
            
        except Exception as e:
            logger.error(f"Error rescheduling monitoring job: {e}")
            
    async def pause_monitoring(self):
        """Pause the monitoring job."""
        try:
            self.scheduler.pause_job('monitoring_cycle')
            logger.info("Monitoring job paused")
            
        except Exception as e:
            logger.error(f"Error pausing monitoring job: {e}")
            
    async def resume_monitoring(self):
        """Resume the monitoring job."""
        try:
            self.scheduler.resume_job('monitoring_cycle')
            logger.info("Monitoring job resumed")
            
        except Exception as e:
            logger.error(f"Error resuming monitoring job: {e}")


async def main():
    """Main function for running the scheduler as a standalone service."""
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and start scheduler
    scheduler_service = SchedulerService()
    
    try:
        await scheduler_service.start()
        
        # Keep the service running
        logger.info("Recovrr monitoring service started. Press Ctrl+C to stop.")
        
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
        
    finally:
        await scheduler_service.stop()
        logger.info("Recovrr monitoring service stopped")


if __name__ == "__main__":
    asyncio.run(main())
