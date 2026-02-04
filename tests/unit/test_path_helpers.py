"""
Unit tests for path configuration helpers.
"""
import pytest
from pathlib import Path

from blog_app.config.paths_config import (
    get_run_output_dir,
    get_markdown_dir,
    get_images_dir
)


class TestPathHelpers:
    """Test path helper functions."""
    
    def test_run_output_dir(self):
        """Test run output directory generation."""
        result = get_run_output_dir("test-blog", "abc123")
        assert result == Path("data/test-blog_abc123")
    
    def test_markdown_dir(self):
        """Test markdown directory generation."""
        run_dir = Path("data/test-blog_abc123")
        result = get_markdown_dir(run_dir)
        assert result == Path("data/test-blog_abc123/markdown")
    
    def test_images_dir(self):
        """Test images directory generation."""
        run_dir = Path("data/test-blog_abc123")
        result = get_images_dir(run_dir)
        assert result == Path("data/test-blog_abc123/images")