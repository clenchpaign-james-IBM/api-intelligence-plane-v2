# User Guide: API Intelligence Plane

**Version**: 1.0.0  
**Last Updated**: 2026-04-29  
**Audience**: Operations Managers, DevOps Engineers, Security Engineers, API Developers

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Dashboard Overview](#dashboard-overview)
4. [Managing API Gateways](#managing-api-gateways)
5. [API Discovery & Inventory](#api-discovery--inventory)
6. [Monitoring API Health](#monitoring-api-health)
7. [Predictive Failure Management](#predictive-failure-management)
8. [Security & Vulnerability Management](#security--vulnerability-management)
9. [Compliance Monitoring](#compliance-monitoring)
10. [Performance Optimization](#performance-optimization)
11. [Natural Language Queries](#natural-language-queries)
12. [Best Practices](#best-practices)
13. [Troubleshooting](#troubleshooting)

---

## Introduction

### What is API Intelligence Plane?

API Intelligence Plane is an AI-driven API management platform that transforms API operations from reactive firefighting to proactive, autonomous management. It works alongside your existing API Gateway (currently supporting webMethods API Gateway) to provide:

- **Autonomous API Discovery**: Automatically discover all APIs, including shadow APIs
- **Predictive Health Management**: Get 24-48 hour advance warnings of potential failures
- **Continuous Security Scanning**: Automated vulnerability detection and remediation
- **Real-time Performance Optimization**: AI-driven recommendations for caching, compression, and rate limiting
- **Natural Language Interface**: Query your API intelligence using plain English

### Who Should Use This Guide?

This guide is designed for:

- **Operations Managers**: Monitor overall API health and make data-driven decisions
- **DevOps Engineers**: Manage gateway configurations and optimize performance
- **Security Engineers**: Track vulnerabilities and ensure compliance
- **API Developers**: Understand API usage patterns and performance characteristics

### Key Concepts

- **Gateway**: Your API Gateway instance (e.g., webMethods API Gateway)
- **API**: A discovered API endpoint or service managed by the gateway
- **Shadow API**: An undocumented or unauthorized API discovered by the system
- **Prediction**: An AI-generated forecast of potential API failures or issues
- **Vulnerability**: A security weakness detected in an API
- **Optimization**: A performance improvement recommendation

---

## Getting Started

### Prerequisites

Before using API Intelligence Plane, ensure you have:

1. **Access Credentials**: Username and password for the platform
2. **Gateway Information**: Connection details for your API Gateway
3. **Web Browser**: Modern browser (Chrome, Firefox, Safari, or Edge)
4. **Network Access**: Ability to reach the platform URL

### First-Time Login

1. Navigate to the platform URL (e.g., `http://localhost:3000` for local development)
2. The dashboard will load automatically (no authentication required in development mode)
3. You'll see the main dashboard with an overview of your API ecosystem

### Quick Start Checklist

- [ ] Register your first API Gateway
- [ ] Wait for initial API discovery (5-10 minutes)
- [ ] Review discovered APIs in the API Inventory
- [ ] Check the Dashboard for health metrics
- [ ] Explore predictions and recommendations

---

## Dashboard Overview

The Dashboard is your central hub for monitoring API health and intelligence.

### Dashboard Sections

#### 1. **Key Metrics Summary**

At the top of the dashboard, you'll see:

- **Total APIs**: Number of discovered APIs across all gateways
- **Active Gateways**: Number of connected gateway instances
- **Critical Predictions**: Number of high-severity failure predictions
- **Open Vulnerabilities**: Number of unresolved security issues

#### 2. **Health Score Trends**

A line chart showing:
- Overall API health score over time (0-100 scale)
- Gateway-specific health trends
- Time range selector (24h, 7d, 30d)

#### 3. **Recent Predictions**

A list of the most recent failure predictions:
- Prediction type (e.g., "Performance Degradation")
- Affected API
- Severity level (Critical, High, Medium, Low)
- Predicted time of occurrence
- Quick action buttons

#### 4. **Top APIs by Traffic**

A bar chart showing:
- APIs with the highest request volume
- Request counts for the selected time period
- Click to drill down into API details

#### 5. **Security Posture**

A gauge showing:
- Overall security score (0-100)
- Breakdown by vulnerability severity
- Trend indicator (improving/declining)

### Customizing Your Dashboard

1. **Time Range**: Use the date picker to adjust the time window
2. **Gateway Filter**: Filter metrics by specific gateway
3. **Refresh Rate**: Auto-refresh every 30 seconds (configurable)

---

## Managing API Gateways

### Registering a New Gateway

1. Navigate to **Gateways** in the sidebar
2. Click **"Add Gateway"** button
3. Fill in the gateway details:
   - **Name**: Descriptive name (e.g., "Production Gateway")
   - **Vendor**: Select "webMethods" (currently supported)
   - **Base URL**: Gateway URL (e.g., `https://gateway.example.com:5555`)
   - **Username**: Gateway admin username
   - **Password**: Gateway admin password
4. Configure sync settings:
   - **Sync Interval**: How often to sync data (default: 5 minutes)
   - **Enable Discovery**: Automatically discover new APIs
   - **Enable Metrics**: Collect performance metrics
5. Click **"Register Gateway"**

### Gateway Status Indicators

- 🟢 **Connected**: Gateway is online and syncing
- 🟡 **Syncing**: Currently performing data sync
- 🔴 **Disconnected**: Cannot reach gateway
- ⚠️ **Error**: Configuration or authentication issue
- 🔧 **Maintenance**: Manually set to maintenance mode

### Viewing Gateway Details

1. Click on a gateway name in the list
2. View detailed information:
   - Connection status and last sync time
   - Number of managed APIs
   - Health score and trends
   - Recent activity log
   - Configuration settings

### Updating Gateway Configuration

1. Navigate to gateway details
2. Click **"Edit Configuration"**
3. Modify settings as needed
4. Click **"Save Changes"**

### Removing a Gateway

1. Navigate to gateway details
2. Click **"Remove Gateway"**
3. Confirm the action (this will not delete APIs from the gateway itself)

---

## API Discovery & Inventory

### Understanding API Discovery

API Intelligence Plane automatically discovers APIs from your connected gateways every 5 minutes (configurable). This includes:

- **Documented APIs**: APIs registered in the gateway
- **Shadow APIs**: Undocumented APIs detected through traffic analysis
- **API Versions**: Multiple versions of the same API
- **Endpoints**: Individual paths and methods within each API

### Viewing the API Inventory

1. Navigate to **APIs** in the sidebar
2. Browse the list of discovered APIs
3. Use filters to narrow down results:
   - **Gateway**: Filter by specific gateway
   - **Status**: Active, Inactive, Deprecated, Failed
   - **Shadow APIs**: Show only shadow APIs
   - **Search**: Search by API name or path

### API List Columns

- **Name**: API name and version
- **Gateway**: Source gateway
- **Status**: Current operational status
- **Health Score**: Overall health (0-100)
- **Risk Score**: Risk level (0-100, higher = riskier)
- **Security Score**: Security posture (0-100)
- **Requests (24h)**: Request count in last 24 hours
- **Error Rate**: Percentage of failed requests
- **Last Seen**: Last time API was accessed

### Viewing API Details

Click on an API to see:

1. **Overview Tab**:
   - Basic information (name, version, base path)
   - Health, risk, and security scores
   - Status and discovery information

2. **Endpoints Tab**:
   - List of all endpoints (paths and methods)
   - Request counts per endpoint
   - Response time statistics

3. **Metrics Tab**:
   - Time-series charts for:
     - Request volume
     - Response time (avg, p95, p99)
     - Error rate
     - Success rate
   - Adjustable time range and interval

4. **Policies Tab**:
   - Applied gateway policies:
     - Authentication methods
     - Rate limiting rules
     - Caching configuration
     - Compression settings

5. **Predictions Tab**:
   - Active predictions for this API
   - Historical predictions
   - Prediction accuracy metrics

6. **Security Tab**:
   - Open vulnerabilities
   - Compliance violations
   - Security recommendations

### Shadow API Detection

Shadow APIs are highlighted with a 🔍 icon. To investigate:

1. Click on the shadow API
2. Review the **Discovery Details**:
   - How it was discovered (traffic analysis, log analysis)
   - First seen timestamp
   - Request patterns
3. Take action:
   - **Document**: Add to official API catalog
   - **Investigate**: Review with development team
   - **Block**: Disable if unauthorized

---

## Monitoring API Health

### Health Score Explained

The health score (0-100) is calculated based on:

- **Availability**: Uptime and error rates (40% weight)
- **Performance**: Response times and latency (30% weight)
- **Security**: Vulnerability count and severity (20% weight)
- **Compliance**: Compliance violation count (10% weight)

**Score Ranges**:
- 90-100: Excellent (🟢 Green)
- 70-89: Good (🟡 Yellow)
- 50-69: Fair (🟠 Orange)
- 0-49: Poor (🔴 Red)

### Real-Time Metrics

View real-time metrics for any API:

1. Navigate to API details
2. Click **Metrics** tab
3. Select time range and interval:
   - **1 minute**: Real-time monitoring
   - **5 minutes**: Recent trends
   - **1 hour**: Short-term analysis
   - **1 day**: Long-term patterns

### Key Metrics to Monitor

#### Request Volume
- Total requests over time
- Identifies traffic patterns and spikes
- Helps with capacity planning

#### Response Time
- **Average**: Mean response time
- **P95**: 95th percentile (most requests faster than this)
- **P99**: 99th percentile (outlier detection)

#### Error Rate
- Percentage of failed requests (4xx, 5xx errors)
- Trend over time
- Breakdown by error type

#### Success Rate
- Percentage of successful requests (2xx, 3xx)
- Inverse of error rate
- Target: >99.9% for production APIs

### Setting Up Alerts

While the platform provides predictive alerts automatically, you can also:

1. Monitor the **Predictions** page for new alerts
2. Check the dashboard daily for critical predictions
3. Subscribe to email notifications (if configured by admin)

---

## Predictive Failure Management

### Understanding Predictions

API Intelligence Plane uses AI to predict potential failures 24-48 hours in advance. Predictions are based on:

- Historical performance patterns
- Current metric trends
- Similar incidents in the past
- External factors (if configured)

### Prediction Types

1. **Performance Degradation**: Response times increasing
2. **Capacity Issues**: Approaching resource limits
3. **Error Rate Spike**: Increasing failure rate
4. **Availability Risk**: Potential downtime
5. **Security Threat**: Emerging security risk

### Viewing Predictions

1. Navigate to **Predictions** in the sidebar
2. Filter by:
   - **Severity**: Critical, High, Medium, Low
   - **Status**: Active, Resolved, False Positive, Expired
   - **API**: Specific API
   - **Gateway**: Specific gateway

### Prediction Details

Click on a prediction to see:

1. **Overview**:
   - Prediction type and severity
   - Confidence level (0-100%)
   - Predicted time of occurrence
   - Affected API and gateway

2. **Evidence**:
   - Data points supporting the prediction
   - Trend charts
   - Historical comparisons

3. **Recommendations**:
   - Suggested actions to prevent the issue
   - Priority order
   - Estimated impact

4. **Similar Incidents**:
   - Past incidents with similar patterns
   - How they were resolved
   - Lessons learned

### Taking Action on Predictions

#### For Performance Degradation:
1. Review the recommendations
2. Consider scaling resources
3. Enable caching or compression
4. Optimize backend services

#### For Capacity Issues:
1. Check resource utilization
2. Scale horizontally (add instances)
3. Implement rate limiting
4. Review traffic patterns

#### For Error Rate Spikes:
1. Investigate recent changes
2. Check backend service health
3. Review error logs
4. Consider rollback if needed

#### For Security Threats:
1. Review vulnerability details
2. Apply security patches
3. Update policies
4. Monitor for suspicious activity

### Marking Predictions

You can mark predictions as:

- **Resolved**: Issue has been addressed
- **False Positive**: Prediction was incorrect
- **Acknowledged**: Aware but accepting the risk

This feedback helps improve prediction accuracy over time.

---

## Security & Vulnerability Management

### Security Dashboard

Navigate to **Security** to see:

1. **Security Posture Score**: Overall security health (0-100)
2. **Vulnerability Breakdown**: Count by severity
3. **Recent Vulnerabilities**: Latest detected issues
4. **Remediation Progress**: Tracking of fixes

### Vulnerability Severity Levels

- **Critical**: Immediate action required (e.g., exposed credentials)
- **High**: Address within 24 hours (e.g., missing authentication)
- **Medium**: Address within 7 days (e.g., weak encryption)
- **Low**: Address within 30 days (e.g., missing headers)

### Common Vulnerability Types

1. **Missing Authentication**: Endpoints without auth
2. **Weak Authentication**: Basic auth instead of OAuth2
3. **Missing Authorization**: No permission checks
4. **Exposed Sensitive Data**: PII in responses
5. **Insecure Communication**: HTTP instead of HTTPS
6. **SQL Injection**: Vulnerable to SQL attacks
7. **XSS Vulnerabilities**: Cross-site scripting risks
8. **CSRF Vulnerabilities**: Cross-site request forgery

### Viewing Vulnerability Details

Click on a vulnerability to see:

1. **Description**: What the vulnerability is
2. **Affected Endpoints**: Which APIs/endpoints are vulnerable
3. **CVE IDs**: Related CVE identifiers (if applicable)
4. **CVSS Score**: Industry-standard severity score
5. **Remediation Steps**: How to fix the issue
6. **Automated Remediation**: If available

### Automated Remediation

For supported vulnerabilities:

1. Click **"Remediate Automatically"**
2. Review the proposed changes
3. Confirm the action
4. Monitor remediation progress
5. Verify the fix

**Note**: Automated remediation is available for:
- Enabling authentication policies
- Updating rate limiting rules
- Enabling HTTPS enforcement
- Adding security headers

### Manual Remediation

For vulnerabilities requiring manual fixes:

1. Review the remediation steps
2. Coordinate with development team
3. Implement the fix in your codebase
4. Deploy the changes
5. Mark vulnerability as **Remediated**

### Security Best Practices

- Review security dashboard daily
- Address critical vulnerabilities immediately
- Enable automated remediation when available
- Conduct regular security audits
- Keep gateway and APIs updated
- Monitor for new vulnerability types

---

## Compliance Monitoring

### Supported Compliance Frameworks

API Intelligence Plane monitors compliance with:

- **PCI DSS**: Payment Card Industry Data Security Standard
- **HIPAA**: Health Insurance Portability and Accountability Act
- **GDPR**: General Data Protection Regulation
- **SOX**: Sarbanes-Oxley Act

### Viewing Compliance Status

Navigate to **Compliance** to see:

1. **Overall Compliance Score**: Percentage of requirements met
2. **Violations by Framework**: Breakdown by standard
3. **Recent Violations**: Latest detected issues
4. **Remediation Progress**: Tracking of fixes

### Compliance Violation Details

Click on a violation to see:

1. **Framework & Requirement**: Which standard and section
2. **Severity**: Critical, High, Medium, Low
3. **Description**: What the violation is
4. **Affected APIs**: Which APIs are non-compliant
5. **Remediation Steps**: How to achieve compliance
6. **Audit Trail**: History of the violation

### Common Compliance Violations

#### PCI DSS:
- Insufficient logging for payment transactions
- Weak encryption for cardholder data
- Missing access controls

#### HIPAA:
- PHI exposed in logs
- Insufficient audit logging
- Missing encryption at rest

#### GDPR:
- Personal data without consent
- Missing data retention policies
- Inadequate data deletion mechanisms

#### SOX:
- Insufficient audit trails
- Missing change management controls
- Inadequate access controls

### Achieving Compliance

1. Review violation details
2. Implement remediation steps
3. Update policies and configurations
4. Document changes for audit
5. Mark violation as **Resolved**
6. Verify compliance in next scan

### Compliance Reporting

Generate compliance reports:

1. Navigate to **Compliance** > **Reports**
2. Select framework and time period
3. Click **"Generate Report"**
4. Download PDF or CSV format

Reports include:
- Compliance score trends
- Violation history
- Remediation timeline
- Audit trail

---

## Performance Optimization

### Optimization Dashboard

Navigate to **Optimization** to see:

1. **Optimization Opportunities**: Count of recommendations
2. **Potential Impact**: Estimated performance gains
3. **Cost Savings**: Estimated monthly savings
4. **Recent Recommendations**: Latest suggestions

### Optimization Types

#### 1. **Caching**
- Enable response caching for frequently accessed data
- Reduce backend load
- Improve response times

**When to Use**:
- APIs serving mostly static data
- High request volume
- Low data change frequency

#### 2. **Compression**
- Enable response compression (gzip, brotli)
- Reduce bandwidth usage
- Improve transfer speeds

**When to Use**:
- Large response payloads
- Text-based responses (JSON, XML)
- Mobile or low-bandwidth clients

#### 3. **Rate Limiting**
- Implement adaptive rate limiting
- Prevent abuse and overload
- Ensure fair usage

**When to Use**:
- Public APIs
- High-traffic endpoints
- Protection against DDoS

#### 4. **Routing Optimization**
- Optimize request routing
- Load balancing improvements
- Geographic routing

**When to Use**:
- Multi-region deployments
- High latency issues
- Uneven load distribution

### Viewing Recommendations

Click on a recommendation to see:

1. **Description**: What the optimization does
2. **Impact Analysis**:
   - Estimated latency reduction
   - Estimated load reduction
   - Estimated cost savings
3. **Configuration**: Proposed settings
4. **Risks**: Potential side effects
5. **Similar Implementations**: Success stories

### Applying Optimizations

#### Automated Application:
1. Click **"Apply Automatically"**
2. Review proposed configuration
3. Confirm the action
4. Monitor impact

#### Manual Application:
1. Review the recommendation
2. Test in staging environment
3. Implement in production
4. Monitor results
5. Mark as **Applied**

### Monitoring Optimization Impact

After applying an optimization:

1. Navigate to API metrics
2. Compare before/after performance
3. Check for any negative impacts
4. Adjust configuration if needed

### Optimization Best Practices

- Start with high-impact, low-risk optimizations
- Test in staging before production
- Monitor impact for 24-48 hours
- Roll back if negative effects observed
- Document all changes
- Review optimization effectiveness monthly

---

## Natural Language Queries

### Query Interface

Navigate to **Query** to access the natural language interface.

### How to Use

1. Type your question in plain English
2. Press Enter or click **"Ask"**
3. View the results
4. Refine your query if needed

### Example Queries

#### API Discovery:
- "Show me all APIs"
- "Which APIs were discovered in the last week?"
- "List all shadow APIs"
- "Show APIs with more than 10,000 requests today"

#### Performance:
- "Which APIs have the highest error rates?"
- "Show me APIs with response times over 500ms"
- "What are the slowest APIs?"
- "Which APIs had performance issues yesterday?"

#### Security:
- "Show me all critical vulnerabilities"
- "Which APIs have security issues?"
- "List APIs without authentication"
- "Show recent security scans"

#### Predictions:
- "What failures are predicted for tomorrow?"
- "Show me all critical predictions"
- "Which APIs are at risk?"
- "What are the latest predictions?"

#### Optimization:
- "Which APIs should I optimize?"
- "Show caching recommendations"
- "What are the top optimization opportunities?"
- "Which APIs can benefit from compression?"

### Query Tips

1. **Be Specific**: "Show APIs with error rate > 5%" vs "Show bad APIs"
2. **Use Time Ranges**: "in the last 24 hours", "yesterday", "this week"
3. **Combine Filters**: "Show critical predictions for production gateway"
4. **Ask Follow-ups**: Refine based on initial results

### Query History

View your previous queries:

1. Click **"History"** tab
2. Browse past queries
3. Click to re-run a query
4. Save frequently used queries

### Understanding Results

Query results include:

1. **Summary**: High-level answer to your question
2. **Data Table**: Detailed results
3. **Visualizations**: Charts and graphs (when applicable)
4. **Actions**: Quick actions on results
5. **Related Queries**: Suggested follow-up questions

---

## Best Practices

### Daily Operations

1. **Morning Routine**:
   - Check dashboard for overnight issues
   - Review critical predictions
   - Address any new vulnerabilities
   - Check compliance status

2. **Throughout the Day**:
   - Monitor real-time metrics
   - Respond to new predictions
   - Review optimization recommendations
   - Investigate anomalies

3. **End of Day**:
   - Review daily summary
   - Plan for predicted issues
   - Document any actions taken
   - Prepare for next day

### Weekly Tasks

- Review API inventory for shadow APIs
- Analyze performance trends
- Conduct security review
- Apply optimization recommendations
- Generate compliance reports
- Review prediction accuracy

### Monthly Tasks

- Comprehensive security audit
- Performance optimization review
- Compliance framework updates
- Gateway configuration review
- Team training and knowledge sharing
- Platform usage analysis

### Team Collaboration

1. **Operations Team**:
   - Monitor dashboard daily
   - Respond to predictions
   - Coordinate remediation efforts

2. **Security Team**:
   - Review vulnerabilities
   - Conduct security audits
   - Implement security policies

3. **Development Team**:
   - Address API issues
   - Implement optimizations
   - Fix vulnerabilities

4. **Management**:
   - Review compliance status
   - Track KPIs and metrics
   - Make strategic decisions

---

## Troubleshooting

### Common Issues

#### Gateway Connection Failed

**Symptoms**: Gateway shows "Disconnected" status

**Solutions**:
1. Verify gateway URL is correct
2. Check network connectivity
3. Verify credentials are valid
4. Check gateway is running
5. Review firewall rules

#### APIs Not Discovered

**Symptoms**: API inventory is empty or incomplete

**Solutions**:
1. Wait for initial discovery (5-10 minutes)
2. Check gateway connection status
3. Verify discovery is enabled in gateway settings
4. Check gateway has APIs configured
5. Review discovery logs

#### Metrics Not Updating

**Symptoms**: Metrics show stale data

**Solutions**:
1. Check gateway connection
2. Verify metrics collection is enabled
3. Check OpenSearch status
4. Review backend logs
5. Restart backend service if needed

#### Predictions Not Appearing

**Symptoms**: No predictions shown

**Solutions**:
1. Wait for sufficient data (24-48 hours)
2. Check LLM service configuration
3. Verify prediction service is running
4. Review prediction logs
5. Check API has sufficient traffic

#### Slow Query Performance

**Symptoms**: Natural language queries take >10 seconds

**Solutions**:
1. Simplify query
2. Reduce time range
3. Check OpenSearch performance
4. Review backend logs
5. Contact administrator

### Getting Help

#### Self-Service Resources:
- **Documentation**: This user guide
- **API Documentation**: [`docs/api-documentation.md`](./api-documentation.md)
- **Architecture Guide**: [`docs/architecture.md`](./architecture.md)
- **Deployment Guide**: [`docs/deployment.md`](./deployment.md)

#### Support Channels:
- **Email**: support@intelligence-plane.example.com
- **GitHub Issues**: Report bugs and feature requests
- **Community Forum**: Ask questions and share knowledge
- **Slack Channel**: Real-time support (if available)

#### Reporting Issues:

When reporting an issue, include:
1. **Description**: What happened vs what you expected
2. **Steps to Reproduce**: How to recreate the issue
3. **Screenshots**: Visual evidence
4. **Environment**: Browser, OS, platform version
5. **Logs**: Relevant error messages

---

## Appendix

### Glossary

- **API**: Application Programming Interface
- **Gateway**: API Gateway (e.g., webMethods)
- **Shadow API**: Undocumented or unauthorized API
- **Health Score**: Overall API health metric (0-100)
- **Risk Score**: Potential risk level (0-100)
- **Security Score**: Security posture (0-100)
- **Prediction**: AI-generated failure forecast
- **Vulnerability**: Security weakness
- **Compliance Violation**: Non-compliance with standards
- **Optimization**: Performance improvement recommendation
- **CVSS**: Common Vulnerability Scoring System
- **CVE**: Common Vulnerabilities and Exposures

### Keyboard Shortcuts

- `Ctrl/Cmd + K`: Open query interface
- `Ctrl/Cmd + /`: Open search
- `Ctrl/Cmd + D`: Go to dashboard
- `Ctrl/Cmd + G`: Go to gateways
- `Ctrl/Cmd + A`: Go to APIs
- `Esc`: Close modal/dialog

### Version History

- **1.0.0** (2026-04-29): Initial release

---

## Feedback

We value your feedback! Help us improve API Intelligence Plane:

- **Feature Requests**: Submit via GitHub Issues
- **Bug Reports**: Report via support email
- **Documentation**: Suggest improvements
- **User Experience**: Share your experience

Thank you for using API Intelligence Plane! 🚀