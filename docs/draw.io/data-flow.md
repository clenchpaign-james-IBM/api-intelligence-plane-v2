# Data Flow Diagrams

## Core Application Data Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Backend
    participant OpenSearch
    participant Gateway
    
    User->>Frontend: Access Dashboard
    Frontend->>Backend: GET /api/v1/apis
    Backend->>OpenSearch: Query api-inventory
    OpenSearch-->>Backend: API List
    Backend-->>Frontend: JSON Response
    Frontend-->>User: Display Dashboard
    
    User->>Frontend: View API Details
    Frontend->>Backend: GET /api/v1/apis/{id}/metrics
    Backend->>OpenSearch: Query api-metrics-*
    OpenSearch-->>Backend: Metrics Data
    Backend-->>Frontend: Time-series Data
    Frontend-->>User: Display Charts
```

## API Discovery Flow

```mermaid
flowchart TD
    Start([Scheduler Trigger<br/>Every 5 minutes]) --> CheckGW{Check<br/>Gateways}
    CheckGW --> |For each gateway| GetAdapter[Get Gateway Adapter<br/>Strategy Pattern]
    GetAdapter --> Connect[Connect to Gateway]
    Connect --> |Success| Discover[Discover APIs<br/>Query Gateway API]
    Connect --> |Failure| LogError[Log Error]
    LogError --> Next{More<br/>Gateways?}
    
    Discover --> Parse[Parse API Metadata<br/>name, version, endpoints]
    Parse --> Compare[Compare with<br/>Existing Inventory]
    Compare --> |New API| AddNew[Add to Inventory<br/>is_shadow: false]
    Compare --> |Existing API| Update[Update Metadata]
    Compare --> |Undocumented| Shadow[Flag as Shadow API<br/>is_shadow: true]
    
    AddNew --> Store[Store in OpenSearch<br/>api-inventory index]
    Update --> Store
    Shadow --> Store
    Store --> Next
    Next --> |Yes| GetAdapter
    Next --> |No| Notify[Notify Frontend<br/>WebSocket/Polling]
    Notify --> End([End])
    
    style Start fill:#e3f2fd
    style Discover fill:#fff3e0
    style Shadow fill:#ffebee
    style Store fill:#e8f5e9
    style End fill:#e3f2fd
```

## Prediction Generation Flow

```mermaid
flowchart TD
    Start([Scheduler Trigger<br/>Every 15 minutes]) --> FetchAPIs[Fetch All Active APIs<br/>from api-inventory]
    FetchAPIs --> Loop{For Each<br/>API}
    
    Loop --> |Process| FetchMetrics[Fetch Recent Metrics<br/>Last 24-48 hours]
    FetchMetrics --> Analyze[Analyze Metrics<br/>Detect Anomalies]
    
    Analyze --> CheckAI{AI-Enhanced<br/>Mode?}
    CheckAI --> |Yes| LLMAnalysis[LangGraph Agent<br/>AI Trend Analysis]
    CheckAI --> |No| RuleBased[Rule-Based Analysis<br/>Threshold Checks]
    
    LLMAnalysis --> |Success| GeneratePred[Generate Prediction<br/>with AI Explanation]
    LLMAnalysis --> |LLM Unavailable| RuleBased
    RuleBased --> GeneratePred
    
    GeneratePred --> CalcConfidence[Calculate Confidence<br/>Score 0-1]
    CalcConfidence --> Severity{Severity<br/>Level}
    
    Severity --> |Critical| HighPriority[Priority: Critical<br/>Immediate Action]
    Severity --> |High| MedPriority[Priority: High<br/>24h Window]
    Severity --> |Medium/Low| LowPriority[Priority: Medium/Low<br/>48h Window]
    
    HighPriority --> StorePred[Store in OpenSearch<br/>api-predictions index]
    MedPriority --> StorePred
    LowPriority --> StorePred
    
    StorePred --> Alert{Critical<br/>Severity?}
    Alert --> |Yes| SendAlert[Send Alert to Frontend<br/>Dashboard Notification]
    Alert --> |No| Continue
    SendAlert --> Continue[Continue]
    
    Continue --> Loop
    Loop --> |Done| End([End])
    
    style Start fill:#e3f2fd
    style LLMAnalysis fill:#f3e5f5
    style HighPriority fill:#ffebee
    style StorePred fill:#e8f5e9
    style End fill:#e3f2fd
