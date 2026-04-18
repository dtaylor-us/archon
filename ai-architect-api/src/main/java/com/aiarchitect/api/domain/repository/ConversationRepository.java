package com.aiarchitect.api.domain.repository;

import com.aiarchitect.api.domain.model.Conversation;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface ConversationRepository extends JpaRepository<Conversation, UUID> {
    List<Conversation> findByUserIdOrderByCreatedAtDesc(String userId);
    Optional<Conversation> findByIdAndUserId(UUID id, String userId);
}
