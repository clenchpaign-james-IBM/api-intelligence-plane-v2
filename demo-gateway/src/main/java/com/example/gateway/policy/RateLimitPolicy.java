package com.example.gateway.policy;

import java.time.Instant;
import java.util.List;
import java.util.Map;

/**
 * Rate Limiting Policy
 * 
 * Represents a rate limiting policy that can be applied to APIs in the Gateway.
 * Supports various policy types including fixed, adaptive, priority-based, and burst allowance.
 */
public class RateLimitPolicy {
    
    private String policyId;
    private String policyName;
    private String policyType;
    private LimitThresholds limitThresholds;
    private String enforcementAction;
    private Integer burstAllowance;
    private List<PriorityRule> priorityRules;
    private AdaptationParameters adaptationParameters;
    private List<ConsumerTier> consumerTiers;
    private Instant appliedAt;
    
    // Constructors
    public RateLimitPolicy() {}
    
    public RateLimitPolicy(String policyId, String policyName, String policyType, 
                          LimitThresholds limitThresholds, String enforcementAction) {
        this.policyId = policyId;
        this.policyName = policyName;
        this.policyType = policyType;
        this.limitThresholds = limitThresholds;
        this.enforcementAction = enforcementAction;
        this.appliedAt = Instant.now();
    }
    
    // Getters and Setters
    public String getPolicyId() { return policyId; }
    public void setPolicyId(String policyId) { this.policyId = policyId; }
    
    public String getPolicyName() { return policyName; }
    public void setPolicyName(String policyName) { this.policyName = policyName; }
    
    public String getPolicyType() { return policyType; }
    public void setPolicyType(String policyType) { this.policyType = policyType; }
    
    public LimitThresholds getLimitThresholds() { return limitThresholds; }
    public void setLimitThresholds(LimitThresholds limitThresholds) { this.limitThresholds = limitThresholds; }
    
    public String getEnforcementAction() { return enforcementAction; }
    public void setEnforcementAction(String enforcementAction) { this.enforcementAction = enforcementAction; }
    
    public Integer getBurstAllowance() { return burstAllowance; }
    public void setBurstAllowance(Integer burstAllowance) { this.burstAllowance = burstAllowance; }
    
    public List<PriorityRule> getPriorityRules() { return priorityRules; }
    public void setPriorityRules(List<PriorityRule> priorityRules) { this.priorityRules = priorityRules; }
    
    public AdaptationParameters getAdaptationParameters() { return adaptationParameters; }
    public void setAdaptationParameters(AdaptationParameters adaptationParameters) { 
        this.adaptationParameters = adaptationParameters; 
    }
    
    public List<ConsumerTier> getConsumerTiers() { return consumerTiers; }
    public void setConsumerTiers(List<ConsumerTier> consumerTiers) { this.consumerTiers = consumerTiers; }
    
    public Instant getAppliedAt() { return appliedAt; }
    public void setAppliedAt(Instant appliedAt) { this.appliedAt = appliedAt; }
    
    // Nested Classes
    public static class LimitThresholds {
        private Integer requestsPerSecond;
        private Integer requestsPerMinute;
        private Integer requestsPerHour;
        private Integer concurrentRequests;
        
        public LimitThresholds() {}
        
        public Integer getRequestsPerSecond() { return requestsPerSecond; }
        public void setRequestsPerSecond(Integer requestsPerSecond) { 
            this.requestsPerSecond = requestsPerSecond; 
        }
        
        public Integer getRequestsPerMinute() { return requestsPerMinute; }
        public void setRequestsPerMinute(Integer requestsPerMinute) { 
            this.requestsPerMinute = requestsPerMinute; 
        }
        
        public Integer getRequestsPerHour() { return requestsPerHour; }
        public void setRequestsPerHour(Integer requestsPerHour) { 
            this.requestsPerHour = requestsPerHour; 
        }
        
        public Integer getConcurrentRequests() { return concurrentRequests; }
        public void setConcurrentRequests(Integer concurrentRequests) { 
            this.concurrentRequests = concurrentRequests; 
        }
    }
    
    public static class PriorityRule {
        private String tier;
        private Double multiplier;
        private Integer guaranteedThroughput;
        private Double burstMultiplier;
        
        public PriorityRule() {}
        
        public String getTier() { return tier; }
        public void setTier(String tier) { this.tier = tier; }
        
        public Double getMultiplier() { return multiplier; }
        public void setMultiplier(Double multiplier) { this.multiplier = multiplier; }
        
        public Integer getGuaranteedThroughput() { return guaranteedThroughput; }
        public void setGuaranteedThroughput(Integer guaranteedThroughput) { 
            this.guaranteedThroughput = guaranteedThroughput; 
        }
        
        public Double getBurstMultiplier() { return burstMultiplier; }
        public void setBurstMultiplier(Double burstMultiplier) { this.burstMultiplier = burstMultiplier; }
    }
    
    public static class AdaptationParameters {
        private Double learningRate;
        private Integer adjustmentFrequency;
        private Integer minThreshold;
        private Integer maxThreshold;
        
        public AdaptationParameters() {}
        
        public Double getLearningRate() { return learningRate; }
        public void setLearningRate(Double learningRate) { this.learningRate = learningRate; }
        
        public Integer getAdjustmentFrequency() { return adjustmentFrequency; }
        public void setAdjustmentFrequency(Integer adjustmentFrequency) { 
            this.adjustmentFrequency = adjustmentFrequency; 
        }
        
        public Integer getMinThreshold() { return minThreshold; }
        public void setMinThreshold(Integer minThreshold) { this.minThreshold = minThreshold; }
        
        public Integer getMaxThreshold() { return maxThreshold; }
        public void setMaxThreshold(Integer maxThreshold) { this.maxThreshold = maxThreshold; }
    }
    
    public static class ConsumerTier {
        private String tierName;
        private Integer tierLevel;
        private Double rateMultiplier;
        private Integer priorityScore;
        
        public ConsumerTier() {}
        
        public String getTierName() { return tierName; }
        public void setTierName(String tierName) { this.tierName = tierName; }
        
        public Integer getTierLevel() { return tierLevel; }
        public void setTierLevel(Integer tierLevel) { this.tierLevel = tierLevel; }
        
        public Double getRateMultiplier() { return rateMultiplier; }
        public void setRateMultiplier(Double rateMultiplier) { this.rateMultiplier = rateMultiplier; }
        
        public Integer getPriorityScore() { return priorityScore; }
        public void setPriorityScore(Integer priorityScore) { this.priorityScore = priorityScore; }
    }
}

// Made with Bob
