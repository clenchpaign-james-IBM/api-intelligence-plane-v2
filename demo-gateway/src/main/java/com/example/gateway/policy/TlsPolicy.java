package com.example.gateway.policy;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * TLS/HTTPS policy engine for managing transport security at the gateway level.
 * Handles HTTPS enforcement, TLS version requirements, and cipher suite configuration.
 */
@Component
public class TlsPolicy {

    private static final Logger logger = LoggerFactory.getLogger(TlsPolicy.class);

    // Store active TLS policies per API
    private final Map<String, TlsConfiguration> activePolicies = new ConcurrentHashMap<>();

    /**
     * Apply a TLS policy to an API.
     *
     * @param apiId API identifier
     * @param policy TLS policy configuration containing:
     *               - enforce_https: Whether to enforce HTTPS
     *               - min_tls_version: Minimum TLS version (1.2, 1.3)
     *               - cipher_suites: Allowed cipher suites
     *               - hsts_enabled: Enable HTTP Strict Transport Security
     * @return true if policy applied successfully, false otherwise
     */
    public boolean apply(String apiId, Map<String, Object> policy) {
        try {
            logger.info("Applying TLS policy to API: {}", apiId);

            // Extract policy parameters
            Boolean enforceHttps = (Boolean) policy.getOrDefault("enforce_https", true);
            String minTlsVersion = (String) policy.getOrDefault("min_tls_version", "1.2");
            String[] cipherSuites = policy.containsKey("cipher_suites") ? 
                ((String) policy.get("cipher_suites")).split(",") : 
                new String[]{"TLS_AES_128_GCM_SHA256", "TLS_AES_256_GCM_SHA384"};
            Boolean hstsEnabled = (Boolean) policy.getOrDefault("hsts_enabled", true);

            // Create TLS configuration
            TlsConfiguration config = new TlsConfiguration(
                apiId,
                enforceHttps,
                minTlsVersion,
                cipherSuites,
                hstsEnabled
            );

            // Store the policy
            activePolicies.put(apiId, config);

            logger.info("TLS policy applied successfully to API {}: HTTPS={}, MinTLS={}, HSTS={}", 
                apiId, enforceHttps, minTlsVersion, hstsEnabled);

            return true;

        } catch (Exception e) {
            logger.error("Failed to apply TLS policy to API {}: {}", apiId, e.getMessage(), e);
            return false;
        }
    }

    /**
     * Remove TLS policy from an API.
     *
     * @param apiId API identifier
     * @return true if policy removed successfully, false otherwise
     */
    public boolean remove(String apiId) {
        try {
            logger.info("Removing TLS policy from API: {}", apiId);

            TlsConfiguration removed = activePolicies.remove(apiId);

            if (removed != null) {
                logger.info("TLS policy removed successfully from API: {}", apiId);
                return true;
            } else {
                logger.warn("No TLS policy found for API: {}", apiId);
                return false;
            }

        } catch (Exception e) {
            logger.error("Failed to remove TLS policy from API {}: {}", apiId, e.getMessage(), e);
            return false;
        }
    }

    /**
     * Get the active TLS policy for an API.
     *
     * @param apiId API identifier
     * @return TlsConfiguration if found, null otherwise
     */
    public TlsConfiguration getPolicy(String apiId) {
        return activePolicies.get(apiId);
    }

    /**
     * Check if an API has an active TLS policy.
     *
     * @param apiId API identifier
     * @return true if policy exists, false otherwise
     */
    public boolean hasPolicy(String apiId) {
        return activePolicies.containsKey(apiId);
    }

    /**
     * Inner class representing TLS configuration for an API.
     */
    public static class TlsConfiguration {
        private final String apiId;
        private final boolean enforceHttps;
        private final String minTlsVersion;
        private final String[] cipherSuites;
        private final boolean hstsEnabled;

        public TlsConfiguration(
                String apiId,
                boolean enforceHttps,
                String minTlsVersion,
                String[] cipherSuites,
                boolean hstsEnabled) {
            this.apiId = apiId;
            this.enforceHttps = enforceHttps;
            this.minTlsVersion = minTlsVersion;
            this.cipherSuites = cipherSuites;
            this.hstsEnabled = hstsEnabled;
        }

        public String getApiId() {
            return apiId;
        }

        public boolean isEnforceHttps() {
            return enforceHttps;
        }

        public String getMinTlsVersion() {
            return minTlsVersion;
        }

        public String[] getCipherSuites() {
            return cipherSuites;
        }

        public boolean isHstsEnabled() {
            return hstsEnabled;
        }
    }
}

// Made with Bob