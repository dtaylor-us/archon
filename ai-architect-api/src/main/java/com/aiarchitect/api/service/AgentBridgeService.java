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

@Service @RequiredArgsConstructor @Slf4j
public class AgentBridgeService {

    private final AgentHttpClient agentHttpClient;
    private final ObjectMapper objectMapper;

    public Flux<AgentResponse> stream(AgentRequest request) {
        return agentHttpClient.stream(request)
                .map(this::parseLine)
                .onErrorMap(
                    e -> !(e instanceof AgentCommunicationException),
                    e -> new AgentCommunicationException(
                             "Agent stream failed", e));
    }

    private AgentResponse parseLine(String line) {
        try {
            return objectMapper.readValue(line, AgentResponse.class);
        } catch (JsonProcessingException e) {
            log.warn("Unparseable agent chunk: {}", line);
            AgentResponse err = new AgentResponse();
            err.setType(AgentResponse.EventType.ERROR);
            err.setContent("Parse error on agent response");
            return err;
        }
    }
}
