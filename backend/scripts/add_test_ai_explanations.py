#!/usr/bin/env python3
"""
TEMPORARY TEST SCRIPT - Add AI explanations to some predictions for UI testing
This will be removed after testing
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.repositories.prediction_repository import PredictionRepository

def main():
    """Add AI explanations to first 5 predictions for testing."""
    print("Adding AI explanations to predictions for UI testing...")
    print("=" * 70)
    
    pred_repo = PredictionRepository()
    
    # Search for predictions to get their OpenSearch _id
    result = pred_repo.client.search(
        index=pred_repo.index_name,
        body={
            "query": {"match_all": {}},
            "size": 10
        }
    )
    
    hits = result['hits']['hits']
    print(f"Found {len(hits)} predictions")
    print(f"Adding AI explanations to first 5 predictions...\n")
    
    for i, hit in enumerate(hits[:5], 1):
        doc_id = hit['_id']
        pred_data = hit['_source']
        
        # Add AI explanation to metadata
        if 'metadata' not in pred_data:
            pred_data['metadata'] = {}
        
        pred_data['metadata']['ai_explanation'] = f"""**{pred_data['prediction_type'].replace('_', ' ').title()} Prediction Analysis**

Based on comprehensive analysis of recent metrics and historical patterns, this prediction indicates a {pred_data['severity']} risk scenario for {pred_data.get('api_name', 'Unknown API')}.

**Key Factors:**
• {pred_data['contributing_factors'][0]['factor'].replace('_', ' ').title()}: Current value {pred_data['contributing_factors'][0]['current_value']:.2f} exceeds threshold {pred_data['contributing_factors'][0]['threshold']:.2f}
• Trend analysis shows {pred_data['contributing_factors'][0]['trend']} pattern over the last 24 hours
• Confidence level: {pred_data['confidence_score']:.1%} based on {len(pred_data['contributing_factors'])} contributing factors

**Recommended Actions:**
The system recommends immediate attention to prevent potential service degradation. Priority actions include monitoring the identified metrics and implementing the suggested remediation steps.

**Impact Assessment:**
If left unaddressed, this could affect API availability and user experience. The prediction window allows sufficient time for preventive measures."""
        
        # Update prediction using OpenSearch document ID
        pred_repo.update(doc_id, {"metadata": pred_data['metadata']})
        print(f"  [{i}/5] Added AI explanation to: {pred_data.get('api_name', 'Unknown')} ({pred_data['prediction_type']})")
    
    print(f"\n{'=' * 70}")
    print("✓ AI explanations added successfully!")
    print("  Refresh the frontend to see the 'AI Enhanced' badges")
    print("=" * 70)

if __name__ == "__main__":
    main()

# Made with Bob
