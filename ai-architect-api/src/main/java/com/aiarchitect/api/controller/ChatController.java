package com.aiarchitect.api.controller;

import com.aiarchitect.api.dto.*;
import com.aiarchitect.api.service.ChatService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Flux;

@RestController
@RequestMapping("/api/v1/chat")
@RequiredArgsConstructor @Slf4j
public class ChatController {

    private final ChatService chatService;
    private static final String DEV_USER = "dev-user";

    @PostMapping(value = "/stream",
                 produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public Flux<AgentResponse> streamChat(
            @RequestBody @Valid ChatRequest request) {
        log.info("Chat stream request conversation={} mode={}",
                request.getConversationId(), request.getMode());
        return chatService.streamChat(request, DEV_USER);
    }
}
