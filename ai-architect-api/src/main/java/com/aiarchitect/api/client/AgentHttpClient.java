package com.aiarchitect.api.client;

import com.aiarchitect.api.config.AgentClientConfig;
import com.aiarchitect.api.dto.AgentRequest;
import com.aiarchitect.api.exception.AgentCommunicationException;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Flux;
import java.time.Duration;

/**
 * HTTP client for communicating with the AI Agent service.
 * Handles streaming responses from the agent using Spring WebClient.
 */
@Component
@Slf4j
public class AgentHttpClient {

    private final WebClient webClient;
    private final AgentClientConfig config;

    /**
     * Initializes the HTTP client with configuration and builds the WebClient.
     *
     * @param config the agent client configuration
     */
    public AgentHttpClient(AgentClientConfig config) {
        this.config = config;
        this.webClient = WebClient.builder()
                .baseUrl(config.getBaseUrl())
                .defaultHeader(HttpHeaders.CONTENT_TYPE,
                               MediaType.APPLICATION_JSON_VALUE)
                .defaultHeader("X-Internal-Secret", config.getInternalSecret())
                .codecs(c -> c.defaultCodecs()
                              .maxInMemorySize(10 * 1024 * 1024))
                .build();
    }

    /**
     * Streams responses from the agent service.
     *
     * @param request the agent request
     * @return a Flux of response strings
     */
    public Flux<String> stream(AgentRequest request) {
        return webClient.post()
                .uri("/agent/stream")
                .bodyValue(request)
                .retrieve()
                .onStatus(HttpStatusCode::isError, response ->
                        response.bodyToMono(String.class).map(body ->
                                new AgentCommunicationException(
                                    "Agent error " + response.statusCode()
                                    + ": " + body)))
                .bodyToFlux(String.class)
                .timeout(Duration.ofSeconds(config.getTimeoutSeconds()))
                .filter(line -> !line.isBlank())
                .doOnError(e -> log.error("Agent stream error", e));
    }
}
