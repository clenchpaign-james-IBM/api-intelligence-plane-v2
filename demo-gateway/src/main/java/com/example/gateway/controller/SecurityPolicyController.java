package com.example.gateway.controller;

import com.example.gateway.policy.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

/**
 * REST controller for managing security policies (authentication, authorization, TLS, CORS, validation, security headers).
 * Provides endpoints for applying and removing security policies on APIs.
 */
@RestController
@RequestMapping("/policies")
public class SecurityPolicyController {

    private static final Logger logger = LoggerFactory.getLogger(SecurityPolicyController.class);

    private final AuthenticationPolicy authenticationPolicy;
    private final AuthorizationPolicy authorizationPolicy;
    private final TlsPolicy tlsPolicy;
    private final CorsPolicy corsPolicy;
    private final ValidationPolicy validationPolicy;
    private final SecurityHeadersPolicy securityHeadersPolicy;

    public SecurityPolicyController(
            AuthenticationPolicy authenticationPolicy,
            AuthorizationPolicy authorizationPolicy,
            TlsPolicy tlsPolicy,
            CorsPolicy corsPolicy,
            ValidationPolicy validationPolicy,
            SecurityHeadersPolicy securityHeadersPolicy) {
        this.authenticationPolicy = authenticationPolicy;
        this.authorizationPolicy = authorizationPolicy;
        this.tlsPolicy = tlsPolicy;
        this.corsPolicy = corsPolicy;
        this.validationPolicy = validationPolicy;
        this.securityHeadersPolicy = securityHeadersPolicy;
    }

    /**
     * Apply authentication policy to an API.
     *
     * @param request Request containing apiId and policy configuration
     * @return Response with success status
     */
    @PostMapping("/authentication")
    public ResponseEntity<Map<String, Object>> applyAuthenticationPolicy(
            @RequestBody Map<String, Object> request) {
        
        String apiId = (String) request.get("apiId");
        Map<String, Object> policy = (Map<String, Object>) request.get("policy");
        
        logger.info("Applying authentication policy to API: {}", apiId);
        
        try {
            boolean success = authenticationPolicy.apply(apiId, policy);
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", success);
            response.put("apiId", apiId);
            response.put("policyType", "authentication");
            response.put("message", success ? 
                "Authentication policy applied successfully" : 
                "Failed to apply authentication policy");
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            logger.error("Error applying authentication policy to API {}: {}", apiId, e.getMessage());
            
            Map<String, Object> errorResponse = new HashMap<>();
            errorResponse.put("success", false);
            errorResponse.put("apiId", apiId);
            errorResponse.put("error", e.getMessage());
            
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
        }
    }

    /**
     * Apply authorization policy to an API.
     *
     * @param request Request containing apiId and policy configuration
     * @return Response with success status
     */
    @PostMapping("/authorization")
    public ResponseEntity<Map<String, Object>> applyAuthorizationPolicy(
            @RequestBody Map<String, Object> request) {
        
        String apiId = (String) request.get("apiId");
        Map<String, Object> policy = (Map<String, Object>) request.get("policy");
        
        logger.info("Applying authorization policy to API: {}", apiId);
        
        try {
            boolean success = authorizationPolicy.apply(apiId, policy);
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", success);
            response.put("apiId", apiId);
            response.put("policyType", "authorization");
            response.put("message", success ? 
                "Authorization policy applied successfully" : 
                "Failed to apply authorization policy");
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            logger.error("Error applying authorization policy to API {}: {}", apiId, e.getMessage());
            
            Map<String, Object> errorResponse = new HashMap<>();
            errorResponse.put("success", false);
            errorResponse.put("apiId", apiId);
            errorResponse.put("error", e.getMessage());
            
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
        }
    }

