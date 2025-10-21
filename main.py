"""
Main entry point for Task Scheduler LLM Service
"""
import asyncio
import signal
import sys
from loguru import logger
from config import LOG_LEVEL, LOG_FILE
from task_scheduler import TaskScheduler

# Configure logging
logger.remove()  # Remove default handler
logger.add(
    sys.stdout,
    level=LOG_LEVEL,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)
logger.add(
    LOG_FILE,
    level=LOG_LEVEL,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    rotation="10 MB",
    retention="7 days"
)

class TaskSchedulerService:
    def __init__(self):
        self.scheduler = TaskScheduler()
        self.running = False
        
    async def start(self):
        """Start the task scheduler service"""
        logger.info("Starting Task Scheduler LLM Service...")
        
        try:
            # Initialize the scheduler
            await self.scheduler.initialize()
            
            # Start the scheduler
            self.running = True
            await self.scheduler.start()
            
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            raise
            
    async def stop(self):
        """Stop the task scheduler service"""
        logger.info("Stopping Task Scheduler LLM Service...")
        self.running = False
        
        if self.scheduler:
            await self.scheduler.stop()
            
        logger.info("Task Scheduler LLM Service stopped")

# Global service instance
service = TaskSchedulerService()

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    asyncio.create_task(service.stop())
    sys.exit(0)

async def main():
    """Main function"""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await service.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        await service.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Service interrupted by user")
    except Exception as e:
        logger.error(f"Service failed: {e}")
        sys.exit(1)
