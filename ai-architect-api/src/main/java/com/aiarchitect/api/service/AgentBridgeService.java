package com.aiarchitect.api.service;

import com.aiarchitect.api.client.AgentHttpClient;
import com.aiarchitect.api.dto.AgentRequest;
import com.aiarchitect.api.dto.AgentResponse;
import com.aiarchitect.api.exception.AgentCommunicationException;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Flux;

/**
 * Service that bridges communication with the Agent API.
 * Handles streaming responses and JSON parsing with error handling.
 */
@Service @RequiredArgsConstructor @Slf4j
public class AgentBridgeService {

    private final AgentHttpClient agentHttpClient;
    private final ObjectMapper objectMapper;

    /**
     * Streams agent responses as a Flux of parsed AgentResponse objects.
     * 
     * @param request the agent request to send
     * @return a Flux of parsed responses
     */
    public Flux<AgentResponse> stream(AgentRequest request) {
        return agentHttpClient.stream(request)
                // Parse each line into an AgentResponse
                .map(this::parseLine)
                .filter(r -> r != null)
                // Convert non-AgentCommunicationException errors to AgentCommunicationException
                .onErrorMap(
                    e -> !(e instanceof AgentCommunicationException),
                    e -> new AgentCommunicationException(
                             "Agent stream failed", e));
    }

    /**
     * Parses a JSON line into an AgentResponse object.
     * Returns an error response if parsing fails.
     * 
     * @param line the JSON string to parse
     * @return parsed AgentResponse or error response on failure
     */
    private AgentResponse parseLine(String line) {
        if (line != null && line.startsWith(":")) {
            // Keepalive comment line from the agent. Not JSON, intentionally ignored.
            return null;
        }
        try {
            return objectMapper.readValue(line, AgentResponse.class);
        } catch (JsonProcessingException e) {
            // Log unparseable chunks and return error response
            log.warn("Unparseable agent chunk: {}", line);
            AgentResponse err = new AgentResponse();
            err.setType(AgentResponse.EventType.ERROR);
            err.setContent("Parse error on agent response");
            return err;
        }
    }
}
