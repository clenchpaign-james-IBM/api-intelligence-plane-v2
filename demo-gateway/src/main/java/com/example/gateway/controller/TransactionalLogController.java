package com.example.gateway.controller;

import com.example.gateway.service.TransactionalLogService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.Map;

@RestController
@RequestMapping("/gateway")
public class TransactionalLogController {

    private static final Logger logger = LoggerFactory.getLogger(TransactionalLogController.class);

    private final TransactionalLogService transactionalLogService;

    public TransactionalLogController(TransactionalLogService transactionalLogService) {
        this.transactionalLogService = transactionalLogService;
    }

    @GetMapping("/logs")
    public ResponseEntity<Map<String, Object>> getTransactionalLogs(
            @RequestParam(required = false, name = "apiId") String apiId,
            @RequestParam(required = false, name = "startTime")
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) Instant startTime,
            @RequestParam(required = false, name = "endTime")
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) Instant endTime,
            @RequestParam(defaultValue = "100") int limit,
            @RequestParam(defaultValue = "0") int offset) {

        Instant effectiveEndTime = endTime != null ? endTime : Instant.now();
        Instant effectiveStartTime = startTime != null ? startTime : effectiveEndTime.minus(24, ChronoUnit.HOURS);

        logger.info(
            "Fetching transactional logs - apiId: {}, startTime: {}, endTime: {}, limit: {}, offset: {}",
            apiId,
            effectiveStartTime,
            effectiveEndTime,
            limit,
            offset
        );

        Map<String, Object> response = transactionalLogService.getTransactionalLogs(
            apiId,
            effectiveStartTime,
            effectiveEndTime,
            limit,
            offset
        );

        return ResponseEntity.ok(response);
    }
}

// Made with Bob
