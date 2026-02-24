package com.cvassistant.apigateway.service;

import com.cvassistant.apigateway.dto.CVHistoryDto;
import com.cvassistant.apigateway.model.CVHistory;
import com.cvassistant.apigateway.model.User;
import com.cvassistant.apigateway.repository.CVHistoryRepository;
import com.cvassistant.apigateway.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;
import java.util.List;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class CVHistoryService {

    private final CVHistoryRepository cvHistoryRepository;
    private final UserRepository userRepository;

    public List<CVHistoryDto> getHistory(String email) {
        User user = userRepository.findByEmail(email)
                .orElseThrow(() -> new UsernameNotFoundException("User not found"));
        
        return cvHistoryRepository.findAllByUserOrderByUploadedAtDesc(user).stream()
                .map(cv -> CVHistoryDto.builder()
                        .id(cv.getId())
                        .fileName(cv.getFileName())
                        .fileUrl(cv.getFileUrl())
                        .uploadedAt(cv.getUploadedAt())
                        .build())
                .collect(Collectors.toList());
    }

    public CVHistoryDto saveHistory(String email, CVHistoryDto.SaveRequest request) {
        User user = userRepository.findByEmail(email)
                .orElseThrow(() -> new UsernameNotFoundException("User not found"));
        
        CVHistory history = CVHistory.builder()
                .user(user)
                .fileName(request.getFileName())
                .fileUrl(request.getFileUrl())
                .extractionResult(request.getExtractionResult())
                .build();
        
        cvHistoryRepository.save(history);
        
        return CVHistoryDto.builder()
                .id(history.getId())
                .fileName(history.getFileName())
                .fileUrl(history.getFileUrl())
                .uploadedAt(history.getUploadedAt())
                .build();
    }
}
