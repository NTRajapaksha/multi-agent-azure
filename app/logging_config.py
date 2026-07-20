import logging
import sys
from azure.monitor.opentelemetry.exporter import AzureMonitorLogExporter
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from app.config import settings

def setup_logging():
    logger = logging.getLogger("agent")
    logger.setLevel(logging.INFO)
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if settings.appinsights_connection_string:
        try:
            logger_provider = LoggerProvider()
            set_logger_provider(logger_provider)
            exporter = AzureMonitorLogExporter(connection_string=settings.appinsights_connection_string)
            logger_provider.add_log_record_processor(BatchLogRecordProcessor(exporter))
            handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
            logger.addHandler(handler)
        except Exception as e:
            logger.warning(f"Failed to setup Azure Monitor logging: {e}")
        
    return logger

logger = setup_logging()
