package com.aiarchitect.api.controller;

import com.aiarchitect.api.dto.*;
import com.aiarchitect.api.service.ChatService;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.io.IOException;

@RestController
@RequestMapping("/api/v1/chat")
@RequiredArgsConstructor @Slf4j
public class ChatController {

    private final ChatService chatService;
    private final ObjectMapper objectMapper;

    @PostMapping(value = "/stream",
                 produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter streamChat(
            @RequestBody @Valid ChatRequest request,
            @AuthenticationPrincipal String userId) {
        log.info("Chat stream request conversation={} mode={} user={}",
                request.getConversationId(), request.getMode(), userId);

        SseEmitter emitter = new SseEmitter(180_000L);

        chatService.streamChat(request, userId).subscribe(
                response -> {
                    try {
                        emitter.send(SseEmitter.event()
                                .data(objectMapper.writeValueAsString(response),
                                      MediaType.APPLICATION_JSON));
                    } catch (IOException e) {
                        emitter.completeWithError(e);
                    }
                },
                emitter::completeWithError,
                emitter::complete
        );

        return emitter;
    }
}
