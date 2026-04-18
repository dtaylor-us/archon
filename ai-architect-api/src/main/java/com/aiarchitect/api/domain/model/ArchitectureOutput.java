package com.aiarchitect.api.domain.model;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "architecture_outputs")
@Data @Builder @NoArgsConstructor @AllArgsConstructor
@EqualsAndHashCode(onlyExplicitlyIncluded = true)
public class ArchitectureOutput {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @EqualsAndHashCode.Include
    private UUID id;

    @Column(name = "conversation_id", nullable = false)
    private UUID conversationId;

    private String style;
    private String domain;

    @Column(name = "system_type")
    private String systemType;

    @Column(name = "component_count", nullable = false)
    @Builder.Default
    private int componentCount = 0;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(columnDefinition = "jsonb")
    private String components;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(columnDefinition = "jsonb")
    private String interactions;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(columnDefinition = "jsonb")
    private String characteristics;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(columnDefinition = "jsonb")
    private String conflicts;

    @Column(name = "component_diagram", columnDefinition = "TEXT")
    private String componentDiagram;

    @Column(name = "sequence_diagram", columnDefinition = "TEXT")
    private String sequenceDiagram;

    @CreationTimestamp
    private Instant createdAt;
}
