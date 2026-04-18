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

---

## TESTING REQUIREMENTS

These rules apply at the end of every phase and whenever new code is generated.
Do not consider a phase complete until all rules in this section pass.

---

### RULE T-1 — Write tests alongside code, not after

Every new class, function, or endpoint generated in a phase must have
corresponding tests written in the same session, before moving on.
Never defer tests to a cleanup task. If Copilot generates a class without
tests, immediately follow up with: "Now write the tests for that class."

---

### RULE T-2 — Spring Boot test requirements (ai-architect-api)

#### Unit tests
Location: src/test/java/com/aiarchitect/api/

Every service class must have a unit test class named {ClassName}Test.
Use Mockito for all dependencies. Do not start the Spring context for unit tests.
Annotate with @ExtendWith(MockitoExtension.class) only.

Classes that require unit tests:
- ChatService — mock ConversationService and AgentBridgeService
- ConversationService — mock ConversationRepository and MessageRepository
- AgentBridgeService — mock AgentHttpClient, test JSON parsing and error mapping
- JwtService (Phase 2+) — test token generation, extraction, and expiry
- AgentHttpClient — mock WebClient using MockWebServer from okhttp3

What to assert in each:
  ChatService:
    - streamChat() saves user message before calling agent
    - streamChat() saves assistant message in doOnComplete, not doOnNext
    - streamChat() creates new conversation when conversationId is null
    - streamChat() reuses existing conversation when conversationId is provided
    - streamChat() emits ERROR event when AgentBridgeService throws

  ConversationService:
    - resolveConversation() creates new conversation when id is null
    - resolveConversation() throws IllegalArgumentException for unknown id
    - getRecentMessages() returns at most the requested limit
    - saveMessage() persists role and content correctly

  AgentBridgeService:
    - Returns parsed AgentResponse for valid NDJSON line
    - Returns ERROR type AgentResponse for malformed JSON line
    - Propagates AgentCommunicationException wrapped in correct type

  JwtService:
    - generateToken() produces a non-blank string
    - extractUsername() returns the username used to generate the token
    - isTokenValid() returns false for an expired token
    - isTokenValid() returns false for a tampered token

#### Integration tests
Location: src/test/java/com/aiarchitect/api/

Use @SpringBootTest(webEnvironment = RANDOM_PORT) with a real
PostgreSQL test container (org.testcontainers:postgresql).
Add testcontainers to pom.xml in test scope if not already present:

  <dependency>
    <groupId>org.testcontainers</groupId>
    <artifactId>postgresql</artifactId>
    <scope>test</scope>
  </dependency>
  <dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-testcontainers</artifactId>
    <scope>test</scope>
  </dependency>

Classes that require integration tests:
- ChatControllerIntegrationTest
- SessionControllerIntegrationTest

What to assert in each:
  ChatControllerIntegrationTest:
    - POST /api/v1/chat/stream without token returns 401 (Phase 2+)
    - POST /api/v1/chat/stream with valid token and mocked agent
      returns content-type text/event-stream
    - POST /api/v1/chat/stream with invalid request body returns 400
      with validation error JSON
    - POST /api/v1/chat/stream persists conversation and message to DB

  SessionControllerIntegrationTest:
    - GET /api/v1/sessions/{id}/messages returns messages in order
    - GET /api/v1/sessions/{unknown-id}/messages returns 400

For integration tests, mock the AgentHttpClient using MockWebServer
so tests do not depend on the Python service being running.

---

### RULE T-3 — Python test requirements (ai-architect-agent)

#### Unit tests
Location: ai-architect-agent/tests/unit/

Use pytest with pytest-asyncio. All async test functions use
@pytest.mark.asyncio. Mock the LLM client using unittest.mock.AsyncMock.
Never make real LLM API calls in tests.

Files that require unit tests:

  tests/unit/test_llm_client.py
    - LLMClient.complete() retries on RateLimitError (mock tenacity)
    - LLMClient.complete() raises LLMCallException after max retries
    - LLMClient.complete() appends JSON instruction when response_format="json"
    - LLMClient.complete() logs token counts at DEBUG level

  tests/unit/test_prompt_loader.py
    - load_prompt() renders template variables correctly
    - load_prompt() raises FileNotFoundError for missing template
    - load_prompt() renders parsed_entities as valid JSON via tojson filter

  tests/unit/tools/test_requirement_parser.py
    - run() writes domain and system_type to context.parsed_entities
    - run() writes functional_requirements list to context.parsed_entities
    - run() raises ToolExecutionException when LLM returns invalid JSON
    - run() does not mutate other ArchitectureContext fields

  tests/unit/tools/test_challenge_engine.py
    - run() writes missing_requirements to context
    - run() writes clarifying_questions to context
    - run() trims clarifying_questions to 8 items when LLM returns more
    - run() logs a warning when trimming occurs
    - run() raises ToolExecutionException on invalid JSON response

  tests/unit/tools/test_scenario_modeler.py
    - run() writes exactly 3 scenarios to context
    - run() raises ToolExecutionException when fewer than 3 scenarios returned
    - run() validates tier values are exactly small, medium, large in order
    - run() does not mutate other ArchitectureContext fields

  tests/unit/test_pipeline_nodes.py
    - parse_node() calls RequirementParserTool.run() with the context
    - challenge_node() calls RequirementChallengeEngineTool.run()
    - scenarios_node() calls ScenarioModelerTool.run()
    - stub nodes return context unchanged
    - stub nodes do not raise exceptions

