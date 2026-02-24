package com.cvassistant.apigateway.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.time.LocalDateTime;

@Data
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class CVHistoryDto {
    private Long id;
    private String fileName;
    private String fileUrl;
    private LocalDateTime uploadedAt;

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class SaveRequest {
        private String fileName;
        private String fileUrl;
        private String extractionResult;
    }
}
