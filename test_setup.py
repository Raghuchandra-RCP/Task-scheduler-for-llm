#!/usr/bin/env python3
"""
Test script for Windows Trial Scheduler

This script tests the basic functionality without making API calls or database writes.
Use this to verify your setup before running the full scheduler.
"""

import os
import sys
import logging
from dotenv import load_dotenv
from config import get_config

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Test if all required modules can be imported"""
    logger.info("Testing imports...")
    
    try:
        import requests
        logger.info("✓ requests imported successfully")
    except ImportError as e:
        logger.error(f"✗ Failed to import requests: {e}")
        return False
    
    try:
        import sqlalchemy
        logger.info("✓ sqlalchemy imported successfully")
    except ImportError as e:
        logger.error(f"✗ Failed to import sqlalchemy: {e}")
        return False
    
    try:
        import psycopg2
        logger.info("✓ psycopg2 imported successfully")
    except ImportError as e:
        logger.error(f"✗ Failed to import psycopg2: {e}")
        return False
    
    return True

def test_configuration():
    """Test configuration loading"""
    logger.info("Testing configuration...")
    
    try:
        config = get_config()
        logger.info(f"✓ Configuration loaded: {config.__class__.__name__}")
        
        # Test database URL generation
        db_url = config.get_database_url()
        logger.info(f"✓ Database URL generated: {db_url.split('@')[0]}@***")
        
        # Test API parameters
        api_params = config.get_api_params("RECRUITING")
        logger.info(f"✓ API parameters generated: {api_params}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Configuration test failed: {e}")
        return False

def test_database_connection():
    """Test database connection"""
    logger.info("Testing database connection...")
    
    try:
        from sqlalchemy import create_engine, text
        
        config = get_config()
        engine = create_engine(config.get_database_url())
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            test_value = result.fetchone()[0]
            
        if test_value == 1:
            logger.info("✓ Database connection successful")
            return True
        else:
            logger.error("✗ Database connection test failed")
            return False
            
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        return False

def test_api_connectivity():
    """Test API connectivity"""
    logger.info("Testing API connectivity...")
    
    try:
        import requests
        
        config = get_config()
        api_params = config.get_api_params("RECRUITING", 1)  # Small test request
        
        response = requests.get(config.API_BASE_URL, params=api_params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            studies = data.get('studies', [])
            logger.info(f"✓ API connectivity successful - received {len(studies)} studies")
            return True
        else:
            logger.error(f"✗ API request failed with status {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"✗ API connectivity test failed: {e}")
        return False

def test_logs_directory():
    """Test logs directory creation"""
    logger.info("Testing logs directory...")
    
    try:
        os.makedirs('logs', exist_ok=True)
        logger.info("✓ Logs directory ready")
        return True
    except Exception as e:
        logger.error(f"✗ Logs directory test failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("=" * 60)
    logger.info("WINDOWS TRIAL SCHEDULER - SETUP TEST")
    logger.info("=" * 60)
    
    tests = [
        ("Import Test", test_imports),
        ("Configuration Test", test_configuration),
        ("Database Connection Test", test_database_connection),
        ("API Connectivity Test", test_api_connectivity),
        ("Logs Directory Test", test_logs_directory)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\nRunning {test_name}...")
        try:
            if test_func():
                passed += 1
                logger.info(f"✓ {test_name} PASSED")
            else:
                logger.error(f"✗ {test_name} FAILED")
        except Exception as e:
            logger.error(f"✗ {test_name} FAILED with exception: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info(f"TEST RESULTS: {passed}/{total} tests passed")
    logger.info("=" * 60)
    
    if passed == total:
        logger.info("🎉 All tests passed! Your setup is ready.")
        logger.info("You can now run: python trial_scheduler.py")
        return True
    else:
        logger.error("❌ Some tests failed. Please fix the issues before running the scheduler.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
