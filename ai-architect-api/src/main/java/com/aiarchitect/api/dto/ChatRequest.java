package com.aiarchitect.api.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Data;
import java.util.UUID;

@Data
public class ChatRequest {
    @NotBlank
    @Size(max = 32000)
    private String message;

    private UUID conversationId;
    private PipelineMode mode = PipelineMode.AUTO;

    public enum PipelineMode {
        AUTO, ARCHITECTURE_ONLY, TRADE_OFF_ONLY, ADL_ONLY, REVIEW_ONLY
    }
}
