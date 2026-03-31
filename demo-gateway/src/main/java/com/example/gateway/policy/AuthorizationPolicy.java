package com.example.gateway.policy;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Authorization policy engine for managing access control at the gateway level.
 * Handles RBAC (Role-Based Access Control) and ABAC (Attribute-Based Access Control).
 */
@Component
public class AuthorizationPolicy {

    private static final Logger logger = LoggerFactory.getLogger(AuthorizationPolicy.class);

    // Store active authorization policies per API
    private final Map<String, AuthorizationConfiguration> activePolicies = new ConcurrentHashMap<>();

    /**
     * Apply an authorization policy to an API.
     *
     * @param apiId API identifier
     * @param policy Authorization policy configuration containing:
     *               - policy_type: Type of authorization (rbac, abac)
     *               - roles: List of roles
     *               - permissions: Role-permission mappings
     *               - rules: Authorization rules
     * @return true if policy applied successfully, false otherwise
     */
    public boolean apply(String apiId, Map<String, Object> policy) {
        try {
            logger.info("Applying authorization policy to API: {}", apiId);

            // Extract policy parameters
            String policyType = (String) policy.getOrDefault("policy_type", "rbac");
            List<String> roles = (List<String>) policy.getOrDefault("roles", List.of("user", "admin"));
            Map<String, Object> permissions = (Map<String, Object>) policy.get("permissions");
            List<Map<String, Object>> rules = (List<Map<String, Object>>) policy.get("rules");

            // Create authorization configuration
            AuthorizationConfiguration config = new AuthorizationConfiguration(
                apiId,
                policyType,
                roles,
                permissions,
                rules
            );

            // Store the policy
            activePolicies.put(apiId, config);

            logger.info("Authorization policy applied successfully to API {}: Type={}, Roles={}", 
                apiId, policyType, roles);

            return true;

        } catch (Exception e) {
            logger.error("Failed to apply authorization policy to API {}: {}", apiId, e.getMessage(), e);
            return false;
        }
    }

    /**
     * Remove authorization policy from an API.
     *
     * @param apiId API identifier
     * @return true if policy removed successfully, false otherwise
     */
    public boolean remove(String apiId) {
        try {
            logger.info("Removing authorization policy from API: {}", apiId);

            AuthorizationConfiguration removed = activePolicies.remove(apiId);

            if (removed != null) {
                logger.info("Authorization policy removed successfully from API: {}", apiId);
                return true;
            } else {
                logger.warn("No authorization policy found for API: {}", apiId);
                return false;
            }

        } catch (Exception e) {
            logger.error("Failed to remove authorization policy from API {}: {}", apiId, e.getMessage(), e);
            return false;
        }
    }

    /**
     * Get the active authorization policy for an API.
     *
     * @param apiId API identifier
     * @return AuthorizationConfiguration if found, null otherwise
     */
    public AuthorizationConfiguration getPolicy(String apiId) {
        return activePolicies.get(apiId);
    }

    /**
     * Check if an API has an active authorization policy.
     *
     * @param apiId API identifier
     * @return true if policy exists, false otherwise
     */
    public boolean hasPolicy(String apiId) {
        return activePolicies.containsKey(apiId);
    }

    /**
     * Inner class representing authorization configuration for an API.
     */
    public static class AuthorizationConfiguration {
        private final String apiId;
        private final String policyType;
        private final List<String> roles;
        private final Map<String, Object> permissions;
        private final List<Map<String, Object>> rules;

        public AuthorizationConfiguration(
                String apiId,
                String policyType,
                List<String> roles,
                Map<String, Object> permissions,
                List<Map<String, Object>> rules) {
            this.apiId = apiId;
            this.policyType = policyType;
            this.roles = roles;
            this.permissions = permissions;
            this.rules = rules;
        }

        public String getApiId() {
            return apiId;
        }

        public String getPolicyType() {
            return policyType;
        }

        public List<String> getRoles() {
            return roles;
        }

        public Map<String, Object> getPermissions() {
            return permissions;
        }

        public List<Map<String, Object>> getRules() {
            return rules;
        }
    }
}

// Made with Bob