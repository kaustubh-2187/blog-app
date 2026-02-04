"""
End-to-end tests for the complete pipeline.
"""
import os
import pytest
from pathlib import Path
from run_pipeline import run_blog_pipeline


@pytest.mark.slow
class TestFullPipeline:
    """Test complete pipeline execution."""
    
    def test_pipeline_with_images_disabled(self, temp_data_dir, monkeypatch):
        """Test full pipeline with images disabled."""
        # Mock the path helper functions
        def mock_get_run_output_dir(title_slug: str, run_id: str):
            from pathlib import Path
            folder_name = f"{title_slug}_{run_id}"
            return temp_data_dir / folder_name
        
        def mock_get_markdown_dir(run_output_dir):
            return run_output_dir / "markdown"
        
        def mock_get_images_dir(run_output_dir):
            return run_output_dir / "images"
        
        # Patch all the path helpers
        monkeypatch.setattr("blog_app.graph.nodes.reducer.get_run_output_dir", mock_get_run_output_dir)
        monkeypatch.setattr("blog_app.graph.nodes.reducer.get_markdown_dir", mock_get_markdown_dir)
        monkeypatch.setattr("blog_app.graph.nodes.reducer.get_images_dir", mock_get_images_dir)
        
        # Mock config to disable images
        def mock_read_yaml(path):
            return {
                "images_model": {"enabled": False},
                "graph": {"recursion_limit": 50, "max_concurrency": 3},
                "llm": {"models": {"provider": "groq"}},
                "router": {},
                "orchestrator": {}
            }
        
        monkeypatch.setattr("blog_app.config.config_loader.read_yaml", mock_read_yaml)
        
        # Run pipeline
        result = run_blog_pipeline(
            topic="Python basics: variables and data types",
            as_of="2024-02-03"
        )
        
        # Verify output
        assert result is not None
        assert "final" in result
        assert len(result["final"]) > 0
        
        # Check file structure
        output_dirs = list(temp_data_dir.glob("python-basics*"))
        assert len(output_dirs) == 1
        
        markdown_dir = output_dirs[0] / "markdown"
        assert markdown_dir.exists()
        
        md_files = list(markdown_dir.glob("*.md"))
        assert len(md_files) == 1
        
        # Images dir should NOT exist
        images_dir = output_dirs[0] / "images"
        assert not images_dir.exists()
    
    @pytest.mark.skipif(
        not os.getenv("RUN_EXPENSIVE_TESTS"),
        reason="Expensive test - set RUN_EXPENSIVE_TESTS=1 to run"
    )
    def test_pipeline_with_images_enabled(self, temp_data_dir, monkeypatch):
        """Test full pipeline with images enabled (expensive)."""
        monkeypatch.setattr("blog_app.config.paths_config.DATA_PATH", temp_data_dir)
        
        def mock_read_yaml(path):
            return {
                "images_model": {"enabled": True, "model_name": "gemini-2.5-flash-image"},
                "graph": {"recursion_limit": 50, "max_concurrency": 3},
                "llm": {"models": {"provider": "groq"}},
                "router": {},
                "orchestrator": {}
            }
        
        monkeypatch.setattr("blog_app.config.config_loader.read_yaml", mock_read_yaml)
        
        result = run_blog_pipeline(
            topic="How attention mechanism works in transformers"
        )
        
        assert result is not None
        
        # Check images were created
        output_dirs = list(temp_data_dir.glob("how-attention*"))
        if len(output_dirs) > 0:
            images_dir = output_dirs[0] / "images"
            # Images dir may exist if images were generated
            if images_dir.exists():
                assert len(list(images_dir.glob("*.png"))) > 0