```

## Natural Language Query Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant QueryService
    participant QueryAgent
    participant LLMService
    participant OpenSearch
    
    User->>Frontend: Enter Query<br/>"Show APIs with high latency"
    Frontend->>QueryService: POST /api/v1/query
    
    QueryService->>QueryService: Parse Query Intent<br/>Extract Entities
    QueryService->>QueryAgent: Process Query<br/>LangChain Workflow
    
    QueryAgent->>LLMService: Understand Query<br/>Generate Search Plan
    LLMService-->>QueryAgent: Search Strategy
    
    QueryAgent->>OpenSearch: Execute Search<br/>api-metrics-* indices
    OpenSearch-->>QueryAgent: Raw Results
    
    QueryAgent->>QueryAgent: Aggregate Data<br/>Apply Filters
    QueryAgent->>LLMService: Generate Response<br/>Natural Language
    LLMService-->>QueryAgent: Formatted Response
    
    QueryAgent-->>QueryService: Query Result
    QueryService->>OpenSearch: Store in query-history
    QueryService-->>Frontend: JSON Response<br/>+ Visualizations
    Frontend-->>User: Display Results<br/>+ Follow-up Suggestions
```

## Metrics Collection Flow

```mermaid
flowchart LR
    subgraph "Scheduler"
        Timer[Every 1 Minute]
    end
    
    subgraph "Metrics Service"
        Trigger[Trigger Collection]
        GetAPIs[Get All APIs<br/>from Inventory]
        Collect[Collect Metrics<br/>via Gateway Adapter]
    end
    
    subgraph "Gateway Adapter"
        Connect[Connect to Gateway]
        Query[Query Metrics API]
        Parse[Parse Response]
    end
    
    subgraph "Data Processing"
        Validate[Validate Data]
        Enrich[Enrich with Metadata]
        Aggregate[Calculate Aggregates<br/>p50, p95, p99]
    end
    
    subgraph "Storage"
        Index[Store in OpenSearch<br/>api-metrics-YYYY-MM-DD]
        Rollover{Index Size<br/>>50GB?}
        NewIndex[Create New Index]
    end
    
    subgraph "Consumers"
        Dashboard[Frontend Dashboard]
        Predictions[Prediction Service]
        Optimization[Optimization Service]
    end
    
    Timer --> Trigger
    Trigger --> GetAPIs
    GetAPIs --> Collect
    Collect --> Connect
    Connect --> Query
    Query --> Parse
    Parse --> Validate
    Validate --> Enrich
    Enrich --> Aggregate
    Aggregate --> Index
    Index --> Rollover
    Rollover -->|Yes| NewIndex
    Rollover -->|No| Dashboard
    NewIndex --> Dashboard
    Dashboard --> Predictions
    Dashboard --> Optimization
    
    style Timer fill:#e3f2fd
    style Collect fill:#fff3e0
    style Index fill:#e8f5e9
    style Dashboard fill:#f3e5f5
```

## Rate Limit Policy Application Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant RateLimitService
    participant OpenSearch
    participant GatewayAdapter
    participant Gateway
    
    User->>Frontend: Create Rate Limit Policy
    Frontend->>RateLimitService: POST /api/v1/rate-limits
    
    RateLimitService->>RateLimitService: Validate Policy<br/>Check Thresholds
    RateLimitService->>OpenSearch: Store Policy<br/>rate-limit-policies
    OpenSearch-->>RateLimitService: Policy ID
    
    RateLimitService->>GatewayAdapter: Apply Policy<br/>Translate to Gateway Format
    GatewayAdapter->>Gateway: Configure Rate Limit<br/>Gateway-Specific API
    Gateway-->>GatewayAdapter: Confirmation
    GatewayAdapter-->>RateLimitService: Applied Successfully
    
    RateLimitService->>OpenSearch: Update Policy Status<br/>status: active
    RateLimitService-->>Frontend: Success Response
    Frontend-->>User: Policy Applied
    
    Note over Gateway: Policy Now Active<br/>Enforcing Limits
    
    Gateway->>OpenSearch: Log Throttled Requests<br/>api-metrics-*
    
    RateLimitService->>OpenSearch: Analyze Effectiveness<br/>Every 1 hour
    OpenSearch-->>RateLimitService: Metrics Data
    RateLimitService->>RateLimitService: Calculate Score<br/>Protection, Fairness, Efficiency
    RateLimitService->>OpenSearch: Store Analysis<br/>rate-limit-policies
