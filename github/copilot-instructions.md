# Copilot instructions for AI Architect Assistant

Before generating any code in this repository, read ARCHITECTURE.md at the
workspace root. That file is the authoritative architecture governance document.

Every code suggestion must conform to the rules in ARCHITECTURE.md.
If a suggestion would violate any ASSERT or REQUIRE rule, do not make it.
Instead, explain which rule it would violate and suggest a compliant alternative.

Key rules to check on every generation:
- ddl-auto must always be "validate" — never create, update, or create-drop
- Never use RestTemplate — always WebClient
- Never put LLM calls in ai-architect-api
- Never set open-in-view to true
- Never hardcode secrets
- Always add default values to new ArchitectureContext fields
- Always emit STAGE_START and STAGE_COMPLETE events in every pipeline stage