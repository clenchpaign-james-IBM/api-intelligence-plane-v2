package com.example.gateway.model;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.time.Instant;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * API model representing a registered API in the Demo Gateway.
 * 
 * This model corresponds to the API entity in the API Intelligence Plane
 * data model and is stored in OpenSearch.
 */
public class API {
    
    @JsonProperty("id")
    private String id;
    
    @JsonProperty("name")
    private String name;
    
    @JsonProperty("version")
    private String version;
    
    @JsonProperty("basePath")
    private String basePath;
    
    @JsonProperty("endpoints")
    private List<Endpoint> endpoints = new ArrayList<>();
    
    @JsonProperty("methods")
    private List<String> methods = new ArrayList<>();
    
    @JsonProperty("authenticationType")
    private String authenticationType = "none";
    
    @JsonProperty("authenticationConfig")
    private Map<String, Object> authenticationConfig = new HashMap<>();
    
    @JsonProperty("tags")
    private List<String> tags = new ArrayList<>();
    
    @JsonProperty("isShadow")
    private boolean isShadow = false;
    
    @JsonProperty("status")
    private String status = "active";
    
    @JsonProperty("healthScore")
    private double healthScore = 100.0;
    
    @JsonProperty("currentMetrics")
    private CurrentMetrics currentMetrics;
    
    @JsonProperty("createdAt")
    @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd'T'HH:mm:ss'Z'", timezone = "UTC")
    private Instant createdAt;
    
    @JsonProperty("updatedAt")
    @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd'T'HH:mm:ss'Z'", timezone = "UTC")
    private Instant updatedAt;
    
    // Constructors
    
    public API() {
        this.createdAt = Instant.now();
        this.updatedAt = Instant.now();
        this.currentMetrics = new CurrentMetrics();
    }
    
    public API(String id, String name, String basePath) {
        this();
        this.id = id;
        this.name = name;
        this.basePath = basePath;
    }
    
    // Getters and Setters
    
    public String getId() {
        return id;
    }
    
    public void setId(String id) {
        this.id = id;
    }
    
    public String getName() {
        return name;
    }
    
    public void setName(String name) {
        this.name = name;
    }
    
    public String getVersion() {
        return version;
    }
    
    public void setVersion(String version) {
        this.version = version;
    }
    
    public String getBasePath() {
        return basePath;
    }
    
    public void setBasePath(String basePath) {
        this.basePath = basePath;
    }
    
    public List<Endpoint> getEndpoints() {
        return endpoints;
    }
    
    public void setEndpoints(List<Endpoint> endpoints) {
        this.endpoints = endpoints;
    }
    
    public List<String> getMethods() {
        return methods;
    }
    
    public void setMethods(List<String> methods) {
        this.methods = methods;
    }
    
    public String getAuthenticationType() {
        return authenticationType;
    }
    
    public void setAuthenticationType(String authenticationType) {
        this.authenticationType = authenticationType;
    }
    
    public Map<String, Object> getAuthenticationConfig() {
        return authenticationConfig;
    }
    
    public void setAuthenticationConfig(Map<String, Object> authenticationConfig) {
        this.authenticationConfig = authenticationConfig;
    }
    
    public List<String> getTags() {
        return tags;
    }
    
    public void setTags(List<String> tags) {
        this.tags = tags;
    }
    
    public boolean isShadow() {
        return isShadow;
    }
    
    public void setShadow(boolean shadow) {
        isShadow = shadow;
    }
    
    public String getStatus() {
        return status;
    }
    
    public void setStatus(String status) {
        this.status = status;
    }
    
    public double getHealthScore() {
        return healthScore;
    }
    
    public void setHealthScore(double healthScore) {
        this.healthScore = healthScore;
    }
    
    public CurrentMetrics getCurrentMetrics() {
        return currentMetrics;
    }
    
    public void setCurrentMetrics(CurrentMetrics currentMetrics) {
        this.currentMetrics = currentMetrics;
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
     * Endpoint definition within an API.
     */
    public static class Endpoint {
        @JsonProperty("path")
        private String path;
        
        @JsonProperty("method")
        private String method;
        
        @JsonProperty("description")
        private String description;
        
        @JsonProperty("responseCodes")
        private List<Integer> responseCodes = new ArrayList<>();
        
        public Endpoint() {}
        
        public Endpoint(String path, String method) {
            this.path = path;
            this.method = method;
        }
        
        // Getters and Setters
        
        public String getPath() {
            return path;
        }
        
        public void setPath(String path) {
            this.path = path;
        }
        
        public String getMethod() {
            return method;
        }
        
        public void setMethod(String method) {
            this.method = method;
        }
        
        public String getDescription() {
            return description;
        }
        
        public void setDescription(String description) {
            this.description = description;
        }
        
        public List<Integer> getResponseCodes() {
            return responseCodes;
        }
        
        public void setResponseCodes(List<Integer> responseCodes) {
            this.responseCodes = responseCodes;
        }
    }
    
    /**
     * Current metrics snapshot for an API.
     */
    public static class CurrentMetrics {
        @JsonProperty("responseTimeP50")
        private double responseTimeP50 = 0.0;
        
        @JsonProperty("responseTimeP95")
        private double responseTimeP95 = 0.0;
        
        @JsonProperty("responseTimeP99")
        private double responseTimeP99 = 0.0;
        
        @JsonProperty("errorRate")
        private double errorRate = 0.0;
        
        @JsonProperty("throughput")
        private double throughput = 0.0;
        
        @JsonProperty("availability")
        private double availability = 100.0;
        
        @JsonProperty("measuredAt")
        @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd'T'HH:mm:ss'Z'", timezone = "UTC")
        private Instant measuredAt;
        
        public CurrentMetrics() {
            this.measuredAt = Instant.now();
        }
        
        // Getters and Setters
        
        public double getResponseTimeP50() {
            return responseTimeP50;
        }
        
        public void setResponseTimeP50(double responseTimeP50) {
            this.responseTimeP50 = responseTimeP50;
        }
        
        public double getResponseTimeP95() {
            return responseTimeP95;
        }
        
        public void setResponseTimeP95(double responseTimeP95) {
            this.responseTimeP95 = responseTimeP95;
        }
        
        public double getResponseTimeP99() {
            return responseTimeP99;
        }
        
        public void setResponseTimeP99(double responseTimeP99) {
            this.responseTimeP99 = responseTimeP99;
        }
        
        public double getErrorRate() {
            return errorRate;
        }
        
        public void setErrorRate(double errorRate) {
            this.errorRate = errorRate;
        }
        
        public double getThroughput() {
            return throughput;
        }
        
        public void setThroughput(double throughput) {
            this.throughput = throughput;
        }
        
        public double getAvailability() {
            return availability;
        }
        
        public void setAvailability(double availability) {
            this.availability = availability;
        }
        
        public Instant getMeasuredAt() {
            return measuredAt;
        }
        
        public void setMeasuredAt(Instant measuredAt) {
            this.measuredAt = measuredAt;
        }
    }
}

// Made with Bob
