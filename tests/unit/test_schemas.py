"""
Unit tests for Pydantic schemas.
"""
import pytest
from pydantic import ValidationError

from blog_app.core.schemas import Task, Plan, EvidenceItem, RouterDecision


class TestTask:
    """Test Task schema."""
    
    def test_valid_task_creation(self):
        """Test creating a valid task."""
        task = Task(
            id=1,
            title="Test Task",
            goal="Test goal",
            bullets=["Point 1", "Point 2", "Point 3"],
            target_words=200
        )
        assert task.id == 1
        assert task.title == "Test Task"
        assert len(task.bullets) == 3
    
    def test_task_minimum_bullets(self):
        """Test task requires minimum 3 bullets."""
        with pytest.raises(ValidationError) as exc:
            Task(
                id=1,
                title="Test Task",
                goal="Test goal",
                bullets=["Only one"],  # Too few
                target_words=200
            )
        assert "at least 3 items" in str(exc.value).lower()
    
    def test_task_defaults(self):
        """Test task default values."""
        task = Task(
            id=1,
            title="Test Task",
            goal="Test goal",
            bullets=["1", "2", "3"],
            target_words=200
        )
        assert task.requires_research is False
        assert task.requires_citations is False
        assert task.requires_code is False
        assert task.tags == []


class TestPlan:
    """Test Plan schema."""
    
    def test_valid_plan_creation(self, sample_task):
        """Test creating a valid plan."""
        plan = Plan(
            blog_title="Test Blog",
            audience="developers",
            tone="technical",
            blog_kind="explainer",
            tasks=[sample_task]
        )
        assert plan.blog_title == "Test Blog"
        assert len(plan.tasks) == 1
    
    def test_plan_blog_kind_validation(self, sample_task):
        """Test blog_kind accepts only valid values."""
        valid_kinds = ["explainer", "tutorial", "news_roundup", "comparison", "system_design"]
        
        for kind in valid_kinds:
            plan = Plan(
                blog_title="Test",
                audience="dev",
                tone="tech",
                blog_kind=kind,
                tasks=[sample_task]
            )
            assert plan.blog_kind == kind


class TestEvidenceItem:
    """Test EvidenceItem schema."""
    
    def test_valid_evidence_creation(self):
        """Test creating valid evidence."""
        evidence = EvidenceItem(
            title="Test Article",
            url="https://example.com/article",
            published_at="2024-02-03",
            snippet="Test snippet",
            source="Example"
        )
        assert evidence.title == "Test Article"
        assert evidence.url == "https://example.com/article"
    
    def test_evidence_optional_fields(self):
        """Test evidence with minimal fields."""
        evidence = EvidenceItem(
            title="Test",
            url="https://example.com"
        )
        assert evidence.published_at is None
        assert evidence.snippet is None
        assert evidence.source is None


class TestRouterDecision:
    """Test RouterDecision schema."""
    
    def test_valid_router_decision(self):
        """Test valid router decision."""
        decision = RouterDecision(
            needs_research=True,
            mode="hybrid",
            reason="Needs current data",
            queries=["query1", "query2"]
        )
        assert decision.needs_research is True
        assert decision.mode == "hybrid"
        assert len(decision.queries) == 2
    
    def test_router_mode_validation(self):
        """Test mode accepts only valid values."""
        valid_modes = ["closed_book", "hybrid", "open_book"]
        
        for mode in valid_modes:
            decision = RouterDecision(
                needs_research=True,
                mode=mode,
                reason="Test"
            )
            assert decision.mode == mode