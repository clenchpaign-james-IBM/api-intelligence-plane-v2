package com.example.gateway.policy;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Input validation policy engine for managing request/response validation at the gateway level.
 * Handles schema validation, content type validation, size limits, and sanitization rules.
 */
@Component
public class ValidationPolicy {

    private static final Logger logger = LoggerFactory.getLogger(ValidationPolicy.class);

    // Store active validation policies per API
    private final Map<String, ValidationConfiguration> activePolicies = new ConcurrentHashMap<>();

    /**
     * Apply a validation policy to an API.
     *
     * @param apiId API identifier
     * @param policy Validation policy configuration containing:
     *               - schema_validation: Enable schema validation
     *               - content_type_validation: Enable content type validation
     *               - size_limits: Request/response size limits
     *               - sanitization_rules: Input sanitization rules
     * @return true if policy applied successfully, false otherwise
     */
    public boolean apply(String apiId, Map<String, Object> policy) {
        try {
            logger.info("Applying validation policy to API: {}", apiId);

            // Extract policy parameters
            Boolean schemaValidation = (Boolean) policy.getOrDefault("schema_validation", true);
            Boolean contentTypeValidation = (Boolean) policy.getOrDefault("content_type_validation", true);
            Map<String, Object> sizeLimits = (Map<String, Object>) policy.getOrDefault("size_limits", 
                Map.of("request", 10485760, "response", 10485760)); // 10MB default
            List<String> sanitizationRules = (List<String>) policy.getOrDefault("sanitization_rules", 
                List.of("strip_html", "escape_sql"));

            // Create validation configuration
            ValidationConfiguration config = new ValidationConfiguration(
                apiId,
                schemaValidation,
                contentTypeValidation,
                sizeLimits,
                sanitizationRules
            );

            // Store the policy
            activePolicies.put(apiId, config);

            logger.info("Validation policy applied successfully to API {}: Schema={}, ContentType={}", 
                apiId, schemaValidation, contentTypeValidation);

            return true;

        } catch (Exception e) {
            logger.error("Failed to apply validation policy to API {}: {}", apiId, e.getMessage(), e);
            return false;
        }
    }

    /**
     * Remove validation policy from an API.
     *
     * @param apiId API identifier
     * @return true if policy removed successfully, false otherwise
     */
    public boolean remove(String apiId) {
        try {
            logger.info("Removing validation policy from API: {}", apiId);

            ValidationConfiguration removed = activePolicies.remove(apiId);

            if (removed != null) {
                logger.info("Validation policy removed successfully from API: {}", apiId);
                return true;
            } else {
                logger.warn("No validation policy found for API: {}", apiId);
                return false;
            }

        } catch (Exception e) {
            logger.error("Failed to remove validation policy from API {}: {}", apiId, e.getMessage(), e);
            return false;
        }
    }

    /**
     * Get the active validation policy for an API.
     *
     * @param apiId API identifier
     * @return ValidationConfiguration if found, null otherwise
     */
    public ValidationConfiguration getPolicy(String apiId) {
        return activePolicies.get(apiId);
    }

    /**
     * Check if an API has an active validation policy.
     *
     * @param apiId API identifier
     * @return true if policy exists, false otherwise
     */
    public boolean hasPolicy(String apiId) {
        return activePolicies.containsKey(apiId);
    }

    /**
     * Inner class representing validation configuration for an API.
     */
    public static class ValidationConfiguration {
        private final String apiId;
        private final boolean schemaValidation;
        private final boolean contentTypeValidation;
        private final Map<String, Object> sizeLimits;
        private final List<String> sanitizationRules;

        public ValidationConfiguration(
                String apiId,
                boolean schemaValidation,
                boolean contentTypeValidation,
                Map<String, Object> sizeLimits,
                List<String> sanitizationRules) {
            this.apiId = apiId;
            this.schemaValidation = schemaValidation;
            this.contentTypeValidation = contentTypeValidation;
            this.sizeLimits = sizeLimits;
            this.sanitizationRules = sanitizationRules;
        }

        public String getApiId() {
            return apiId;
        }

        public boolean isSchemaValidation() {
            return schemaValidation;
        }

        public boolean isContentTypeValidation() {
            return contentTypeValidation;
        }

        public Map<String, Object> getSizeLimits() {
            return sizeLimits;
        }

        public List<String> getSanitizationRules() {
            return sanitizationRules;
        }
    }
}

// Made with Bob