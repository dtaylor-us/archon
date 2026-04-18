package com.aiarchitect.api.controller;

import com.aiarchitect.api.dto.MessageDto;
import com.aiarchitect.api.service.ConversationService;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;
import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/sessions")
@RequiredArgsConstructor
public class SessionController {

    private final ConversationService conversationService;

    @GetMapping("/{id}/messages")
    public List<MessageDto> getMessages(
            @PathVariable UUID id,
            @AuthenticationPrincipal String userId) {
        return conversationService.getRecentMessages(id, 100);
    }
}
