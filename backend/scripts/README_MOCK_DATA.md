# Mock Data Generators

This directory contains scripts for generating realistic mock data for testing and development purposes.

## Available Generators

### 1. Compliance Violations (`generate_mock_compliance.py`)

Generates realistic compliance violation data across 5 compliance standards (GDPR, HIPAA, SOC2, PCI-DSS, ISO 27001).

**Usage:**

```bash
# Generate violations for a specific API
python backend/scripts/generate_mock_compliance.py --api-id <API_UUID> --count 10

# Generate violations for all APIs in the system
python backend/scripts/generate_mock_compliance.py --all-apis --count 5

# Generate violations for specific compliance standards only
python backend/scripts/generate_mock_compliance.py --api-id <API_UUID> --standards gdpr hipaa --count 8

# Generate violations for all APIs with specific standards
python backend/scripts/generate_mock_compliance.py --all-apis --standards pci_dss soc2 --count 3
```

**Options:**
- `--api-id`: Specific API ID to generate violations for
- `--count`: Number of violations to generate per API (default: 10)
- `--all-apis`: Generate violations for all APIs in the system
- `--standards`: Specific compliance standards (choices: gdpr, hipaa, soc2, pci_dss, iso_27001)

**Features:**
- Generates violations with realistic severity distribution (15% critical, 30% high, 35% medium, 20% low)
- Creates violations with various statuses (50% open, 25% in progress, 15% remediated, 8% accepted risk, 2% false positive)
- Includes evidence from multiple sources (gateway config, traffic logs, policy evaluation)
- Generates complete audit trails for each violation
- Creates remediation documentation for remediated violations
- Maps violations to specific regulatory clauses
- Calculates remediation deadlines based on severity

### 2. Predictions (`generate_mock_predictions.py`)

Generates realistic prediction data for API failure predictions.

**Usage:**

```bash
# Generate predictions for a specific API
python backend/scripts/generate_mock_predictions.py --api-id <API_UUID> --count 10
```

### 3. Optimization Recommendations (`generate_mock_optimizations.py`)

Generates realistic optimization recommendation data.

**Usage:**

```bash
# Generate recommendations for a specific API
python backend/scripts/generate_mock_optimizations.py --api-id <API_UUID> --count 5
```

## Prerequisites

1. **OpenSearch Running**: Ensure OpenSearch is running and accessible
2. **Indices Created**: Run the OpenSearch initialization script first:
   ```bash
   python backend/scripts/init_opensearch.py
   ```
3. **APIs Exist**: For `--all-apis` option, ensure APIs are already registered in the system

## Data Distribution

### Compliance Violations

**Severity Distribution:**
- Critical: 15%
- High: 30%
- Medium: 35%
- Low: 20%

**Status Distribution:**
- Open: 50%
- In Progress: 25%
- Remediated: 15%
- Accepted Risk: 8%
- False Positive: 2%

**Standard-Specific Violations:**
- GDPR: 4 specific violation types + cross-standard
- HIPAA: 4 specific violation types + cross-standard
- SOC2: 4 specific violation types + cross-standard
- PCI-DSS: 4 specific violation types + cross-standard
- ISO 27001: 4 specific violation types + cross-standard

**Cross-Standard Violations:**
- Insufficient Logging/Monitoring
- Inadequate Access Controls
- Missing Encryption Controls
- Inadequate Availability Controls

## Examples

### Example 1: Generate GDPR violations for testing

```bash
# Generate 15 GDPR violations for a specific API
python backend/scripts/generate_mock_compliance.py \
  --api-id 550e8400-e29b-41d4-a716-446655440000 \
  --standards gdpr \
  --count 15
```

### Example 2: Generate mixed violations for all APIs

```bash
# Generate 5 violations per API across all standards
python backend/scripts/generate_mock_compliance.py \
  --all-apis \
  --count 5
```

### Example 3: Generate healthcare compliance violations

```bash
# Generate HIPAA and SOC2 violations for healthcare API
python backend/scripts/generate_mock_compliance.py \
  --api-id <HEALTHCARE_API_UUID> \
  --standards hipaa soc2 \
  --count 12
```

### Example 4: Generate payment compliance violations

```bash
# Generate PCI-DSS violations for payment API
python backend/scripts/generate_mock_compliance.py \
  --api-id <PAYMENT_API_UUID> \
  --standards pci_dss \
  --count 20
```

## Output

Each generator logs its progress and provides summary information:

```
INFO:__main__:Generated violation 1/10: gdpr - gdpr_data_protection_by_design (high)
INFO:__main__:Generated violation 2/10: hipaa - hipaa_access_control (critical)
...
INFO:__main__:Generated 10 violations
INFO:__main__:Mock compliance data generation complete!
```

## Troubleshooting

### "No APIs found in system"
- Ensure APIs are registered in the system first
- Use the Demo Gateway to register test APIs

### "Connection refused"
- Verify OpenSearch is running: `docker-compose ps`
- Check OpenSearch connection settings in `.env`

### "Index not found"
- Run the OpenSearch initialization script:
  ```bash
  python backend/scripts/init_opensearch.py
  ```

## Integration with Frontend

After generating mock data, the violations will be immediately available in the frontend:

1. Navigate to `/compliance` in the web UI
2. View violations in the "Violations" tab
3. Check compliance posture in the "Posture" tab
4. Generate audit reports in the "Audit Reports" tab

## Notes

- Mock data is marked with `metadata.generated = true` for easy identification
- All timestamps are realistic (detected_at in the past, remediation_deadline in the future)
- Evidence and audit trails are automatically generated for each violation
- Regulatory references are mapped to actual regulation clauses
- Remediation deadlines are calculated based on severity (Critical: 7 days, High: 30 days, Medium: 90 days, Low: 180 days)

## Made with Bob