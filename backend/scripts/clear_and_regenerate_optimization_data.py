#!/usr/bin/env python3
"""
Clear and Regenerate Performance Optimization Data

This script:
1. Clears existing optimization recommendations and rate limit policies
2. Regenerates fresh mock data with unified optimization approach
3. Includes caching, compression, and rate limiting recommendations

Usage:
    python scripts/clear_and_regenerate_optimization_data.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from opensearchpy import OpenSearch
from app.db.client import get_client


async def clear_optimization_data():
    """Clear optimization recommendations and rate limit policies from OpenSearch."""
    print("=" * 80)
    print("CLEARING PERFORMANCE OPTIMIZATION DATA")
    print("=" * 80)
    
    client = get_client()
    
    # Indices to clear
    indices = [
        "optimization-recommendations",
        "rate-limit-policies",
    ]
    
    for index in indices:
        try:
            print(f"\n🗑️  Deleting index: {index}")
            client.indices.delete(index=index, ignore=[404])
            print(f"✅ Deleted: {index}")
        except Exception as e:
            print(f"⚠️  Error deleting {index}: {e}")
    
    print("\n" + "=" * 80)
    print("✅ OPTIMIZATION DATA CLEARED")
    print("=" * 80)


async def recreate_indices():
    """Recreate optimization indices."""
    print("\n" + "=" * 80)
    print("RECREATING OPTIMIZATION INDICES")
    print("=" * 80)
    
    from app.db.migrations import (
        create_optimization_recommendations_index,
        create_rate_limit_policies_index,
    )
    
    client = get_client()
    
    try:
        print("\n📋 Creating optimization-recommendations index...")
        create_optimization_recommendations_index(client)
        print("✅ optimization-recommendations index created")
    except Exception as e:
        print(f"⚠️  Error creating optimization-recommendations: {e}")
    
    try:
        print("\n📋 Creating rate-limit-policies index...")
        create_rate_limit_policies_index(client)
        print("✅ rate-limit-policies index created")
    except Exception as e:
        print(f"⚠️  Error creating rate-limit-policies: {e}")
    
    print("\n" + "=" * 80)
    print("✅ INDICES RECREATED")
    print("=" * 80)


async def generate_optimization_data():
    """Generate fresh optimization mock data."""
    print("\n" + "=" * 80)
    print("GENERATING FRESH OPTIMIZATION DATA")
    print("=" * 80)
    
    scripts = [
        ("Unified Optimization Recommendations", "generate_mock_optimizations.py"),
        ("Rate Limit Policies", "generate_mock_rate_limits.py"),
    ]
    
    for name, script in scripts:
        print(f"\n📊 Generating {name}...")
        try:
            import subprocess
            result = subprocess.run(
                ["python", f"scripts/{script}"],
                cwd=Path(__file__).parent.parent,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                print(f"✅ {name} generated successfully")
                if result.stdout:
                    # Print only summary lines
                    for line in result.stdout.split('\n'):
                        if '✅' in line or '📊' in line or 'Generated' in line:
                            print(f"  {line}")
            else:
                print(f"⚠️  Warning generating {name}")
                if result.stderr:
                    print(result.stderr)
        except Exception as e:
            print(f"❌ Error generating {name}: {e}")
    
    print("\n" + "=" * 80)
    print("✅ OPTIMIZATION DATA GENERATED")
    print("=" * 80)


async def main():
    """Main execution function."""
    print("\n" + "=" * 80)
    print("PERFORMANCE OPTIMIZATION DATA REFRESH")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    try:
        # Step 1: Clear existing optimization data
        await clear_optimization_data()
        
        # Step 2: Recreate indices
        await recreate_indices()
        
        # Step 3: Generate fresh optimization data
        await generate_optimization_data()
        
        print("\n" + "=" * 80)
        print("✅ OPTIMIZATION DATA REFRESH COMPLETE")
        print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        print("\n📝 Summary:")
        print("  - Old optimization recommendations cleared")
        print("  - Old rate limit policies cleared")
        print("  - Indices recreated")
        print("  - Fresh unified optimization data generated")
        print("  - Includes: caching, compression, and rate limiting recommendations")
        print("\n🚀 Performance optimization feature ready with fresh data!")
        
    except Exception as e:
        print(f"\n❌ Error during optimization data refresh: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

# Made with Bob
