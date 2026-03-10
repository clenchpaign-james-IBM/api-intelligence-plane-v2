package com.example.gateway.controller;

import com.example.gateway.model.API;
import com.example.gateway.service.APIService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.io.IOException;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/**
 * API Controller for Demo Gateway.
 * 
 * Provides REST endpoints for API registration, management, and lifecycle operations.
 * These endpoints allow the API Intelligence Plane to discover and manage APIs
 * registered in this gateway.
 */
@RestController
@RequestMapping("/apis")
public class APIController {
    
    private static final Logger logger = LoggerFactory.getLogger(APIController.class);
    
    private final APIService apiService;
    
    public APIController(APIService apiService) {
        this.apiService = apiService;
    }
    
    /**
     * List all registered APIs.
     * 
     * GET /apis
     * 
     * Supports filtering by status via query parameter.
     * 
     * @param status Optional status filter (active, inactive, deprecated, failed)
     * @param page Page number (default: 1)
     * @param pageSize Page size (default: 20)
     * @return List of APIs
     */
    @GetMapping
    public ResponseEntity<Map<String, Object>> listAPIs(
            @RequestParam(required = false) String status,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(name = "page_size", defaultValue = "20") int pageSize) {
        
        logger.info("Listing APIs - status: {}, page: {}, pageSize: {}", status, page, pageSize);
        
        try {
            List<API> apis;
            
            if (status != null && !status.isEmpty()) {
                apis = apiService.listAPIsByStatus(status);
            } else {
                apis = apiService.listAPIs();
            }
            
            // Simple pagination (in-memory)
            int start = (page - 1) * pageSize;
            int end = Math.min(start + pageSize, apis.size());
            
            List<API> paginatedAPIs = start < apis.size() ? 
                apis.subList(start, end) : List.of();
            
            Map<String, Object> response = new HashMap<>();
            response.put("apis", paginatedAPIs);
            response.put("total", apis.size());
            response.put("page", page);
            response.put("page_size", pageSize);
            response.put("total_pages", (int) Math.ceil((double) apis.size() / pageSize));
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            logger.error("Failed to list APIs: {}", e.getMessage());
            
            Map<String, Object> error = new HashMap<>();
            error.put("error", "Failed to list APIs");
            error.put("message", e.getMessage());
            
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
        }
    }
    
    /**
     * Register a new API.
     * 
     * POST /apis
     * 
     * @param api API to register
     * @return Registered API with generated ID
     */
    @PostMapping
    public ResponseEntity<Object> registerAPI(@RequestBody API api) {
        logger.info("Registering new API: {}", api.getName());
        
        try {
            API registeredAPI = apiService.registerAPI(api);
            return ResponseEntity.status(HttpStatus.CREATED).body(registeredAPI);
            
        } catch (IllegalArgumentException e) {
            logger.warn("Invalid API data: {}", e.getMessage());
            
            Map<String, String> error = new HashMap<>();
            error.put("error", "Invalid API data");
            error.put("message", e.getMessage());
            
            return ResponseEntity.badRequest().body(error);
            
        } catch (IOException e) {
            logger.error("Failed to register API: {}", e.getMessage());
            
            Map<String, String> error = new HashMap<>();
            error.put("error", "Failed to register API");
            error.put("message", e.getMessage());
            
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
        }
    }
    
    /**
     * Get API details by ID.
     * 
     * GET /apis/{api_id}
     * 
     * @param apiId API ID
     * @return API details
     */
    @GetMapping("/{api_id}")
    public ResponseEntity<Object> getAPI(@PathVariable("api_id") String apiId) {
        logger.info("Fetching API with ID: {}", apiId);
        
        Optional<API> api = apiService.getAPI(apiId);
        
        if (api.isPresent()) {
            return ResponseEntity.ok(api.get());
        } else {
            logger.warn("API not found: {}", apiId);
            
            Map<String, String> error = new HashMap<>();
            error.put("error", "API not found");
            error.put("message", "No API found with ID: " + apiId);
            
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(error);
        }
    }
    
    /**
     * Update an existing API.
     * 
     * PUT /apis/{api_id}
     * 
     * @param apiId API ID
     * @param api Updated API data
     * @return Updated API
     */
    @PutMapping("/{api_id}")
    public ResponseEntity<Object> updateAPI(
            @PathVariable("api_id") String apiId,
            @RequestBody API api) {
        
        logger.info("Updating API with ID: {}", apiId);
        
        try {
            API updatedAPI = apiService.updateAPI(apiId, api);
            return ResponseEntity.ok(updatedAPI);
            
        } catch (IllegalArgumentException e) {
            logger.warn("Invalid update request: {}", e.getMessage());
            
            Map<String, String> error = new HashMap<>();
            error.put("error", "Invalid request");
            error.put("message", e.getMessage());
            
            return ResponseEntity.badRequest().body(error);
            
        } catch (IOException e) {
            logger.error("Failed to update API: {}", e.getMessage());
            
            Map<String, String> error = new HashMap<>();
            error.put("error", "Failed to update API");
            error.put("message", e.getMessage());
            
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
        }
    }
    
    /**
     * Delete an API.
     * 
     * DELETE /apis/{api_id}
     * 
     * @param apiId API ID
     * @return No content on success
     */
    @DeleteMapping("/{api_id}")
    public ResponseEntity<Object> deleteAPI(@PathVariable("api_id") String apiId) {
        logger.info("Deleting API with ID: {}", apiId);
        
        boolean deleted = apiService.deleteAPI(apiId);
        
        if (deleted) {
            return ResponseEntity.noContent().build();
        } else {
            logger.warn("API not found for deletion: {}", apiId);
            
            Map<String, String> error = new HashMap<>();
            error.put("error", "API not found");
            error.put("message", "No API found with ID: " + apiId);
            
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(error);
        }
    }
    
    /**
     * Update API status.
     * 
     * PATCH /apis/{api_id}/status
     * 
     * @param apiId API ID
     * @param request Status update request
     * @return Updated API
     */
    @PatchMapping("/{api_id}/status")
    public ResponseEntity<Object> updateAPIStatus(
            @PathVariable("api_id") String apiId,
            @RequestBody Map<String, String> request) {
        
        logger.info("Updating status for API: {}", apiId);
        
        String status = request.get("status");
        if (status == null || status.isEmpty()) {
            Map<String, String> error = new HashMap<>();
            error.put("error", "Invalid request");
            error.put("message", "Status is required");
            
            return ResponseEntity.badRequest().body(error);
        }
        
        try {
            apiService.updateStatus(apiId, status);
            
            Optional<API> updatedAPI = apiService.getAPI(apiId);
            return updatedAPI.<ResponseEntity<Object>>map(api -> ResponseEntity.ok(api))
                .orElse(ResponseEntity.notFound().build());
            
        } catch (IllegalArgumentException e) {
            logger.warn("Invalid status update: {}", e.getMessage());
            
            Map<String, String> error = new HashMap<>();
            error.put("error", "Invalid request");
            error.put("message", e.getMessage());
            
            return ResponseEntity.badRequest().body(error);
            
        } catch (IOException e) {
            logger.error("Failed to update status: {}", e.getMessage());
            
            Map<String, String> error = new HashMap<>();
            error.put("error", "Failed to update status");
            error.put("message", e.getMessage());
            
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
        }
    }
}

// Made with Bob