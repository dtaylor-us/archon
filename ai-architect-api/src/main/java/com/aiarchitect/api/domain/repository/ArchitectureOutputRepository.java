package com.aiarchitect.api.domain.repository;

import com.aiarchitect.api.domain.model.ArchitectureOutput;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;
import java.util.UUID;

public interface ArchitectureOutputRepository extends JpaRepository<ArchitectureOutput, UUID> {

    Optional<ArchitectureOutput> findTopByConversationIdOrderByCreatedAtDesc(UUID conversationId);
}
