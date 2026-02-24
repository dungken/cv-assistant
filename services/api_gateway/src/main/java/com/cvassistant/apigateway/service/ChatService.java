package com.cvassistant.apigateway.service;

import com.cvassistant.apigateway.dto.ChatDto;
import com.cvassistant.apigateway.model.ChatMessage;
import com.cvassistant.apigateway.model.ChatSession;
import com.cvassistant.apigateway.model.User;
import com.cvassistant.apigateway.repository.ChatMessageRepository;
import com.cvassistant.apigateway.repository.ChatSessionRepository;
import com.cvassistant.apigateway.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;
import java.util.List;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class ChatService {

    private final ChatSessionRepository sessionRepository;
    private final ChatMessageRepository messageRepository;
    private final UserRepository userRepository;

    public List<ChatDto.SessionResponse> getSessions(String email) {
        User user = userRepository.findByEmail(email).orElseThrow();
        return sessionRepository.findAllByUserOrderByUpdatedAtDesc(user).stream()
                .map(s -> ChatDto.SessionResponse.builder()
                        .id(s.getId())
                        .title(s.getTitle())
                        .updatedAt(s.getUpdatedAt())
                        .build())
                .collect(Collectors.toList());
    }

    public ChatDto.SessionResponse createSession(String email, String title) {
        User user = userRepository.findByEmail(email).orElseThrow();
        ChatSession session = ChatSession.builder()
                .user(user)
                .title(title)
                .build();
        sessionRepository.save(session);
        return ChatDto.SessionResponse.builder()
                .id(session.getId())
                .title(session.getTitle())
                .updatedAt(session.getUpdatedAt())
                .build();
    }

    public void deleteSession(Long sessionId) {
        sessionRepository.deleteById(sessionId);
    }

    public ChatDto.SessionResponse updateTitle(Long sessionId, String title) {
        ChatSession session = sessionRepository.findById(sessionId).orElseThrow();
        session.setTitle(title);
        sessionRepository.save(session);
        return ChatDto.SessionResponse.builder()
                .id(session.getId())
                .title(session.getTitle())
                .updatedAt(session.getUpdatedAt())
                .build();
    }

    public List<ChatDto.MessageResponse> getMessages(Long sessionId) {
        ChatSession session = sessionRepository.findById(sessionId).orElseThrow();
        return messageRepository.findAllBySessionOrderByTimestampAsc(session).stream()
                .map(m -> ChatDto.MessageResponse.builder()
                        .id(m.getId())
                        .role(m.getRole())
                        .content(m.getContent())
                        .timestamp(m.getTimestamp())
                        .build())
                .collect(Collectors.toList());
    }

    public void saveMessage(Long sessionId, ChatDto.SaveMessageRequest request) {
        ChatSession session = sessionRepository.findById(sessionId).orElseThrow();
        ChatMessage message = ChatMessage.builder()
                .session(session)
                .role(request.getRole())
                .content(request.getContent())
                .build();
        messageRepository.save(message);
        
        // Update session's updatedAt timestamp
        sessionRepository.save(session);
    }
}
