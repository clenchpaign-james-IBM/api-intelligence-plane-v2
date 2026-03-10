package com.example.gateway.service;

import com.example.gateway.model.API;
import com.example.gateway.repository.APIRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

/**
 * Service layer for API management in Demo Gateway.
 * 
 * Provides business logic for API registration, updates, and lifecycle management.
 * Handles validation, ID generation, and timestamp management.
 */
@Service
public class APIService {
    
    private static final Logger logger = LoggerFactory.getLogger(APIService.class);
    
    private final APIRepository apiRepository;
    
    public APIService(APIRepository apiRepository) {
        this.apiRepository = apiRepository;
    }
    
    /**
     * Register a new API.
     * 
     * @param api API to register
     * @return Registered API with generated ID
     * @throws IOException if registration fails
     * @throws IllegalArgumentException if API data is invalid
     */
    public API registerAPI(API api) throws IOException {
        logger.info("Registering new API: {}", api.getName());
        
        // Validate required fields
        validateAPI(api);
        
        // Generate ID if not provided
        if (api.getId() == null || api.getId().isEmpty()) {
            api.setId(UUID.randomUUID().toString());
        }
        
        // Set timestamps
        Instant now = Instant.now();
        api.setCreatedAt(now);
        api.setUpdatedAt(now);
        
        // Set default status if not provided
        if (api.getStatus() == null || api.getStatus().isEmpty()) {
            api.setStatus("active");
        }
        
        // Initialize current metrics if not provided
        if (api.getCurrentMetrics() == null) {
            api.setCurrentMetrics(new API.CurrentMetrics());
        }
        
        // Save to repository
        API savedAPI = apiRepository.save(api);
        logger.info("Successfully registered API {} with ID {}", api.getName(), api.getId());
        
        return savedAPI;
    }
    
    /**
     * Get an API by ID.
     * 
     * @param id API ID
     * @return Optional containing the API if found
     */
    public Optional<API> getAPI(String id) {
        logger.debug("Fetching API with ID: {}", id);
        return apiRepository.findById(id);
    }
    
    /**
     * List all APIs.
     * 
     * @return List of all APIs
     */
    public List<API> listAPIs() {
        logger.debug("Listing all APIs");
        return apiRepository.findAll();
    }
    
    /**
     * List APIs by status.
     * 
     * @param status API status filter
     * @return List of APIs with the specified status
     */
    public List<API> listAPIsByStatus(String status) {
        logger.debug("Listing APIs with status: {}", status);
        return apiRepository.findByStatus(status);
    }
    
    /**
     * Update an existing API.
     * 
     * @param id API ID
     * @param updatedAPI Updated API data
     * @return Updated API
     * @throws IOException if update fails
     * @throws IllegalArgumentException if API not found or data is invalid
     */
    public API updateAPI(String id, API updatedAPI) throws IOException {
        logger.info("Updating API with ID: {}", id);
        
        // Check if API exists
        Optional<API> existingAPI = apiRepository.findById(id);
        if (existingAPI.isEmpty()) {
            throw new IllegalArgumentException("API not found with ID: " + id);
        }
        
        // Validate updated data
        validateAPI(updatedAPI);
        
        // Preserve ID and creation timestamp
        updatedAPI.setId(id);
        updatedAPI.setCreatedAt(existingAPI.get().getCreatedAt());
        updatedAPI.setUpdatedAt(Instant.now());
        
        // Update in repository
        API savedAPI = apiRepository.update(updatedAPI);
        logger.info("Successfully updated API {}", id);
        
        return savedAPI;
    }
    
    /**
     * Delete an API.
     * 
     * @param id API ID
     * @return true if deleted, false if not found
     */
    public boolean deleteAPI(String id) {
        logger.info("Deleting API with ID: {}", id);
        
        boolean deleted = apiRepository.deleteById(id);
        
        if (deleted) {
            logger.info("Successfully deleted API {}", id);
        } else {
            logger.warn("API not found for deletion: {}", id);
        }
        
        return deleted;
    }
    
    /**
     * Check if an API exists.
     * 
     * @param id API ID
     * @return true if exists, false otherwise
     */
    public boolean existsAPI(String id) {
        return apiRepository.existsById(id);
    }
    
    /**
     * Get total API count.
     * 
     * @return Total number of APIs
     */
    public long getAPICount() {
        return apiRepository.count();
    }
    
    /**
     * Update API health score.
     * 
     * @param id API ID
     * @param healthScore New health score (0-100)
     * @throws IOException if update fails
     * @throws IllegalArgumentException if API not found or score is invalid
     */
    public void updateHealthScore(String id, double healthScore) throws IOException {
        logger.debug("Updating health score for API {}: {}", id, healthScore);
        
        if (healthScore < 0 || healthScore > 100) {
            throw new IllegalArgumentException("Health score must be between 0 and 100");
        }
        
        Optional<API> apiOpt = apiRepository.findById(id);
        if (apiOpt.isEmpty()) {
            throw new IllegalArgumentException("API not found with ID: " + id);
        }
        
        API api = apiOpt.get();
        api.setHealthScore(healthScore);
        api.setUpdatedAt(Instant.now());
        
        apiRepository.update(api);
    }
    
    /**
     * Update API status.
     * 
     * @param id API ID
     * @param status New status (active, inactive, deprecated, failed)
     * @throws IOException if update fails
     * @throws IllegalArgumentException if API not found or status is invalid
     */
    public void updateStatus(String id, String status) throws IOException {
        logger.info("Updating status for API {}: {}", id, status);
        
        // Validate status
        if (!isValidStatus(status)) {
            throw new IllegalArgumentException("Invalid status: " + status);
        }
        
        Optional<API> apiOpt = apiRepository.findById(id);
        if (apiOpt.isEmpty()) {
            throw new IllegalArgumentException("API not found with ID: " + id);
        }
        
        API api = apiOpt.get();
        api.setStatus(status);
        api.setUpdatedAt(Instant.now());
        
        apiRepository.update(api);
    }
    
    /**
     * Validate API data.
     * 
     * @param api API to validate
     * @throws IllegalArgumentException if validation fails
     */
    private void validateAPI(API api) {
        if (api == null) {
            throw new IllegalArgumentException("API cannot be null");
        }
        
        if (api.getName() == null || api.getName().trim().isEmpty()) {
            throw new IllegalArgumentException("API name is required");
        }
        
        if (api.getBasePath() == null || api.getBasePath().trim().isEmpty()) {
            throw new IllegalArgumentException("API base path is required");
        }
        
        // Validate base path format
        if (!api.getBasePath().startsWith("/")) {
            throw new IllegalArgumentException("API base path must start with /");
        }
        
        // Validate status if provided
        if (api.getStatus() != null && !api.getStatus().isEmpty()) {
            if (!isValidStatus(api.getStatus())) {
                throw new IllegalArgumentException("Invalid status: " + api.getStatus());
            }
        }
    }
    
    /**
     * Check if status is valid.
     * 
     * @param status Status to check
     * @return true if valid, false otherwise
     */
    private boolean isValidStatus(String status) {
        return status != null && (
            status.equals("active") ||
            status.equals("inactive") ||
            status.equals("deprecated") ||
            status.equals("failed")
        );
    }
}

// Made with Bob