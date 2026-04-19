package com.aiarchitect.api.service;

import com.aiarchitect.api.domain.model.*;
import com.aiarchitect.api.domain.repository.*;
import com.aiarchitect.api.dto.MessageDto;
import com.aiarchitect.api.dto.SessionDto;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;
import java.util.List;
import java.util.UUID;

@Service @RequiredArgsConstructor
public class ConversationService {

    private final ConversationRepository conversationRepo;
    private final MessageRepository messageRepo;

    @Transactional
    public Conversation resolveConversation(UUID conversationId,
                                            String userId,
                                            String firstMessage) {
        if (conversationId != null) {
            return conversationRepo.findByIdAndUserId(conversationId, userId)
                    .orElseThrow(() -> new ResponseStatusException(
                            HttpStatus.NOT_FOUND, "Conversation not found"));
        }
        String title = firstMessage.length() > 60
                ? firstMessage.substring(0, 60) + "..."
                : firstMessage;
        return conversationRepo.save(Conversation.builder()
                .userId(userId).title(title).build());
    }

    @Transactional
    public Message saveMessage(Conversation conversation,
                               MessageRole role,
                               String content,
                               String structuredOutput) {
        return messageRepo.save(Message.builder()
                .conversation(conversation)
                .role(role)
                .content(content)
                .structuredOutput(structuredOutput)
                .build());
    }

    @Transactional(readOnly = true)
    public List<MessageDto> getRecentMessages(UUID conversationId, int limit) {
        // Query fetches newest-first (DESC) to honour the limit, then we
        // reverse so the caller receives messages in chronological order.
        var recent = messageRepo.findRecentByConversationId(
                        conversationId, PageRequest.of(0, limit))
                .stream()
                .map(m -> MessageDto.builder()
                        .id(m.getId())
                        .role(m.getRole())
                        .content(m.getContent())
                        .createdAt(m.getCreatedAt())
                        .build())
                .toList();
        return recent.reversed();
    }

    @Transactional(readOnly = true)
    public List<MessageDto> getRecentMessages(UUID conversationId,
                                             String userId,
                                             int limit) {
        // Ensure the authenticated user owns this conversation.
        conversationRepo.findByIdAndUserId(conversationId, userId)
                .orElseThrow(() -> new ResponseStatusException(
                        HttpStatus.NOT_FOUND, "Conversation not found"));
        return getRecentMessages(conversationId, limit);
    }

    @Transactional(readOnly = true)
    public List<SessionDto> listSessions(String userId) {
        return conversationRepo.findByUserIdOrderByCreatedAtDesc(userId)
                .stream()
                .map(c -> SessionDto.builder()
                        .id(c.getId())
                        .title(c.getTitle())
                        .status(c.getStatus())
                        .createdAt(c.getCreatedAt())
                        .updatedAt(c.getUpdatedAt())
                        .build())
                .toList();
    }
}
