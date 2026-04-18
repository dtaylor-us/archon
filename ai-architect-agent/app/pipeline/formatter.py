"""Format ArchitectureContext into a human-readable Markdown response."""

from __future__ import annotations

from app.models import ArchitectureContext


def format_response(ctx: ArchitectureContext) -> str:
    """Convert the pipeline context into a readable architecture report.

    Sections are only included when the corresponding context field is populated.
    """
    sections: list[str] = []

    sections.append("# Architecture Analysis Report\n")

    # --- Parsed Requirements ---
    if ctx.parsed_entities:
        sections.append("## Parsed Requirements\n")
        _fmt = ctx.parsed_entities
        if isinstance(_fmt, dict):
            for key, value in _fmt.items():
                if isinstance(value, list):
                    sections.append(f"### {_title(key)}\n")
                    for item in value:
                        sections.append(f"- {_format_item(item)}")
                elif isinstance(value, dict):
                    sections.append(f"### {_title(key)}\n")
                    for k, v in value.items():
                        sections.append(f"- **{_title(k)}**: {v}")
                else:
                    sections.append(f"- **{_title(key)}**: {value}")
        sections.append("")

    # --- Requirement Challenges ---
    _has_challenges = (
        ctx.missing_requirements
        or ctx.ambiguities
        or ctx.hidden_assumptions
        or ctx.clarifying_questions
    )
    if _has_challenges:
        sections.append("## Requirement Challenges\n")

        if ctx.missing_requirements:
            sections.append("### Missing Requirements\n")
            for item in ctx.missing_requirements:
                sections.append(f"- {_format_item(item)}")
            sections.append("")

        if ctx.ambiguities:
            sections.append("### Ambiguities\n")
            for item in ctx.ambiguities:
                sections.append(f"- {_format_item(item)}")
            sections.append("")

        if ctx.hidden_assumptions:
            sections.append("### Hidden Assumptions\n")
            for item in ctx.hidden_assumptions:
                sections.append(f"- {_format_item(item)}")
            sections.append("")

        if ctx.clarifying_questions:
            sections.append("### Clarifying Questions\n")
            for item in ctx.clarifying_questions:
                sections.append(f"- {_format_item(item)}")
            sections.append("")

    # --- Scenarios ---
    if ctx.scenarios:
        sections.append("## Scenarios\n")
        for i, scenario in enumerate(ctx.scenarios, 1):
            if isinstance(scenario, dict):
                name = scenario.get("name", scenario.get("title", f"Scenario {i}"))
                sections.append(f"### {name}\n")
                for k, v in scenario.items():
                    if k not in ("name", "title"):
                        sections.append(f"- **{_title(k)}**: {v}")
            else:
                sections.append(f"- {scenario}")
        sections.append("")

    # --- Quality Characteristics ---
    if ctx.characteristics:
        sections.append("## Quality Characteristics\n")
        for char in ctx.characteristics:
            sections.append(f"- {_format_item(char)}")
        sections.append("")

    # --- Characteristic Conflicts ---
    if ctx.characteristic_conflicts:
        sections.append("## Characteristic Conflicts\n")
        for conflict in ctx.characteristic_conflicts:
            sections.append(f"- {_format_item(conflict)}")
        sections.append("")

    # --- Architecture Design ---
    if ctx.architecture_design:
        sections.append("## Architecture Design\n")
        _fmt_nested(ctx.architecture_design, sections, depth=0)
        sections.append("")

    # --- Trade-offs ---
    if ctx.trade_offs:
        sections.append("## Trade-off Analysis\n")
        for trade_off in ctx.trade_offs:
            sections.append(f"- {_format_item(trade_off)}")
        sections.append("")

    # --- ADL Rules ---
    if ctx.adl_rules:
        sections.append("## Architecture Decision Log\n")
        for rule in ctx.adl_rules:
            sections.append(f"- {_format_item(rule)}")
        sections.append("")

    # --- Weaknesses ---
    if ctx.weaknesses:
        sections.append("## Weakness Analysis\n")
        for weakness in ctx.weaknesses:
            sections.append(f"- {_format_item(weakness)}")
        sections.append("")

    # --- FMEA Risks ---
    if ctx.fmea_risks:
        sections.append("## FMEA Risk Analysis\n")
        for risk in ctx.fmea_risks:
            sections.append(f"- {_format_item(risk)}")
        sections.append("")

    # --- Review Findings ---
    if ctx.review_findings:
        sections.append("## Architecture Review\n")
        _fmt_nested(ctx.review_findings, sections, depth=0)
        sections.append("")

    # --- Governance Score ---
    if ctx.governance_score is not None:
        sections.append(f"**Governance Score**: {ctx.governance_score}/100\n")

    return "\n".join(sections).strip() + "\n"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _title(key: str) -> str:
    """Convert snake_case or camelCase key to Title Case."""
    # Handle camelCase
    import re
    spaced = re.sub(r"([a-z])([A-Z])", r"\1 \2", key)
    return spaced.replace("_", " ").title()


def _format_item(item: object) -> str:
    """Format a single list item (dict, str, or other) for Markdown output."""
    if isinstance(item, dict):
        # Try to find a primary field for the bullet
        primary = item.get("description") or item.get("name") or item.get("title")
        if primary:
            extras = {k: v for k, v in item.items()
                      if k not in ("description", "name", "title") and v}
            if extras:
                parts = ", ".join(f"{_title(k)}: {v}" for k, v in extras.items())
                return f"{primary} ({parts})"
            return str(primary)
        # Fallback: key=value list
        return ", ".join(f"{_title(k)}: {v}" for k, v in item.items())
    return str(item)


def _fmt_nested(data: dict, sections: list[str], depth: int) -> None:
    """Recursively format nested dicts for Markdown."""
    prefix = "  " * depth
    for key, value in data.items():
        if isinstance(value, dict):
            sections.append(f"{prefix}- **{_title(key)}**:")
            _fmt_nested(value, sections, depth + 1)
        elif isinstance(value, list):
            sections.append(f"{prefix}- **{_title(key)}**:")
            for item in value:
                if isinstance(item, dict):
                    sections.append(f"{prefix}  - {_format_item(item)}")
                else:
                    sections.append(f"{prefix}  - {item}")
        else:
            sections.append(f"{prefix}- **{_title(key)}**: {value}")
