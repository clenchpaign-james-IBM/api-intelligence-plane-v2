package com.example.gateway.policy;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Caching policy engine for managing response caching at the gateway level.
 * Handles cache configuration, TTL management, and cache key strategies.
 */
@Component
public class CachingPolicy {

    private static final Logger logger = LoggerFactory.getLogger(CachingPolicy.class);

    // Store active caching policies per API
    private final Map<String, CachingConfiguration> activePolicies = new ConcurrentHashMap<>();

    /**
     * Apply a caching policy to an API.
     *
     * @param apiId API identifier
     * @param policy Caching policy configuration containing:
     *               - ttl_seconds: Cache time-to-live in seconds
     *               - cache_key_strategy: Strategy for generating cache keys
     *               - invalidation_rules: Rules for cache invalidation
     *               - vary_headers: Headers to include in cache key
     * @return true if policy applied successfully, false otherwise
     */
    public boolean apply(String apiId, Map<String, Object> policy) {
        try {
            logger.info("Applying caching policy to API: {}", apiId);

            // Extract policy parameters
            Integer ttlSeconds = (Integer) policy.getOrDefault("ttl_seconds", 300); // Default 5 minutes
            String cacheKeyStrategy = (String) policy.getOrDefault("cache_key_strategy", "url_based");
            Map<String, Object> invalidationRules = (Map<String, Object>) policy.get("invalidation_rules");
            String[] varyHeaders = policy.containsKey("vary_headers") ? 
                ((String) policy.get("vary_headers")).split(",") : 
                new String[]{"Accept", "Accept-Encoding"};

            // Create caching configuration
            CachingConfiguration config = new CachingConfiguration(
                apiId,
                ttlSeconds,
                cacheKeyStrategy,
                invalidationRules,
                varyHeaders
            );

            // Store the policy
            activePolicies.put(apiId, config);

            logger.info("Caching policy applied successfully to API {}: TTL={}s, Strategy={}", 
                apiId, ttlSeconds, cacheKeyStrategy);

            return true;

        } catch (Exception e) {
            logger.error("Failed to apply caching policy to API {}: {}", apiId, e.getMessage(), e);
            return false;
        }
    }

    /**
     * Remove caching policy from an API.
     *
     * @param apiId API identifier
     * @return true if policy removed successfully, false otherwise
     */
    public boolean remove(String apiId) {
        try {
            logger.info("Removing caching policy from API: {}", apiId);

            CachingConfiguration removed = activePolicies.remove(apiId);

            if (removed != null) {
                logger.info("Caching policy removed successfully from API: {}", apiId);
                return true;
            } else {
                logger.warn("No caching policy found for API: {}", apiId);
                return false;
            }

        } catch (Exception e) {
            logger.error("Failed to remove caching policy from API {}: {}", apiId, e.getMessage(), e);
            return false;
        }
    }

    /**
     * Get the active caching policy for an API.
     *
     * @param apiId API identifier
     * @return CachingConfiguration if found, null otherwise
     */
    public CachingConfiguration getPolicy(String apiId) {
        return activePolicies.get(apiId);
    }

    /**
     * Check if an API has an active caching policy.
     *
     * @param apiId API identifier
     * @return true if policy exists, false otherwise
     */
    public boolean hasPolicy(String apiId) {
        return activePolicies.containsKey(apiId);
    }

    /**
     * Inner class representing caching configuration for an API.
     */
    public static class CachingConfiguration {
        private final String apiId;
        private final int ttlSeconds;
        private final String cacheKeyStrategy;
        private final Map<String, Object> invalidationRules;
        private final String[] varyHeaders;

        public CachingConfiguration(
                String apiId,
                int ttlSeconds,
                String cacheKeyStrategy,
                Map<String, Object> invalidationRules,
                String[] varyHeaders) {
            this.apiId = apiId;
            this.ttlSeconds = ttlSeconds;
            this.cacheKeyStrategy = cacheKeyStrategy;
            this.invalidationRules = invalidationRules;
            this.varyHeaders = varyHeaders;
        }

        public String getApiId() {
            return apiId;
        }

        public int getTtlSeconds() {
            return ttlSeconds;
        }

        public String getCacheKeyStrategy() {
            return cacheKeyStrategy;
        }

        public Map<String, Object> getInvalidationRules() {
            return invalidationRules;
        }

        public String[] getVaryHeaders() {
            return varyHeaders;
        }
    }
}

// Made with Bob
