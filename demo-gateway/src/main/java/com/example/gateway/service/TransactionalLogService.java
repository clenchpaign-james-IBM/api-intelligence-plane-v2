package com.example.gateway.service;

import com.example.gateway.model.API;
import org.opensearch.client.opensearch.OpenSearchClient;
import org.opensearch.client.opensearch._types.OpenSearchException;
import org.opensearch.client.opensearch._types.SortOrder;
import org.opensearch.client.opensearch.core.IndexRequest;
import org.opensearch.client.opensearch.core.IndexResponse;
import org.opensearch.client.opensearch.core.SearchRequest;
import org.opensearch.client.opensearch.core.SearchResponse;
import org.opensearch.client.opensearch.core.search.Hit;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneOffset;
import java.time.format.DateTimeParseException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class TransactionalLogService {

    private static final Logger logger = LoggerFactory.getLogger(TransactionalLogService.class);

    private final OpenSearchClient client;
    private final APIService apiService;
    private final String transactionalLogsIndexPrefix;
    private final String gatewayId;
    private final String gatewayName;

    public TransactionalLogService(
            OpenSearchClient client,
            APIService apiService,
            @Value("${opensearch.indices.transactional-logs:transactional-logs}") String transactionalLogsIndexPrefix,
            @Value("${gateway.id:demo-gateway-001}") String gatewayId,
            @Value("${gateway.name:Demo API Gateway}") String gatewayName) {
        this.client = client;
        this.apiService = apiService;
        this.transactionalLogsIndexPrefix = transactionalLogsIndexPrefix;
        this.gatewayId = gatewayId;
        this.gatewayName = gatewayName;
    }

    public Map<String, Object> createTransactionalEvent(
            String apiId,
            String requestPath,
            String httpMethod,
            String clientIp,
            String userAgent,
            int statusCode,
            int totalTimeMs,
            int gatewayTimeMs,
            int backendTimeMs,
            int requestSize,
            int responseSize,
            String correlationId,
            Map<String, Object> requestHeaders,
            Map<String, Object> responseHeaders,
            Map<String, Object> queryParameters) {

        API api = apiService.getAPI(apiId).orElseGet(() -> buildFallbackApi(apiId, requestPath));

        long timestamp = Instant.now().toEpochMilli();
        Map<String, Object> event = new HashMap<>();
        event.put("event_type", "transactional");
        event.put("timestamp", timestamp);
        event.put("api_id", apiId);
        event.put("api_name", api.getName());
        event.put("api_version", api.getVersion() != null ? api.getVersion() : "1.0.0");
        event.put("operation", requestPath);
        event.put("http_method", httpMethod);
        event.put("request_path", requestPath);
        event.put("request_headers", sanitizeMap(requestHeaders));
        event.put("request_payload", null);
        event.put("request_size", Math.max(requestSize, 0));
        event.put("query_parameters", sanitizeMap(queryParameters));
        event.put("status_code", statusCode);
        event.put("response_headers", sanitizeMap(responseHeaders));
        event.put("response_payload", null);
        event.put("response_size", Math.max(responseSize, 0));
        event.put("client_id", deriveClientId(userAgent, clientIp));
        event.put("client_name", deriveClientName(userAgent));
        event.put("client_ip", clientIp != null ? clientIp : "unknown");
        event.put("user_agent", userAgent);
        event.put("total_time_ms", Math.max(totalTimeMs, 0));
        event.put("gateway_time_ms", Math.max(gatewayTimeMs, 0));
        event.put("backend_time_ms", Math.max(backendTimeMs, 0));
        event.put("status", statusCode >= 500 ? "failure" : "success");
        event.put("correlation_id", correlationId);
        event.put("session_id", null);
        event.put("trace_id", correlationId);
        event.put("cache_status", "disabled");
        event.put("backend_url", api.getBasePath() != null ? api.getBasePath() : requestPath);
        event.put("backend_method", httpMethod);
        event.put("backend_request_headers", sanitizeMap(requestHeaders));
        event.put("backend_response_headers", sanitizeMap(responseHeaders));
        event.put("error_origin", statusCode >= 500 ? "backend" : null);
        event.put("error_message", statusCode >= 500 ? "Backend request failed" : null);
        event.put("error_code", statusCode >= 500 ? "HTTP_" + statusCode : null);
        event.put("external_calls", List.of());
        event.put("gateway_id", gatewayId);
        event.put("gateway_node", gatewayName);
        event.put("vendor_metadata", Map.of("source", "demo-gateway"));
        event.put("created_at", Instant.now().toString());

        return event;
    }

    public void storeTransactionalEvent(Map<String, Object> event) {
        try {
            String indexName = resolveIndexName(extractEventInstant(event));
            IndexRequest<Map<String, Object>> request = IndexRequest.of(i -> i
                .index(indexName)
                .document(event)
            );

            IndexResponse response = client.index(request);
            logger.debug("Stored transactional event in {} with result {}", indexName, response.result());
        } catch (OpenSearchException | IOException e) {
            logger.error("Failed to store transactional event: {}", e.getMessage());
        }
    }

    public Map<String, Object> recordTransactionalEvent(
            String apiId,
            String requestPath,
            String httpMethod,
            String clientIp,
            String userAgent,
            int statusCode,
            int totalTimeMs,
            int gatewayTimeMs,
            int backendTimeMs,
            int requestSize,
            int responseSize,
            String correlationId,
            Map<String, Object> requestHeaders,
            Map<String, Object> responseHeaders,
            Map<String, Object> queryParameters) {

        Map<String, Object> event = createTransactionalEvent(
            apiId,
            requestPath,
            httpMethod,
            clientIp,
            userAgent,
            statusCode,
            totalTimeMs,
            gatewayTimeMs,
            backendTimeMs,
            requestSize,
            responseSize,
            correlationId,
            requestHeaders,
            responseHeaders,
            queryParameters
        );
        storeTransactionalEvent(event);
        return event;
    }

    public Map<String, Object> getTransactionalLogs(
            String apiId,
            Instant startTime,
            Instant endTime,
            int limit,
            int offset) {

        try {
            SearchRequest request = SearchRequest.of(s -> s
                .index(transactionalLogsIndexPrefix + "-*")
                .from(offset)
                .size(limit)
                .sort(sort -> sort.field(f -> f.field("timestamp").order(SortOrder.Desc)))
                .query(q -> q.bool(b -> {
                    b.must(m -> m.range(r -> r.field("timestamp")
                        .gte(org.opensearch.client.json.JsonData.of(startTime.toString()))
                        .lte(org.opensearch.client.json.JsonData.of(endTime.toString()))));
                    if (apiId != null && !apiId.isBlank()) {
                        b.must(m -> m.term(t -> t.field("api_id").value(v -> v.stringValue(apiId))));
                    }
                    return b;
                }))
            );

            SearchResponse<Map> response = client.search(request, Map.class);

            List<Map<String, Object>> items = new ArrayList<>();
            for (Hit<Map> hit : response.hits().hits()) {
                if (hit.source() != null) {
                    @SuppressWarnings("unchecked")
                    Map<String, Object> source = new HashMap<>((Map<String, Object>) hit.source());
                    items.add(source);
                }
            }

            long total = response.hits().total() != null ? response.hits().total().value() : items.size();

            Map<String, Object> result = new HashMap<>();
            result.put("items", items);
            result.put("total", total);
            result.put("limit", limit);
            result.put("offset", offset);
            result.put("gateway_id", gatewayId);
            return result;
        } catch (OpenSearchException | IOException e) {
            logger.error("Failed to query transactional logs: {}", e.getMessage());

            Map<String, Object> errorResult = new HashMap<>();
            errorResult.put("items", List.of());
            errorResult.put("total", 0);
            errorResult.put("limit", limit);
            errorResult.put("offset", offset);
            errorResult.put("gateway_id", gatewayId);
            errorResult.put("error", e.getMessage());
            return errorResult;
        }
    }

    private API buildFallbackApi(String apiId, String requestPath) {
        API api = new API();
        api.setId(apiId);
        api.setName("Unknown API");
        api.setBasePath(requestPath != null ? requestPath : "/");
        api.setVersion("1.0.0");
        return api;
    }

    private Map<String, Object> sanitizeMap(Map<String, Object> value) {
        return value != null ? new HashMap<>(value) : new HashMap<>();
    }

    private String deriveClientId(String userAgent, String clientIp) {
        if (userAgent != null && !userAgent.isBlank()) {
            return userAgent.toLowerCase().contains("mozilla") ? "browser-client" : "service-client";
        }
        if (clientIp != null && !clientIp.isBlank()) {
            return "client-" + clientIp.replace(":", "-").replace(".", "-");
        }
        return "unknown-client";
    }

    private String deriveClientName(String userAgent) {
        if (userAgent == null || userAgent.isBlank()) {
            return "Unknown Client";
        }
        if (userAgent.toLowerCase().contains("mozilla")) {
            return "Browser Client";
        }
        return "Service Client";
    }

    private Instant extractEventInstant(Map<String, Object> event) {
        Object rawTimestamp = event.get("timestamp");
        if (rawTimestamp instanceof Number number) {
            return Instant.ofEpochMilli(number.longValue());
        }
        if (rawTimestamp instanceof String value) {
            try {
                return Instant.parse(value);
            } catch (DateTimeParseException ignored) {
                return Instant.now();
            }
        }
        return Instant.now();
    }

    private String resolveIndexName(Instant eventTime) {
        LocalDate date = eventTime.atZone(ZoneOffset.UTC).toLocalDate();
        return transactionalLogsIndexPrefix + "-" + date;
    }
}

// Made with Bob
