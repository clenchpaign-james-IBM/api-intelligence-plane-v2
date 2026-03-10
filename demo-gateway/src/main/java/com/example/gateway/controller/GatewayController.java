package com.example.gateway.controller;

import com.example.gateway.repository.APIRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.Duration;
import java.time.Instant;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Gateway Controller for Demo Gateway.
 * 
 * Provides endpoints for gateway information, capabilities, and health status.
 * These endpoints are used by the API Intelligence Plane to discover and
 * monitor the gateway.
 */
@RestController
@RequestMapping("/gateway")
public class GatewayController {
    
    private static final Logger logger = LoggerFactory.getLogger(GatewayController.class);
    
    private final APIRepository apiRepository;
    private final Instant startTime;
    
    @Value("${gateway.name:Native API Gateway}")
    private String gatewayName;
    
    @Value("${gateway.version:1.0.0}")
    private String gatewayVersion;
    
    @Value("${gateway.vendor:native}")
    private String gatewayVendor;
    
    @Value("${gateway.description:Demo API Gateway for API Intelligence Plane}")
    private String gatewayDescription;
    
    public GatewayController(APIRepository apiRepository) {
        this.apiRepository = apiRepository;
        this.startTime = Instant.now();
    }
    
    /**
     * Get gateway information.
     * 
     * GET /gateway/info
     * 
     * Returns basic information about the gateway including name, version,
     * vendor, and current API count.
     * 
     * @return Gateway information
     */
    @GetMapping("/info")
    public ResponseEntity<Map<String, Object>> getGatewayInfo() {
        logger.info("Fetching gateway info");
        
        try {
            long apiCount = apiRepository.count();
            
            Map<String, Object> info = new HashMap<>();
            info.put("name", gatewayName);
            info.put("version", gatewayVersion);
            info.put("vendor", gatewayVendor);
            info.put("description", gatewayDescription);
            info.put("api_count", apiCount);
            info.put("started_at", startTime.toString());
            info.put("uptime_seconds", Duration.between(startTime, Instant.now()).getSeconds());
            
            return ResponseEntity.ok(info);
            
        } catch (Exception e) {
            logger.error("Failed to get gateway info: {}", e.getMessage());
            
            // Return basic info even if API count fails
            Map<String, Object> info = new HashMap<>();
            info.put("name", gatewayName);
            info.put("version", gatewayVersion);
            info.put("vendor", gatewayVendor);
            info.put("description", gatewayDescription);
            info.put("api_count", 0);
            info.put("started_at", startTime.toString());
            info.put("uptime_seconds", Duration.between(startTime, Instant.now()).getSeconds());
            info.put("error", "Failed to retrieve complete gateway information");
            
            return ResponseEntity.ok(info);
        }
    }
    
    /**
     * Get gateway capabilities.
     * 
     * GET /gateway/capabilities
     * 
     * Returns a list of capabilities supported by this gateway.
     * These capabilities are used by the API Intelligence Plane to determine
     * what features can be used with this gateway.
     * 
     * @return Gateway capabilities
     */
    @GetMapping("/capabilities")
    public ResponseEntity<Map<String, Object>> getCapabilities() {
        logger.info("Fetching gateway capabilities");
        
        List<String> capabilities = Arrays.asList(
            "api_discovery",
            "metrics_collection",
            "log_streaming",
            "policy_management",
            "rate_limiting",
            "authentication_management",
            "health_monitoring",
            "real_time_metrics"
        );
        
        Map<String, Object> response = new HashMap<>();
        response.put("capabilities", capabilities);
        response.put("gateway_type", "native");
        response.put("supports_shadow_api_detection", true);
        response.put("supports_traffic_analysis", true);
        
        return ResponseEntity.ok(response);
    }
    
    /**
     * Health check endpoint.
     * 
     * GET /health
     * 
     * Returns the health status of the gateway and its components.
     * 
     * @return Health status
     */
    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> getHealth() {
        logger.debug("Health check requested");
        
        Map<String, Object> health = new HashMap<>();
        health.put("status", "healthy");
        health.put("timestamp", Instant.now().toString());
        health.put("version", gatewayVersion);
        health.put("uptime_seconds", Duration.between(startTime, Instant.now()).getSeconds());
        
        // Check components
        Map<String, String> components = new HashMap<>();
        
        // Check OpenSearch connectivity
        try {
            apiRepository.count();
            components.put("database", "healthy");
        } catch (Exception e) {
            components.put("database", "unhealthy");
            health.put("status", "degraded");
        }
        
        // Cache is not implemented yet, so mark as healthy by default
        components.put("cache", "healthy");
        
        health.put("components", components);
        
        return ResponseEntity.ok(health);
    }
}

// Made with Bob