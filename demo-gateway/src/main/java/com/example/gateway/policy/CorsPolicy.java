package com.example.gateway.policy;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * CORS (Cross-Origin Resource Sharing) policy engine for managing cross-origin requests.
 * Handles allowed origins, methods, headers, and credentials configuration.
 */
@Component
public class CorsPolicy {

    private static final Logger logger = LoggerFactory.getLogger(CorsPolicy.class);

    // Store active CORS policies per API
    private final Map<String, CorsConfiguration> activePolicies = new ConcurrentHashMap<>();

    /**
     * Apply a CORS policy to an API.
     *
     * @param apiId API identifier
     * @param policy CORS policy configuration containing:
     *               - allowed_origins: List of allowed origins
     *               - allowed_methods: List of allowed HTTP methods
     *               - allowed_headers: List of allowed headers
     *               - expose_headers: List of headers to expose
     *               - max_age: Preflight cache duration in seconds
     *               - allow_credentials: Whether to allow credentials
     * @return true if policy applied successfully, false otherwise
     */
    public boolean apply(String apiId, Map<String, Object> policy) {
        try {
            logger.info("Applying CORS policy to API: {}", apiId);

            // Extract policy parameters
            List<String> allowedOrigins = (List<String>) policy.getOrDefault("allowed_origins", List.of("*"));
            List<String> allowedMethods = (List<String>) policy.getOrDefault("allowed_methods", 
                List.of("GET", "POST", "PUT", "DELETE"));
            List<String> allowedHeaders = (List<String>) policy.getOrDefault("allowed_headers", 
                List.of("Content-Type", "Authorization"));
            List<String> exposeHeaders = (List<String>) policy.getOrDefault("expose_headers", List.of());
            Integer maxAge = (Integer) policy.getOrDefault("max_age", 3600);
            Boolean allowCredentials = (Boolean) policy.getOrDefault("allow_credentials", true);

            // Create CORS configuration
            CorsConfiguration config = new CorsConfiguration(
                apiId,
                allowedOrigins,
                allowedMethods,
                allowedHeaders,
                exposeHeaders,
                maxAge,
                allowCredentials
            );

            // Store the policy
            activePolicies.put(apiId, config);

            logger.info("CORS policy applied successfully to API {}: Origins={}, Methods={}", 
                apiId, allowedOrigins, allowedMethods);

            return true;

        } catch (Exception e) {
            logger.error("Failed to apply CORS policy to API {}: {}", apiId, e.getMessage(), e);
            return false;
        }
    }

    /**
     * Remove CORS policy from an API.
     *
     * @param apiId API identifier
     * @return true if policy removed successfully, false otherwise
     */
    public boolean remove(String apiId) {
        try {
            logger.info("Removing CORS policy from API: {}", apiId);

            CorsConfiguration removed = activePolicies.remove(apiId);

            if (removed != null) {
                logger.info("CORS policy removed successfully from API: {}", apiId);
                return true;
            } else {
                logger.warn("No CORS policy found for API: {}", apiId);
                return false;
            }

        } catch (Exception e) {
            logger.error("Failed to remove CORS policy from API {}: {}", apiId, e.getMessage(), e);
            return false;
        }
    }

    /**
     * Get the active CORS policy for an API.
     *
     * @param apiId API identifier
     * @return CorsConfiguration if found, null otherwise
     */
    public CorsConfiguration getPolicy(String apiId) {
        return activePolicies.get(apiId);
    }

    /**
     * Check if an API has an active CORS policy.
     *
     * @param apiId API identifier
     * @return true if policy exists, false otherwise
     */
    public boolean hasPolicy(String apiId) {
        return activePolicies.containsKey(apiId);
    }

    /**
     * Inner class representing CORS configuration for an API.
     */
    public static class CorsConfiguration {
        private final String apiId;
        private final List<String> allowedOrigins;
        private final List<String> allowedMethods;
        private final List<String> allowedHeaders;
        private final List<String> exposeHeaders;
        private final int maxAge;
        private final boolean allowCredentials;

        public CorsConfiguration(
                String apiId,
                List<String> allowedOrigins,
                List<String> allowedMethods,
                List<String> allowedHeaders,
                List<String> exposeHeaders,
                int maxAge,
                boolean allowCredentials) {
            this.apiId = apiId;
            this.allowedOrigins = allowedOrigins;
            this.allowedMethods = allowedMethods;
            this.allowedHeaders = allowedHeaders;
            this.exposeHeaders = exposeHeaders;
            this.maxAge = maxAge;
            this.allowCredentials = allowCredentials;
        }

        public String getApiId() {
            return apiId;
        }

        public List<String> getAllowedOrigins() {
            return allowedOrigins;
        }

        public List<String> getAllowedMethods() {
            return allowedMethods;
        }

        public List<String> getAllowedHeaders() {
            return allowedHeaders;
        }

        public List<String> getExposeHeaders() {
            return exposeHeaders;
        }

        public int getMaxAge() {
            return maxAge;
        }

        public boolean isAllowCredentials() {
            return allowCredentials;
        }
    }
}

// Made with Bob