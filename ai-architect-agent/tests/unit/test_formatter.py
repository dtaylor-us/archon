"""Tests for pipeline response formatter."""

import pytest
from app.models import ArchitectureContext
from app.pipeline.formatter import format_response, _title, _format_item


class TestFormatResponse:
    """Tests for the main format_response function."""

    def test_empty_context_returns_header_only(self):
        ctx = ArchitectureContext(raw_requirements="test")
        result = format_response(ctx)
        assert result.startswith("# Architecture Analysis Report")
        # Should have no section headers beyond the main title
        assert "## " not in result

    def test_parsed_entities_included(self):
        ctx = ArchitectureContext(
            raw_requirements="test",
            parsed_entities={
                "functional_requirements": ["Auth", "Payments"],
                "system_name": "PaymentGateway",
            },
        )
        result = format_response(ctx)
        assert "## Parsed Requirements" in result
        assert "Auth" in result
        assert "Payments" in result
        assert "PaymentGateway" in result

    def test_challenges_section_shows_all_subsections(self):
        ctx = ArchitectureContext(
            raw_requirements="test",
            missing_requirements=[{"description": "No SLA defined"}],
            ambiguities=[{"description": "Unclear scaling needs"}],
            hidden_assumptions=[{"description": "Assumes single region"}],
            clarifying_questions=[{"description": "What is target RPS?"}],
        )
        result = format_response(ctx)
        assert "## Requirement Challenges" in result
        assert "### Missing Requirements" in result
        assert "No SLA defined" in result
        assert "### Ambiguities" in result
        assert "Unclear scaling needs" in result
        assert "### Hidden Assumptions" in result
        assert "Assumes single region" in result
        assert "### Clarifying Questions" in result
        assert "What is target RPS?" in result

    def test_scenarios_with_named_items(self):
        ctx = ArchitectureContext(
            raw_requirements="test",
            scenarios=[
                {"name": "Happy Path", "stimulus": "User pays", "response": "OK"},
                {"name": "Failure", "stimulus": "Payment fails"},
            ],
        )
        result = format_response(ctx)
        assert "## Scenarios" in result
        assert "### Happy Path" in result
        assert "### Failure" in result
        assert "User pays" in result

    def test_architecture_design_nested(self):
        ctx = ArchitectureContext(
            raw_requirements="test",
            architecture_design={
                "style": "Microservices",
                "components": ["API Gateway", "Payment Service"],
            },
        )
        result = format_response(ctx)
        assert "## Architecture Design" in result
        assert "Microservices" in result
        assert "API Gateway" in result

    def test_governance_score_included(self):
        ctx = ArchitectureContext(
            raw_requirements="test",
            governance_score=85,
        )
        result = format_response(ctx)
        assert "**Governance Score**: 85/100" in result

    def test_empty_fields_are_omitted(self):
        """Only populated fields should produce sections."""
        ctx = ArchitectureContext(
            raw_requirements="test",
            trade_offs=[{"description": "Latency vs consistency"}],
        )
        result = format_response(ctx)
        assert "## Trade-off Analysis" in result
        assert "Latency vs consistency" in result
        # Empty sections should not appear
        assert "## Parsed Requirements" not in result
        assert "## Scenarios" not in result
        assert "## Architecture Design" not in result

    def test_all_analysis_sections(self):
        ctx = ArchitectureContext(
            raw_requirements="test",
            characteristics=[{"description": "High availability"}],
            characteristic_conflicts=[{"description": "Availability vs cost"}],
            adl_rules=[{"description": "Use async messaging"}],
            weaknesses=[{"description": "Single point of failure"}],
            fmea_risks=[{"description": "Database outage", "severity": "high"}],
            review_findings={"overall": "Needs improvement"},
        )
        result = format_response(ctx)
        assert "## Quality Characteristics" in result
        assert "## Characteristic Conflicts" in result
        assert "## Architecture Decision Log" in result
        assert "## Weakness Analysis" in result
        assert "## FMEA Risk Analysis" in result
        assert "## Architecture Review" in result


class TestTitle:
    """Tests for the _title helper."""

    def test_snake_case(self):
        assert _title("functional_requirements") == "Functional Requirements"

    def test_camel_case(self):
        assert _title("hiddenAssumptions") == "Hidden Assumptions"

    def test_single_word(self):
        assert _title("name") == "Name"


class TestFormatItem:
    """Tests for the _format_item helper."""

    def test_string_item(self):
        assert _format_item("hello") == "hello"

    def test_dict_with_description(self):
        result = _format_item({"description": "My item", "severity": "high"})
        assert "My item" in result
        assert "high" in result

    def test_dict_without_description(self):
        result = _format_item({"key": "val", "other": "data"})
        assert "val" in result
        assert "data" in result

    def test_dict_with_name(self):
        result = _format_item({"name": "Widget"})
        assert result == "Widget"
