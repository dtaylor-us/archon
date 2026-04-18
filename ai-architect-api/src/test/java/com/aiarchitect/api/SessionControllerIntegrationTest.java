package com.aiarchitect.api;

import com.aiarchitect.api.domain.model.*;
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
class SessionControllerIntegrationTest {

    @Autowired private WebTestClient webTestClient;
    @Autowired private JwtService jwtService;
    @Autowired private ConversationRepository conversationRepo;
    @Autowired private MessageRepository messageRepo;

    private String validToken;

    @BeforeEach
    void setUp() {
        messageRepo.deleteAll();
        conversationRepo.deleteAll();
        validToken = jwtService.generateToken("test@example.com");
    }

    @Test
    void getMessages_returnsMessagesInOrder() {
        Conversation conv = conversationRepo.save(Conversation.builder()
                .userId("test@example.com").title("test conv").build());

        messageRepo.save(Message.builder()
                .conversation(conv).role(MessageRole.USER)
                .content("first message").build());
        messageRepo.save(Message.builder()
                .conversation(conv).role(MessageRole.ASSISTANT)
                .content("second message").build());

        webTestClient.get()
                .uri("/api/v1/sessions/{id}/messages", conv.getId())
                .header("Authorization", "Bearer " + validToken)
                .exchange()
                .expectStatus().isOk()
                .expectBody()
                .jsonPath("$.length()").isEqualTo(2)
                .jsonPath("$[0].content").isEqualTo("second message")
                .jsonPath("$[1].content").isEqualTo("first message");
    }

    @Test
    void getMessages_returnsEmptyForUnknownId() {
        UUID unknownId = UUID.randomUUID();

        webTestClient.get()
                .uri("/api/v1/sessions/{id}/messages", unknownId)
                .header("Authorization", "Bearer " + validToken)
                .exchange()
                .expectStatus().isOk()
                .expectBody()
                .jsonPath("$.length()").isEqualTo(0);
    }

    @Test
    void getMessages_returns401WithoutToken() {
        webTestClient.get()
                .uri("/api/v1/sessions/{id}/messages", UUID.randomUUID())
                .exchange()
                .expectStatus().isUnauthorized();
    }
}
