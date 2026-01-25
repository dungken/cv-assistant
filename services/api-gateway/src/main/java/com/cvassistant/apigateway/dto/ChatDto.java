package com.cvassistant.apigateway.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.time.LocalDateTime;

public class ChatDto {

    @Data
    @Builder
    @AllArgsConstructor
    @NoArgsConstructor
    public static class SessionResponse {
        private Long id;
        private String title;
        private LocalDateTime updatedAt;
    }

    @Data
    @Builder
    @AllArgsConstructor
    @NoArgsConstructor
    public static class CreateSessionRequest {
        private String title;
    }

    @Data
    @Builder
    @AllArgsConstructor
    @NoArgsConstructor
    public static class MessageResponse {
        private Long id;
        private String role;
        private String content;
        private LocalDateTime timestamp;
    }
    
    @Data
    @Builder
    @AllArgsConstructor
    @NoArgsConstructor
    public static class SaveMessageRequest {
        private String role;
        private String content;
    }
}
