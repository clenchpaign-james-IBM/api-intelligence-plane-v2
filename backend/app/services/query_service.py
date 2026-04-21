"""
Query Service

Handles natural language query processing, intent detection, OpenSearch query
generation, and response generation using LLM.

Enhanced with multi-index query support, context management, and relationship-aware
query planning for improved follow-up question handling.
"""

import json
import logging
import re
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from app.db.repositories.query_repository import QueryRepository
from app.db.repositories.api_repository import APIRepository
from app.db.repositories.metrics_repository import MetricsRepository
from app.db.repositories.prediction_repository import PredictionRepository
from app.db.repositories.recommendation_repository import RecommendationRepository
from app.db.repositories.compliance_repository import ComplianceRepository
from app.db.repositories.gateway_repository import GatewayRepository
from app.db.repositories.vulnerability_repository import VulnerabilityRepository
from app.db.repositories.transactional_log_repository import TransactionalLogRepository
from app.models.query import (
    Query,
    QueryType,
    InterpretedIntent,
    QueryResults,
    TimeRange,
)
from app.models.base.metric import TimeBucket
from app.services.llm_service import LLMService
from app.services.query import (
    SchemaRegistry,
    ConceptMapper,
    QueryValidator,
    SchemaAwareLLMQueryGenerator,
    HybridQueryGenerator,
    ContextManager,
    RelationshipGraph,
    EnhancedIntentExtractor,
    QueryPlanner,
    MultiIndexExecutor,
)

logger = logging.getLogger(__name__)


