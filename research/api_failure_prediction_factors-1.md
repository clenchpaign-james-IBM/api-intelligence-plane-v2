# Predicting API Failures 24 Hours in Advance

## 1. Traffic & Usage Patterns

-   Request rate trends (RPS/QPS)
-   Traffic seasonality
-   Burstiness
-   Consumer behavior anomalies

## 2. Latency Degradation Trends

-   P95 / P99 latency trends
-   Latency variance (jitter)
-   Queue wait times

## 3. Error Rate Progression

-   4xx vs 5xx ratio
-   Retry rates
-   Timeout errors
-   Circuit breaker activations

## 4. Dependency Health

-   Downstream service success rates
-   Dependency latency trends
-   SLA adherence

## 5. Resource Utilization Trends

-   CPU usage trends
-   Memory growth
-   Thread pool saturation
-   Connection pool exhaustion

## 6. Retry, Throttling & Backpressure

-   Retry amplification
-   Throttling events (429s)
-   Queue lengths
-   Backpressure signals

## 7. Deployment & Change Events

-   Recent deployments
-   Config changes
-   API version rollouts
-   Feature flags

## 8. Network & Infrastructure Instability

-   Packet loss
-   DNS latency
-   TLS handshake time
-   Cross-region latency

## 9. Security & Anomaly Signals

-   Unauthorized traffic spikes
-   Credential abuse
-   DDoS patterns

## 10. Historical Failure Patterns

-   Pre-failure signatures
-   Time-to-failure trends
-   Correlated metrics

## 11. Derived Signals

-   Rate of change
-   Rolling averages
-   Anomaly scores
-   Lagged features

## 12. System-Level Context

-   API criticality
-   SLA definitions
-   Maintenance windows
-   Business events

## Prediction Strategy

-   Time-series forecasting
-   Anomaly detection
-   Dependency graph analysis
-   Classification models

## Key Insight

Failures are gradual and result from accumulating stress signals across
systems.