#### Integration tests
Location: ai-architect-agent/tests/integration/

  tests/integration/test_agent_endpoint.py
    - POST /agent/stream without X-Internal-Secret returns 401
    - POST /agent/stream with wrong secret returns 401
    - POST /agent/stream with valid secret and mocked LLM returns
      content-type application/x-ndjson
    - Response stream contains STAGE_START event for requirement_parsing
    - Response stream contains STAGE_COMPLETE event for each stage
    - Response stream ends with COMPLETE event
    - COMPLETE payload contains conversationId
    - If a tool raises ToolExecutionException, stream emits ERROR event
      and terminates cleanly

Use httpx.AsyncClient as the test HTTP client.
Mock LLMClient at the app.state level so no real API calls are made.

#### Fixture file
Create tests/conftest.py with:
- A pytest fixture named mock_llm that returns an AsyncMock of LLMClient
- A pytest fixture named sample_requirements that returns a multi-sentence
  requirements string suitable for testing all three tools
- A pytest fixture named base_context that returns an ArchitectureContext
  populated with sample_requirements

---

### RULE T-4 — Coverage requirements

#### Spring Boot
Add the JaCoCo plugin to pom.xml:

  <plugin>
    <groupId>org.jacoco</groupId>
    <artifactId>jacoco-maven-plugin</artifactId>
    <version>0.8.12</version>
    <executions>
      <execution>
        <goals><goal>prepare-agent</goal></goals>
      </execution>
      <execution>
        <id>report</id>
        <phase>verify</phase>
        <goals><goal>report</goal></goals>
      </execution>
      <execution>
        <id>check</id>
        <goals><goal>check</goal></goals>
        <configuration>
          <rules>
            <rule>
              <element>PACKAGE</element>
              <limits>
                <limit>
                  <counter>LINE</counter>
                  <value>COVEREDRATIO</value>
                  <minimum>0.80</minimum>
                </limit>
              </limits>
            </rule>
          </rules>
        </configuration>
      </execution>
    </executions>
    <configuration>
      <excludes>
        <exclude>com/aiarchitect/api/AiArchitectApplication.class</exclude>
        <exclude>com/aiarchitect/api/domain/model/**</exclude>
        <exclude>com/aiarchitect/api/dto/**</exclude>
        <exclude>com/aiarchitect/api/exception/AgentCommunicationException.class</exclude>
      </excludes>
    </configuration>
  </plugin>

Run coverage check with: mvn verify
Report is generated at: target/site/jacoco/index.html
The build fails if any non-excluded package falls below 80% line coverage.

#### Python
Add pytest-cov to pyproject.toml dev dependencies:

  [project.optional-dependencies]
  dev = [
      "pytest>=8.0",
      "pytest-asyncio>=0.23",
      "pytest-cov>=5.0",
      "httpx>=0.27.0",
  ]

Add a [tool.coverage.run] section to pyproject.toml:

  [tool.coverage.run]
  source = ["app"]
  omit = ["app/prompts/*", "*/conftest.py"]

  [tool.coverage.report]
  fail_under = 80
  show_missing = true
  exclude_lines = [
      "pragma: no cover",
      "if __name__ == .__main__.:",
      "raise NotImplementedError",
  ]

Run coverage check with:
  pytest --cov=app --cov-report=term-missing --cov-fail-under=80

The command exits with code 1 if coverage falls below 80%.
Always run this command at the end of every phase before declaring done.

---

### RULE T-5 — End-of-phase checklist

At the end of every phase, before declaring it complete, run all of
the following commands and confirm each one passes:

#### Spring Boot
  mvn test                         # all unit tests pass
  mvn verify                       # integration tests + coverage check pass
  mvn verify -Dfailsafe.skip=false # ensure integration tests are not skipped

#### Python
  pytest tests/unit/ -v                           # all unit tests pass
  pytest tests/integration/ -v                    # all integration tests pass
  pytest --cov=app --cov-report=term-missing \
         --cov-fail-under=80                      # coverage gate passes

If any command fails, fix the failures before moving to the next phase.
Do not move on with known failing tests. Do not skip tests by adding
@pytest.mark.skip or @Disabled without a comment explaining why and a
linked issue.

---

### RULE T-6 — What Copilot must never do with tests

1. Never generate tests that mock the class under test.
   The class under test must be a real instance; only its dependencies are mocked.

2. Never write tests that only assert no exception was thrown.
   Every test must assert something about the output or side effect.

3. Never use @SpringBootTest for tests that only need to test a single
   service class. Use @ExtendWith(MockitoExtension.class) instead.

4. Never generate tests with names like test1(), testMethod(), or
   shouldWork(). Test names must describe the behaviour being verified:
   e.g. saveMessage_persistsRoleAndContent(),
        run_trimsClarifyingQuestionsToEight()

5. Never add real API keys or secrets to test files or test resources.
   Use placeholder strings like "test-key" or environment variable stubs.

6. Never skip the coverage check step at the end of a phase.
   Coverage is a gate, not a suggestion.