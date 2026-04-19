package com.aiarchitect.api.service;

import com.aiarchitect.api.domain.model.*;
import com.aiarchitect.api.dto.*;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Flux;

import java.util.Map;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.atomic.AtomicReference;

@Service @RequiredArgsConstructor @Slf4j
public class ChatService {

    private final ConversationService conversationService;
    private final AgentBridgeService agentBridgeService;
    private final ArchitectureOutputService architectureOutputService;
    private final GovernanceService governanceService;
    private final UsageService usageService;
    private final ObjectMapper objectMapper;

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
        AtomicReference<Map<String, Object>> structuredMap = new AtomicReference<>();
        AtomicReference<Map<String, Object>> completePayload = new AtomicReference<>();

        return agentBridgeService.stream(agentRequest)
                .doOnNext(chunk -> {
                    if (chunk.getType() == AgentResponse.EventType.CHUNK
                            && chunk.getContent() != null) {
                        buffer.get().append(chunk.getContent());
                    }
                    if (chunk.getType() == AgentResponse.EventType.COMPLETE
                            && chunk.getPayload() != null) {
                        try {
                            structuredOutput.set(
                                    objectMapper.writeValueAsString(
                                            chunk.getPayload()));
                            // Capture full COMPLETE payload for token_usage extraction
                            if (chunk.getPayload() instanceof Map<?, ?> payloadMap) {
                                @SuppressWarnings("unchecked")
                                Map<String, Object> pm = (Map<String, Object>) payloadMap;
                                completePayload.set(pm);
                                @SuppressWarnings("unchecked")
                                Map<String, Object> so = (Map<String, Object>)
                                        pm.get("structured_output");
                                if (so != null) {
                                    structuredMap.set(so);
                                }
                            }
                        } catch (JsonProcessingException e) {
                            log.warn("Failed to serialize structured output", e);
                        }
                    }
                })
                .doOnComplete(() -> {
                    // Schedule blocking JPA persistence off the reactive
                    // thread so the SSE completion signal propagates
                    // immediately and the HTTP connection closes.
                    CompletableFuture.runAsync(() -> {
                        try {
                            String text = buffer.get().toString();
                            if (!text.isBlank()) {
                                conversationService.saveMessage(
                                        conversation, MessageRole.ASSISTANT,
                                        text, structuredOutput.get());
                            }
                            // Persist architecture output if present
                            Map<String, Object> so = structuredMap.get();
                            if (so != null
                                    && so.containsKey("architecture_design")) {
                                architectureOutputService
                                        .saveFromStructuredOutput(
                                                conversation.getId(), so);
                            }
                            // Persist FMEA risks if present
                            if (so != null && so.containsKey("fmea_risks")) {
                                @SuppressWarnings("unchecked")
                                var fmeaRisks = (java.util.List<Map<String, Object>>)
                                        so.get("fmea_risks");
                                if (fmeaRisks != null && !fmeaRisks.isEmpty()) {
                                    governanceService.saveFmeaRisks(
                                            conversation.getId(), fmeaRisks);
                                }
                            }
                            // Persist governance report if present
                            if (so != null && so.containsKey("governance_score")) {
                                governanceService.saveGovernanceReport(
                                        conversation.getId(), so);
                            }
                            // Persist token usage if the agent reported it
                            // token_usage lives at the COMPLETE payload level,
                            // not inside structured_output.
                            Map<String, Object> cp = completePayload.get();
                            if (cp != null) {
                                persistTokenUsage(conversation.getId(), cp);
                            }

                            log.info("Stream complete conversation={}",
                                     conversation.getId());
                        } catch (Exception e) {
                            log.warn("Post-stream persistence failed for "
                                     + "conversation={}",
                                     conversation.getId(), e);
                        }
                    });
                });
    }

    /**
     * Extract and persist token_usage from the COMPLETE payload.
     * Best-effort — never throws.
     */
    @SuppressWarnings("unchecked")
    private void persistTokenUsage(UUID conversationId,
                                   Map<String, Object> payload) {
        try {
            Object tu = payload.get("token_usage");
            if (tu instanceof Map<?, ?> tokenUsageMap) {
                usageService.saveFromPayload(
                        conversationId,
                        (Map<String, Object>) tokenUsageMap);
            }
        } catch (Exception e) {
            log.warn("Failed to persist token usage for conversation={}",
                     conversationId, e);
        }
    }
}
