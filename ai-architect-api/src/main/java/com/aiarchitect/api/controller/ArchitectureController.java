package com.aiarchitect.api.controller;

import com.aiarchitect.api.dto.ArchitectureOutputDto;
import com.aiarchitect.api.service.ArchitectureOutputService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/sessions")
@RequiredArgsConstructor
public class ArchitectureController {

    private final ArchitectureOutputService architectureOutputService;

    /**
     * GET /api/v1/sessions/{id}/architecture
     * Returns the latest architecture output for the given conversation.
     */
    @GetMapping("/{id}/architecture")
    public ResponseEntity<ArchitectureOutputDto> getArchitecture(
            @PathVariable UUID id,
            @AuthenticationPrincipal String userId) {
        return architectureOutputService.getLatest(id)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    /**
     * GET /api/v1/sessions/{id}/diagram
     * Returns only the Mermaid diagrams for the given conversation.
     */
    @GetMapping("/{id}/diagram")
    public ResponseEntity<Map<String, String>> getDiagram(
            @PathVariable UUID id,
            @AuthenticationPrincipal String userId) {
        return architectureOutputService.getLatest(id)
                .map(dto -> ResponseEntity.ok(Map.of(
                        "componentDiagram",
                        dto.getComponentDiagram() != null
                                ? dto.getComponentDiagram() : "",
                        "sequenceDiagram",
                        dto.getSequenceDiagram() != null
                                ? dto.getSequenceDiagram() : ""
                )))
                .orElse(ResponseEntity.notFound().build());
    }
}
