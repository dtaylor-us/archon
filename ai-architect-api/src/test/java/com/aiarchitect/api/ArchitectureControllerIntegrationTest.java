package com.aiarchitect.api;

import com.aiarchitect.api.domain.model.*;
import com.aiarchitect.api.domain.repository.ArchitectureOutputRepository;
import com.aiarchitect.api.domain.repository.ConversationRepository;
import com.aiarchitect.api.domain.repository.MessageRepository;
import com.aiarchitect.api.security.JwtService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.annotation.Import;
import org.springframework.test.web.reactive.server.WebTestClient;

import java.util.UUID;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@Import(TestcontainersConfig.class)
class ArchitectureControllerIntegrationTest {

    @Autowired private WebTestClient webTestClient;
    @Autowired private JwtService jwtService;
    @Autowired private ConversationRepository conversationRepo;
    @Autowired private MessageRepository messageRepo;
    @Autowired private ArchitectureOutputRepository architectureOutputRepo;

    private String validToken;

    @BeforeEach
    void setUp() {
        architectureOutputRepo.deleteAll();
        messageRepo.deleteAll();
        conversationRepo.deleteAll();
        validToken = jwtService.generateToken("test@example.com");
    }

    @Test
    void getArchitecture_returnsOutputWhenPresent() {
        Conversation conv = conversationRepo.save(Conversation.builder()
                .userId("test@example.com").title("test conv").build());

        architectureOutputRepo.save(ArchitectureOutput.builder()
                .conversationId(conv.getId())
                .style("microservices")
                .domain("fintech")
                .systemType("payment platform")
                .componentCount(2)
                .components("[{\"name\":\"Gateway\"},{\"name\":\"FraudEngine\"}]")
                .interactions("[{\"from\":\"Gateway\",\"to\":\"FraudEngine\"}]")
                .characteristics("[{\"name\":\"scalability\"}]")
                .conflicts("[]")
                .componentDiagram("graph TD\nA-->B")
                .sequenceDiagram("sequenceDiagram\nA->>B: call")
                .build());

        webTestClient.get()
                .uri("/api/v1/sessions/{id}/architecture", conv.getId())
                .header("Authorization", "Bearer " + validToken)
                .exchange()
                .expectStatus().isOk()
                .expectBody()
                .jsonPath("$.style").isEqualTo("microservices")
                .jsonPath("$.domain").isEqualTo("fintech")
                .jsonPath("$.componentCount").isEqualTo(2)
                .jsonPath("$.componentDiagram").isNotEmpty();
    }

    @Test
    void getArchitecture_returns404WhenMissing() {
        Conversation conv = conversationRepo.save(Conversation.builder()
                .userId("test@example.com").title("test conv").build());

        webTestClient.get()
                .uri("/api/v1/sessions/{id}/architecture", conv.getId())
                .header("Authorization", "Bearer " + validToken)
                .exchange()
                .expectStatus().isNotFound();
    }

    @Test
    void getArchitecture_returns401WithoutToken() {
        webTestClient.get()
                .uri("/api/v1/sessions/{id}/architecture", UUID.randomUUID())
                .exchange()
                .expectStatus().isUnauthorized();
    }

    @Test
    void getDiagram_returnsDiagramsWhenPresent() {
        Conversation conv = conversationRepo.save(Conversation.builder()
                .userId("test@example.com").title("test conv").build());

        architectureOutputRepo.save(ArchitectureOutput.builder()
                .conversationId(conv.getId())
                .style("microservices")
                .componentCount(1)
                .componentDiagram("graph TD\nA-->B")
                .sequenceDiagram("sequenceDiagram\nA->>B: call")
                .build());

        webTestClient.get()
                .uri("/api/v1/sessions/{id}/diagram", conv.getId())
                .header("Authorization", "Bearer " + validToken)
                .exchange()
                .expectStatus().isOk()
                .expectBody()
                .jsonPath("$.componentDiagram").isEqualTo("graph TD\nA-->B")
                .jsonPath("$.sequenceDiagram").isEqualTo("sequenceDiagram\nA->>B: call");
    }

    @Test
    void getDiagram_returns404WhenMissing() {
        Conversation conv = conversationRepo.save(Conversation.builder()
                .userId("test@example.com").title("test conv").build());

        webTestClient.get()
                .uri("/api/v1/sessions/{id}/diagram", conv.getId())
                .header("Authorization", "Bearer " + validToken)
                .exchange()
                .expectStatus().isNotFound();
    }

    @Test
    void getDiagram_returns401WithoutToken() {
        webTestClient.get()
                .uri("/api/v1/sessions/{id}/diagram", UUID.randomUUID())
                .exchange()
                .expectStatus().isUnauthorized();
    }
}
