package com.example.gateway.model;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.time.Instant;
import java.util.HashMap;
import java.util.Map;

/**
 * Policy model representing a rate limiting policy in the Demo Gateway.
 * 
 * This model corresponds to the RateLimitPolicy entity in the API Intelligence Plane
 * data model and is stored in OpenSearch.
 */
public class Policy {
    
    @JsonProperty("id")
    private String id;
    
    @JsonProperty("apiId")
    private String apiId;
    
    @JsonProperty("policyName")
    private String policyName;
    
    @JsonProperty("policyType")
    private String policyType = "fixed";
    
    @JsonProperty("status")
    private String status = "inactive";
    
    @JsonProperty("limitThresholds")
    private LimitThresholds limitThresholds;
    
    @JsonProperty("burstAllowance")
    private Integer burstAllowance;
    
    @JsonProperty("enforcementAction")
    private String enforcementAction = "throttle";
    
    @JsonProperty("appliedAt")
    @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd'T'HH:mm:ss'Z'", timezone = "UTC")
    private Instant appliedAt;
    
    @JsonProperty("effectivenessScore")
    private Double effectivenessScore;
    
    @JsonProperty("createdAt")
    @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd'T'HH:mm:ss'Z'", timezone = "UTC")
    private Instant createdAt;
    
    @JsonProperty("updatedAt")
    @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd'T'HH:mm:ss'Z'", timezone = "UTC")
    private Instant updatedAt;
    
    // Constructors
    
    public Policy() {
        this.createdAt = Instant.now();
        this.updatedAt = Instant.now();
        this.limitThresholds = new LimitThresholds();
    }
    
    public Policy(String id, String apiId, String policyName) {
        this();
        this.id = id;
        this.apiId = apiId;
        this.policyName = policyName;
    }
    
    // Getters and Setters
    
    public String getId() {
        return id;
    }
    
    public void setId(String id) {
        this.id = id;
    }
    
    public String getApiId() {
        return apiId;
    }
    
    public void setApiId(String apiId) {
        this.apiId = apiId;
    }
    
    public String getPolicyName() {
        return policyName;
    }
    
    public void setPolicyName(String policyName) {
        this.policyName = policyName;
    }
    
    public String getPolicyType() {
        return policyType;
    }
    
    public void setPolicyType(String policyType) {
        this.policyType = policyType;
    }
    
    public String getStatus() {
        return status;
    }
    
    public void setStatus(String status) {
        this.status = status;
    }
    
    public LimitThresholds getLimitThresholds() {
        return limitThresholds;
    }
    
    public void setLimitThresholds(LimitThresholds limitThresholds) {
        this.limitThresholds = limitThresholds;
    }
    
    public Integer getBurstAllowance() {
        return burstAllowance;
    }
    
    public void setBurstAllowance(Integer burstAllowance) {
        this.burstAllowance = burstAllowance;
    }
    
    public String getEnforcementAction() {
        return enforcementAction;
    }
    
    public void setEnforcementAction(String enforcementAction) {
        this.enforcementAction = enforcementAction;
    }
    
    public Instant getAppliedAt() {
        return appliedAt;
    }
    
    public void setAppliedAt(Instant appliedAt) {
        this.appliedAt = appliedAt;
    }
    
    public Double getEffectivenessScore() {
        return effectivenessScore;
    }
    
    public void setEffectivenessScore(Double effectivenessScore) {
        this.effectivenessScore = effectivenessScore;
    }
    
    public Instant getCreatedAt() {
        return createdAt;
    }
    
    public void setCreatedAt(Instant createdAt) {
        this.createdAt = createdAt;
    }
    
    public Instant getUpdatedAt() {
        return updatedAt;
    }
    
    public void setUpdatedAt(Instant updatedAt) {
        this.updatedAt = updatedAt;
    }
    
    // Nested classes
    
    /**
     * Rate limit threshold values.
     */
    public static class LimitThresholds {
        @JsonProperty("requestsPerSecond")
        private Integer requestsPerSecond;
        
        @JsonProperty("requestsPerMinute")
        private Integer requestsPerMinute;
        
        @JsonProperty("requestsPerHour")
        private Integer requestsPerHour;
        
        @JsonProperty("concurrentRequests")
        private Integer concurrentRequests;
        
        public LimitThresholds() {}
        
        public LimitThresholds(Integer requestsPerSecond, Integer requestsPerMinute, Integer requestsPerHour) {
            this.requestsPerSecond = requestsPerSecond;
            this.requestsPerMinute = requestsPerMinute;
            this.requestsPerHour = requestsPerHour;
        }
        
        // Getters and Setters
        
        public Integer getRequestsPerSecond() {
            return requestsPerSecond;
        }
        
        public void setRequestsPerSecond(Integer requestsPerSecond) {
            this.requestsPerSecond = requestsPerSecond;
        }
        
        public Integer getRequestsPerMinute() {
            return requestsPerMinute;
        }
        
        public void setRequestsPerMinute(Integer requestsPerMinute) {
            this.requestsPerMinute = requestsPerMinute;
        }
        
        public Integer getRequestsPerHour() {
            return requestsPerHour;
        }
        
        public void setRequestsPerHour(Integer requestsPerHour) {
            this.requestsPerHour = requestsPerHour;
        }
        
        public Integer getConcurrentRequests() {
            return concurrentRequests;
        }
        
        public void setConcurrentRequests(Integer concurrentRequests) {
            this.concurrentRequests = concurrentRequests;
        }
    }
}

// Made with Bob
