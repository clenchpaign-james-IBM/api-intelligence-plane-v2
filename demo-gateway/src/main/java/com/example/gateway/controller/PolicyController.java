package com.example.gateway.controller;

import com.example.gateway.policy.CachingPolicy;
import com.example.gateway.policy.CompressionPolicy;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

/**
 * REST controller for managing API policies (caching, compression, rate limiting).
 * Provides endpoints for applying and removing policies on APIs.
 */
@RestController
@RequestMapping("/api/v1/apis/{apiId}")
public class PolicyController {

    private static final Logger logger = LoggerFactory.getLogger(PolicyController.class);

    private final CachingPolicy cachingPolicy;
    private final CompressionPolicy compressionPolicy;

    public PolicyController(CachingPolicy cachingPolicy, CompressionPolicy compressionPolicy) {
        this.cachingPolicy = cachingPolicy;
        this.compressionPolicy = compressionPolicy;
    }

    /**
     * Apply caching policy to an API.
     *
     * @param apiId API identifier
     * @param policy Caching policy configuration
     * @return Response with success status
     */
    @PostMapping("/caching")
    public ResponseEntity<Map<String, Object>> applyCachingPolicy(
            @PathVariable String apiId,
            @RequestBody Map<String, Object> policy) {
        
        logger.info("Applying caching policy to API: {}", apiId);
        
        try {
            boolean success = cachingPolicy.apply(apiId, policy);
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", success);
            response.put("apiId", apiId);
            response.put("policyType", "caching");
            response.put("message", success ? 
                "Caching policy applied successfully" : 
                "Failed to apply caching policy");
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            logger.error("Error applying caching policy to API {}: {}", apiId, e.getMessage());
            
            Map<String, Object> errorResponse = new HashMap<>();
            errorResponse.put("success", false);
            errorResponse.put("apiId", apiId);
            errorResponse.put("error", e.getMessage());
            
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
        }
    }

    /**
     * Remove caching policy from an API.
     *
     * @param apiId API identifier
     * @return Response with success status
     */
    @DeleteMapping("/caching")
    public ResponseEntity<Map<String, Object>> removeCachingPolicy(@PathVariable String apiId) {
        
        logger.info("Removing caching policy from API: {}", apiId);
        
        try {
            boolean success = cachingPolicy.remove(apiId);
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", success);
            response.put("apiId", apiId);
            response.put("message", success ? 
                "Caching policy removed successfully" : 
                "Failed to remove caching policy");
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            logger.error("Error removing caching policy from API {}: {}", apiId, e.getMessage());
            
            Map<String, Object> errorResponse = new HashMap<>();
            errorResponse.put("success", false);
            errorResponse.put("apiId", apiId);
            errorResponse.put("error", e.getMessage());
            
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
        }
    }

    /**
     * Apply compression policy to an API.
     *
     * @param apiId API identifier
     * @param policy Compression policy configuration
     * @return Response with success status
     */
    @PostMapping("/compression")
    public ResponseEntity<Map<String, Object>> applyCompressionPolicy(
            @PathVariable String apiId,
            @RequestBody Map<String, Object> policy) {
        
        logger.info("Applying compression policy to API: {}", apiId);
        
        try {
            boolean success = compressionPolicy.apply(apiId, policy);
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", success);
            response.put("apiId", apiId);
            response.put("policyType", "compression");
            response.put("message", success ? 
                "Compression policy applied successfully" : 
                "Failed to apply compression policy");
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            logger.error("Error applying compression policy to API {}: {}", apiId, e.getMessage());
            
            Map<String, Object> errorResponse = new HashMap<>();
            errorResponse.put("success", false);
            errorResponse.put("apiId", apiId);
            errorResponse.put("error", e.getMessage());
            
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
        }
    }

    /**
     * Remove compression policy from an API.
     *
     * @param apiId API identifier
     * @return Response with success status
     */
    @DeleteMapping("/compression")
    public ResponseEntity<Map<String, Object>> removeCompressionPolicy(@PathVariable String apiId) {
        
        logger.info("Removing compression policy from API: {}", apiId);
        
        try {
            boolean success = compressionPolicy.remove(apiId);
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", success);
            response.put("apiId", apiId);
            response.put("message", success ? 
                "Compression policy removed successfully" : 
                "Failed to remove compression policy");
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            logger.error("Error removing compression policy from API {}: {}", apiId, e.getMessage());
            
            Map<String, Object> errorResponse = new HashMap<>();
            errorResponse.put("success", false);
            errorResponse.put("apiId", apiId);
            errorResponse.put("error", e.getMessage());
            
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
        }
    }
}

// Made with Bob
