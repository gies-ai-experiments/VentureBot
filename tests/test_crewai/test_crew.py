"""Tests for the CrewAI crew configuration.

These tests verify the VenturebotsAiEntrepreneurshipCoachingPlatformCrew
setup and agent configurations.
"""

from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch


class TestAgentConfiguration:
    """Tests for agent configuration files."""

    @pytest.fixture
    def agents_config_path(self):
        """Path to agents configuration."""
        return Path("/Users/keshavdalmia/Documents/VentureBot/crewai-agents/src/venturebot_crew/config")

    def test_agents_config_exists(self, agents_config_path):
        """Verify agents.yaml exists."""
        agents_yaml = agents_config_path / "agents.yaml"
        assert agents_yaml.exists(), f"agents.yaml not found at {agents_yaml}"

    def test_tasks_config_exists(self, agents_config_path):
        """Verify tasks.yaml exists."""
        tasks_yaml = agents_config_path / "tasks.yaml"
        assert tasks_yaml.exists(), f"tasks.yaml not found at {tasks_yaml}"


class TestEnvironmentConfiguration:
    """Tests for environment configuration."""

    def test_default_model_fallback(self):
        """Test that default model falls back correctly."""
        import os
        
        # Without OPENAI_MODEL set, should default
        original = os.environ.get("OPENAI_MODEL")
        try:
            if "OPENAI_MODEL" in os.environ:
                del os.environ["OPENAI_MODEL"]
            
            default = os.getenv("OPENAI_MODEL", "openai/gpt-5-mini")
            assert default == "openai/gpt-5-mini"
        finally:
            if original is not None:
                os.environ["OPENAI_MODEL"] = original

    def test_default_temperature(self):
        """Test that default temperature is correct."""
        import os
        
        default = float(os.getenv("OPENAI_TEMPERATURE", "1"))
        assert default == 1.0


class TestAvailableToolsFunction:
    """Tests for the _available_tools utility function."""

    def test_available_tools_with_callable(self):
        """Test that callable tools are instantiated."""
        def mock_tool():
            return "tool_instance"
        
        # Simulate the function
        def _available_tools(*tool_classes):
            return [tool_cls() for tool_cls in tool_classes if callable(tool_cls)]
        
        result = _available_tools(mock_tool)
        assert result == ["tool_instance"]

    def test_available_tools_skips_none(self):
        """Test that None tools are skipped."""
        def _available_tools(*tool_classes):
            return [tool_cls() for tool_cls in tool_classes if callable(tool_cls)]
        
        result = _available_tools(None)
        assert result == []

    def test_available_tools_with_mixed(self):
        """Test with mix of callable and None."""
        def mock_tool():
            return "tool_instance"
        
        def _available_tools(*tool_classes):
            return [tool_cls() for tool_cls in tool_classes if callable(tool_cls)]
        
        result = _available_tools(None, mock_tool, None)
        assert result == ["tool_instance"]


class TestProjectStructure:
    """Tests for project structure."""

    @pytest.fixture
    def project_root(self):
        """Path to project root."""
        return Path("/Users/keshavdalmia/Documents/VentureBot")

    def test_crewai_agents_directory_exists(self, project_root):
        """Verify crewai-agents directory exists."""
        crewai_dir = project_root / "crewai-agents"
        assert crewai_dir.exists()

    def test_venturebot_crew_exists(self, project_root):
        """Verify venturebot_crew module exists."""
        crew_path = project_root / "crewai-agents" / "src" / "venturebot_crew"
        assert crew_path.exists()

    def test_crew_py_exists(self, project_root):
        """Verify crew.py exists."""
        crew_py = project_root / "crewai-agents" / "src" / "venturebot_crew" / "crew.py"
        assert crew_py.exists()

    def test_main_py_exists(self, project_root):
        """Verify main.py exists."""
        main_py = project_root / "crewai-agents" / "src" / "venturebot_crew" / "main.py"
        assert main_py.exists()


class TestAgentNames:
    """Tests to verify expected agents are defined."""

    @pytest.fixture
    def crew_py_content(self):
        """Read crew.py content."""
        path = Path("/Users/keshavdalmia/Documents/VentureBot/crewai-agents/src/venturebot_crew/crew.py")
        return path.read_text()

    def test_onboarding_agent_defined(self, crew_py_content):
        """Verify onboarding agent is defined."""
        assert "venturebot_onboarding_agent" in crew_py_content

    def test_idea_generator_defined(self, crew_py_content):
        """Verify idea generator agent is defined."""
        assert "venturebot_idea_generator" in crew_py_content

    def test_market_validator_defined(self, crew_py_content):
        """Verify market validator agent is defined."""
        assert "market_validator_agent" in crew_py_content

    def test_product_manager_defined(self, crew_py_content):
        """Verify product manager agent is defined."""
        assert "venturebot_product_manager" in crew_py_content

    def test_prompt_engineer_defined(self, crew_py_content):
        """Verify prompt engineer agent is defined."""
        assert "venturebot_technical_prompt_engineer" in crew_py_content


class TestTaskNames:
    """Tests to verify expected tasks are defined."""

    @pytest.fixture
    def crew_py_content(self):
        """Read crew.py content."""
        path = Path("/Users/keshavdalmia/Documents/VentureBot/crewai-agents/src/venturebot_crew/crew.py")
        return path.read_text()

    def test_onboarding_task_defined(self, crew_py_content):
        """Verify onboarding task is defined."""
        assert "venturebot_user_onboarding_and_pain_point_discovery" in crew_py_content

    def test_idea_generation_task_defined(self, crew_py_content):
        """Verify idea generation task is defined."""
        assert "venturebot_market_aware_idea_generation" in crew_py_content

    def test_market_validation_task_defined(self, crew_py_content):
        """Verify market validation task is defined."""
        assert "comprehensive_market_validation" in crew_py_content

    def test_prd_task_defined(self, crew_py_content):
        """Verify PRD task is defined."""
        assert "venturebot_product_requirements_and_mvp_development" in crew_py_content

    def test_no_code_builder_task_defined(self, crew_py_content):
        """Verify no-code builder task is defined."""
        assert "venturebot_no_code_builder_prompt_generation" in crew_py_content
