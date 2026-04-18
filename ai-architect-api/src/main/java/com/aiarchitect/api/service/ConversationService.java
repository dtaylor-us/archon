package com.aiarchitect.api.service;

import com.aiarchitect.api.domain.model.*;
import com.aiarchitect.api.domain.repository.*;
import com.aiarchitect.api.dto.MessageDto;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
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
                    .orElseThrow(() -> new IllegalArgumentException(
                                     "Conversation not found"));
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
        return messageRepo.findRecentByConversationId(
                        conversationId, PageRequest.of(0, limit))
                .stream()
                .map(m -> MessageDto.builder()
                        .id(m.getId())
                        .role(m.getRole())
                        .content(m.getContent())
                        .createdAt(m.getCreatedAt())
                        .build())
                .toList();
    }
}
