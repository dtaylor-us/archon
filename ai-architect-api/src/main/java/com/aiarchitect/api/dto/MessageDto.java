package com.aiarchitect.api.dto;

import com.aiarchitect.api.domain.model.MessageRole;
import lombok.Builder;
import lombok.Data;
import java.time.Instant;
import java.util.UUID;

@Data @Builder
public class MessageDto {
    private UUID id;
    private MessageRole role;
    private String content;
    private Instant createdAt;
}
