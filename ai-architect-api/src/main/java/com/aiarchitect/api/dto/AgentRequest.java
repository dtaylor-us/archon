package com.aiarchitect.api.dto;

import lombok.Builder;
import lombok.Data;
import java.util.List;
import java.util.Map;

@Data @Builder
public class AgentRequest {
    private String conversationId;
    private String userMessage;
    private String mode;
    private List<MessageDto> history;
    private Map<String, Object> context;
}
