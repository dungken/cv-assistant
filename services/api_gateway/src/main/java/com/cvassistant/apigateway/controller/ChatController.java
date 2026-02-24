package com.cvassistant.apigateway.controller;

import com.cvassistant.apigateway.dto.ChatDto;
import com.cvassistant.apigateway.service.ChatService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/chats")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class ChatController {

    private final ChatService chatService;

    @GetMapping
    public ResponseEntity<List<ChatDto.SessionResponse>> getSessions(Authentication auth) {
        return ResponseEntity.ok(chatService.getSessions(auth.getName()));
    }

    @PostMapping
    public ResponseEntity<ChatDto.SessionResponse> createSession(
            Authentication auth, @RequestBody ChatDto.CreateSessionRequest request) {
        return ResponseEntity.ok(chatService.createSession(auth.getName(), request.getTitle()));
    }

    @PutMapping("/{id}")
    public ResponseEntity<ChatDto.SessionResponse> updateTitle(
            @PathVariable Long id, @RequestBody ChatDto.CreateSessionRequest request) {
        return ResponseEntity.ok(chatService.updateTitle(id, request.getTitle()));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteSession(@PathVariable Long id) {
        chatService.deleteSession(id);
        return ResponseEntity.ok().build();
    }

    @GetMapping("/{id}/messages")
    public ResponseEntity<List<ChatDto.MessageResponse>> getMessages(@PathVariable Long id) {
        return ResponseEntity.ok(chatService.getMessages(id));
    }

    @PostMapping("/{id}/messages")
    public ResponseEntity<Void> saveMessage(
            @PathVariable Long id, @RequestBody ChatDto.SaveMessageRequest request) {
        chatService.saveMessage(id, request);
        return ResponseEntity.ok().build();
    }
}
