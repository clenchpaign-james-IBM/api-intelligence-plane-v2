package com.example.gateway.service;

import com.example.gateway.model.API;
import com.example.gateway.repository.APIRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ThreadLocalRandom;
import java.util.stream.Collectors;

/**
 * Service for collecting and managing API metrics in the Demo Gateway.
 * 
 * This service simulates metrics collection for demonstration purposes.
 * In a production environment, this would integrate with actual monitoring
 * systems and collect real traffic data.
 */
@Service
public class MetricsService {
    
    @Autowired
    private APIRepository apiRepository;
    
    // In-memory storage for simulated metrics (for demo purposes)
    private final Map<String, List<MetricSnapshot>> metricsStore = new ConcurrentHashMap<>();
    
    /**
     * Collect current metrics for a specific API.
     * 
     * @param apiId The API ID
     * @return Map containing current metrics
     * @throws IOException if API not found or metrics collection fails
     */
    public Map<String, Object> collectMetrics(String apiId) throws IOException {
        Optional<API> apiOpt = apiRepository.findById(apiId);
        if (apiOpt.isEmpty()) {
            throw new IOException("API not found: " + apiId);
        }
        
        API api = apiOpt.get();
        
        // Generate simulated metrics
        MetricSnapshot snapshot = generateMetricSnapshot(apiId);
        
        // Store snapshot
        metricsStore.computeIfAbsent(apiId, k -> new ArrayList<>()).add(snapshot);
        
        // Keep only last 1000 snapshots per API
        List<MetricSnapshot> snapshots = metricsStore.get(apiId);
        if (snapshots.size() > 1000) {
            snapshots.remove(0);
        }
        
        // Update API's current metrics
        API.CurrentMetrics currentMetrics = api.getCurrentMetrics();
        currentMetrics.setResponseTimeP50(snapshot.responseTimeP50);
        currentMetrics.setResponseTimeP95(snapshot.responseTimeP95);
        currentMetrics.setResponseTimeP99(snapshot.responseTimeP99);
        currentMetrics.setErrorRate(snapshot.errorRate);
        currentMetrics.setThroughput(snapshot.throughput);
        currentMetrics.setAvailability(snapshot.availability);
        currentMetrics.setMeasuredAt(snapshot.timestamp);
        
        // Calculate and update health score
        double healthScore = calculateHealthScore(currentMetrics);
        api.setHealthScore(healthScore);
        api.setUpdatedAt(Instant.now());
        
        // Save updated API
        apiRepository.save(api);
        
        // Return metrics summary
        Map<String, Object> result = new HashMap<>();
        result.put("api_id", apiId);
        result.put("timestamp", snapshot.timestamp);
        result.put("metrics", Map.of(
            "response_time_p50", snapshot.responseTimeP50,
            "response_time_p95", snapshot.responseTimeP95,
            "response_time_p99", snapshot.responseTimeP99,
            "error_rate", snapshot.errorRate,
            "throughput", snapshot.throughput,
            "availability", snapshot.availability
        ));
        result.put("health_score", healthScore);
        result.put("status", "collected");
        
        return result;
    }
    
    /**
     * Get metrics time-series for an API.
     * 
     * @param apiId The API ID
     * @param startTime Start of time range (optional)
     * @param endTime End of time range (optional)
     * @param interval Aggregation interval in minutes (default: 5)
     * @return List of aggregated metrics
     */
    public List<Map<String, Object>> getMetricsTimeSeries(
            String apiId, 
            Instant startTime, 
            Instant endTime,
            Integer interval) {
        
        List<MetricSnapshot> snapshots = metricsStore.getOrDefault(apiId, new ArrayList<>());
        
        // Apply time range filter
        Instant start = startTime != null ? startTime : Instant.now().minus(1, ChronoUnit.HOURS);
        Instant end = endTime != null ? endTime : Instant.now();
        int intervalMinutes = interval != null ? interval : 5;
        
        List<MetricSnapshot> filtered = snapshots.stream()
            .filter(s -> !s.timestamp.isBefore(start) && !s.timestamp.isAfter(end))
            .collect(Collectors.toList());
        
        if (filtered.isEmpty()) {
            return new ArrayList<>();
        }
        
        // Group by interval and aggregate
        Map<Instant, List<MetricSnapshot>> grouped = new TreeMap<>();
        for (MetricSnapshot snapshot : filtered) {
            Instant bucket = roundToInterval(snapshot.timestamp, intervalMinutes);
            grouped.computeIfAbsent(bucket, k -> new ArrayList<>()).add(snapshot);
        }
        
        // Aggregate each bucket
        List<Map<String, Object>> result = new ArrayList<>();
        for (Map.Entry<Instant, List<MetricSnapshot>> entry : grouped.entrySet()) {
            List<MetricSnapshot> bucket = entry.getValue();
            
            Map<String, Object> aggregated = new HashMap<>();
            aggregated.put("timestamp", entry.getKey());
            aggregated.put("response_time_p50", average(bucket, s -> s.responseTimeP50));
            aggregated.put("response_time_p95", average(bucket, s -> s.responseTimeP95));
            aggregated.put("response_time_p99", average(bucket, s -> s.responseTimeP99));
            aggregated.put("error_rate", average(bucket, s -> s.errorRate));
            aggregated.put("throughput", sum(bucket, s -> s.throughput));
            aggregated.put("availability", average(bucket, s -> s.availability));
            aggregated.put("sample_count", bucket.size());
            
            result.add(aggregated);
        }
        
        return result;
    }
    
