package com.example.gateway.service;

import com.example.gateway.policy.RateLimitPolicy;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;

/**
 * Rate Limiting Service
 * 
 * Manages rate limiting policies for APIs in the Gateway.
 * Tracks request counts and enforces rate limits based on configured policies.
 */
@Service
public class RateLimitService {
    
    private static final Logger logger = LoggerFactory.getLogger(RateLimitService.class);
    
    // Store active policies by API ID
    private final Map<String, RateLimitPolicy> activePolicies = new ConcurrentHashMap<>();
    
    // Track request counts per API
    private final Map<String, RequestCounter> requestCounters = new ConcurrentHashMap<>();
    
    /**
     * Apply a rate limiting policy to an API
     * 
     * @param apiId API identifier
     * @param policy Rate limiting policy configuration
     * @return true if policy applied successfully
     */
    public boolean applyPolicy(String apiId, RateLimitPolicy policy) {
        try {
            logger.info("Applying rate limit policy '{}' to API {}", policy.getPolicyName(), apiId);
            
            // Validate policy
            if (policy.getLimitThresholds() == null) {
                logger.error("Policy must have limit thresholds defined");
                return false;
            }
            
            // Store policy
            policy.setAppliedAt(Instant.now());
            activePolicies.put(apiId, policy);
            
            // Initialize request counter
            requestCounters.put(apiId, new RequestCounter());
            
            logger.info("Successfully applied rate limit policy to API {}", apiId);
            return true;
            
        } catch (Exception e) {
            logger.error("Failed to apply rate limit policy to API {}: {}", apiId, e.getMessage());
            return false;
        }
    }
    
    /**
     * Remove rate limiting policy from an API
     * 
     * @param apiId API identifier
     * @return true if policy removed successfully
     */
    public boolean removePolicy(String apiId) {
        try {
            logger.info("Removing rate limit policy from API {}", apiId);
            
            activePolicies.remove(apiId);
            requestCounters.remove(apiId);
            
            logger.info("Successfully removed rate limit policy from API {}", apiId);
            return true;
            
        } catch (Exception e) {
            logger.error("Failed to remove rate limit policy from API {}: {}", apiId, e.getMessage());
            return false;
        }
    }
    
    /**
     * Get active policy for an API
     * 
     * @param apiId API identifier
     * @return Active policy or null if none exists
     */
    public RateLimitPolicy getPolicy(String apiId) {
        return activePolicies.get(apiId);
    }
    
    /**
     * Check if a request should be allowed based on rate limits
     * 
     * @param apiId API identifier
     * @return true if request is allowed, false if rate limited
     */
    public boolean allowRequest(String apiId) {
        RateLimitPolicy policy = activePolicies.get(apiId);
        if (policy == null) {
            // No policy, allow request
            return true;
        }
        
        RequestCounter counter = requestCounters.get(apiId);
        if (counter == null) {
            // No counter, allow request
            return true;
        }
        
        // Check rate limits
        RateLimitPolicy.LimitThresholds thresholds = policy.getLimitThresholds();
        long now = System.currentTimeMillis();
        
        // Check requests per second
        if (thresholds.getRequestsPerSecond() != null) {
            int rps = counter.getRequestsInLastSecond(now);
            if (rps >= thresholds.getRequestsPerSecond()) {
                logger.debug("Rate limit exceeded for API {}: {} RPS (limit: {})", 
                    apiId, rps, thresholds.getRequestsPerSecond());
                return handleRateLimitExceeded(policy);
            }
        }
        
        // Check requests per minute
        if (thresholds.getRequestsPerMinute() != null) {
            int rpm = counter.getRequestsInLastMinute(now);
            if (rpm >= thresholds.getRequestsPerMinute()) {
                logger.debug("Rate limit exceeded for API {}: {} RPM (limit: {})", 
                    apiId, rpm, thresholds.getRequestsPerMinute());
                return handleRateLimitExceeded(policy);
            }
        }
        
        // Check concurrent requests
        if (thresholds.getConcurrentRequests() != null) {
            int concurrent = counter.getConcurrentRequests();
            if (concurrent >= thresholds.getConcurrentRequests()) {
                logger.debug("Concurrent request limit exceeded for API {}: {} (limit: {})", 
                    apiId, concurrent, thresholds.getConcurrentRequests());
                return handleRateLimitExceeded(policy);
            }
        }
        
        // Record request
        counter.recordRequest(now);
        
        return true;
    }
    
    /**
     * Mark request as completed (for concurrent request tracking)
     * 
     * @param apiId API identifier
     */
    public void completeRequest(String apiId) {
        RequestCounter counter = requestCounters.get(apiId);
        if (counter != null) {
            counter.completeRequest();
        }
    }
    
    /**
     * Handle rate limit exceeded based on enforcement action
     * 
     * @param policy Rate limiting policy
     * @return true if request should be allowed (queued), false if rejected
     */
    private boolean handleRateLimitExceeded(RateLimitPolicy policy) {
        String action = policy.getEnforcementAction();
        
        switch (action.toLowerCase()) {
            case "reject":
                return false;
            case "throttle":
                // In a real implementation, this would delay the request
                return false;
            case "queue":
                // In a real implementation, this would queue the request
                return true;
            default:
                return false;
        }
    }
    
    /**
     * Get all active policies
     * 
     * @return Map of API ID to active policy
     */
    public Map<String, RateLimitPolicy> getAllPolicies() {
        return new ConcurrentHashMap<>(activePolicies);
    }
    
    /**
     * Request Counter
     * 
     * Tracks request counts and timing for rate limiting
     */
    private static class RequestCounter {
        private final AtomicLong lastRequestTime = new AtomicLong(0);
        private final AtomicInteger requestsInLastSecond = new AtomicInteger(0);
        private final AtomicInteger requestsInLastMinute = new AtomicInteger(0);
        private final AtomicInteger concurrentRequests = new AtomicInteger(0);
        
        private long lastSecondReset = System.currentTimeMillis();
        private long lastMinuteReset = System.currentTimeMillis();
        
        public void recordRequest(long now) {
            lastRequestTime.set(now);
            
            // Reset counters if time windows have passed
            if (now - lastSecondReset >= 1000) {
                requestsInLastSecond.set(0);
                lastSecondReset = now;
            }
            
            if (now - lastMinuteReset >= 60000) {
                requestsInLastMinute.set(0);
                lastMinuteReset = now;
            }
            
            // Increment counters
            requestsInLastSecond.incrementAndGet();
            requestsInLastMinute.incrementAndGet();
            concurrentRequests.incrementAndGet();
        }
        
        public void completeRequest() {
            concurrentRequests.decrementAndGet();
        }
        
        public int getRequestsInLastSecond(long now) {
            if (now - lastSecondReset >= 1000) {
                requestsInLastSecond.set(0);
                lastSecondReset = now;
            }
            return requestsInLastSecond.get();
        }
        
        public int getRequestsInLastMinute(long now) {
            if (now - lastMinuteReset >= 60000) {
                requestsInLastMinute.set(0);
                lastMinuteReset = now;
            }
            return requestsInLastMinute.get();
        }
        
        public int getConcurrentRequests() {
            return Math.max(0, concurrentRequests.get());
        }
    }
}

// Made with Bob
