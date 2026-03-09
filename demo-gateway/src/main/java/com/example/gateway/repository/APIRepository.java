package com.example.gateway.repository;

import com.example.gateway.model.API;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.opensearch.client.opensearch.OpenSearchClient;
import org.opensearch.client.opensearch._types.OpenSearchException;
import org.opensearch.client.opensearch.core.*;
import org.opensearch.client.opensearch.core.search.Hit;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Repository;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

/**
 * Repository for API entities in OpenSearch.
 * 
 * Provides CRUD operations and search functionality for APIs
 * stored in the OpenSearch api-inventory index.
 */
@Repository
public class APIRepository {
    
    private static final Logger logger = LoggerFactory.getLogger(APIRepository.class);
    
    private final OpenSearchClient client;
    private final ObjectMapper objectMapper;
    private final String indexName;
    
    public APIRepository(
            OpenSearchClient client,
            ObjectMapper objectMapper,
            @Value("${opensearch.indices.apis:api-inventory}") String indexName) {
        this.client = client;
        this.objectMapper = objectMapper;
        this.indexName = indexName;
    }
    
    /**
     * Save an API to OpenSearch.
     * 
     * @param api API to save
     * @return Saved API with ID
     * @throws IOException if save fails
     */
    public API save(API api) throws IOException {
        try {
            IndexRequest<API> request = IndexRequest.of(i -> i
                .index(indexName)
                .id(api.getId())
                .document(api)
            );
            
            IndexResponse response = client.index(request);
            logger.info("Saved API {} with result: {}", api.getId(), response.result());
            
            return api;
        } catch (OpenSearchException | IOException e) {
            logger.error("Failed to save API {}: {}", api.getId(), e.getMessage());
            throw e;
        }
    }
    
    /**
     * Find an API by ID.
     * 
     * @param id API ID
     * @return Optional containing the API if found
     */
    public Optional<API> findById(String id) {
        try {
            GetRequest request = GetRequest.of(g -> g
                .index(indexName)
                .id(id)
            );
            
            GetResponse<API> response = client.get(request, API.class);
            
            if (response.found()) {
                return Optional.ofNullable(response.source());
            }
            return Optional.empty();
            
        } catch (OpenSearchException | IOException e) {
            logger.error("Failed to find API {}: {}", id, e.getMessage());
            return Optional.empty();
        }
    }
    
    /**
     * Find all APIs.
     * 
     * @return List of all APIs
     */
    public List<API> findAll() {
        try {
            SearchRequest request = SearchRequest.of(s -> s
                .index(indexName)
                .size(1000)
            );
            
            SearchResponse<API> response = client.search(request, API.class);
            
            List<API> apis = new ArrayList<>();
            for (Hit<API> hit : response.hits().hits()) {
                if (hit.source() != null) {
                    apis.add(hit.source());
                }
            }
            
            logger.info("Found {} APIs", apis.size());
            return apis;
            
        } catch (OpenSearchException | IOException e) {
            logger.error("Failed to find all APIs: {}", e.getMessage());
            return new ArrayList<>();
        }
    }
    
    /**
     * Find APIs by status.
     * 
     * @param status API status (active, inactive, deprecated, failed)
     * @return List of APIs with the specified status
     */
    public List<API> findByStatus(String status) {
        try {
            SearchRequest request = SearchRequest.of(s -> s
                .index(indexName)
                .query(q -> q
                    .term(t -> t
                        .field("status")
                        .value(status)
                    )
                )
                .size(1000)
            );
            
            SearchResponse<API> response = client.search(request, API.class);
            
            List<API> apis = new ArrayList<>();
            for (Hit<API> hit : response.hits().hits()) {
                if (hit.source() != null) {
                    apis.add(hit.source());
                }
            }
            
            logger.info("Found {} APIs with status {}", apis.size(), status);
            return apis;
            
        } catch (OpenSearchException | IOException e) {
            logger.error("Failed to find APIs by status {}: {}", status, e.getMessage());
            return new ArrayList<>();
        }
    }
    
    /**
     * Update an API.
     * 
     * @param api API to update
     * @return Updated API
     * @throws IOException if update fails
     */
    public API update(API api) throws IOException {
        try {
            UpdateRequest<API, API> request = UpdateRequest.of(u -> u
                .index(indexName)
                .id(api.getId())
                .doc(api)
            );
            
            UpdateResponse<API> response = client.update(request, API.class);
            logger.info("Updated API {} with result: {}", api.getId(), response.result());
            
            return api;
        } catch (OpenSearchException | IOException e) {
            logger.error("Failed to update API {}: {}", api.getId(), e.getMessage());
            throw e;
        }
    }
    
    /**
     * Delete an API by ID.
     * 
     * @param id API ID
     * @return true if deleted, false otherwise
     */
    public boolean deleteById(String id) {
        try {
            DeleteRequest request = DeleteRequest.of(d -> d
                .index(indexName)
                .id(id)
            );
            
            DeleteResponse response = client.delete(request);
            logger.info("Deleted API {} with result: {}", id, response.result());
            
            return response.result().name().equals("DELETED");
            
        } catch (OpenSearchException | IOException e) {
            logger.error("Failed to delete API {}: {}", id, e.getMessage());
            return false;
        }
    }
    
    /**
     * Check if an API exists by ID.
     * 
     * @param id API ID
     * @return true if exists, false otherwise
     */
    public boolean existsById(String id) {
        try {
            ExistsRequest request = ExistsRequest.of(e -> e
                .index(indexName)
                .id(id)
            );
            
            return client.exists(request).value();
            
        } catch (OpenSearchException | IOException e) {
            logger.error("Failed to check if API {} exists: {}", id, e.getMessage());
            return false;
        }
    }
    
    /**
     * Count total number of APIs.
     * 
     * @return Total count
     */
    public long count() {
        try {
            CountRequest request = CountRequest.of(c -> c
                .index(indexName)
            );
            
            CountResponse response = client.count(request);
            return response.count();
            
        } catch (OpenSearchException | IOException e) {
            logger.error("Failed to count APIs: {}", e.getMessage());
            return 0;
        }
    }
}

// Made with Bob
