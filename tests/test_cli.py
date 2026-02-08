"""Tests for CLI."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from llm_integration_starter.cli import cli


class TestCLI:
    """Tests for CLI commands."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    def test_cli_help(self, runner):
        """Test CLI help message."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "LLM Integration Starter Kit" in result.output

    def test_cli_version(self, runner):
        """Test CLI version command."""
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_chat_command(self, runner):
        """Test chat command."""
        result = runner.invoke(cli, ["chat", "Hello"])
        assert result.exit_code == 0
        assert "Mock response" in result.output

    def test_chat_command_with_provider(self, runner):
        """Test chat with specific provider."""
        result = runner.invoke(cli, ["chat", "--provider", "mock", "Hello"])
        assert result.exit_code == 0

    def test_compare_command(self, runner):
        """Test compare command."""
        result = runner.invoke(cli, ["compare", "--providers", "mock", "Hello"])
        assert result.exit_code == 0
        assert "Provider: mock" in result.output

    def test_benchmark_command(self, runner):
        """Test benchmark command."""
        result = runner.invoke(cli, ["benchmark", "--n-requests", "3", "Hello"])
        assert result.exit_code == 0
        assert "Successful requests" in result.output
        assert "Latency" in result.output

    def test_fallback_command(self, runner):
        """Test fallback command."""
        result = runner.invoke(cli, ["fallback", "--providers", "mock", "Hello"])
        assert result.exit_code == 0
        assert "Success!" in result.output
        assert "Successful provider: mock" in result.output

    def test_chat_command_with_invalid_provider(self, runner):
        """Test chat with invalid provider."""
        result = runner.invoke(cli, ["chat", "--provider", "invalid", "Hello"])
        assert result.exit_code != 0
