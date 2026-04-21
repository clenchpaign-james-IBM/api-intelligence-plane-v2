"""
Schema-Aware LLM Query Generator

Generates OpenSearch DSL queries from natural language using LLM with schema context.
Provides few-shot learning examples and validates generated queries against schema.
"""

import json
import logging
import re
from typing import Dict, Any, Optional

from app.services.llm_service import LLMService
from .schema_registry import SchemaRegistry
from .concept_mapper import ConceptMapper, ConceptCategory
from .validator import QueryValidator

logger = logging.getLogger(__name__)


class SchemaAwareLLMQueryGenerator:
    """
    Generate OpenSearch queries using LLM with schema awareness.
    
    Features:
    - Schema-aware prompt generation
    - Few-shot learning with examples
    - DSL parsing and validation
    - Error recovery with retry logic
    - Query complexity handling
    
    Example:
        >>> generator = SchemaAwareLLMQueryGenerator(llm_service, schema_registry, concept_mapper, validator)
        >>> dsl = await generator.generate_query("Show me insecure APIs", "api-inventory")
        >>> # Returns: {"query": {"range": {"intelligence_metadata.security_score": {"lt": 50}}}}
    """
    
    def __init__(
        self,
        llm_service: LLMService,
        schema_registry: SchemaRegistry,
        concept_mapper: ConceptMapper,
        validator: QueryValidator
    ):
        """
        Initialize the LLM query generator.
        
        Args:
            llm_service: LLM service for generating completions
            schema_registry: Schema registry for field validation
            concept_mapper: Concept mapper for domain knowledge
            validator: Query validator for DSL validation
        """
        self.llm_service = llm_service
        self.schema_registry = schema_registry
        self.concept_mapper = concept_mapper
        self.validator = validator
        self.max_retries = 2
    
    async def generate_query(
        self,
        query_text: str,
        index: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate OpenSearch DSL query from natural language.
        
        Args:
            query_text: Natural language query
            index: Target OpenSearch index
            context: Optional context (e.g., time range, filters)
            
        Returns:
            OpenSearch DSL query dictionary
            
        Raises:
            ValueError: If query generation fails after retries
        """
        # Get schema context
        schema_context = self.schema_registry.get_schema_context(index)
        
        # Build enhanced prompt with schema and examples
        system_prompt = self._build_system_prompt(schema_context, index)
        
        # Try to generate query with retries
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                # Generate DSL using LLM
                user_message = self._build_user_message(query_text, context, last_error)
                
                response = await self.llm_service.generate_completion(
                    messages=[{"role": "user", "content": user_message}],
                    system_prompt=system_prompt,
                    temperature=0.1,  # Low temperature for consistency
                    max_tokens=1500
                )
                
                # Check if response content is empty
                content = response.get("content", "")
                if not content or not content.strip():
                    logger.warning(f"LLM returned empty content (attempt {attempt + 1})")
                    last_error = "LLM returned empty response"
                    if attempt == self.max_retries:
                        raise ValueError(f"Failed to generate query: {last_error}")
                    continue
                
                # Parse DSL from response
                dsl = self._parse_dsl(content)
                
                # Validate DSL
                is_valid, error = self.validator.validate(dsl, index)
                
                if is_valid:
                    logger.info(f"Successfully generated query for: {query_text}")
                    return dsl
                else:
                    logger.warning(f"Generated invalid query (attempt {attempt + 1}): {error}")
                    last_error = error
                    
                    if attempt == self.max_retries:
                        raise ValueError(f"Failed to generate valid query after {self.max_retries + 1} attempts: {error}")
                    
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse DSL (attempt {attempt + 1}): {e}")
                last_error = f"JSON parsing error: {str(e)}"
                
                if attempt == self.max_retries:
                    raise ValueError(f"Failed to parse generated DSL: {e}")
            
            except Exception as e:
                logger.error(f"Error generating query (attempt {attempt + 1}): {e}", exc_info=True)
                last_error = str(e)
                
                if attempt == self.max_retries:
                    raise ValueError(f"Failed to generate query: {e}")
        
        raise ValueError("Query generation failed unexpectedly")
    
    def _build_system_prompt(self, schema_context: str, index: str) -> str:
        """
        Build system prompt with schema context and examples.
        
        Args:
            schema_context: Schema context string from registry
            index: Target index name
            
        Returns:
            System prompt string
        """
        # Get relevant concepts for this index
        security_concepts = self.concept_mapper.get_concepts_by_category(ConceptCategory.SECURITY)
        health_concepts = self.concept_mapper.get_concepts_by_category(ConceptCategory.HEALTH)
        
        prompt = f"""You are an expert at translating natural language queries into OpenSearch DSL queries.

SCHEMA CONTEXT:
{schema_context}

IMPORTANT RULES:
1. Only use fields that exist in the schema above
2. Use correct field types:
   - keyword fields: Use "term" for exact match
   - text fields: Use "match" for full-text search
   - numeric fields: Use "range" for comparisons
3. For nested fields, use dot notation (e.g., intelligence_metadata.security_score)
4. For score-based fields, use appropriate thresholds:
   - High: >= 70
   - Medium: 40-70
   - Low: < 40
5. Handle negations correctly:
   - "not secure" means security_score < 70
   - "not active" means status != "active"
6. For status fields, use exact values: "active", "inactive", "deprecated", "failed"
7. For nested arrays (policy_actions, endpoints), use nested queries
8. Always return valid JSON

DOMAIN CONCEPTS:
Security: {', '.join(security_concepts[:5])}
Health: {', '.join(health_concepts[:5])}

EXAMPLES:

Query: "Show me insecure APIs"
DSL:
{{
  "query": {{
    "range": {{
      "intelligence_metadata.security_score": {{
        "lt": 50
      }}
    }}
  }}
}}

Query: "Which APIs are active and have high risk?"
DSL:
{{
  "query": {{
    "bool": {{
      "must": [
        {{"term": {{"status": "active"}}}},
        {{"range": {{"intelligence_metadata.risk_score": {{"gte": 70}}}}}}
      ]
    }}
  }}
}}

Query: "Find APIs with authentication but no rate limiting"
DSL:
{{
  "query": {{
    "bool": {{
      "must": [
        {{
          "nested": {{
            "path": "policy_actions",
            "query": {{
              "term": {{"policy_actions.action_type": "authentication"}}
            }}
          }}
        }}
      ],
      "must_not": [
        {{
          "nested": {{
            "path": "policy_actions",
            "query": {{
              "term": {{"policy_actions.action_type": "rate_limiting"}}
            }}
          }}
        }}
      ]
    }}
  }}
}}

Query: "Show me shadow APIs"
DSL:
{{
  "query": {{
    "term": {{
      "intelligence_metadata.is_shadow": true
    }}
  }}
}}

Query: "Find unhealthy APIs that are not deprecated"
DSL:
{{
  "query": {{
    "bool": {{
      "must": [
        {{"range": {{"intelligence_metadata.health_score": {{"lt": 50}}}}}}
      ],
      "must_not": [
        {{"term": {{"status": "deprecated"}}}}
      ]
    }}
  }}
}}

RESPONSE FORMAT:
Return ONLY the OpenSearch DSL query as valid JSON. Do not include explanations or markdown formatting.
"""
        return prompt
    
    def _build_user_message(
        self,
        query_text: str,
        context: Optional[Dict[str, Any]],
        last_error: Optional[str]
    ) -> str:
        """
        Build user message with query and optional context.
        
        Args:
            query_text: Natural language query
            context: Optional context information
            last_error: Error from previous attempt (for retry)
            
        Returns:
            User message string
        """
        message = f"Query: \"{query_text}\"\n"
        
        if context:
            message += f"\nContext: {json.dumps(context, indent=2)}\n"
        
        if last_error:
            message += f"\nPrevious attempt failed with error: {last_error}\n"
            message += "Please fix the error and generate a valid query.\n"
        
        message += "\nDSL:"
        
        return message
    
    def _parse_dsl(self, response_content: str) -> Dict[str, Any]:
        """
        Parse DSL from LLM response.
        
        Args:
            response_content: LLM response content
            
        Returns:
            Parsed DSL dictionary
            
        Raises:
            json.JSONDecodeError: If parsing fails
        """
        # Remove markdown code blocks if present
        content = response_content.strip()
        
        # Remove ```json and ``` markers
        if content.startswith("```"):
            # Find the first newline after ```
            start = content.find("\n")
            if start != -1:
                content = content[start + 1:]
            
            # Remove trailing ```
            if content.endswith("```"):
                content = content[:-3]
        
        content = content.strip()
        
        # Try to extract JSON from response
        # Look for first { and last }
        start_idx = content.find("{")
        end_idx = content.rfind("}")
        
        if start_idx != -1 and end_idx != -1:
            content = content[start_idx:end_idx + 1]
        
        # Parse JSON
        try:
            dsl: Dict[str, Any] = json.loads(content)
            return dsl
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse DSL: {content}")
            raise
    
    def _extract_fields(self, dsl: Dict[str, Any]) -> set[str]:
        """
        Extract all field references from DSL query.
        
        Args:
            dsl: DSL query dictionary
            
        Returns:
            Set of field names
        """
        fields = set()
        
        def recurse(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    # Skip operator keys
                    if key not in ["query", "bool", "must", "must_not", "should", "filter", 
                                   "range", "term", "match", "nested", "path"]:
                        fields.add(key)
                    recurse(value)
            elif isinstance(obj, list):
                for item in obj:
                    recurse(item)
        
        recurse(dsl)
        return fields
    
    async def explain_query(self, dsl: Dict[str, Any], index: str) -> str:
        """
        Generate natural language explanation of DSL query.
        
        Args:
            dsl: OpenSearch DSL query
            index: Target index name
            
        Returns:
            Natural language explanation
        """
        system_prompt = """You are an expert at explaining OpenSearch queries in simple terms.
        
Explain the query in a clear, concise way that a non-technical user can understand.
Focus on what data will be returned and what conditions are being applied."""
        
        user_message = f"Explain this OpenSearch query:\n\n{json.dumps(dsl, indent=2)}"
        
        try:
            response = await self.llm_service.generate_completion(
                messages=[{"role": "user", "content": user_message}],
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=500
            )
            
            content: str = response["content"]
            return content
            
        except Exception as e:
            logger.error(f"Failed to explain query: {e}")
            return "Unable to generate explanation"

# Made with Bob