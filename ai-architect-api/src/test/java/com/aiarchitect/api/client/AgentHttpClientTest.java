package com.aiarchitect.api.client;

import com.aiarchitect.api.config.AgentClientConfig;
import com.aiarchitect.api.dto.AgentRequest;
import com.aiarchitect.api.exception.AgentCommunicationException;
import okhttp3.mockwebserver.MockResponse;
import okhttp3.mockwebserver.MockWebServer;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import reactor.test.StepVerifier;

import java.io.IOException;

import static org.junit.jupiter.api.Assertions.*;

class AgentHttpClientTest {

    private MockWebServer mockServer;
    private AgentHttpClient agentHttpClient;

    @BeforeEach
    void setUp() throws IOException {
        mockServer = new MockWebServer();
        mockServer.start();

        AgentClientConfig config = new AgentClientConfig();
        config.setBaseUrl(mockServer.url("/").toString());
        config.setInternalSecret("test-secret");
        config.setTimeoutSeconds(5);
        agentHttpClient = new AgentHttpClient(config);
    }

    @AfterEach
    void tearDown() throws IOException {
        mockServer.shutdown();
    }

    @Test
    void stream_returnsNdjsonLinesForValidResponse() {
        String body = "{\"type\":\"CHUNK\",\"content\":\"hello\"}\n"
                    + "{\"type\":\"COMPLETE\",\"conversationId\":\"c1\"}\n";
        mockServer.enqueue(new MockResponse()
                .setHeader("Content-Type", "application/x-ndjson")
                .setBody(body));

        AgentRequest request = AgentRequest.builder()
                .conversationId("c1").userMessage("hi").build();

        StepVerifier.create(agentHttpClient.stream(request))
                .assertNext(line -> assertTrue(line.contains("CHUNK")))
                .assertNext(line -> assertTrue(line.contains("COMPLETE")))
                .verifyComplete();
    }

    @Test
    void stream_emitsErrorForServerError() {
        mockServer.enqueue(new MockResponse()
                .setResponseCode(500)
                .setBody("Internal Server Error"));

        AgentRequest request = AgentRequest.builder()
                .conversationId("c1").userMessage("hi").build();

        StepVerifier.create(agentHttpClient.stream(request))
                .expectErrorMatches(e ->
                        e instanceof AgentCommunicationException
                        && e.getMessage().contains("Agent error"))
                .verify();
    }

    @Test
    void stream_filtersBlankLines() {
        String body = "{\"type\":\"CHUNK\",\"content\":\"data\"}\n\n\n";
        mockServer.enqueue(new MockResponse()
                .setHeader("Content-Type", "application/x-ndjson")
                .setBody(body));

        AgentRequest request = AgentRequest.builder()
                .conversationId("c1").userMessage("hi").build();

        StepVerifier.create(agentHttpClient.stream(request))
                .assertNext(line -> assertTrue(line.contains("CHUNK")))
                .verifyComplete();
    }

    @Test
    void stream_sendsInternalSecretHeader() throws Exception {
        mockServer.enqueue(new MockResponse()
                .setHeader("Content-Type", "application/x-ndjson")
                .setBody("{\"type\":\"COMPLETE\"}\n"));

        AgentRequest request = AgentRequest.builder()
                .conversationId("c1").userMessage("hi").build();

        StepVerifier.create(agentHttpClient.stream(request)).expectNextCount(1)
                .verifyComplete();

        var recordedRequest = mockServer.takeRequest();
        assertEquals("test-secret", recordedRequest.getHeader("X-Internal-Secret"));
        assertEquals("/agent/stream", recordedRequest.getPath());
    }
}
