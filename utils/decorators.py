from PyQt6.QtWidgets import QMessageBox
import functools
from services.logging_service import get_logger

logger = get_logger("UIErrorHandler")

def handle_ui_errors(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"UI Error in {func.__name__}: {str(e)}", exc_info=True)
            instance = args[0]
            QMessageBox.critical(instance, "Error", str(e))
    return wrapper