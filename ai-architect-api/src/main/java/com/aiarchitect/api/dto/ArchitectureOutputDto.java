package com.aiarchitect.api.dto;

import lombok.Builder;
import lombok.Data;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

@Data @Builder
public class ArchitectureOutputDto {

    private UUID id;
    private UUID conversationId;
    private String style;
    private String domain;
    private String systemType;
    private int componentCount;
    private List<Object> components;
    private List<Object> interactions;
    private List<Object> characteristics;
    private List<Object> conflicts;
    private String componentDiagram;
    private String sequenceDiagram;
    private Instant createdAt;
}
