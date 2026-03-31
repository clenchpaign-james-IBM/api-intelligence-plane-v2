package com.example.gateway.policy;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Authentication policy engine for managing authentication at the gateway level.
 * Handles OAuth2, JWT, API keys, and other authentication mechanisms.
 */
@Component
public class AuthenticationPolicy {

    private static final Logger logger = LoggerFactory.getLogger(AuthenticationPolicy.class);

    // Store active authentication policies per API
    private final Map<String, AuthenticationConfiguration> activePolicies = new ConcurrentHashMap<>();

    /**
     * Apply an authentication policy to an API.
     *
     * @param apiId API identifier
     * @param policy Authentication policy configuration containing:
     *               - auth_type: Type of authentication (oauth2, jwt, api_key, basic)
     *               - provider: Authentication provider
     *               - scopes: Required OAuth2 scopes
     *               - validation_rules: Token validation rules
     * @return true if policy applied successfully, false otherwise
     */
    public boolean apply(String apiId, Map<String, Object> policy) {
        try {
            logger.info("Applying authentication policy to API: {}", apiId);

            // Extract policy parameters
            String authType = (String) policy.getOrDefault("auth_type", "oauth2");
            String provider = (String) policy.getOrDefault("provider", "default");
            String[] scopes = policy.containsKey("scopes") ? 
                ((String) policy.get("scopes")).split(",") : 
                new String[]{"read", "write"};
            Map<String, Object> validationRules = (Map<String, Object>) policy.get("validation_rules");

            // Create authentication configuration
            AuthenticationConfiguration config = new AuthenticationConfiguration(
                apiId,
                authType,
                provider,
                scopes,
                validationRules
            );

            // Store the policy
            activePolicies.put(apiId, config);

            logger.info("Authentication policy applied successfully to API {}: Type={}, Provider={}", 
                apiId, authType, provider);

            return true;

        } catch (Exception e) {
            logger.error("Failed to apply authentication policy to API {}: {}", apiId, e.getMessage(), e);
            return false;
        }
    }

    /**
     * Remove authentication policy from an API.
     *
     * @param apiId API identifier
     * @return true if policy removed successfully, false otherwise
     */
    public boolean remove(String apiId) {
        try {
            logger.info("Removing authentication policy from API: {}", apiId);

            AuthenticationConfiguration removed = activePolicies.remove(apiId);

            if (removed != null) {
                logger.info("Authentication policy removed successfully from API: {}", apiId);
                return true;
            } else {
                logger.warn("No authentication policy found for API: {}", apiId);
                return false;
            }

        } catch (Exception e) {
            logger.error("Failed to remove authentication policy from API {}: {}", apiId, e.getMessage(), e);
            return false;
        }
    }

    /**
     * Get the active authentication policy for an API.
     *
     * @param apiId API identifier
     * @return AuthenticationConfiguration if found, null otherwise
     */
    public AuthenticationConfiguration getPolicy(String apiId) {
        return activePolicies.get(apiId);
    }

    /**
     * Check if an API has an active authentication policy.
     *
     * @param apiId API identifier
     * @return true if policy exists, false otherwise
     */
    public boolean hasPolicy(String apiId) {
        return activePolicies.containsKey(apiId);
    }

    /**
     * Inner class representing authentication configuration for an API.
     */
    public static class AuthenticationConfiguration {
        private final String apiId;
        private final String authType;
        private final String provider;
        private final String[] scopes;
        private final Map<String, Object> validationRules;

        public AuthenticationConfiguration(
                String apiId,
                String authType,
                String provider,
                String[] scopes,
                Map<String, Object> validationRules) {
            this.apiId = apiId;
            this.authType = authType;
            this.provider = provider;
            this.scopes = scopes;
            this.validationRules = validationRules;
        }

        public String getApiId() {
            return apiId;
        }

        public String getAuthType() {
            return authType;
        }

        public String getProvider() {
            return provider;
        }

        public String[] getScopes() {
            return scopes;
        }

        public Map<String, Object> getValidationRules() {
            return validationRules;
        }
    }
}

// Made with Bob