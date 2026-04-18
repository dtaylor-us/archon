# Architecture Definition Language — AI Architect Assistant
# Version: 1.0
# Owner: Architecture Team
# Last updated: 2025
#
# This file is the authoritative architecture governance document.
# It defines structural rules, service boundaries, and invariants
# that ALL code in this repository must conform to.
#
# Copilot and all AI coding assistants must treat this file as
# a hard constraint. When generating code, verify every suggestion
# against the rules below before presenting it.

---

## SYSTEM DEFINITION

DEFINE system AIArchitectAssistant {
  RESPONSIBILITY: "AI-powered architecture governance and design assistant"
  SERVICES: [ai-architect-api, ai-architect-agent]
  DATABASES: [PostgreSQL, Qdrant]
  COMMUNICATION: [HTTP/SSE between client and api, HTTP/NDJSON between api and agent]
  DEPLOYMENT: Docker Compose (local), AKS (production)
}


---

## SERVICE: ai-architect-api (Spring Boot)

DEFINE service ai-architect-api {
  LANGUAGE: Java 21
  FRAMEWORK: Spring Boot 3.3.4
  RESPONSIBILITY: "API gateway — auth, session management, SSE streaming, agent bridge"
  OWNS: [Conversation, Message, ConversationStatus, MessageRole]
  DOES_NOT_OWN: [ArchitectureContext, pipeline logic, LLM calls, tool execution]
  EXPOSES: [POST /api/v1/chat/stream, GET /api/v1/sessions/{id}/messages]
  CALLS: [ai-architect-agent via AgentHttpClient]
  ROOT_PACKAGE: com.aiarchitect.api
}

ASSERT ai-architect-api {
  MUST use Flyway for all schema changes
    — ddl-auto MUST be "validate", never "create", "update", or "create-drop"

  MUST NOT contain LLM API calls
    — no openai, azure-openai, langchain, or llm client dependencies in pom.xml

  MUST NOT contain pipeline logic
    — no stage orchestration, no tool invocation, no ArchitectureContext manipulation

  MUST use WebClient (not RestTemplate) for all HTTP calls to ai-architect-agent
    — RestTemplate is blocking and will deadlock the SSE response thread

  MUST NOT enable open-in-view
    — spring.jpa.open-in-view MUST be false in application.yml

  MUST stream agent responses as Server-Sent Events
    — ChatController.streamChat() MUST return Flux<AgentResponse>
    — endpoint MUST produce MediaType.TEXT_EVENT_STREAM_VALUE

  MUST persist every user message BEFORE forwarding to agent
    — ConversationService.saveMessage() called with MessageRole.USER before
      AgentBridgeService.stream() is invoked

  MUST persist assistant response AFTER stream completes
    — doOnComplete() callback saves accumulated text, not doOnNext()

  MUST validate all incoming requests
    — @Valid annotation required on all @RequestBody parameters
    — @NotBlank and @Size constraints required on ChatRequest.message

  MUST authenticate service-to-service calls with X-Internal-Secret header
    — AgentHttpClient MUST set this header on every request to ai-architect-agent

  MUST NOT expose internal exceptions to API consumers
    — AgentCommunicationException MUST be caught and mapped to a safe error response

  MUST limit conversation history sent to agent
    — getRecentMessages() MUST be called with limit <= 20 before building AgentRequest
}

REQUIRE ai-architect-api {
  IF a new JPA entity is added
    THEN a corresponding Flyway migration MUST be created in db/migration/
    AND the migration filename MUST follow pattern V{n}__{description}.sql

  IF a new REST endpoint is added
    THEN it MUST be covered by an integration test using @SpringBootTest
    AND it MUST be documented in this file under EXPOSES

  IF a new external dependency is added to pom.xml
    THEN its purpose MUST be documented in a comment in pom.xml
    AND it MUST NOT duplicate functionality already provided by an existing dependency

  IF open-in-view is set to anything other than false
    THEN the build pipeline MUST fail
}


---

## SERVICE: ai-architect-agent (Python / FastAPI)

DEFINE service ai-architect-agent {
  LANGUAGE: Python 3.11
  FRAMEWORK: FastAPI + LangGraph (Phase 2+)
  RESPONSIBILITY: "LLM orchestration — pipeline execution, tool dispatch, streaming"
  OWNS: [ArchitectureContext, pipeline stages, tool registry, prompt templates]
  DOES_NOT_OWN: [Conversation, Message, session state, JWT auth]
  EXPOSES: [POST /agent/stream, GET /health]
  ROOT_MODULE: app
}

