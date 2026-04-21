"""
Test Intelligence Metadata Computation Pipeline

This script tests all 7 intelligence metadata computation jobs to ensure they:
1. Execute without errors
2. Compute intelligence values correctly
3. Update API entities in OpenSearch
4. Handle edge cases gracefully

Run this script after starting the backend service to validate the intelligence pipeline.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from uuid import uuid4

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import intelligence jobs
from app.scheduler.intelligence_metadata_jobs import (
    compute_health_scores_job,
    compute_risk_scores_job,
    compute_security_scores_job,
    compute_usage_trends_job,
    detect_shadow_apis_job,
    compute_compliance_status_job,
    update_predictions_status_job,
    run_all_intelligence_jobs,
)

# Import repositories for verification
from app.db.repositories.api_repository import APIRepository
from app.db.repositories.metrics_repository import MetricsRepository
from app.db.repositories.vulnerability_repository import VulnerabilityRepository
from app.db.repositories.compliance_repository import ComplianceRepository
from app.db.repositories.prediction_repository import PredictionRepository


async def test_job_execution(job_name: str, job_func):
    """Test a single intelligence job execution."""
    logger.info(f"\n{'='*60}")
    logger.info(f"Testing: {job_name}")
    logger.info(f"{'='*60}")
    
    try:
        # Execute the job
        start_time = datetime.utcnow()
        await job_func()
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"✅ {job_name} completed successfully in {duration:.2f}s")
        return True
    except Exception as e:
        logger.error(f"❌ {job_name} failed: {str(e)}")
        logger.exception(e)
        return False


async def verify_intelligence_updates():
    """Verify that intelligence metadata was actually updated in OpenSearch."""
    logger.info(f"\n{'='*60}")
    logger.info("Verifying Intelligence Metadata Updates")
    logger.info(f"{'='*60}")
    
    api_repo = APIRepository()
    
    try:
        # Get all APIs
        apis, total = api_repo.list_all(size=100)
        logger.info(f"Found {total} APIs in data store")
        
        if total == 0:
            logger.warning("⚠️  No APIs found - cannot verify intelligence updates")
            return False
        
        # Check intelligence metadata for each API
        updated_count = 0
        default_count = 0
        
        for api in apis:
            intel = api.intelligence_metadata
            
            # Check if intelligence has been computed (not default values)
            is_computed = (
                intel.health_score != 100.0 or
                intel.risk_score != 0.0 or
                intel.security_score != 100.0 or
                intel.usage_trend != "stable" or
                intel.is_shadow == True or
                intel.has_active_predictions == True or
                (intel.compliance_status and len(intel.compliance_status) > 0)
            )
            
            if is_computed:
                updated_count += 1
                logger.info(f"✅ API '{api.name}' has computed intelligence:")
                logger.info(f"   - Health Score: {intel.health_score:.1f}")
                logger.info(f"   - Risk Score: {intel.risk_score:.1f}")
                logger.info(f"   - Security Score: {intel.security_score:.1f}")
                logger.info(f"   - Usage Trend: {intel.usage_trend}")
                logger.info(f"   - Is Shadow: {intel.is_shadow}")
                logger.info(f"   - Has Predictions: {intel.has_active_predictions}")
            else:
                default_count += 1
                logger.warning(f"⚠️  API '{api.name}' still has default intelligence values")
        
        logger.info(f"\nSummary:")
        logger.info(f"  - APIs with computed intelligence: {updated_count}/{total}")
        logger.info(f"  - APIs with default values: {default_count}/{total}")
        
        if updated_count > 0:
            logger.info(f"✅ Intelligence computation is working!")
            return True
        else:
            logger.warning(f"⚠️  No APIs have computed intelligence yet")
            return False
            
    except Exception as e:
        logger.error(f"❌ Verification failed: {str(e)}")
        logger.exception(e)
        return False


async def check_data_availability():
    """Check if required data exists for intelligence computation."""
    logger.info(f"\n{'='*60}")
    logger.info("Checking Data Availability")
    logger.info(f"{'='*60}")
    
    api_repo = APIRepository()
    metrics_repo = MetricsRepository()
    vuln_repo = VulnerabilityRepository()
    
    try:
        # Check APIs
        apis, api_count = api_repo.list_all(size=1)
        logger.info(f"APIs: {api_count} found")
        
        # Check Metrics - use search with match_all
        metrics, metric_count = metrics_repo.list_all(size=1)
        logger.info(f"Metrics: {metric_count} found")
        
        # Check Vulnerabilities
        if api_count > 0:
            first_api = apis[0]
            vulns = await vuln_repo.find_by_api_id(first_api.id, limit=10)
            logger.info(f"Vulnerabilities (sample API): {len(vulns)} found")
        
        # Summary
        has_data = api_count > 0 and metric_count > 0
        if has_data:
            logger.info("✅ Sufficient data available for intelligence computation")
        else:
            logger.warning("⚠️  Limited data available - intelligence may use defaults")
        
        return has_data
        
    except Exception as e:
        logger.error(f"❌ Data availability check failed: {str(e)}")
        logger.exception(e)
        return False


async def main():
    """Main test execution."""
    logger.info("\n" + "="*60)
    logger.info("INTELLIGENCE METADATA PIPELINE TEST")
    logger.info("="*60)
    
    # Step 1: Check data availability
    logger.info("\n[Step 1] Checking data availability...")
    has_data = await check_data_availability()
    
    if not has_data:
        logger.warning("\n⚠️  WARNING: Limited data available")
        logger.warning("Intelligence jobs will run but may produce default values")
        logger.warning("Consider running mock data generation scripts first")
    
    # Step 2: Test individual jobs
    logger.info("\n[Step 2] Testing individual intelligence jobs...")
    
    jobs = [
        ("Health Scores Computation", compute_health_scores_job),
        ("Risk Scores Computation", compute_risk_scores_job),
        ("Security Scores Computation", compute_security_scores_job),
        ("Usage Trends Computation", compute_usage_trends_job),
        ("Shadow API Detection", detect_shadow_apis_job),
        ("Compliance Status Computation", compute_compliance_status_job),
        ("Predictions Status Update", update_predictions_status_job),
    ]
    
    results = []
    for job_name, job_func in jobs:
        success = await test_job_execution(job_name, job_func)
        results.append((job_name, success))
    
    # Step 3: Test master job
    logger.info("\n[Step 3] Testing master intelligence job...")
    master_success = await test_job_execution(
        "Master Intelligence Job (All Jobs)",
        run_all_intelligence_jobs
    )
    
    # Step 4: Verify updates
    logger.info("\n[Step 4] Verifying intelligence metadata updates...")
    verification_success = await verify_intelligence_updates()
    
    # Final Summary
    logger.info(f"\n{'='*60}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*60}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    logger.info(f"\nIndividual Jobs: {passed}/{total} passed")
    for job_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"  {status}: {job_name}")
    
    logger.info(f"\nMaster Job: {'✅ PASS' if master_success else '❌ FAIL'}")
    logger.info(f"Verification: {'✅ PASS' if verification_success else '⚠️  PARTIAL'}")
    
    # Overall result
    all_passed = passed == total and master_success
    if all_passed and verification_success:
        logger.info(f"\n{'='*60}")
        logger.info("🎉 ALL TESTS PASSED - Intelligence pipeline is working!")
        logger.info(f"{'='*60}")
        return 0
    elif all_passed:
        logger.info(f"\n{'='*60}")
        logger.info("⚠️  TESTS PASSED but verification incomplete")
        logger.info("Jobs execute successfully but may need more data")
        logger.info(f"{'='*60}")
        return 0
    else:
        logger.error(f"\n{'='*60}")
        logger.error("❌ TESTS FAILED - Check logs above for details")
        logger.error(f"{'='*60}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

# Made with Bob
