package com.aiarchitect.api.domain.repository;

import com.aiarchitect.api.domain.model.Message;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import java.util.List;
import java.util.UUID;

public interface MessageRepository extends JpaRepository<Message, UUID> {
    @Query("SELECT m FROM Message m WHERE m.conversation.id = :convId " +
           "ORDER BY m.createdAt DESC")
    List<Message> findRecentByConversationId(UUID convId, Pageable pageable);
}