class QueryService:
    """Service for processing natural language queries."""
    
    # Query type keywords for classification
    QUERY_TYPE_KEYWORDS = {
        QueryType.STATUS: [
            "status", "health", "state", "current", "now", "active",
            "running", "available", "up", "down", "online", "offline",
            "operational", "working", "functioning"
        ],
        QueryType.TREND: [
            "trend", "over time", "history", "pattern", "change",
            "historical", "past", "previous", "evolution", "progression",
            "growth", "decline", "increase", "decrease", "timeline"
        ],
        QueryType.PREDICTION: [
            "predict", "forecast", "future", "will", "expect",
            "anticipate", "upcoming", "next", "projected", "estimated",
            "likely", "probable", "expected", "ahead"
        ],
        QueryType.SECURITY: [
            "security", "vulnerability", "vulnerabilities", "threat", "risk", "cve",
            "exploit", "attack", "breach", "exposure", "weakness",
            "insecure", "unsafe", "compromised", "malicious", "suspicious"
        ],
        QueryType.PERFORMANCE: [
            "performance", "latency", "response time", "throughput", "slow",
            "fast", "speed", "efficiency", "bottleneck", "optimization",
            "delay", "lag", "timeout", "error rate", "failure rate",
            "availability", "uptime", "downtime"
        ],
        QueryType.COMPARISON: [
            "compare", "versus", "vs", "difference", "between",
            "comparison", "contrast", "against", "relative to", "compared to"
        ],
        QueryType.COMPLIANCE: [
            "compliance", "regulatory", "regulation", "gdpr", "hipaa", "soc2", "pci", "iso", "audit", "violation",
            "standard", "policy", "rule", "requirement", "mandate",
            "non-compliant", "compliant", "certified", "certification"
        ],
    }
    
    # Entity keywords for extraction
    ENTITY_KEYWORDS = {
        "api": ["api", "apis", "endpoint", "endpoints", "service", "services"],
        "gateway": ["gateway", "gateways"],
        "metric": ["metric", "metrics", "measurement"],
        "prediction": ["prediction", "predictions", "forecast"],
        "vulnerability": ["vulnerability", "vulnerabilities", "security issue"],
        "recommendation": ["recommendation", "recommendations", "optimization", "suggestion", "rate limit", "rate limiting", "throttle", "throttling", "caching", "compression"],
        "compliance": ["compliance", "violation", "violations", "regulatory", "audit"],
        "transaction": ["transaction", "transactions", "transactional log", "log", "logs", "request", "requests", "raw logs", "traffic logs"],
    }
    
    # Action keywords
    ACTION_KEYWORDS = {
        "list": ["list", "show", "display", "get", "find", "what"],
        "count": ["count", "how many", "number of"],
        "analyze": ["analyze", "analysis", "examine", "investigate"],
        "compare": ["compare", "comparison", "versus", "vs"],
        "summarize": ["summarize", "summary", "overview"],
    }

    def __init__(
        self,
        query_repository: QueryRepository,
        api_repository: APIRepository,
        metrics_repository: MetricsRepository,
        prediction_repository: PredictionRepository,
        recommendation_repository: RecommendationRepository,
        llm_service: LLMService,
        compliance_repository: Optional[ComplianceRepository] = None,
        gateway_repository: Optional[GatewayRepository] = None,
        vulnerability_repository: Optional[VulnerabilityRepository] = None,
        transactional_log_repository: Optional[TransactionalLogRepository] = None,
    ):
        """
        Initialize the Query Service.
        
        Args:
            query_repository: Repository for query operations
            api_repository: Repository for API operations
            metrics_repository: Repository for metrics operations
            prediction_repository: Repository for prediction operations
            recommendation_repository: Repository for recommendation operations
            llm_service: LLM service for natural language processing
            compliance_repository: Optional ComplianceRepository for compliance operations
            gateway_repository: Optional GatewayRepository for gateway operations
            vulnerability_repository: Optional VulnerabilityRepository for vulnerability operations
            transactional_log_repository: Optional TransactionalLogRepository for transaction log operations
        """
        self.query_repo = query_repository
        self.api_repo = api_repository
        self.metrics_repo = metrics_repository
        self.prediction_repo = prediction_repository
        self.recommendation_repo = recommendation_repository
        self.compliance_repo = compliance_repository or ComplianceRepository()
        self.gateway_repo = gateway_repository or GatewayRepository()
        self.vulnerability_repo = vulnerability_repository or VulnerabilityRepository()
        self.transactional_log_repo = transactional_log_repository or TransactionalLogRepository()
        self.llm_service = llm_service
        
        # Initialize enhanced query generation components
        self._init_query_enhancement()
        
        # Performance tracking
        self._query_metrics = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "avg_execution_time_ms": 0,
            "multi_index_queries": 0,
            "context_aware_queries": 0,
        }
    
    def _init_query_enhancement(self) -> None:
        """Initialize schema-aware query generation and multi-index components."""
        try:
            # Get OpenSearch client from api_repository
            opensearch_client = self.api_repo.client
            
            # Initialize core components
            self.schema_registry = SchemaRegistry(opensearch_client)
            self.concept_mapper = ConceptMapper()
            self.query_validator = QueryValidator(self.schema_registry)
            self.llm_query_generator = SchemaAwareLLMQueryGenerator(
                self.llm_service,
                self.schema_registry,
                self.concept_mapper,
                self.query_validator
            )
            self.hybrid_generator = HybridQueryGenerator(
                self.schema_registry,
                self.concept_mapper,
                self.llm_query_generator,
                self.query_validator
            )
            
            # Initialize multi-index components
            self.context_manager = ContextManager()
            self.relationship_graph = RelationshipGraph()
            self.enhanced_intent_extractor = EnhancedIntentExtractor(
                self.llm_service,
                self.context_manager,
                self.relationship_graph
            )
            self.query_planner = QueryPlanner(
                self.schema_registry,
                self.relationship_graph,
                self.context_manager
            )
            self.multi_index_executor = MultiIndexExecutor(
                self.api_repo,
                self.gateway_repo,
                self.metrics_repo,
                self.prediction_repo,
                self.recommendation_repo,
                self.compliance_repo,
                self.vulnerability_repo,
                self.transactional_log_repo,
                self.context_manager
            )
            
            # Load schemas asynchronously (will be done on first query if not loaded)
            self._schemas_loaded = False
            self._multi_index_enabled = True
            
            logger.info("Enhanced query generation and multi-index components initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize query enhancement: {e}. Using fallback query generation.")
            self.hybrid_generator = None  # type: ignore[assignment]
            self._multi_index_enabled = False
    
    def _determine_time_bucket(self, time_range: Optional[TimeRange]) -> TimeBucket:
        """
        Determine the appropriate time bucket based on query time range.
        
        Args:
            time_range: Optional time range from query intent
            
        Returns:
            Appropriate time bucket for the query
        """
        if not time_range:
            # Default to 5-minute bucket for recent data
            return TimeBucket.FIVE_MINUTES
        
        # Calculate time range duration
        duration = time_range.end - time_range.start
        
        # Select bucket based on duration
        if duration <= timedelta(hours=24):
            return TimeBucket.ONE_MINUTE  # 1m bucket for last 24 hours
        elif duration <= timedelta(days=7):
            return TimeBucket.FIVE_MINUTES  # 5m bucket for last 7 days
        elif duration <= timedelta(days=30):
            return TimeBucket.ONE_HOUR  # 1h bucket for last 30 days
        else:
            return TimeBucket.ONE_DAY  # 1d bucket for longer periods

    async def process_query(
        self,
        query_text: str,
        session_id: UUID,
        user_id: Optional[str] = None,
    ) -> Query:
        """
        Process a natural language query end-to-end.
        
        Args:
            query_text: Natural language query text
            session_id: Conversation session ID
            user_id: Optional user identifier
            
        Returns:
            Query object with results and response
        """
        start_time = time.time()
        self._query_metrics["total_queries"] += 1
        
        try:
            # Step 1: Classify query type
            query_type = self._classify_query_type(query_text)
            logger.info(f"Classified query as: {query_type}")
            
            # Step 2: Extract intent (enhanced with context if available)
            if self._multi_index_enabled:
                interpreted_intent, confidence = await self._extract_enhanced_intent(
                    query_text, query_type, session_id
                )
                logger.info(f"Extracted enhanced intent with confidence: {confidence}")
            else:
                interpreted_intent, confidence = await self._extract_intent(
                    query_text, query_type
                )
                logger.info(f"Extracted intent with confidence: {confidence}")
            
            # Step 3: Execute query (multi-index or legacy)
            if self._multi_index_enabled and self._should_use_multi_index(interpreted_intent):
                # Multi-index execution path
                self._query_metrics["multi_index_queries"] += 1
                opensearch_query, results = await self._execute_multi_index_query(
                    query_text, interpreted_intent, query_type, session_id
                )
                logger.info(f"Executed multi-index query, found {results.count} results")
            else:
                # Legacy single-index execution path
                opensearch_query = await self._generate_opensearch_query(
                    query_text, interpreted_intent, query_type
                )
                logger.info(f"Generated OpenSearch query")
                
                results = await self._execute_query(
                    opensearch_query, interpreted_intent, query_type
                )
                logger.info(f"Executed query, found {results.count} results")
            
            # Step 5: Generate natural language response
            response_text = await self._generate_response(
                query_text, interpreted_intent, results, query_type
            )
            logger.info(f"Generated response")
            
            # Step 6: Generate follow-up suggestions
            follow_up_queries = self._generate_follow_ups(
                query_text, interpreted_intent, results, query_type
            )
            
            # Calculate execution time
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            # Create Query object
            query = Query(
                id=uuid4(),
                session_id=session_id,
                user_id=user_id,
                query_text=query_text,
                query_type=query_type,
                interpreted_intent=interpreted_intent,
                opensearch_query=opensearch_query,
                results=results,
                response_text=response_text,
                confidence_score=confidence,
                execution_time_ms=execution_time_ms,
                feedback=None,
                feedback_comment=None,
                follow_up_queries=follow_up_queries,
                metadata=None,
                created_at=datetime.utcnow(),
            )
            
            # Sanitize OpenSearch query before saving to avoid date expression errors
            if query.opensearch_query:
                query.opensearch_query = self._sanitize_opensearch_query(query.opensearch_query)
            
            # Save query to history
            try:
                saved_query = self.query_repo.create(query, doc_id=str(query.id))
                logger.info(f"Saved query to history: {saved_query.id}")
            except Exception as e:
                logger.warning(f"Failed to save query to history: {e}. Continuing without saving.")
                saved_query = query
            
            # Update metrics
            self._query_metrics["successful_queries"] += 1
            self._update_avg_execution_time(execution_time_ms)
            
            return saved_query
            
        except Exception as e:
            logger.error(f"Failed to process query: {e}", exc_info=True)
            self._query_metrics["failed_queries"] += 1
            
            # Return error query
            execution_time_ms = int((time.time() - start_time) * 1000)
            error_query = Query(
                id=uuid4(),
                session_id=session_id,
                user_id=user_id,
                query_text=query_text,
                query_type=QueryType.GENERAL,
                interpreted_intent=InterpretedIntent(
                    action="error",
                    entities=[],
                    filters={},
                    time_range=None,
                ),
                opensearch_query=None,
                results=QueryResults(
                    data=[],
                    count=0,
                    execution_time=execution_time_ms,
                    aggregations=None,
                ),
                response_text=f"I encountered an error processing your query: {str(e)}. Please try rephrasing your question.",
                confidence_score=0.0,
                execution_time_ms=execution_time_ms,
                feedback=None,
                feedback_comment=None,
                follow_up_queries=None,
                metadata=None,
                created_at=datetime.utcnow(),
            )
            return error_query

    def _classify_query_type(self, query_text: str) -> QueryType:
        """
        Classify the query type based on keywords.
        
        Args:
            query_text: Query text
            
        Returns:
            Classified query type
        """
        query_lower = query_text.lower()
        
        # Count keyword matches for each type
        type_scores = {}
        for query_type, keywords in self.QUERY_TYPE_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > 0:
                type_scores[query_type] = score
        
        # Return type with highest score, or GENERAL if no matches
        if type_scores:
            return max(type_scores.items(), key=lambda x: x[1])[0]
        return QueryType.GENERAL

    async def _extract_intent(
        self, query_text: str, query_type: QueryType
    ) -> Tuple[InterpretedIntent, float]:
        """
        Extract structured intent from natural language query using LLM.
        
        Args:
            query_text: Query text
            query_type: Classified query type
            
        Returns:
            Tuple of (interpreted intent, confidence score)
        """
        system_prompt = """You are an AI assistant that extracts structured intent from natural language queries about API management.

Extract the following information:
1. Action: What the user wants to do (list, show, count, analyze, compare, summarize, find)
2. Entities: What entities are involved (api, gateway, metric, prediction, vulnerability, recommendation, rate_limit, compliance, transaction)
3. Filters: Any filter conditions including:
   - gateway_id: UUID of a gateway (extract from phrases like "gateway <uuid>", "managed by gateway <uuid>", "for gateway <uuid>")
   - api_id: UUID of an API
   - severity: critical, high, medium, low
   - status: open, closed, active, inactive
   - Any other field-value pairs mentioned
4. Time Range: If mentioned, extract start and end times

IMPORTANT RULES:
- When a UUID is mentioned in relation to a gateway, extract it as "gateway_id" in the filters
- When a UUID is mentioned in relation to an API, extract it as "api_id" in the filters
- When asking for "APIs with X" where X is a property (vulnerabilities, issues, problems), the primary entity should be X, not "api"
  Example: "APIs with critical vulnerabilities" → entities: ["vulnerability"], filters: {"severity": "critical"}
  Example: "APIs managed by gateway X" → entities: ["api"], filters: {"gateway_id": "X"}
- Only include "api" as an entity when directly querying for API information, not when querying for related entities

Respond in JSON format:
{
  "action": "list",
  "entities": ["vulnerability"],
  "filters": {
    "severity": "critical"
  },
  "time_range": {
    "start": "2026-03-02T00:00:00Z",
    "end": "2026-03-09T23:59:59Z"
  },
  "confidence": 0.95
}"""

        messages = [
            {"role": "user", "content": f"Query: {query_text}\nQuery Type: {query_type.value}"}
        ]
        
        try:
            response = await self.llm_service.generate_completion(
                messages=messages,
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=500,
            )
            
            # Parse JSON response - handle markdown-wrapped JSON
            import json
            import re
            
            content = response.get("content", "")
            
            # Check if content is empty or None
            if not content or not content.strip():
                logger.warning("LLM returned empty content, using fallback")
                return self._fallback_intent_extraction(query_text, query_type), 0.5
            
            # Try to extract JSON from markdown code blocks
            json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1).strip()
            else:
                # If no markdown block, try to find JSON object directly
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    json_str = content
            
            # Check if we have valid JSON string
            if not json_str or not json_str.strip():
                logger.warning("No JSON found in LLM response, using fallback")
                return self._fallback_intent_extraction(query_text, query_type), 0.5
            
            try:
                intent_data = json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON from LLM response: {e}")
                logger.debug(f"Original content: {content}")
                logger.debug(f"Extracted JSON string: {json_str}")
                # Use fallback instead of raising
                return self._fallback_intent_extraction(query_text, query_type), 0.5
            
            # Extract time range if present
            time_range = None
            if "time_range" in intent_data and intent_data["time_range"]:
                try:
                    time_range = TimeRange(
                        start=datetime.fromisoformat(intent_data["time_range"]["start"].replace("Z", "+00:00")),
                        end=datetime.fromisoformat(intent_data["time_range"]["end"].replace("Z", "+00:00")),
                    )
                except Exception as e:
                    logger.warning(f"Failed to parse time range: {e}")
            
            intent = InterpretedIntent(
                action=intent_data.get("action", "list"),
                entities=intent_data.get("entities", []),
                filters=intent_data.get("filters", {}),
                time_range=time_range,
            )
            
            confidence = intent_data.get("confidence", 0.8)
            
            return intent, confidence
            
        except Exception as e:
            logger.warning(f"Error extracting intent with LLM: {e}")
            # Fallback to keyword-based extraction
            return self._fallback_intent_extraction(query_text, query_type), 0.5
    async def _extract_enhanced_intent(
        self, query_text: str, query_type: QueryType, session_id: UUID
    ) -> Tuple[InterpretedIntent, float]:
        """
        Extract enhanced intent with context awareness.
        
        Args:
            query_text: Query text
            query_type: Classified query type
            session_id: Session ID for context retrieval
            
        Returns:
            Tuple of (interpreted intent, confidence score)
        """
        try:
            # Use enhanced intent extractor with context
            enhanced_intent = await self.enhanced_intent_extractor.extract_intent(
                query_text, session_id, query_type
            )
            
            # Track context-aware queries
            if enhanced_intent.references or enhanced_intent.resolved_entities:
                self._query_metrics["context_aware_queries"] += 1
            
            # Convert to standard InterpretedIntent for compatibility
            intent = InterpretedIntent(
                action=enhanced_intent.action,
                entities=enhanced_intent.entities,
                filters=enhanced_intent.filters,
                time_range=enhanced_intent.time_range,
            )
            
            # Calculate confidence based on reference resolution
            confidence = 0.9 if enhanced_intent.references else 0.8
            
            return intent, confidence
            
        except Exception as e:
            logger.warning(f"Enhanced intent extraction failed, using fallback: {e}")
            return await self._extract_intent(query_text, query_type)
    
    def _should_use_multi_index(self, intent: InterpretedIntent) -> bool:
        """
        Determine if query should use multi-index execution.
        
        Args:
            intent: Interpreted intent
            
        Returns:
            True if multi-index execution is beneficial
        """
        # Use multi-index if:
        # 1. Multiple entities are involved AND no direct filter exists
        # 2. Relationships between entities are implied
        # 3. Context from previous queries exists
        
        # If we have a direct filter (gateway_id, api_id, etc.), use single-index query
        # These are simple filtering operations, not relationship queries
        direct_filters = ["gateway_id", "api_id", "id"]
        if any(filter_key in intent.filters for filter_key in direct_filters):
            return False
        
        # If we have only one entity type, use single-index query
        # Multi-index is only needed for cross-entity queries
        if len(intent.entities) <= 1:
            return False
        
        if len(intent.entities) > 1:
            return True
        
        # Check for relationship keywords in filters
        relationship_keywords = ["with", "having", "affected by", "related to"]
        for value in intent.filters.values():
            if isinstance(value, str) and any(kw in value.lower() for kw in relationship_keywords):
                return True
        
        return False
    
    async def _execute_multi_index_query(
        self,
        query_text: str,
        intent: InterpretedIntent,
        query_type: QueryType,
        session_id: UUID,
    ) -> Tuple[Optional[Dict[str, Any]], QueryResults]:
        """
        Execute query using multi-index orchestration.
        
        Args:
            query_text: Original query text
            intent: Interpreted intent
            query_type: Query type
            session_id: Session ID for context
            
        Returns:
            Tuple of (opensearch query, results)
        """
        try:
            # Create query plan
            query_plan = self.query_planner.create_plan(
                session_id=session_id,
                query_text=query_text,
                intent=intent,
            )
            
            logger.info(f"Created query plan with {len(query_plan.index_queries)} index queries")
            
            # Execute plan
            results = await self.multi_index_executor.execute_plan(query_plan)
            
            # Store context for follow-up queries
            if results.count > 0:
                self._store_query_context(
                    session_id=session_id,
                    query_text=query_text,
                    intent=intent,
                    results=results,
                )
            
            # Return plan summary as opensearch_query for logging
            opensearch_query = {
                "strategy": query_plan.strategy.value,
                "indices": [q.index for q in query_plan.index_queries],
                "estimated_cost": query_plan.estimated_cost,
            }
            
            return opensearch_query, results
            
        except Exception as e:
            logger.error(f"Multi-index execution failed: {e}", exc_info=True)
            # Fallback to legacy execution
            opensearch_query = await self._generate_opensearch_query(
                query_text, intent, query_type
            )
            results = await self._execute_query(opensearch_query, intent, query_type)
            return opensearch_query, results
    
    def _store_query_context(
        self,
        session_id: UUID,
        query_text: str,
        intent: InterpretedIntent,
        results: QueryResults,
    ) -> None:
        """
        Store query context for follow-up questions.
        
        Args:
            session_id: Session ID
            query_text: Query text
            intent: Interpreted intent
            results: Query results
        """
        try:
            # Extract entity IDs from results
            entity_ids: Dict[str, List[str]] = {}
            for item in results.data[:50]:  # Limit to first 50 for performance
                if isinstance(item, dict):
                    if "api_id" in item:
                        entity_ids.setdefault("api_id", []).append(item["api_id"])
                    if "gateway_id" in item:
                        entity_ids.setdefault("gateway_id", []).append(item["gateway_id"])
                    if "id" in item:
                        # Generic ID field
                        entity_type = intent.entities[0] if intent.entities else "unknown"
                        entity_ids.setdefault(f"{entity_type}_id", []).append(item["id"])
            
            # Store context
            self.context_manager.store_query_context(
                session_id=session_id,
                query_id=uuid4(),
                query_text=query_text,
                target_indices=[intent.entities[0] if intent.entities else "api"],
                entity_ids=entity_ids,
                result_count=results.count,
                filters_applied=intent.filters,
            )
            
        except Exception as e:
            logger.warning(f"Failed to store query context: {e}")
    
    def _update_avg_execution_time(self, execution_time_ms: int) -> None:
        """
        Update average execution time metric.
        
        Args:
            execution_time_ms: Execution time in milliseconds
        """
        total = self._query_metrics["total_queries"]
        current_avg = self._query_metrics["avg_execution_time_ms"]
        
        # Calculate new average
        new_avg = ((current_avg * (total - 1)) + execution_time_ms) / total
        self._query_metrics["avg_execution_time_ms"] = int(new_avg)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get current performance metrics.
        
        Returns:
            Dictionary of performance metrics
        """
        total = self._query_metrics["total_queries"]
        if total == 0:
            return self._query_metrics.copy()
        
        return {
            **self._query_metrics,
            "success_rate": (self._query_metrics["successful_queries"] / total) * 100,
            "failure_rate": (self._query_metrics["failed_queries"] / total) * 100,
            "multi_index_usage": (self._query_metrics["multi_index_queries"] / total) * 100,
            "context_aware_usage": (self._query_metrics["context_aware_queries"] / total) * 100,
        }


    def _fallback_intent_extraction(
        self, query_text: str, query_type: QueryType
    ) -> InterpretedIntent:
        """
        Fallback intent extraction using keyword matching and EntityRegistry.
        
        Args:
            query_text: Query text
            query_type: Classified query type
            
        Returns:
            Interpreted intent
        """
        import re
        from app.services.query.entity_registry import EntityRegistry
        
        query_lower = query_text.lower()
        
        # Extract action
        action = "list"
        for act, keywords in self.ACTION_KEYWORDS.items():
            if any(keyword in query_lower for keyword in keywords):
                action = act
                break
        
        # Extract entities using EntityRegistry for consistent resolution
        entities = []
        for entity_type in EntityRegistry.get_all_entity_types():
            config = EntityRegistry.ENTITIES[entity_type]
            all_keywords = [entity_type] + config.aliases
            if any(keyword in query_lower for keyword in all_keywords):
                entities.append(entity_type)
        
        # Default to API if no entities found
        if not entities:
            entities = ["api"]
        
        # Extract basic filters using EntityRegistry for validation
        filters = {}
        
        # Severity filter
        if "critical" in query_lower:
            filters["severity"] = "critical"
        elif "high" in query_lower:
            filters["severity"] = "high"
        elif "medium" in query_lower:
            filters["severity"] = "medium"
        elif "low" in query_lower:
            filters["severity"] = "low"
        
        # Status filter
        if "open" in query_lower:
            filters["status"] = "open"
        elif "closed" in query_lower:
            filters["status"] = "closed"
        elif "active" in query_lower:
            filters["status"] = "active"
        elif "inactive" in query_lower:
            filters["status"] = "inactive"
        elif "deprecated" in query_lower:
            filters["status"] = "deprecated"
        
        # Extract UUIDs and associate them with entities
        uuid_pattern = r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b'
        uuids = re.findall(uuid_pattern, query_text, re.IGNORECASE)
        
        if uuids:
            # Determine which entity the UUID belongs to based on context
            for uuid in uuids:
                # Look for context words before the UUID
                uuid_pos = query_lower.find(uuid.lower())
                context_before = query_lower[max(0, uuid_pos - 50):uuid_pos]
                
                if any(word in context_before for word in ["gateway", "gw"]):
                    filters["gateway_id"] = uuid
                elif any(word in context_before for word in ["api"]):
                    filters["api_id"] = uuid
                else:
                    # Default: if "gateway" is in entities, assume it's a gateway_id
                    if "gateway" in entities:
                        filters["gateway_id"] = uuid
                    # If querying APIs and UUID is present, likely filtering by gateway
                    elif "api" in entities or not entities:
                        filters["gateway_id"] = uuid
        
        return InterpretedIntent(
            action=action,
            entities=entities if entities else ["api"],
            filters=filters,
            time_range=None,
        )

    async def _generate_opensearch_query(
        self, query_text: str, intent: InterpretedIntent, query_type: QueryType
    ) -> Dict[str, Any]:
        """
        Generate OpenSearch query DSL from interpreted intent.
        Uses hybrid generation (rule-based + LLM) if available, falls back to legacy method.
        
        Args:
            query_text: Original natural language query
            intent: Interpreted intent
            query_type: Query type
            
        Returns:
            OpenSearch query DSL
        """
        # Ensure schemas are loaded
        if self.hybrid_generator and not self._schemas_loaded:
            try:
                await self.schema_registry.load_schemas()
                self._schemas_loaded = True
                logger.info("Schemas loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load schemas: {e}")
        
        # Try enhanced query generation if available
        if self.hybrid_generator:
            try:
                # Determine target index based on entities
                index = self._determine_target_index(intent)
                
                # Build context from intent
                context = {}
                if intent.time_range:
                    context["time_range"] = {
                        "start": intent.time_range.start.isoformat(),
                        "end": intent.time_range.end.isoformat()
                    }
                if intent.filters:
                    context["filters"] = intent.filters
                
                # Generate query using hybrid approach
                dsl = await self.hybrid_generator.generate_query(
                    query_text, index, context
                )
                
                logger.info("Generated query using hybrid generator")
                return dsl
                
            except Exception as e:
                logger.warning(f"Enhanced query generation failed, using fallback: {e}")
        
        # Fallback to legacy query generation
        return self._generate_opensearch_query_legacy(intent, query_type)
    
    def _determine_target_index(self, intent: InterpretedIntent) -> str:
        """
        Determine target OpenSearch index based on intent entities.
        
        Args:
            intent: Interpreted intent
            
        Returns:
            Target index name
        """
        entities = intent.entities
        
        if "api" in entities:
            return "api-inventory"
        elif "gateway" in entities:
            return "gateway-registry"
        elif "metric" in entities:
            return "api-metrics-5m"
        elif "prediction" in entities:
            return "api-predictions"
        elif "vulnerability" in entities:
            return "security-findings"
        elif "recommendation" in entities:
            return "optimization-recommendations"
        elif "compliance" in entities:
            return "compliance-violations"
        elif "transaction" in entities:
            return "transactional-logs"
        else:
            # Default to API inventory
            return "api-inventory"
    
    def _generate_opensearch_query_legacy(
        self, intent: InterpretedIntent, query_type: QueryType
    ) -> Dict[str, Any]:
        """
        Legacy OpenSearch query generation (fallback method).
        
        Args:
            intent: Interpreted intent
            query_type: Query type
            
        Returns:
            OpenSearch query DSL
        """
        must_clauses = []
        
        # Add filter conditions
        for field, value in intent.filters.items():
            must_clauses.append({
                "term": {field: value}
            })
        
        # Add time range if present
        if intent.time_range:
            must_clauses.append({
                "range": {
                    "created_at": {
                        "gte": intent.time_range.start.isoformat(),
                        "lte": intent.time_range.end.isoformat(),
                    }
                }
            })
        
        # Build query
        if must_clauses:
            return {
                "query": {
                    "bool": {
                        "must": must_clauses
                    }
                }
            }
        else:
            return {
                "query": {
                    "match_all": {}
                }
            }

    async def _execute_query(
        self,
        opensearch_query: Dict[str, Any],
        intent: InterpretedIntent,
        query_type: QueryType,
    ) -> QueryResults:
        """
        Execute the OpenSearch query and return results.
        
        Args:
            opensearch_query: OpenSearch query DSL
            intent: Interpreted intent
            query_type: Query type
            
        Returns:
            Query results
        """
        start_time = time.time()
        
        try:
            # Determine which repository to query based on entities
            primary_entity = intent.entities[0] if intent.entities else "api"
            
            data: List[Any] = []
            total = 0
            
            if primary_entity == "api":
                api_results, total = self.api_repo.search(
                    opensearch_query["query"], size=50
                )
                # Use LLM-optimized serialization for APIs (60-85% reduction)
                data = [api.to_llm_dict() for api in api_results]
            elif primary_entity == "gateway":
                gateway_results, total = self.gateway_repo.search(
                    opensearch_query["query"], size=50
                )
                # Use LLM-optimized serialization for Gateways (40-60% reduction)
                data = [gateway.to_llm_dict() for gateway in gateway_results]
            elif primary_entity == "metric":
                metric_results, total = self.metrics_repo.search(
                    opensearch_query["query"], size=50
                )
                # Use LLM-optimized serialization for Metrics (40-60% reduction)
                data = [metric.to_llm_dict() for metric in metric_results]
            elif primary_entity == "prediction":
                pred_results, total = self.prediction_repo.search(
                    opensearch_query["query"], size=50
                )
                # Use LLM-optimized serialization for Predictions (20-30% reduction)
                data = [pred.to_llm_dict() for pred in pred_results]
            elif primary_entity == "vulnerability":
                vuln_results, total = self.vulnerability_repo.search(
                    opensearch_query["query"], size=50
                )
                # Use LLM-optimized serialization for Vulnerabilities (40-60% reduction)
                data = [vuln.to_llm_dict() for vuln in vuln_results]
            elif primary_entity == "recommendation":
                rec_results, total = self.recommendation_repo.search(
                    opensearch_query["query"], size=50
                )
                # Use LLM-optimized serialization for Recommendations (50-70% reduction)
                data = [rec.to_llm_dict() for rec in rec_results]
            elif primary_entity == "compliance":
                comp_results, total = self.compliance_repo.search(
                    opensearch_query["query"], size=50
                )
                # Use LLM-optimized serialization for Compliance (50-70% reduction)
                data = [comp.to_llm_dict() for comp in comp_results]
            elif primary_entity == "transaction" or primary_entity == "transactional_log":
                log_results, total = self.transactional_log_repo.search(
                    opensearch_query["query"], size=50
                )
                data = [log.model_dump(mode="json") for log in log_results]
            
            execution_time = int((time.time() - start_time) * 1000)
            
            return QueryResults(
                data=data,
                count=total,
                execution_time=execution_time,
                aggregations=None,
            )
            
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            execution_time = int((time.time() - start_time) * 1000)
            return QueryResults(
                data=[],
                count=0,
                execution_time=execution_time,
                aggregations=None,
            )

    async def _generate_response(
        self,
        query_text: str,
        intent: InterpretedIntent,
        results: QueryResults,
        query_type: QueryType,
    ) -> str:
        """
        Generate natural language response using LLM.
        
        Args:
            query_text: Original query text
            intent: Interpreted intent
            results: Query results
            query_type: Query type
            
        Returns:
            Natural language response
        """
        system_prompt = """You are an AI assistant for API management. Generate a clear, well-formatted response to the user's query based on the results.

