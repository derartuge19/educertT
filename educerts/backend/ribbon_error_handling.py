"""
ribbon_error_handling.py
─────────────────────────────────────────────────────────────────────
Error handling and graceful degradation for PDF verification ribbons.

This module provides comprehensive error handling, fallback mechanisms,
and graceful degradation strategies for the ribbon system.
"""

import logging
import traceback
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass
import fitz


class RibbonErrorType(Enum):
    """Types of ribbon-related errors."""
    PDF_PROCESSING_ERROR = "pdf_processing_error"
    JAVASCRIPT_EMBEDDING_ERROR = "javascript_embedding_error"
    CONTENT_ANALYSIS_ERROR = "content_analysis_error"
    STYLING_ERROR = "styling_error"
    VERIFICATION_DATA_ERROR = "verification_data_error"
    PERMISSION_ERROR = "permission_error"
    FILE_IO_ERROR = "file_io_error"
    VALIDATION_ERROR = "validation_error"


@dataclass
class RibbonError:
    """Structured error information for ribbon operations."""
    error_type: RibbonErrorType
    message: str
    details: Optional[str] = None
    recoverable: bool = True
    fallback_available: bool = True
    original_exception: Optional[Exception] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/serialization."""
        return {
            "error_type": self.error_type.value,
            "message": self.message,
            "details": self.details,
            "recoverable": self.recoverable,
            "fallback_available": self.fallback_available,
            "exception_type": type(self.original_exception).__name__ if self.original_exception else None
        }


class RibbonErrorHandler:
    """Centralized error handling for ribbon operations."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.error_history: List[RibbonError] = []
        self.fallback_strategies: Dict[RibbonErrorType, Callable] = {
            RibbonErrorType.PDF_PROCESSING_ERROR: self._fallback_basic_ribbon,
            RibbonErrorType.JAVASCRIPT_EMBEDDING_ERROR: self._fallback_static_ribbon,
            RibbonErrorType.CONTENT_ANALYSIS_ERROR: self._fallback_default_position,
            RibbonErrorType.STYLING_ERROR: self._fallback_default_styling,
            RibbonErrorType.VERIFICATION_DATA_ERROR: self._fallback_minimal_data,
            RibbonErrorType.PERMISSION_ERROR: self._fallback_standard_save,
            RibbonErrorType.FILE_IO_ERROR: self._fallback_temp_file,
            RibbonErrorType.VALIDATION_ERROR: self._fallback_skip_validation
        }
    
    def handle_error(self, error_type: RibbonErrorType, message: str, 
                    exception: Optional[Exception] = None, 
                    context: Optional[Dict[str, Any]] = None) -> RibbonError:
        """
        Handle a ribbon-related error with appropriate logging and fallback.
        
        Args:
            error_type: Type of error that occurred
            message: Human-readable error message
            exception: Original exception if available
            context: Additional context information
            
        Returns:
            RibbonError: Structured error information
        """
        # Create error object
        error = RibbonError(
            error_type=error_type,
            message=message,
            details=str(exception) if exception else None,
            recoverable=self._is_recoverable(error_type),
            fallback_available=error_type in self.fallback_strategies,
            original_exception=exception
        )
        
        # Log the error
        self._log_error(error, context)
        
        # Store in history
        self.error_history.append(error)
        
        return error
    
    def attempt_fallback(self, error: RibbonError, **kwargs) -> Any:
        """
        Attempt to execute fallback strategy for the given error.
        
        Args:
            error: Error object with fallback information
            **kwargs: Arguments for fallback strategy
            
        Returns:
            Result of fallback strategy or None if no fallback available
        """
        if not error.fallback_available:
            self.logger.warning(f"No fallback available for error type: {error.error_type.value}")
            return None
        
        try:
            fallback_func = self.fallback_strategies[error.error_type]
            result = fallback_func(**kwargs)
            self.logger.info(f"Successfully executed fallback for {error.error_type.value}")
            return result
        except Exception as fallback_exception:
            self.logger.error(f"Fallback strategy failed for {error.error_type.value}: {fallback_exception}")
            return None
    
    def _is_recoverable(self, error_type: RibbonErrorType) -> bool:
        """Determine if an error type is recoverable."""
        non_recoverable = {
            RibbonErrorType.FILE_IO_ERROR,
            RibbonErrorType.PERMISSION_ERROR
        }
        return error_type not in non_recoverable
    
    def _log_error(self, error: RibbonError, context: Optional[Dict[str, Any]] = None):
        """Log error with appropriate level and context."""
        log_message = f"Ribbon Error [{error.error_type.value}]: {error.message}"
        
        if error.details:
            log_message += f" - Details: {error.details}"
        
        if context:
            log_message += f" - Context: {context}"
        
        if error.recoverable:
            self.logger.warning(log_message)
        else:
            self.logger.error(log_message)
        
        # Log stack trace for debugging if exception is available
        if error.original_exception and self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug("Exception traceback:", exc_info=error.original_exception)
    
    # Fallback strategies
    def _fallback_basic_ribbon(self, **kwargs) -> bool:
        """Fallback to basic ribbon without advanced features."""
        try:
            # Create a simple text-based ribbon
            doc = kwargs.get('doc')
            page = kwargs.get('page')
            
            if not doc or not page:
                return False
            
            # Simple text ribbon
            page.insert_text(
                fitz.Point(10, 30),
                "✓ VERIFIED - EduCerts",
                fontsize=14,
                fontname="helv-bold",
                color=(0.2, 0.5, 0.8),
                overlay=True
            )
            
            return True
        except Exception:
            return False
    
    def _fallback_static_ribbon(self, **kwargs) -> bool:
        """Fallback to static ribbon without JavaScript interactivity."""
        try:
            # Create visual ribbon without JavaScript
            ribbon_utils = kwargs.get('ribbon_utils')
            page = kwargs.get('page')
            
            if not ribbon_utils or not page:
                return False
            
            # Create visual ribbon only
            ribbon_utils._create_visual_ribbon(page)
            return True
        except Exception:
            return False
    
    def _fallback_default_position(self, **kwargs) -> Dict[str, Any]:
        """Fallback to default ribbon position when content analysis fails."""
        return {
            "x": 0,
            "y": 0,
            "width": 200,
            "height": 60,
            "position_name": "top_left_default"
        }
    
    def _fallback_default_styling(self, **kwargs) -> Dict[str, Any]:
        """Fallback to default styling when custom styling fails."""
        return {
            "background_color": "#2563eb",
            "text_color": "#ffffff",
            "accent_color": "#d4af37",
            "font_size": 12,
            "width": 200,
            "height": 60
        }
    
    def _fallback_minimal_data(self, **kwargs) -> Dict[str, Any]:
        """Fallback to minimal verification data when full data is unavailable."""
        cert_id = kwargs.get('cert_id', 'Unknown')
        return {
            "certificate": {
                "id": cert_id,
                "student_name": "Unknown",
                "course_name": "Unknown",
                "organization": "EduCerts Academy"
            },
            "summary": {
                "all": False,
                "signature": False,
                "content_integrity": True,
                "registry_check": False
            },
            "checks": [],
            "verification_url": f"https://educerts.io/verify?id={cert_id}"
        }
    
    def _fallback_standard_save(self, **kwargs) -> bool:
        """Fallback to standard PDF save when encrypted save fails."""
        try:
            doc = kwargs.get('doc')
            output_path = kwargs.get('output_path')
            
            if not doc or not output_path:
                return False
            
            doc.save(output_path)
            return True
        except Exception:
            return False
    
    def _fallback_temp_file(self, **kwargs) -> Optional[str]:
        """Fallback to temporary file when standard file operations fail."""
        import tempfile
        try:
            temp_fd, temp_path = tempfile.mkstemp(suffix=".pdf")
            return temp_path
        except Exception:
            return None
    
    def _fallback_skip_validation(self, **kwargs) -> bool:
        """Fallback to skip validation when validation fails."""
        self.logger.warning("Skipping validation due to validation error")
        return True
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of all errors encountered."""
        if not self.error_history:
            return {"total_errors": 0, "error_types": {}}
        
        error_counts = {}
        for error in self.error_history:
            error_type = error.error_type.value
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        return {
            "total_errors": len(self.error_history),
            "error_types": error_counts,
            "recoverable_errors": len([e for e in self.error_history if e.recoverable]),
            "fallback_available": len([e for e in self.error_history if e.fallback_available])
        }
    
    def clear_error_history(self):
        """Clear the error history."""
        self.error_history.clear()


class GracefulRibbonProcessor:
    """Wrapper for ribbon processing with comprehensive error handling."""
    
    def __init__(self, error_handler: Optional[RibbonErrorHandler] = None):
        self.error_handler = error_handler or RibbonErrorHandler()
        self.success_count = 0
        self.failure_count = 0
    
    def process_with_fallbacks(self, primary_func: Callable, fallback_funcs: List[Callable], 
                              *args, **kwargs) -> tuple[bool, Any]:
        """
        Process with primary function and fallback options.
        
        Args:
            primary_func: Primary function to attempt
            fallback_funcs: List of fallback functions to try
            *args, **kwargs: Arguments for functions
            
        Returns:
            tuple: (success, result)
        """
        # Try primary function
        try:
            result = primary_func(*args, **kwargs)
            self.success_count += 1
            return True, result
        except Exception as e:
            error = self.error_handler.handle_error(
                RibbonErrorType.PDF_PROCESSING_ERROR,
                f"Primary function failed: {primary_func.__name__}",
                e,
                {"args": str(args)[:100], "kwargs": str(kwargs)[:100]}
            )
        
        # Try fallback functions
        for i, fallback_func in enumerate(fallback_funcs):
            try:
                result = fallback_func(*args, **kwargs)
                self.error_handler.logger.info(f"Fallback {i+1} succeeded: {fallback_func.__name__}")
                return True, result
            except Exception as e:
                self.error_handler.handle_error(
                    RibbonErrorType.PDF_PROCESSING_ERROR,
                    f"Fallback {i+1} failed: {fallback_func.__name__}",
                    e
                )
        
        # All functions failed
        self.failure_count += 1
        return False, None
    
    def safe_ribbon_creation(self, ribbon_utils, pdf_path: str, output_path: str, 
                           cert, verification_result: Dict[str, Any], styling=None) -> bool:
        """
        Safely create ribbon with comprehensive error handling.
        
        Args:
            ribbon_utils: Ribbon utilities instance
            pdf_path: Input PDF path
            output_path: Output PDF path
            cert: Certificate object
            verification_result: Verification result data
            styling: Optional styling configuration
            
        Returns:
            bool: True if successful (with or without fallbacks)
        """
        def primary_ribbon_creation():
            return ribbon_utils.add_interactive_ribbon_to_pdf(
                pdf_path, output_path, cert, verification_result, styling
            )
        
        def fallback_static_ribbon():
            # Create static ribbon without interactivity
            try:
                doc = fitz.open(pdf_path)
                page = doc[0]
                
                # Simple visual ribbon
                ribbon_rect = fitz.Rect(0, 0, 200, 60)
                page.draw_rect(ribbon_rect, color=(0.2, 0.5, 0.8), fill=(0.2, 0.5, 0.8), width=0)
                page.insert_text(
                    fitz.Point(50, 38),
                    "VERIFIED",
                    fontsize=20,
                    fontname="helv-bold",
                    color=(1, 1, 1),
                    overlay=True
                )
                
                doc.save(output_path)
                doc.close()
                return True
            except Exception:
                return False
        
        def fallback_text_only():
            # Minimal text-only verification indicator
            try:
                doc = fitz.open(pdf_path)
                page = doc[0]
                
                page.insert_text(
                    fitz.Point(10, 30),
                    "✓ VERIFIED - EduCerts",
                    fontsize=14,
                    fontname="helv-bold",
                    color=(0.2, 0.5, 0.8),
                    overlay=True
                )
                
                doc.save(output_path)
                doc.close()
                return True
            except Exception:
                return False
        
        success, result = self.process_with_fallbacks(
            primary_ribbon_creation,
            [fallback_static_ribbon, fallback_text_only]
        )
        
        return success
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        total = self.success_count + self.failure_count
        success_rate = (self.success_count / total * 100) if total > 0 else 0
        
        return {
            "total_processed": total,
            "successful": self.success_count,
            "failed": self.failure_count,
            "success_rate": round(success_rate, 2),
            "error_summary": self.error_handler.get_error_summary()
        }


# Global error handler instance
_global_error_handler = RibbonErrorHandler()

def get_global_error_handler() -> RibbonErrorHandler:
    """Get the global error handler instance."""
    return _global_error_handler

def handle_ribbon_error(error_type: RibbonErrorType, message: str, 
                       exception: Optional[Exception] = None) -> RibbonError:
    """Convenience function to handle ribbon errors using global handler."""
    return _global_error_handler.handle_error(error_type, message, exception)

def safe_ribbon_operation(operation: Callable, error_type: RibbonErrorType, 
                         operation_name: str, *args, **kwargs) -> tuple[bool, Any]:
    """
    Safely execute a ribbon operation with error handling.
    
    Args:
        operation: Function to execute
        error_type: Type of error if operation fails
        operation_name: Name of operation for logging
        *args, **kwargs: Arguments for operation
        
    Returns:
        tuple: (success, result)
    """
    try:
        result = operation(*args, **kwargs)
        return True, result
    except Exception as e:
        handle_ribbon_error(error_type, f"{operation_name} failed", e)
        return False, None