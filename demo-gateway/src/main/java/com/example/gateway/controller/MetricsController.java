package com.example.gateway.controller;

import com.example.gateway.service.MetricsService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.io.IOException;
import java.time.Instant;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * REST controller for metrics endpoints in the Demo Gateway.
 * 
 * Provides endpoints for:
 * - Collecting metrics for specific APIs
 * - Retrieving metrics time-series data
 * - Getting aggregated metrics for all APIs
 */
@RestController
@RequestMapping("/metrics")
public class MetricsController {
    
    @Autowired
    private MetricsService metricsService;
    
    /**
     * Get aggregated metrics for all APIs.
     * 
     * GET /metrics/apis
     * 
     * @return List of API metrics summaries
     */
    @GetMapping("/apis")
    public ResponseEntity<Object> getAllAPIsMetrics() {
        try {
            List<Map<String, Object>> metrics = metricsService.getAllAPIsMetrics();
            
            Map<String, Object> response = new HashMap<>();
            response.put("total", metrics.size());
            response.put("apis", metrics);
            response.put("timestamp", Instant.now());
            
            return ResponseEntity.ok(response);
        } catch (IOException e) {
            Map<String, Object> error = new HashMap<>();
            error.put("error", "Failed to retrieve metrics");
            error.put("message", e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
        }
    }
    
    /**
     * Get metrics for a specific API.
     * 
     * GET /metrics/apis/{id}
     * 
     * Query parameters:
     * - start: Start time (ISO 8601 format, optional)
     * - end: End time (ISO 8601 format, optional)
     * - interval: Aggregation interval in minutes (default: 5)
     * 
     * @param id The API ID
     * @param start Start time (optional)
     * @param end End time (optional)
     * @param interval Aggregation interval in minutes (optional)
     * @return Metrics time-series data
     */
    @GetMapping("/apis/{id}")
    public ResponseEntity<Object> getAPIMetrics(
            @PathVariable String id,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) Instant start,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) Instant end,
            @RequestParam(required = false) Integer interval) {
        
        try {
            List<Map<String, Object>> timeSeries = metricsService.getMetricsTimeSeries(
                id, start, end, interval
            );
            
            Map<String, Object> response = new HashMap<>();
            response.put("api_id", id);
            response.put("start", start != null ? start : Instant.now().minusSeconds(3600));
            response.put("end", end != null ? end : Instant.now());
            response.put("interval_minutes", interval != null ? interval : 5);
            response.put("data_points", timeSeries.size());
            response.put("metrics", timeSeries);
            
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            Map<String, Object> error = new HashMap<>();
            error.put("error", "Failed to retrieve metrics for API");
            error.put("api_id", id);
            error.put("message", e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
        }
    }
    
    /**
     * Collect current metrics for a specific API.
     * 
     * POST /metrics/apis/{id}/collect
     * 
     * This endpoint triggers metrics collection for the specified API.
     * In a production environment, this would be called periodically by
     * a scheduler or monitoring system.
     * 
     * @param id The API ID
     * @return Collected metrics summary
     */
    @PostMapping("/apis/{id}/collect")
    public ResponseEntity<Object> collectAPIMetrics(@PathVariable String id) {
        try {
            Map<String, Object> result = metricsService.collectMetrics(id);
            return ResponseEntity.ok(result);
        } catch (IOException e) {
            Map<String, Object> error = new HashMap<>();
            error.put("error", "Failed to collect metrics");
            error.put("api_id", id);
            error.put("message", e.getMessage());
            
            if (e.getMessage().contains("not found")) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND).body(error);
            }
            
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
        }
    }
    
    /**
     * Get metrics summary statistics.
     * 
     * GET /metrics/summary
     * 
     * @return Aggregated statistics across all APIs
     */
    @GetMapping("/summary")
    public ResponseEntity<Object> getMetricsSummary() {
        try {
            List<Map<String, Object>> allMetrics = metricsService.getAllAPIsMetrics();
            
            // Calculate summary statistics
            int totalAPIs = allMetrics.size();
            int healthyAPIs = 0;
            int warningAPIs = 0;
            int criticalAPIs = 0;
            double avgHealthScore = 0.0;
            double avgErrorRate = 0.0;
            double avgResponseTime = 0.0;
            
            for (Map<String, Object> apiMetrics : allMetrics) {
                double healthScore = (double) apiMetrics.get("health_score");
                avgHealthScore += healthScore;
                
                if (healthScore >= 80) {
                    healthyAPIs++;
                } else if (healthScore >= 50) {
                    warningAPIs++;
                } else {
                    criticalAPIs++;
                }
                
                @SuppressWarnings("unchecked")
                Map<String, Object> currentMetrics = (Map<String, Object>) apiMetrics.get("current_metrics");
                avgErrorRate += (double) currentMetrics.get("error_rate");
                avgResponseTime += (double) currentMetrics.get("response_time_p95");
            }
            
            if (totalAPIs > 0) {
                avgHealthScore /= totalAPIs;
                avgErrorRate /= totalAPIs;
                avgResponseTime /= totalAPIs;
            }
            
            Map<String, Object> summary = new HashMap<>();
            summary.put("total_apis", totalAPIs);
            summary.put("healthy_apis", healthyAPIs);
            summary.put("warning_apis", warningAPIs);
            summary.put("critical_apis", criticalAPIs);
            summary.put("avg_health_score", Math.round(avgHealthScore * 100.0) / 100.0);
            summary.put("avg_error_rate", Math.round(avgErrorRate * 10000.0) / 10000.0);
            summary.put("avg_response_time_p95", Math.round(avgResponseTime * 100.0) / 100.0);
            summary.put("timestamp", Instant.now());
            
            return ResponseEntity.ok(summary);
        } catch (IOException e) {
            Map<String, Object> error = new HashMap<>();
            error.put("error", "Failed to generate metrics summary");
            error.put("message", e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
        }
    }
}

// Made with Bob