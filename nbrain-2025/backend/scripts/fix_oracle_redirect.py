#!/usr/bin/env python3
"""
Fix Oracle OAuth redirect URI for production.
This script updates the redirect URI to use the correct production URL.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_redirect_uri():
    """Log the current redirect URI configuration"""
    current_uri = os.getenv("GOOGLE_REDIRECT_URI", "not set")
    
    logger.info("="*60)
    logger.info("Oracle OAuth Configuration Check")
    logger.info("="*60)
    logger.info(f"Current GOOGLE_REDIRECT_URI: {current_uri}")
    
    if "localhost" in current_uri:
        logger.warning("⚠️  Redirect URI is set to localhost!")
        logger.info("For production, set GOOGLE_REDIRECT_URI to:")
        logger.info("https://command.nbrain.ai/oracle/auth/callback")
    else:
        logger.info("✓ Redirect URI appears to be configured for production")
    
    # Check if Google credentials are set
    client_id = os.getenv("GOOGLE_CLIENT_ID", "not set")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "not set")
    
    if client_id == "not set":
        logger.error("❌ GOOGLE_CLIENT_ID is not set!")
    else:
        logger.info(f"✓ GOOGLE_CLIENT_ID is set: {client_id[:10]}...")
    
    if client_secret == "not set":
        logger.error("❌ GOOGLE_CLIENT_SECRET is not set!")
    else:
        logger.info("✓ GOOGLE_CLIENT_SECRET is set")
    
    logger.info("="*60)
    
    # Instructions for fixing
    if "localhost" in current_uri or client_id == "not set" or client_secret == "not set":
        logger.info("\nTo fix Oracle OAuth:")
        logger.info("1. Set these environment variables in Render:")
        logger.info("   GOOGLE_CLIENT_ID=<your-client-id>")
        logger.info("   GOOGLE_CLIENT_SECRET=<your-client-secret>")
        logger.info("   GOOGLE_REDIRECT_URI=https://command.nbrain.ai/oracle/auth/callback")
        logger.info("\n2. In Google Cloud Console, add this redirect URI:")
        logger.info("   https://command.nbrain.ai/oracle/auth/callback")
        logger.info("\n3. Make sure the OAuth consent screen is configured")

if __name__ == "__main__":
    fix_redirect_uri() 