ASSERT ai-architect-agent {
  MUST validate X-Internal-Secret on every request to POST /agent/stream
    — return HTTP 401 if header is absent or does not match INTERNAL_SECRET env var

  MUST stream responses as NDJSON
    — one JSON object per line, each line terminated with \n
    — media_type MUST be "application/x-ndjson"

  MUST use ArchitectureContext as the single pipeline state object
    — no stage may pass data to another stage except through ArchitectureContext
    — no global variables or module-level state for pipeline data

  MUST use Pydantic models for all inputs and outputs
    — no untyped dict passing across function boundaries in production code
    — raw dicts allowed only in stub/test code

  MUST emit STAGE_START before any work in a stage begins
    AND STAGE_COMPLETE after the stage finishes
    — the client depends on these events for progress display

  MUST emit COMPLETE as the final event in every successful pipeline run
    — payload MUST include conversationId and stages_executed

  MUST emit ERROR event type on unhandled exceptions
    — never let an unhandled exception silently terminate the stream
    — always yield a final ERROR chunk before raising or returning

  MUST NOT call Spring Boot or any ai-architect-api endpoint
    — data flows api → agent only, never agent → api

  MUST NOT store secrets in code
    — INTERNAL_SECRET and OPENAI_API_KEY MUST be read from environment variables
    — no hardcoded keys, tokens, or passwords anywhere in app/

  MUST keep prompt templates in app/prompts/ as .j2 (Jinja2) files
    — no raw prompt strings embedded in tool class bodies (Phase 2+)
    — tool classes MAY contain prompt strings only in Phase 1 stub code
}

REQUIRE ai-architect-agent {
  IF a new pipeline stage is added
    THEN it MUST be added as a LangGraph node (Phase 2+)
    AND it MUST read from and write to ArchitectureContext only
    AND it MUST emit STAGE_START and STAGE_COMPLETE events
    AND it MUST be listed in this file under the pipeline section below

  IF a new tool is added
    THEN it MUST be registered in the tool registry (Phase 2+)
    AND it MUST have a Pydantic input model and output model
    AND it MUST be independently testable with no LLM dependency using mocked LLM calls

  IF ArchitectureContext gains a new field
    THEN the field MUST have a default value so existing runs are not broken
    AND the field MUST be documented with an inline comment stating which stage populates it

  IF a prompt template is changed
    THEN the change MUST be tested against the evaluation set (3 representative inputs)
    BEFORE being merged
}


---

## PIPELINE DEFINITION

DEFINE pipeline ArchitectAssistantPipeline {
  ENTRY_POINT: POST /agent/stream
  STATE_OBJECT: ArchitectureContext
  MAX_ITERATIONS: 2
  PARALLELISM: stages 9 and 10 run concurrently via asyncio.gather()

  STAGES: [
    1  requirement_parsing       — RequirementParser tool
    2  requirement_challenge     — RequirementChallengeEngine tool
    3  scenario_modeling         — ScenarioModeler tool
    4  characteristic_inference  — CharacteristicReasoningEngine tool
    5  conflict_analysis         — CharacteristicConflictAnalyzer tool
    6  architecture_generation   — ArchitectureGenerator tool
    7  trade_off_analysis        — TradeOffEngine tool
    8  adl_generation            — ADLGeneratorV2 tool
    9  weakness_analysis         — WeaknessAnalyzer tool   [parallel with 10]
    10 fmea_analysis             — FMEAPlus tool           [parallel with 9]
    11 architecture_review       — ReviewAgent (separate LangGraph graph)
  ]
}

ASSERT ArchitectAssistantPipeline {
  MUST execute stages in order 1 → 8, then 9+10 in parallel, then 11
    — stage N MUST NOT begin until stage N-1 has written its output to ArchitectureContext

  MUST NOT pass data between stages via function arguments
    — all inter-stage data flows through ArchitectureContext fields only

  MUST trigger re-iteration if ReviewAgent sets should_reiterate = true
    AND ArchitectureContext.iteration < 2
    — if iteration >= 2, proceed to COMPLETE regardless of governance score

  ReviewAgent MUST receive a read-only snapshot of ArchitectureContext
    — ReviewAgent MUST NOT mutate the forward-pass ArchitectureContext
    — ReviewAgent writes to a separate ReviewContext object only
}


---

## DATA LAYER

DEFINE database PostgreSQL {
  OWNS: [conversations table, messages table]
  USED_BY: [ai-architect-api only]
  SCHEMA_MANAGEMENT: Flyway
}

DEFINE database Qdrant {
  OWNS: [architecture pattern embeddings, past design vectors]
  USED_BY: [ai-architect-agent only]
  PURPOSE: "Semantic memory — retrieve similar past architectures at inference time"
}

ASSERT data-layer {
  MUST NOT allow ai-architect-agent to connect to PostgreSQL directly
    — agent has no PostgreSQL connection string in its environment

  MUST NOT allow ai-architect-api to connect to Qdrant directly
    — api has no Qdrant connection string in its environment

  MUST store all structured agent outputs (ADL, trade-offs, weaknesses) as JSONB
    in messages.structured_output
    — do not create separate tables for each output type in Phase 1-4

  MUST use UUID primary keys on all tables
    — no integer or serial primary keys
}


