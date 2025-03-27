"""Environment detection and configuration utilities."""

import os
import logging
import socket
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class Environment:
    """Environment detection and configuration."""
    
    LOCAL = "local"
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    
    @staticmethod
    def get_current():
        """
        Detect the current environment based on various indicators.
        
        Returns:
            str: One of LOCAL, DEVELOPMENT, STAGING, PRODUCTION
        """
        # Check explicit environment variable first
        env = os.environ.get("FLASK_ENV", "").lower()
        if env in ["production", "development", "staging"]:
            return env
            
        # Check for common cloud provider environment variables
        if any([
            os.environ.get("RAILWAY_STATIC_URL"),
            os.environ.get("RAILWAY_SERVICE_ID"),
            os.environ.get("RAILWAY_PROJECT_ID"),
            os.environ.get("HEROKU_APP_ID"),
            os.environ.get("RENDER_SERVICE_ID"),
            os.environ.get("VERCEL_URL")
        ]):
            return Environment.PRODUCTION
            
        # Default to local
        return Environment.LOCAL
    
    @staticmethod
    def is_production():
        """Check if running in production environment."""
        return Environment.get_current() == Environment.PRODUCTION
    
    @staticmethod
    def is_local():
        """Check if running in local environment."""
        return Environment.get_current() == Environment.LOCAL
    
    @staticmethod
    def get_host_url():
        """
        Try to determine the host URL for the current environment.
        
        Returns:
            str: Host URL or None if undeterminable
        """

            if url := os.environ.get(env_var):
                # Ensure URL has proper protocol
                if not url.startswith(("http://", "https://")):
                    url = f"https://{url}"
                logger.info(f"Detected host URL from {env_var}: {url}")
                return url
                
        # In local environment, try to determine local IP
        if Environment.is_local():
            try:
                # Get primary local IP
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                # This doesn't actually establish a connection
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                s.close()
                
                # Default port from config or fallback to 5000
                port = os.environ.get("PORT", "5000")
                return f"http://{local_ip}:{port}"
            except:
                # If can't determine local IP
                return "http://localhost:5000"
                
        logger.warning("Could not determine host URL")
        return None
        
    @staticmethod
    def get_config_json():
        """
        Return environment configuration as a JSON object.
        Useful for exposing to frontend.
        
        Returns:
            dict: Configuration dictionary
        """
        return {
            "environment": Environment.get_current(),
            "host_url": Environment.get_host_url(),
            "is_production": Environment.is_production(),
            "api_version": "1.0.0"
        }

# If run directly, print environment info
if __name__ == "__main__":
    print(json.dumps(Environment.get_config_json(), indent=2))
