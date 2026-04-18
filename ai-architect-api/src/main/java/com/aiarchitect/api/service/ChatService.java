package com.aiarchitect.api.service;

import com.aiarchitect.api.domain.model.*;
import com.aiarchitect.api.dto.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Flux;
import java.util.concurrent.atomic.AtomicReference;

@Service @RequiredArgsConstructor @Slf4j
public class ChatService {

    private final ConversationService conversationService;
    private final AgentBridgeService agentBridgeService;

    public Flux<AgentResponse> streamChat(ChatRequest request, String userId) {

        Conversation conversation = conversationService.resolveConversation(
                request.getConversationId(), userId, request.getMessage());

        conversationService.saveMessage(
                conversation, MessageRole.USER, request.getMessage(), null);

        AgentRequest agentRequest = AgentRequest.builder()
                .conversationId(conversation.getId().toString())
                .userMessage(request.getMessage())
                .mode(request.getMode().name())
                .history(conversationService.getRecentMessages(
                             conversation.getId(), 20))
                .build();

        AtomicReference<StringBuilder> buffer =
                new AtomicReference<>(new StringBuilder());
        AtomicReference<String> structuredOutput = new AtomicReference<>();

        return agentBridgeService.stream(agentRequest)
                .doOnNext(chunk -> {
                    if (chunk.getType() == AgentResponse.EventType.CHUNK
                            && chunk.getContent() != null) {
                        buffer.get().append(chunk.getContent());
                    }
                    if (chunk.getType() == AgentResponse.EventType.COMPLETE
                            && chunk.getPayload() != null) {
                        structuredOutput.set(chunk.getPayload().toString());
                    }
                })
                .doOnComplete(() -> {
                    String text = buffer.get().toString();
                    if (!text.isBlank()) {
                        conversationService.saveMessage(
                                conversation, MessageRole.ASSISTANT,
                                text, structuredOutput.get());
                    }
                    log.info("Stream complete conversation={}",
                             conversation.getId());
                });
    }
}
