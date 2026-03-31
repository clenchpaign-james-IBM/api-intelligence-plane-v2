package com.example.gateway.policy;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Security headers policy engine for managing HTTP security headers at the gateway level.
 * Handles HSTS, CSP, X-Frame-Options, X-Content-Type-Options, and other security headers.
 */
@Component
public class SecurityHeadersPolicy {

    private static final Logger logger = LoggerFactory.getLogger(SecurityHeadersPolicy.class);

    // Store active security headers policies per API
    private final Map<String, SecurityHeadersConfiguration> activePolicies = new ConcurrentHashMap<>();

    /**
     * Apply a security headers policy to an API.
     *
     * @param apiId API identifier
     * @param policy Security headers policy configuration containing:
     *               - hsts: HTTP Strict Transport Security header value
     *               - x_frame_options: X-Frame-Options header value
     *               - x_content_type_options: X-Content-Type-Options header value
     *               - csp: Content Security Policy header value
     *               - x_xss_protection: X-XSS-Protection header value
     * @return true if policy applied successfully, false otherwise
     */
    public boolean apply(String apiId, Map<String, Object> policy) {
        try {
            logger.info("Applying security headers policy to API: {}", apiId);

            // Extract policy parameters
            String hsts = (String) policy.getOrDefault("hsts", "max-age=31536000; includeSubDomains");
            String xFrameOptions = (String) policy.getOrDefault("x_frame_options", "DENY");
            String xContentTypeOptions = (String) policy.getOrDefault("x_content_type_options", "nosniff");
            String csp = (String) policy.getOrDefault("csp", "default-src 'self'");
            String xXssProtection = (String) policy.getOrDefault("x_xss_protection", "1; mode=block");

            // Create security headers configuration
            SecurityHeadersConfiguration config = new SecurityHeadersConfiguration(
                apiId,
                hsts,
                xFrameOptions,
                xContentTypeOptions,
                csp,
                xXssProtection
            );

            // Store the policy
            activePolicies.put(apiId, config);

            logger.info("Security headers policy applied successfully to API {}: HSTS={}, CSP={}", 
                apiId, hsts != null, csp != null);

            return true;

        } catch (Exception e) {
            logger.error("Failed to apply security headers policy to API {}: {}", apiId, e.getMessage(), e);
            return false;
        }
    }

    /**
     * Remove security headers policy from an API.
     *
     * @param apiId API identifier
     * @return true if policy removed successfully, false otherwise
     */
    public boolean remove(String apiId) {
        try {
            logger.info("Removing security headers policy from API: {}", apiId);

            SecurityHeadersConfiguration removed = activePolicies.remove(apiId);

            if (removed != null) {
                logger.info("Security headers policy removed successfully from API: {}", apiId);
                return true;
            } else {
                logger.warn("No security headers policy found for API: {}", apiId);
                return false;
            }

        } catch (Exception e) {
            logger.error("Failed to remove security headers policy from API {}: {}", apiId, e.getMessage(), e);
            return false;
        }
    }

    /**
     * Get the active security headers policy for an API.
     *
     * @param apiId API identifier
     * @return SecurityHeadersConfiguration if found, null otherwise
     */
    public SecurityHeadersConfiguration getPolicy(String apiId) {
        return activePolicies.get(apiId);
    }

    /**
     * Check if an API has an active security headers policy.
     *
     * @param apiId API identifier
     * @return true if policy exists, false otherwise
     */
    public boolean hasPolicy(String apiId) {
        return activePolicies.containsKey(apiId);
    }

    /**
     * Inner class representing security headers configuration for an API.
     */
    public static class SecurityHeadersConfiguration {
        private final String apiId;
        private final String hsts;
        private final String xFrameOptions;
        private final String xContentTypeOptions;
        private final String csp;
        private final String xXssProtection;

        public SecurityHeadersConfiguration(
                String apiId,
                String hsts,
                String xFrameOptions,
                String xContentTypeOptions,
                String csp,
                String xXssProtection) {
            this.apiId = apiId;
            this.hsts = hsts;
            this.xFrameOptions = xFrameOptions;
            this.xContentTypeOptions = xContentTypeOptions;
            this.csp = csp;
            this.xXssProtection = xXssProtection;
        }

        public String getApiId() {
            return apiId;
        }

        public String getHsts() {
            return hsts;
        }

        public String getxFrameOptions() {
            return xFrameOptions;
        }

        public String getxContentTypeOptions() {
            return xContentTypeOptions;
        }

        public String getCsp() {
            return csp;
        }

        public String getxXssProtection() {
            return xXssProtection;
        }
    }
}

// Made with Bob