from platform_commons.logs.platform_logger import PlatformLogger

"""
Singleton logger instance with a unified logging level from settings.
Prevents creation of separate loggers with different levels.
"""

logger = PlatformLogger(log_level="INFO")
