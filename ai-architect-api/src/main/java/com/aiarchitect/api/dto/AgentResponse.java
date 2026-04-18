package com.aiarchitect.api.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.Data;
import java.util.Map;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class AgentResponse {
    public enum EventType {
        CHUNK, STAGE_START, STAGE_COMPLETE, TOOL_CALL, COMPLETE, ERROR
    }
    private EventType type;
    private String content;
    private String stage;
    private String toolName;
    private Object payload;
    private String conversationId;
    private Map<String, Object> metadata;
}
