"""
Centralized configuration for market scanner system.
"""
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Load environment variables from .env file or credentials.py
try:
    from dotenv import load_dotenv
    # Look for .env file in the project root (parent of market_scanner)
    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(env_path)
except ImportError:
    # dotenv not installed, that's okay - will use system env vars
    pass

# Try to import from local credentials.py file
try:
    # Import from parent directory (02_market_scanner/credentials.py)
    import sys
    credentials_path = Path(__file__).parent.parent
    sys.path.insert(0, str(credentials_path))
    import credentials
    # Set environment variables from credentials if they're not already set
    if not os.getenv('POLYGON_API_KEY') and hasattr(credentials, 'POLYGON_API_KEY'):
        os.environ['POLYGON_API_KEY'] = credentials.POLYGON_API_KEY
    if not os.getenv('SUPABASE_URL') and hasattr(credentials, 'SUPABASE_URL'):
        os.environ['SUPABASE_URL'] = credentials.SUPABASE_URL
    if not os.getenv('SUPABASE_KEY') and hasattr(credentials, 'SUPABASE_KEY'):
        os.environ['SUPABASE_KEY'] = credentials.SUPABASE_KEY
except ImportError:
    # credentials.py not found, that's okay - will use env vars
    pass

@dataclass
class ScannerConfig:
    """Global configuration for market scanner."""
    
    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent
    DATA_CACHE_DIR: Path = BASE_DIR / "data" / "cache"
    OUTPUT_DIR: Path = BASE_DIR / "outputs" / "reports"
    TEMPLATE_DIR: Path = BASE_DIR / "outputs" / "templates"
    
    # API Configuration
    POLYGON_API_KEY: Optional[str] = os.getenv('POLYGON_API_KEY')
    POLYGON_CACHE_ENABLED: bool = True
    
    # Supabase Configuration
    SUPABASE_URL: Optional[str] = os.getenv('SUPABASE_URL')
    SUPABASE_KEY: Optional[str] = os.getenv('SUPABASE_KEY')
    
    # Scanner Settings
    DEFAULT_PARALLEL_WORKERS: int = 10
    DEFAULT_LOOKBACK_DAYS: int = 14
    UPDATE_FREQUENCY_DAYS: int = 90
    
    # Market Hours (UTC)
    PREMARKET_START_HOUR: int = 4
    PREMARKET_START_MINUTE: int = 0
    MARKET_OPEN_HOUR: int = 9
    MARKET_OPEN_MINUTE: int = 30
    
    def __post_init__(self):
        """Create directories if they don't exist."""
        self.DATA_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
    def validate(self) -> bool:
        """Validate configuration."""
        if not self.POLYGON_API_KEY:
            raise ValueError("POLYGON_API_KEY not set in environment")
        return True

# Global instance
config = ScannerConfig()