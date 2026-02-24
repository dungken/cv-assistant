package com.cvassistant.apigateway.repository;

import com.cvassistant.apigateway.model.ChatSession;
import com.cvassistant.apigateway.model.User;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface ChatSessionRepository extends JpaRepository<ChatSession, Long> {
    List<ChatSession> findAllByUserOrderByUpdatedAtDesc(User user);
}
