package com.aiarchitect.api.controller;

import com.aiarchitect.api.dto.MessageDto;
import com.aiarchitect.api.service.ConversationService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/sessions")
@RequiredArgsConstructor
public class SessionController {

    private final ConversationService conversationService;
    private static final String DEV_USER = "dev-user";

    @GetMapping("/{id}/messages")
    public List<MessageDto> getMessages(@PathVariable UUID id) {
        return conversationService.getRecentMessages(id, 100);
    }
}