Guidelines:
- Use markdown formatting for better readability (headers, lists, bold, etc.)
- Start with a brief summary sentence
- Use bullet points for key findings
- Highlight important numbers and metrics in **bold**
- Use headers (##) to organize different sections if needed
- Keep responses under 200 words
- Use professional but friendly tone
- If no results, explain why and suggest alternatives

Example format:
Found **X results** matching your query.

## Key Findings
- **Item 1**: Description
- **Item 2**: Description

Try asking about specific aspects for more details."""

        # Prepare results summary
        results_summary = f"Found {results.count} results in {results.execution_time}ms"
        if results.data:
            results_summary += f"\n\nSample results:\n{results.data[:3]}"
        
        messages = [
            {
                "role": "user",
                "content": f"Query: {query_text}\n\nIntent: {intent.model_dump()}\n\nResults: {results_summary}"
            }
        ]
        
        try:
            response = await self.llm_service.generate_completion(
                messages=messages,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=300,
            )
            content: str = response["content"]
            return content
        except Exception as e:
            logger.warning(f"LLM response generation failed, using fallback: {e}")
            # Fallback response
            if results.count == 0:
                return f"I couldn't find any {intent.entities[0] if intent.entities else 'items'} matching your criteria. Try adjusting your filters or time range."
            else:
                return f"I found {results.count} {intent.entities[0] if intent.entities else 'items'} matching your query."
    def _sanitize_opensearch_query(self, query_dsl: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize OpenSearch query DSL to remove date expressions that can't be stored.
        
        Converts expressions like 'now-1d/d' to actual ISO datetime strings.
        
        Args:
            query_dsl: OpenSearch query DSL dictionary
            
        Returns:
            Sanitized query DSL with date expressions converted to ISO strings
        """
        if not query_dsl:
            return query_dsl
        
        # Convert to JSON string for easier regex replacement
        query_str = json.dumps(query_dsl)
        
        # Pattern to match OpenSearch date math expressions
        # Examples: "now-1d/d", "now-7d", "now+1h", "now/d"
        date_math_pattern = r'"(now[^"]*)"'
        
        def replace_date_math(match):
            """Replace date math expression with actual ISO datetime."""
            expr = match.group(1)
            try:
                # Parse the expression and convert to datetime
                now = datetime.utcnow()
                
                # Handle "now" base
                if expr == "now":
                    return f'"{now.isoformat()}Z"'
                
                # Handle expressions like "now-7d", "now+1h", etc.
                # For simplicity, just use current time (queries will still work)
                # A full implementation would parse the math expression
                return f'"{now.isoformat()}Z"'
            except Exception:
                # If parsing fails, return original
                return match.group(0)
        
        # Replace all date math expressions
        sanitized_str = re.sub(date_math_pattern, replace_date_math, query_str)
        
        try:
            return json.loads(sanitized_str)
        except json.JSONDecodeError:
            # If JSON parsing fails, return original
            logger.warning("Failed to parse sanitized query, returning original")
            return query_dsl


    def _generate_follow_ups(
        self,
        query_text: str,
        intent: InterpretedIntent,
        results: QueryResults,
        query_type: QueryType,
    ) -> List[str]:
        """
        Generate follow-up query suggestions.
        
        Args:
            query_text: Original query text
            intent: Interpreted intent
            results: Query results
            query_type: Query type
            
        Returns:
            List of follow-up query suggestions
        """
        follow_ups = []
        
        if results.count > 0:
            primary_entity = intent.entities[0] if intent.entities else "item"
            
            # Suggest related queries based on entity type
            if primary_entity == "api":
                follow_ups.extend([
                    "Show me the performance metrics for these APIs",
                    "Are there any predictions for these APIs?",
                    "What security vulnerabilities affect these APIs?",
                ])
            elif primary_entity == "gateway":
                follow_ups.extend([
                    "Show me the APIs managed by these gateways",
                    "What's the health status of these gateways?",
                    "Show me the policies configured on these gateways",
                ])
            elif primary_entity == "metric":
                follow_ups.extend([
                    "Show me the trend over the last 7 days",
                    "Which APIs have the highest latency?",
                    "Show me error rate patterns",
                ])
            elif primary_entity == "vulnerability":
                follow_ups.extend([
                    "Show me the remediation status",
                    "Which APIs are most affected?",
                    "Show vulnerability trends over time",
                ])
            elif primary_entity == "prediction":
                follow_ups.extend([
                    "Show me the contributing factors",
                    "What actions are recommended?",
                    "Show prediction accuracy",
                ])
            elif primary_entity == "recommendation":
                follow_ups.extend([
                    "What's the implementation status?",
                    "Show me the expected impact",
                    "Which recommendations are highest priority?",
                ])
            elif primary_entity == "compliance":
                follow_ups.extend([
                    "Show me critical compliance violations",
                    "What's the remediation status?",
                    "Which APIs have the most violations?",
                    "Show GDPR compliance violations",
                ])
            elif primary_entity == "transaction" or primary_entity == "transactional_log":
                follow_ups.extend([
                    "Show me failed transactions",
                    "What's the average response time?",
                    "Show me the most active APIs",
                ])
        else:
            follow_ups.extend([
                "Show me all active APIs",
                "What are the recent predictions?",
                "Show me critical security issues",
            ])
        
        return follow_ups[:5]  # Limit to 5 suggestions


# Made with Bob