---

## SECURITY

ASSERT security {
  MUST use X-Internal-Secret header for all api → agent calls
    — secret MUST come from environment variable, never hardcoded
    — agent MUST return HTTP 401 if header is missing or incorrect

  MUST NOT log secret values
    — INTERNAL_SECRET, JWT_SECRET, OPENAI_API_KEY MUST never appear in log output

  MUST disable CSRF protection on the API layer
    — this is a stateless API consumed by non-browser clients
    — CSRF protection is inappropriate and must remain disabled

  MUST run application containers as non-root users
    — Dockerfile MUST create and switch to a non-root user before CMD/ENTRYPOINT

  MUST NOT store API keys in .env files committed to version control
    — .env MUST be in .gitignore
    — only .env.example (with empty values) is committed
}

REQUIRE security {
  IF JWT authentication is added (Phase 2)
    THEN the DEV_USER constant in ChatController MUST be removed
    AND all endpoints under /api/v1/ MUST require a valid JWT
    AND SecurityConfig MUST be updated to reflect this

  IF a new secret or credential is introduced
    THEN it MUST be added to .env.example with an empty value
    AND documented in this file under the security section
}


---

## COMMUNICATION CONTRACT

DEFINE contract api-to-agent {
  PROTOCOL: HTTP POST
  PATH: /agent/stream
  REQUEST_FORMAT: JSON body — AgentRequest schema
  RESPONSE_FORMAT: NDJSON stream — one AgentResponseChunk per line
  AUTH: X-Internal-Secret header
  TIMEOUT: 120 seconds
}

DEFINE contract client-to-api {
  PROTOCOL: HTTP POST with SSE response
  PATH: /api/v1/chat/stream
  REQUEST_FORMAT: JSON body — ChatRequest schema
  RESPONSE_FORMAT: text/event-stream — one AgentResponse per SSE event
  AUTH: none in Phase 1, JWT Bearer in Phase 2+
}

ASSERT communication-contract {
  MUST NOT change the AgentResponseChunk event type enum values
    — EventType values (CHUNK, STAGE_START, STAGE_COMPLETE, TOOL_CALL,
      COMPLETE, ERROR) are part of the client contract
    — adding new values is allowed, removing or renaming existing values is not

  MUST NOT change the /agent/stream request field names without a migration plan
    — conversationId, userMessage, mode, history, context are stable field names

  MUST use application/x-ndjson as media type for api → agent responses
  MUST use text/event-stream as media type for client → api responses
}


---

## OBSERVABILITY

ASSERT observability {
  MUST include conversation_id on every log line during request processing
    — use MDC (Java) or structlog context vars (Python)

  MUST instrument every tool call as a child OpenTelemetry span (Phase 2+)
    — span name pattern: tool.{tool_name}
    — span MUST include conversation_id and stage_name as attributes

  MUST NOT log message content at INFO level or above
    — user message content is sensitive and MUST only appear at DEBUG level
    — never log LLM responses at INFO or above

  MUST expose /actuator/health (Spring Boot) and /health (FastAPI)
    — both MUST return HTTP 200 with a status field when the service is healthy
}


---

## WHAT COPILOT MUST ALWAYS DO

When generating code for this project, Copilot MUST:

1. Read this file before generating any code.

2. Place new Java classes in the correct package under com.aiarchitect.api.
   Never create classes outside the root package.

3. Never write raw SQL outside of Flyway migration files.
   JPA repositories handle all queries; JPQL is allowed in @Query annotations.

4. Never add spring.jpa.hibernate.ddl-auto values other than "validate".

5. Never use RestTemplate. Always use WebClient for HTTP calls.

6. Never call the OpenAI or Azure OpenAI API from ai-architect-api.
   All LLM calls belong exclusively in ai-architect-agent.

7. Never add pipeline logic to ChatService or AgentBridgeService.
   Those classes bridge HTTP only — they contain no domain logic.

8. Always add a default value when adding a field to ArchitectureContext.
   New fields must never break existing pipeline runs.

9. Always emit STAGE_START before a stage begins and STAGE_COMPLETE
   after it finishes. Never skip these events.

10. Never hardcode secrets. Always read from environment variables.

## WHAT COPILOT MUST NEVER DO

1. Never set ddl-auto to anything other than "validate".
2. Never import RestTemplate in any class.
3. Never write LLM calls in the Spring Boot service.
4. Never mutate ArchitectureContext from the ReviewAgent.
5. Never remove or rename existing AgentResponse.EventType enum values.
6. Never log secrets, API keys, or user message content at INFO or above.
7. Never create a new table for structured agent output — use messages.structured_output JSONB.
8. Never skip the X-Internal-Secret validation in the agent endpoint.
9. Never set open-in-view to true.
10. Never commit a .env file containing real credentials.