    /**
     * Apply TLS policy to an API.
     *
     * @param request Request containing apiId and policy configuration
     * @return Response with success status
     */
    @PostMapping("/tls")
    public ResponseEntity<Map<String, Object>> applyTlsPolicy(
            @RequestBody Map<String, Object> request) {
        
        String apiId = (String) request.get("apiId");
        Map<String, Object> policy = (Map<String, Object>) request.get("policy");
        
        logger.info("Applying TLS policy to API: {}", apiId);
        
        try {
            boolean success = tlsPolicy.apply(apiId, policy);
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", success);
            response.put("apiId", apiId);
            response.put("policyType", "tls");
            response.put("message", success ? 
                "TLS policy applied successfully" : 
                "Failed to apply TLS policy");
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            logger.error("Error applying TLS policy to API {}: {}", apiId, e.getMessage());
            
            Map<String, Object> errorResponse = new HashMap<>();
            errorResponse.put("success", false);
            errorResponse.put("apiId", apiId);
            errorResponse.put("error", e.getMessage());
            
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
        }
    }

    /**
     * Apply CORS policy to an API.
     *
     * @param request Request containing apiId and policy configuration
     * @return Response with success status
     */
    @PostMapping("/cors")
    public ResponseEntity<Map<String, Object>> applyCorsPolicy(
            @RequestBody Map<String, Object> request) {
        
        String apiId = (String) request.get("apiId");
        Map<String, Object> policy = (Map<String, Object>) request.get("policy");
        
        logger.info("Applying CORS policy to API: {}", apiId);
        
        try {
            boolean success = corsPolicy.apply(apiId, policy);
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", success);
            response.put("apiId", apiId);
            response.put("policyType", "cors");
            response.put("message", success ? 
                "CORS policy applied successfully" : 
                "Failed to apply CORS policy");
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            logger.error("Error applying CORS policy to API {}: {}", apiId, e.getMessage());
            
            Map<String, Object> errorResponse = new HashMap<>();
            errorResponse.put("success", false);
            errorResponse.put("apiId", apiId);
            errorResponse.put("error", e.getMessage());
            
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
        }
    }

    /**
     * Apply validation policy to an API.
     *
     * @param request Request containing apiId and policy configuration
     * @return Response with success status
     */
    @PostMapping("/validation")
    public ResponseEntity<Map<String, Object>> applyValidationPolicy(
            @RequestBody Map<String, Object> request) {
        
        String apiId = (String) request.get("apiId");
        Map<String, Object> policy = (Map<String, Object>) request.get("policy");
        
        logger.info("Applying validation policy to API: {}", apiId);
        
        try {
            boolean success = validationPolicy.apply(apiId, policy);
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", success);
            response.put("apiId", apiId);
            response.put("policyType", "validation");
            response.put("message", success ? 
                "Validation policy applied successfully" : 
                "Failed to apply validation policy");
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            logger.error("Error applying validation policy to API {}: {}", apiId, e.getMessage());
            
            Map<String, Object> errorResponse = new HashMap<>();
            errorResponse.put("success", false);
            errorResponse.put("apiId", apiId);
            errorResponse.put("error", e.getMessage());
            
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
        }
    }

    /**
     * Apply security headers policy to an API.
     *
     * @param request Request containing apiId and policy configuration
     * @return Response with success status
     */
    @PostMapping("/security-headers")
    public ResponseEntity<Map<String, Object>> applySecurityHeadersPolicy(
            @RequestBody Map<String, Object> request) {
        
        String apiId = (String) request.get("apiId");
        Map<String, Object> policy = (Map<String, Object>) request.get("policy");
        
        logger.info("Applying security headers policy to API: {}", apiId);
        
        try {
            boolean success = securityHeadersPolicy.apply(apiId, policy);
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", success);
            response.put("apiId", apiId);
            response.put("policyType", "security-headers");
            response.put("message", success ? 
                "Security headers policy applied successfully" : 
                "Failed to apply security headers policy");
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            logger.error("Error applying security headers policy to API {}: {}", apiId, e.getMessage());
            
            Map<String, Object> errorResponse = new HashMap<>();
            errorResponse.put("success", false);
            errorResponse.put("apiId", apiId);
            errorResponse.put("error", e.getMessage());
            
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
        }
    }
}

// Made with Bob