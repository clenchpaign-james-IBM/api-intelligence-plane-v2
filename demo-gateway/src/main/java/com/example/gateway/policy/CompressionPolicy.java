package com.example.gateway.policy;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Compression policy engine for managing response compression at the gateway level.
 * Handles compression type selection, compression levels, and content type filtering.
 */
@Component
public class CompressionPolicy {

    private static final Logger logger = LoggerFactory.getLogger(CompressionPolicy.class);

    // Store active compression policies per API
    private final Map<String, CompressionConfiguration> activePolicies = new ConcurrentHashMap<>();

    // Default compressible content types
    private static final List<String> DEFAULT_CONTENT_TYPES = Arrays.asList(
        "application/json",
        "application/xml",
        "text/html",
        "text/plain",
        "text/css",
        "text/javascript",
        "application/javascript"
    );

    /**
     * Apply a compression policy to an API.
     *
     * @param apiId API identifier
     * @param policy Compression policy configuration containing:
     *               - compression_type: Type of compression (gzip, brotli, deflate)
     *               - compression_level: Compression level (1-9)
     *               - min_size_bytes: Minimum response size to compress
     *               - content_types: List of content types to compress
     * @return true if policy applied successfully, false otherwise
     */
    public boolean apply(String apiId, Map<String, Object> policy) {
        try {
            logger.info("Applying compression policy to API: {}", apiId);

            // Extract policy parameters
            String compressionType = (String) policy.getOrDefault("compression_type", "gzip");
            Integer compressionLevel = (Integer) policy.getOrDefault("compression_level", 6);
            Integer minSizeBytes = (Integer) policy.getOrDefault("min_size_bytes", 1024); // Default 1KB
            
            @SuppressWarnings("unchecked")
            List<String> contentTypes = policy.containsKey("content_types") ?
                (List<String>) policy.get("content_types") :
                DEFAULT_CONTENT_TYPES;

            // Validate compression type
            if (!isValidCompressionType(compressionType)) {
                logger.error("Invalid compression type: {}. Must be one of: gzip, brotli, deflate", compressionType);
                return false;
            }

            // Validate compression level
            if (compressionLevel < 1 || compressionLevel > 9) {
                logger.error("Invalid compression level: {}. Must be between 1 and 9", compressionLevel);
                return false;
            }

            // Create compression configuration
            CompressionConfiguration config = new CompressionConfiguration(
                apiId,
                compressionType,
                compressionLevel,
                minSizeBytes,
                contentTypes
            );

            // Store the policy
            activePolicies.put(apiId, config);

            logger.info("Compression policy applied successfully to API {}: Type={}, Level={}, MinSize={}bytes", 
                apiId, compressionType, compressionLevel, minSizeBytes);

            return true;

        } catch (Exception e) {
            logger.error("Failed to apply compression policy to API {}: {}", apiId, e.getMessage(), e);
            return false;
        }
    }

    /**
     * Remove compression policy from an API.
     *
     * @param apiId API identifier
     * @return true if policy removed successfully, false otherwise
     */
    public boolean remove(String apiId) {
        try {
            logger.info("Removing compression policy from API: {}", apiId);

            CompressionConfiguration removed = activePolicies.remove(apiId);

            if (removed != null) {
                logger.info("Compression policy removed successfully from API: {}", apiId);
                return true;
            } else {
                logger.warn("No compression policy found for API: {}", apiId);
                return false;
            }

        } catch (Exception e) {
            logger.error("Failed to remove compression policy from API {}: {}", apiId, e.getMessage(), e);
            return false;
        }
    }

    /**
     * Get the active compression policy for an API.
     *
     * @param apiId API identifier
     * @return CompressionConfiguration if found, null otherwise
     */
    public CompressionConfiguration getPolicy(String apiId) {
        return activePolicies.get(apiId);
    }

    /**
     * Check if an API has an active compression policy.
     *
     * @param apiId API identifier
     * @return true if policy exists, false otherwise
     */
    public boolean hasPolicy(String apiId) {
        return activePolicies.containsKey(apiId);
    }

    /**
     * Validate compression type.
     *
     * @param compressionType Compression type to validate
     * @return true if valid, false otherwise
     */
    private boolean isValidCompressionType(String compressionType) {
        return compressionType != null && 
               (compressionType.equalsIgnoreCase("gzip") ||
                compressionType.equalsIgnoreCase("brotli") ||
                compressionType.equalsIgnoreCase("deflate"));
    }

    /**
     * Inner class representing compression configuration for an API.
     */
    public static class CompressionConfiguration {
        private final String apiId;
        private final String compressionType;
        private final int compressionLevel;
        private final int minSizeBytes;
        private final List<String> contentTypes;

        public CompressionConfiguration(
                String apiId,
                String compressionType,
                int compressionLevel,
                int minSizeBytes,
                List<String> contentTypes) {
            this.apiId = apiId;
            this.compressionType = compressionType;
            this.compressionLevel = compressionLevel;
            this.minSizeBytes = minSizeBytes;
            this.contentTypes = contentTypes;
        }

        public String getApiId() {
            return apiId;
        }

        public String getCompressionType() {
            return compressionType;
        }

        public int getCompressionLevel() {
            return compressionLevel;
        }

        public int getMinSizeBytes() {
            return minSizeBytes;
        }

        public List<String> getContentTypes() {
            return contentTypes;
        }
    }
}

// Made with Bob
