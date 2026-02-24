package com.cvassistant.apigateway.repository;

import com.cvassistant.apigateway.model.CVHistory;
import com.cvassistant.apigateway.model.User;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface CVHistoryRepository extends JpaRepository<CVHistory, Long> {
    List<CVHistory> findAllByUserOrderByUploadedAtDesc(User user);
}