    /**
     * Get aggregated metrics for all APIs.
     * 
     * @return List of API metrics summaries
     */
    public List<Map<String, Object>> getAllAPIsMetrics() throws IOException {
        List<API> apis = apiRepository.findAll();
        List<Map<String, Object>> result = new ArrayList<>();
        
        for (API api : apis) {
            Map<String, Object> summary = new HashMap<>();
            summary.put("api_id", api.getId());
            summary.put("api_name", api.getName());
            summary.put("status", api.getStatus());
            summary.put("health_score", api.getHealthScore());
            
            API.CurrentMetrics metrics = api.getCurrentMetrics();
            summary.put("current_metrics", Map.of(
                "response_time_p50", metrics.getResponseTimeP50(),
                "response_time_p95", metrics.getResponseTimeP95(),
                "response_time_p99", metrics.getResponseTimeP99(),
                "error_rate", metrics.getErrorRate(),
                "throughput", metrics.getThroughput(),
                "availability", metrics.getAvailability(),
                "measured_at", metrics.getMeasuredAt()
            ));
            
            result.add(summary);
        }
        
        return result;
    }
    
    /**
     * Calculate health score based on current metrics.
     * Formula: 40% availability + 30% error rate + 30% response time
     * 
     * @param metrics Current metrics
     * @return Health score (0-100)
     */
    private double calculateHealthScore(API.CurrentMetrics metrics) {
        // Availability component (40%)
        double availabilityScore = (metrics.getAvailability() / 100.0) * 40.0;
        
        // Error rate component (30%) - inverted (lower is better)
        double errorScore = (1.0 - metrics.getErrorRate()) * 30.0;
        
        // Response time component (30%) - normalized (lower is better)
        // Assume 500ms is baseline, 0ms is perfect, 1000ms+ is poor
        double responseTimeScore;
        if (metrics.getResponseTimeP95() <= 100) {
            responseTimeScore = 30.0;
        } else if (metrics.getResponseTimeP95() >= 1000) {
            responseTimeScore = 0.0;
        } else {
            responseTimeScore = 30.0 * (1.0 - (metrics.getResponseTimeP95() - 100) / 900.0);
        }
        
        double healthScore = availabilityScore + errorScore + responseTimeScore;
        return Math.round(Math.max(0.0, Math.min(100.0, healthScore)) * 100.0) / 100.0;
    }
    
    /**
     * Generate simulated metric snapshot for demonstration.
     * 
     * @param apiId The API ID
     * @return Simulated metric snapshot
     */
    private MetricSnapshot generateMetricSnapshot(String apiId) {
        ThreadLocalRandom random = ThreadLocalRandom.current();
        
        MetricSnapshot snapshot = new MetricSnapshot();
        snapshot.apiId = apiId;
        snapshot.timestamp = Instant.now();
        
        // Simulate realistic metrics with some variance
        snapshot.responseTimeP50 = 30.0 + random.nextDouble() * 50.0;
        snapshot.responseTimeP95 = snapshot.responseTimeP50 * (2.0 + random.nextDouble());
        snapshot.responseTimeP99 = snapshot.responseTimeP95 * (1.5 + random.nextDouble() * 0.5);
        snapshot.errorRate = random.nextDouble() * 0.05; // 0-5% error rate
        snapshot.throughput = 10.0 + random.nextDouble() * 40.0; // 10-50 req/s
        snapshot.availability = 95.0 + random.nextDouble() * 5.0; // 95-100%
        
        return snapshot;
    }
    
    /**
     * Round timestamp to interval bucket.
     * 
     * @param timestamp The timestamp
     * @param intervalMinutes Interval in minutes
     * @return Rounded timestamp
     */
    private Instant roundToInterval(Instant timestamp, int intervalMinutes) {
        long epochSeconds = timestamp.getEpochSecond();
        long intervalSeconds = intervalMinutes * 60L;
        long rounded = (epochSeconds / intervalSeconds) * intervalSeconds;
        return Instant.ofEpochSecond(rounded);
    }
    
    /**
     * Calculate average of a metric field.
     */
    private double average(List<MetricSnapshot> snapshots, java.util.function.ToDoubleFunction<MetricSnapshot> extractor) {
        return snapshots.stream()
            .mapToDouble(extractor)
            .average()
            .orElse(0.0);
    }
    
    /**
     * Calculate sum of a metric field.
     */
    private double sum(List<MetricSnapshot> snapshots, java.util.function.ToDoubleFunction<MetricSnapshot> extractor) {
        return snapshots.stream()
            .mapToDouble(extractor)
            .sum();
    }
    
    /**
     * Internal class for storing metric snapshots.
     */
    private static class MetricSnapshot {
        String apiId;
        Instant timestamp;
        double responseTimeP50;
        double responseTimeP95;
        double responseTimeP99;
        double errorRate;
        double throughput;
        double availability;
    }
}

// Made with Bob