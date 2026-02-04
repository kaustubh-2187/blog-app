"""
Unit tests for file service utilities.
"""
import pytest
from blog_app.services.file_service import _safe_slug


class TestSafeSlug:
    """Test _safe_slug function."""
    
    def test_basic_slug(self):
        """Test basic slug generation."""
        assert _safe_slug("Hello World") == "hello_world"
    
    def test_special_characters(self):
        """Test slug with special characters."""
        assert _safe_slug("Hello, World!") == "hello_world"
    
    def test_multiple_spaces(self):
        """Test slug with multiple spaces."""
        assert _safe_slug("Hello    World") == "hello_world"
    
    def test_numbers(self):
        """Test slug with numbers."""
        assert _safe_slug("Python 3.11 Guide") == "python_311_guide"
    
    def test_empty_string(self):
        """Test slug with empty string."""
        assert _safe_slug("") == "blog"
    
    def test_only_special_chars(self):
        """Test slug with only special characters."""
        assert _safe_slug("!!!@@@###") == "blog"