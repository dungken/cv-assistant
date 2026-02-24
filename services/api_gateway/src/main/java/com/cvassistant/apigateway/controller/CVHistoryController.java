package com.cvassistant.apigateway.controller;

import com.cvassistant.apigateway.dto.CVHistoryDto;
import com.cvassistant.apigateway.service.CVHistoryService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/cv-history")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class CVHistoryController {

    private final CVHistoryService cvHistoryService;

    @GetMapping
    public ResponseEntity<List<CVHistoryDto>> getHistory(Authentication authentication) {
        return ResponseEntity.ok(cvHistoryService.getHistory(authentication.getName()));
    }

    @PostMapping
    public ResponseEntity<CVHistoryDto> saveHistory(
            Authentication authentication, 
            @RequestBody CVHistoryDto.SaveRequest request) {
        return ResponseEntity.ok(cvHistoryService.saveHistory(authentication.getName(), request));
    }
}
