"""
Integration tests for reducer nodes.
"""
import pytest
from pathlib import Path

from blog_app.graph.nodes.reducer import ReducerNode


class TestReducerMergeContent:
    """Test merge_content node."""
    
    def test_merge_sections(self, sample_plan):
        """Test merging worker sections."""
        state = {
            "plan": sample_plan,
            "sections": [
                (1, "## Section 1\nContent 1"),
                (2, "## Section 2\nContent 2"),
                (3, "## Section 3\nContent 3")
            ]
        }
        
        result = ReducerNode.merge_content(state)
        
        assert "merged_md" in result
        assert "Section 1" in result["merged_md"]
        assert "Section 2" in result["merged_md"]
        assert sample_plan.blog_title in result["merged_md"]


class TestReducerDecideImages:
    """Test decide_images node."""
    
    def test_images_disabled(self, sample_state, monkeypatch):
        """Test image decision when disabled in config."""
        # Mock config to disable images
        def mock_read_yaml(path):
            return {"images_model": {"enabled": False}}
        
        monkeypatch.setattr("blog_app.graph.nodes.reducer.read_yaml", mock_read_yaml)
        
        result = ReducerNode.decide_images(sample_state)
        
        assert "image_specs" in result
        assert result["image_specs"] == []
        assert "md_with_placeholders" in result


class TestReducerGenerateAndPlaceImages:
    """Test generate_and_place_images node."""
    
    def test_no_images_saves_markdown(self, sample_state, temp_data_dir, monkeypatch):
        """Test markdown saving when no images requested."""
        # Mock the helper functions to use temp_data_dir
        def mock_get_run_output_dir(title_slug: str, run_id: str):
            from pathlib import Path
            folder_name = f"{title_slug}_{run_id}"
            return temp_data_dir / folder_name
        
        def mock_get_markdown_dir(run_output_dir):
            return run_output_dir / "markdown"
        
        monkeypatch.setattr("blog_app.graph.nodes.reducer.get_run_output_dir", mock_get_run_output_dir)
        monkeypatch.setattr("blog_app.graph.nodes.reducer.get_markdown_dir", mock_get_markdown_dir)
        
        sample_state["merged_md"] = "# Test Blog\n\nContent here"
        sample_state["image_specs"] = []
        sample_state["run_id"] = "test123"
        
        result = ReducerNode.generate_and_place_images(sample_state)
        
        assert "final" in result
        
        # Check file was created
        expected_dir = temp_data_dir / "test-blog_test123" / "markdown"
        assert expected_dir.exists()
        
        md_files = list(expected_dir.glob("*.md"))
        assert len(md_files) == 1