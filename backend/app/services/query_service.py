"""
Query Service

Handles natural language query processing, intent detection, OpenSearch query
generation, and response generation using LLM.
"""

import logging
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
from app.models.query import (
    Query,
    QueryType,
    InterpretedIntent,
    QueryResults,
    TimeRange,
)
from app.models.base.metric import TimeBucket
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class QueryService:
    """Service for processing natural language queries."""
    
    # Query type keywords for classification
    QUERY_TYPE_KEYWORDS = {
        QueryType.STATUS: ["status", "health", "state", "current", "now", "active"],
        QueryType.TREND: ["trend", "over time", "history", "pattern", "change"],
        QueryType.PREDICTION: ["predict", "forecast", "future", "will", "expect"],
        QueryType.SECURITY: ["security", "vulnerability", "vulnerabilities", "threat", "risk", "cve"],
        QueryType.PERFORMANCE: ["performance", "latency", "response time", "throughput", "slow"],
        QueryType.COMPARISON: ["compare", "versus", "vs", "difference", "between"],
        QueryType.COMPLIANCE: ["compliance", "regulatory", "regulation", "gdpr", "hipaa", "soc2", "pci", "iso", "audit", "violation"],
    }
    
    # Entity keywords for extraction
    ENTITY_KEYWORDS = {
        "api": ["api", "apis", "endpoint", "endpoints", "service", "services"],
        "gateway": ["gateway", "gateways"],
        "metric": ["metric", "metrics", "measurement"],
        "prediction": ["prediction", "predictions", "forecast"],
        "vulnerability": ["vulnerability", "vulnerabilities", "security issue"],
        "recommendation": ["recommendation", "recommendations", "optimization", "suggestion"],
        "rate_limit": ["rate limit", "rate limiting", "throttle", "throttling"],
        "compliance": ["compliance", "violation", "violations", "regulatory", "audit"],
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
        prediction_agent: Optional[Any] = None,
        optimization_agent: Optional[Any] = None,
        security_agent: Optional[Any] = None,
        compliance_agent: Optional[Any] = None,
        compliance_repository: Optional[ComplianceRepository] = None,
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
            prediction_agent: Optional PredictionAgent for AI-enhanced prediction queries
            optimization_agent: Optional OptimizationAgent for AI-enhanced performance queries
            security_agent: Optional SecurityAgent for AI-enhanced security queries
            compliance_agent: Optional ComplianceAgent for AI-enhanced compliance queries
            compliance_repository: Optional ComplianceRepository for compliance operations
        """
        self.query_repo = query_repository
        self.api_repo = api_repository
        self.metrics_repo = metrics_repository
        self.prediction_repo = prediction_repository
        self.recommendation_repo = recommendation_repository
        self.compliance_repo = compliance_repository or ComplianceRepository()
        self.llm_service = llm_service
        self.prediction_agent = prediction_agent
        self.optimization_agent = optimization_agent
        self.security_agent = security_agent
        self.compliance_agent = compliance_agent
        
        # Cache for agent analysis results (5-minute TTL)
        self._agent_cache: Dict[str, Tuple[Any, float]] = {}
        self._cache_ttl = 300  # 5 minutes in seconds
    
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
        
        try:
            # Step 1: Classify query type
            query_type = self._classify_query_type(query_text)
            logger.info(f"Classified query as: {query_type}")
            
            # Step 2: Extract intent using LLM
            interpreted_intent, confidence = await self._extract_intent(
                query_text, query_type
            )
            logger.info(f"Extracted intent with confidence: {confidence}")
            
            # Step 3: Generate OpenSearch query
            opensearch_query = self._generate_opensearch_query(
                interpreted_intent, query_type
            )
            logger.info(f"Generated OpenSearch query")
            
            # Step 4: Execute query and get results
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
            
            # Save query to history
            saved_query = self.query_repo.create(query, doc_id=str(query.id))
            logger.info(f"Saved query to history: {saved_query.id}")
            
            return saved_query
            
        except Exception as e:
            logger.error(f"Failed to process query: {e}")
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
1. Action: What the user wants to do (list, count, analyze, compare, summarize)
2. Entities: What entities are involved (api, gateway, metric, prediction, vulnerability, recommendation, rate_limit)
3. Filters: Any filter conditions (severity, status, time range, etc.)
4. Time Range: If mentioned, extract start and end times

Respond in JSON format:
{
  "action": "list",
  "entities": ["api", "vulnerability"],
  "filters": {
    "severity": "critical",
    "status": "open"
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
            
            # Parse JSON response
            import json
            intent_data = json.loads(response["content"])
            
            # Extract time range if present
            time_range = None
            if "time_range" in intent_data and intent_data["time_range"]:
                time_range = TimeRange(
                    start=datetime.fromisoformat(intent_data["time_range"]["start"].replace("Z", "+00:00")),
                    end=datetime.fromisoformat(intent_data["time_range"]["end"].replace("Z", "+00:00")),
                )
            
            intent = InterpretedIntent(
                action=intent_data.get("action", "list"),
                entities=intent_data.get("entities", []),
                filters=intent_data.get("filters", {}),
                time_range=time_range,
            )
            
            confidence = intent_data.get("confidence", 0.8)
            
            return intent, confidence
            
        except Exception as e:
            logger.warning(f"LLM intent extraction failed, using fallback: {e}")
            # Fallback to keyword-based extraction
            return self._fallback_intent_extraction(query_text, query_type), 0.5

    def _fallback_intent_extraction(
        self, query_text: str, query_type: QueryType
    ) -> InterpretedIntent:
        """
        Fallback intent extraction using keyword matching.
        
        Args:
            query_text: Query text
            query_type: Classified query type
            
        Returns:
            Interpreted intent
        """
        query_lower = query_text.lower()
        
        # Extract action
        action = "list"
        for act, keywords in self.ACTION_KEYWORDS.items():
            if any(keyword in query_lower for keyword in keywords):
                action = act
                break
        
        # Extract entities
        entities = []
        for entity, keywords in self.ENTITY_KEYWORDS.items():
            if any(keyword in query_lower for keyword in keywords):
                entities.append(entity)
        
        # Extract basic filters
        filters = {}
        if "critical" in query_lower:
            filters["severity"] = "critical"
        if "high" in query_lower and "severity" not in filters:
            filters["severity"] = "high"
        if "open" in query_lower:
            filters["status"] = "open"
        if "active" in query_lower:
            filters["status"] = "active"
        
        return InterpretedIntent(
            action=action,
            entities=entities if entities else ["api"],
            filters=filters,
            time_range=None,
        )

    def _generate_opensearch_query(
        self, intent: InterpretedIntent, query_type: QueryType
    ) -> Dict[str, Any]:
        """
        Generate OpenSearch query DSL from interpreted intent.
        
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

    async def _enhance_with_prediction_agent(
        self,
        results: List[Any],
        intent: InterpretedIntent,
    ) -> List[Dict[str, Any]]:
        """
        Enhance query results with PredictionAgent insights.
        
        Args:
            results: Query results to enhance
            intent: Interpreted intent
            
        Returns:
            Enhanced results with agent insights
        """
        if not self.prediction_agent:
            logger.debug("PredictionAgent not available, skipping enhancement")
            return results
        
        enhanced_results = []
        
        # Limit to top 3 results to avoid latency
        for result in results[:3]:
            try:
                # Check cache first
                cache_key = f"pred_{result.get('id', '')}"
                cached_result = self._get_from_cache(cache_key)
                if cached_result:
                    enhanced_results.append(cached_result)
                    continue
                
                # Get API details
                api_id = result.get("id")
                api_name = result.get("name", "Unknown")
                gateway_id = result.get("gateway_id")
                
                if not gateway_id:
                    logger.warning(f"No gateway_id found for API {api_id}, skipping prediction enhancement")
                    enhanced_results.append(result)
                    continue
                
                # Fetch recent metrics for this API with appropriate time bucket
                time_bucket = self._determine_time_bucket(intent.time_range)
                
                # Build query with time bucket filter
                query = {
                    "bool": {
                        "must": [
                            {"term": {"api_id": api_id}},
                            {"term": {"time_bucket": time_bucket.value}}
                        ]
                    }
                }
                
                # Add time range if specified
                if intent.time_range:
                    query["bool"]["must"].append({
                        "range": {
                            "timestamp": {
                                "gte": intent.time_range.start.isoformat(),
                                "lte": intent.time_range.end.isoformat(),
                            }
                        }
                    })
                
                metrics, _ = self.metrics_repo.search(query, size=100)
                
                # Generate enhanced predictions
                agent_result = await self.prediction_agent.generate_enhanced_predictions(
                    gateway_id=gateway_id,
                    api_id=api_id,
                    api_name=api_name,
                    metrics=metrics,
                )
                
                # Merge agent insights with original result
                enhanced = {**result}
                enhanced["agent_insights"] = {
                    "type": "prediction",
                    "analysis": agent_result.get("analysis", ""),
                    "predictions": agent_result.get("predictions", []),
                    "metrics_analyzed": agent_result.get("metrics_analyzed", 0),
                }
                
                # Cache the result
                self._add_to_cache(cache_key, enhanced)
                enhanced_results.append(enhanced)
                
            except Exception as e:
                logger.warning(f"Failed to enhance result with PredictionAgent: {e}")
                enhanced_results.append(result)
        
        # Add remaining results without enhancement
        enhanced_results.extend(results[3:])
        return enhanced_results
    
    async def _enhance_with_optimization_agent(
        self,
        results: List[Any],
        intent: InterpretedIntent,
    ) -> List[Dict[str, Any]]:
        """
        Enhance query results with OptimizationAgent insights.
        
        Args:
            results: Query results to enhance
            intent: Interpreted intent
            
        Returns:
            Enhanced results with agent insights
        """
        if not self.optimization_agent:
            logger.debug("OptimizationAgent not available, skipping enhancement")
            return results
        
        enhanced_results = []
        
        # Limit to top 3 results to avoid latency
        for result in results[:3]:
            try:
                # Check cache first
                cache_key = f"opt_{result.get('id', '')}"
                cached_result = self._get_from_cache(cache_key)
                if cached_result:
                    enhanced_results.append(cached_result)
                    continue
                
                # Get API details
                api_id = result.get("id")
                api_name = result.get("name", "Unknown")
                
                # Fetch recent metrics for this API with appropriate time bucket
                time_bucket = self._determine_time_bucket(intent.time_range)
                
                # Build query with time bucket filter
                query = {
                    "bool": {
                        "must": [
                            {"term": {"api_id": api_id}},
                            {"term": {"time_bucket": time_bucket.value}}
                        ]
                    }
                }
                
                # Add time range if specified
                if intent.time_range:
                    query["bool"]["must"].append({
                        "range": {
                            "timestamp": {
                                "gte": intent.time_range.start.isoformat(),
                                "lte": intent.time_range.end.isoformat(),
                            }
                        }
                    })
                
                metrics, _ = self.metrics_repo.search(query, size=100)
                
                # Generate enhanced recommendations
                agent_result = await self.optimization_agent.generate_enhanced_recommendations(
                    api_id=api_id,
                    api_name=api_name,
                    metrics=metrics,
                )
                
                # Merge agent insights with original result
                enhanced = {**result}
                enhanced["agent_insights"] = {
                    "type": "optimization",
                    "performance_analysis": agent_result.get("performance_analysis", ""),
                    "recommendations": agent_result.get("recommendations", []),
                    "prioritization": agent_result.get("prioritization", ""),
                    "metrics_analyzed": agent_result.get("metrics_analyzed", 0),
                }
                
                # Cache the result
                self._add_to_cache(cache_key, enhanced)
                enhanced_results.append(enhanced)
                
            except Exception as e:
                logger.warning(f"Failed to enhance result with OptimizationAgent: {e}")
                enhanced_results.append(result)
        
        # Add remaining results without enhancement
        enhanced_results.extend(results[3:])
        return enhanced_results
    
    async def _enhance_with_security_agent(
        self,
        results: List[Any],
        intent: InterpretedIntent,
    ) -> List[Dict[str, Any]]:
        """
        Enhance query results with SecurityAgent insights.
        
        Args:
            results: Query results to enhance
            intent: Interpreted intent
            
        Returns:
            Enhanced results with agent insights
        """
        if not self.security_agent:
            logger.debug("SecurityAgent not available, skipping enhancement")
            return results
        
        enhanced_results = []
        
        # Limit to top 3 results to avoid latency
        for result in results[:3]:
            try:
                # Check cache first
                cache_key = f"sec_{result.get('id', '')}"
                cached_result = self._get_from_cache(cache_key)
                if cached_result:
                    enhanced_results.append(cached_result)
                    continue
                
                # Get API details
                api_id = result.get("id")
                api_name = result.get("name", "Unknown")
                
                # Fetch API object for security analysis
                api = self.api_repo.get(str(api_id))
                if not api:
                    logger.warning(f"API {api_id} not found for security analysis")
                    enhanced_results.append(result)
                    continue
                
                # Perform security analysis
                agent_result = await self.security_agent.analyze_api_security(api)
                
                # Merge agent insights with original result
                enhanced = {**result}
                enhanced["agent_insights"] = {
                    "type": "security",
                    "vulnerabilities": agent_result.get("vulnerabilities", []),
                    "compliance_issues": agent_result.get("compliance_issues", []),
                    "remediation_plan": agent_result.get("remediation_plan", {}),  # Structured dict, not string
                    "total_vulnerabilities": len(agent_result.get("vulnerabilities", [])),
                    "critical_count": sum(
                        1 for v in agent_result.get("vulnerabilities", [])
                        if v.get("severity") == "critical"
                    ),
                    # Include per-vulnerability plan summary
                    "has_per_vulnerability_plans": any(
                        v.get("recommended_remediation") is not None
                        for v in agent_result.get("vulnerabilities", [])
                    ),
                }
                
                # Cache the result
                self._add_to_cache(cache_key, enhanced)
                enhanced_results.append(enhanced)
                
            except Exception as e:
                logger.warning(f"Failed to enhance result with SecurityAgent: {e}")
                enhanced_results.append(result)
        
        # Add remaining results without enhancement
        enhanced_results.extend(results[3:])
        return enhanced_results
    
    async def _enhance_with_compliance_agent(
        self,
        results: List[Any],
        intent: InterpretedIntent,
    ) -> List[Dict[str, Any]]:
        """
        Enhance query results with ComplianceAgent insights.
        
        Args:
            results: Query results to enhance
            intent: Interpreted intent
            
        Returns:
            Enhanced results with agent insights
        """
        if not self.compliance_agent:
            logger.debug("ComplianceAgent not available, skipping enhancement")
            return results
        
        enhanced_results = []
        
        # Limit to top 3 results to avoid latency
        for result in results[:3]:
            try:
                # Check cache first
                cache_key = f"comp_{result.get('id', '')}"
                cached_result = self._get_from_cache(cache_key)
                if cached_result:
                    enhanced_results.append(cached_result)
                    continue
                
                # Get API details if this is a compliance violation
                api_id = result.get("api_id")
                if not api_id:
                    enhanced_results.append(result)
                    continue
                
                # Fetch API object for compliance analysis
                api = self.api_repo.get(str(api_id))
                if not api:
                    logger.warning(f"API {api_id} not found for compliance analysis")
                    enhanced_results.append(result)
                    continue
                
                # Perform compliance analysis
                agent_result = await self.compliance_agent.analyze_api_compliance(api)
                
                # Merge agent insights with original result
                enhanced = {**result}
                enhanced["agent_insights"] = {
                    "type": "compliance",
                    "violations": agent_result.get("violations", []),
                    "standards_checked": agent_result.get("standards_checked", []),
                    "compliance_score": agent_result.get("compliance_score", 0),
                    "audit_evidence": agent_result.get("audit_evidence", []),
                    "total_violations": len(agent_result.get("violations", [])),
                    "critical_count": sum(
                        1 for v in agent_result.get("violations", [])
                        if v.get("severity") == "critical"
                    ),
                }
                
                # Cache the result
                self._add_to_cache(cache_key, enhanced)
                enhanced_results.append(enhanced)
                
            except Exception as e:
                logger.warning(f"Failed to enhance result with ComplianceAgent: {e}")
                enhanced_results.append(result)
        
        # Add remaining results without enhancement
        enhanced_results.extend(results[3:])
        return enhanced_results
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get result from cache if not expired."""
        if key in self._agent_cache:
            result, timestamp = self._agent_cache[key]
            if time.time() - timestamp < self._cache_ttl:
                return result
            else:
                del self._agent_cache[key]
        return None
    
    def _add_to_cache(self, key: str, result: Any) -> None:
        """Add result to cache with current timestamp."""
        self._agent_cache[key] = (result, time.time())

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
            
            if primary_entity == "api":
                results, total = self.api_repo.search(
                    opensearch_query["query"], size=50
                )
                data = [api.model_dump(mode="json") for api in results]
            elif primary_entity == "prediction":
                results, total = self.prediction_repo.search(
                    opensearch_query["query"], size=50
                )
                data = [pred.model_dump(mode="json") for pred in results]
            elif primary_entity == "vulnerability":
                # Would query vulnerability repository
                data = []
                total = 0
            elif primary_entity == "recommendation":
                results, total = self.recommendation_repo.search(
                    opensearch_query["query"], size=50
                )
                data = [rec.model_dump(mode="json") for rec in results]
            elif primary_entity == "compliance":
                results, total = self.compliance_repo.search(
                    opensearch_query["query"], size=50
                )
                data = [comp.model_dump(mode="json") for comp in results]
            else:
                data = []
                total = 0
            
            # Enhance results with agent insights for specific query types
            if query_type == QueryType.PREDICTION and self.prediction_agent and data:
                logger.info("Enhancing results with PredictionAgent")
                data = await self._enhance_with_prediction_agent(data, intent)
            elif query_type == QueryType.PERFORMANCE and self.optimization_agent and data:
                logger.info("Enhancing results with OptimizationAgent")
                data = await self._enhance_with_optimization_agent(data, intent)
            elif query_type == QueryType.SECURITY and self.security_agent and data:
                logger.info("Enhancing results with SecurityAgent")
                data = await self._enhance_with_security_agent(data, intent)
            elif query_type == QueryType.COMPLIANCE and self.compliance_agent and data:
                logger.info("Enhancing results with ComplianceAgent")
                data = await self._enhance_with_compliance_agent(data, intent)
            
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
        # Check if results contain agent insights
        has_agent_insights = any(
            isinstance(item, dict) and "agent_insights" in item
            for item in results.data
        )
        
        if has_agent_insights:
            system_prompt = """You are an AI assistant for API management with access to advanced AI agent analysis. Generate a clear, insightful response that incorporates the AI agent insights.

Guidelines:
- Highlight key insights from the AI agent analysis
- Be specific and use numbers from the results
- Explain predictions or recommendations in context
- Keep responses under 250 words
- Use professional but friendly tone
- Emphasize actionable insights from the agent analysis"""
        else:
            system_prompt = """You are an AI assistant for API management. Generate a clear, concise response to the user's query based on the results.

Guidelines:
- Be specific and use numbers from the results
- Highlight important findings
- Keep responses under 200 words
- Use professional but friendly tone
- If no results, explain why and suggest alternatives"""

        # Prepare results summary
        results_summary = f"Found {results.count} results in {results.execution_time}ms"
        if results.data:
            # Include agent insights in summary if present
            if has_agent_insights:
                results_summary += "\n\nResults with AI Agent Insights:"
                for item in results.data[:3]:
                    if isinstance(item, dict) and "agent_insights" in item:
                        insights = item["agent_insights"]
                        results_summary += f"\n\nAPI: {item.get('name', 'Unknown')}"
                        results_summary += f"\nAgent Type: {insights.get('type', 'unknown')}"
                        if insights.get('analysis'):
                            results_summary += f"\nAnalysis: {insights['analysis'][:200]}..."
                        if insights.get('performance_analysis'):
                            results_summary += f"\nPerformance: {insights['performance_analysis'][:200]}..."
                        if insights.get('compliance_score') is not None:
                            results_summary += f"\nCompliance Score: {insights['compliance_score']}"
                        if insights.get('total_violations'):
                            results_summary += f"\nTotal Violations: {insights['total_violations']}"
            else:
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
                max_tokens=400 if has_agent_insights else 300,
            )
            return response["content"]
        except Exception as e:
            logger.warning(f"LLM response generation failed, using fallback: {e}")
            # Fallback response
            if results.count == 0:
                return f"I couldn't find any {intent.entities[0] if intent.entities else 'items'} matching your criteria. Try adjusting your filters or time range."
            else:
                agent_note = " (including AI agent insights)" if has_agent_insights else ""
                return f"I found {results.count} {intent.entities[0] if intent.entities else 'items'} matching your query{agent_note}."

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
        
        # Check if results contain agent insights
        has_agent_insights = any(
            isinstance(item, dict) and "agent_insights" in item
            for item in results.data
        )
        
        if results.count > 0:
            primary_entity = intent.entities[0] if intent.entities else "item"
            
            # Add agent-specific follow-ups if insights are present
            if has_agent_insights:
                agent_type = None
                for item in results.data:
                    if isinstance(item, dict) and "agent_insights" in item:
                        agent_type = item["agent_insights"].get("type")
                        break
                
                if agent_type == "prediction":
                    follow_ups.extend([
                        "What are the key factors driving these predictions?",
                        "Show me the confidence levels for these predictions",
                        "What preventive actions are recommended?",
                    ])
                elif agent_type == "optimization":
                    follow_ups.extend([
                        "What's the expected impact of these optimizations?",
                        "Show me the implementation priority order",
                        "What are the resource requirements?",
                    ])
                elif agent_type == "compliance":
                    follow_ups.extend([
                        "What are the remediation steps for these violations?",
                        "Show me the audit evidence for these findings",
                        "Which compliance standards are most affected?",
                    ])
            
            # Suggest related queries based on entity type
            if primary_entity == "api":
                follow_ups.extend([
                    "Show me the performance metrics for these APIs",
                    "Are there any predictions for these APIs?",
                    "What security vulnerabilities affect these APIs?",
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
        else:
            follow_ups.extend([
                "Show me all active APIs",
                "What are the recent predictions?",
                "Show me critical security issues",
            ])
        
        return follow_ups[:5]  # Limit to 5 suggestions


# Made with Bob