package com.gidsyc.nlp4re.repositories;

import com.gidsyc.nlp4re.models.Conversation;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface ConversationRepository extends JpaRepository<Conversation, UUID> {
    List<Conversation> findAllByUserIdOrderByCreatedAtDesc(UUID userId);
}