```

## Optimization Recommendation Flow

```mermaid
flowchart TD
    Start([Scheduler Trigger<br/>Every 30 minutes]) --> FetchAPIs[Fetch All APIs<br/>with Recent Activity]
    
    FetchAPIs --> Loop{For Each<br/>API}
    Loop --> |Process| GetMetrics[Get Performance Metrics<br/>Last 7 days]
    
    GetMetrics --> Analyze[Analyze Performance<br/>Identify Bottlenecks]
    Analyze --> CheckPatterns{Performance<br/>Issues?}
    
    CheckPatterns --> |High Latency| LatencyRec[Generate Latency<br/>Recommendations]
    CheckPatterns --> |High Error Rate| ErrorRec[Generate Error<br/>Recommendations]
    CheckPatterns --> |Resource Issues| ResourceRec[Generate Resource<br/>Recommendations]
    CheckPatterns --> |No Issues| Loop
    
    LatencyRec --> AIEnhance{AI-Enhanced<br/>Mode?}
    ErrorRec --> AIEnhance
    ResourceRec --> AIEnhance
    
    AIEnhance --> |Yes| LLMInsights[LangGraph Agent<br/>Generate AI Insights]
    AIEnhance --> |No| RuleInsights[Rule-Based Insights]
    
    LLMInsights --> |Success| CalcImpact[Calculate Impact<br/>% Improvement]
    LLMInsights --> |LLM Unavailable| RuleInsights
    RuleInsights --> CalcImpact
    
    CalcImpact --> Priority[Assign Priority<br/>Impact vs Effort]
    Priority --> Steps[Generate Implementation<br/>Steps]
    
    Steps --> Store[Store in OpenSearch<br/>optimization-recommendations]
    Store --> Loop
    
    Loop --> |Done| Notify[Notify Frontend<br/>New Recommendations]
    Notify --> End([End])
    
    style Start fill:#e3f2fd
    style LLMInsights fill:#f3e5f5
    style Store fill:#e8f5e9
    style End fill:#e3f2fd
```

## Data Persistence Architecture

```mermaid
graph TB
    subgraph "Application Layer"
        Services[Backend Services]
    end
    
    subgraph "Repository Layer"
        REPO_API[API Repository]
        REPO_GW[Gateway Repository]
        REPO_MET[Metrics Repository]
        REPO_PRED[Prediction Repository]
        REPO_REC[Recommendation Repository]
        REPO_RL[Rate Limit Repository]
        REPO_Q[Query Repository]
    end
    
    subgraph "OpenSearch Indices"
        IDX_API[(api-inventory<br/>Permanent)]
        IDX_GW[(gateway-registry<br/>Permanent)]
        IDX_MET[(api-metrics-*<br/>90 days)]
        IDX_PRED[(api-predictions<br/>90 days)]
        IDX_SEC[(security-findings<br/>90 days)]
        IDX_REC[(optimization-recommendations<br/>90 days)]
        IDX_RL[(rate-limit-policies<br/>Permanent)]
        IDX_Q[(query-history<br/>30 days)]
    end
    
    subgraph "Index Lifecycle"
        ILM[Index Lifecycle Management]
        Rollover[Daily Rollover<br/>Time-series Indices]
        Delete[Auto-delete After<br/>Retention Period]
        Snapshot[Daily Snapshots<br/>Backup]
    end
    
    Services --> REPO_API & REPO_GW & REPO_MET & REPO_PRED & REPO_REC & REPO_RL & REPO_Q
    
    REPO_API --> IDX_API
    REPO_GW --> IDX_GW
    REPO_MET --> IDX_MET
    REPO_PRED --> IDX_PRED & IDX_SEC
    REPO_REC --> IDX_REC
    REPO_RL --> IDX_RL
    REPO_Q --> IDX_Q
    
    IDX_MET & IDX_PRED & IDX_SEC & IDX_REC & IDX_Q --> ILM
    ILM --> Rollover
    ILM --> Delete
    ILM --> Snapshot
    
    style Services fill:#fff4e1
    style REPO_API fill:#e3f2fd
    style IDX_API fill:#e8f5e9
    style ILM fill:#f3e5f5