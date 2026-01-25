package com.cvassistant.apigateway.repository;

import com.cvassistant.apigateway.model.ChatMessage;
import com.cvassistant.apigateway.model.ChatSession;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface ChatMessageRepository extends JpaRepository<ChatMessage, Long> {
    List<ChatMessage> findAllBySessionOrderByTimestampAsc(ChatSession session);
}
