# Architecture Diagrams - API Intelligence Plane

This directory contains comprehensive architecture and design diagrams for the API Intelligence Plane project. All diagrams are created using Mermaid syntax for easy rendering in GitHub, documentation tools, and IDEs.

## 📋 Table of Contents

1. [System Architecture Diagrams](#system-architecture-diagrams)
2. [Data Flow Diagrams](#data-flow-diagrams)
3. [Deployment Architecture](#deployment-architecture)
4. [MCP Architecture](#mcp-architecture)
5. [Workflow Diagrams](#workflow-diagrams)
6. [How to Use These Diagrams](#how-to-use-these-diagrams)

---

## System Architecture Diagrams

**File**: [`system-architecture.md`](system-architecture.md)

Comprehensive system architecture views including:

### C4 Model Diagrams
- **System Context Diagram** - High-level view showing users, external systems, and the API Intelligence Plane
- **Container Diagram** - Major containers (Frontend, Backend, Gateway, OpenSearch, MCP Servers)
- **Component Diagram** - Detailed backend component architecture

### Architecture Views
- **High-Level Architecture** - Complete system overview with all layers
- **Component Architecture** - Detailed backend component breakdown showing:
  - API Layer (REST endpoints)
  - Service Layer (business logic)
  - Agent Layer (AI workflows)
  - Adapter Layer (gateway integrations)
  - Repository Layer (data access)
  - Data Access (OpenSearch client)

### Technology Stack
- **Technology Stack Diagram** - Visual representation of all technologies used:
  - Frontend Stack (React, TypeScript, Vite, TanStack Query, Tailwind CSS)
  - Backend Stack (Python, FastAPI, LangChain, LangGraph, LiteLLM)
  - Gateway Stack (Java, Spring Boot)
  - MCP Stack (FastMCP, Streamable HTTP)
  - Infrastructure (Docker, Kubernetes, OpenSearch)

**Use Cases**:
- Understanding overall system design
- Onboarding new team members
- Architecture reviews
- Technical presentations

---

## Data Flow Diagrams

**File**: [`data-flow.md`](data-flow.md)

Detailed sequence diagrams and flowcharts showing data movement through the system:

### Core Flows
1. **Core Application Data Flow** - User → Frontend → Backend → OpenSearch → Gateway
2. **API Discovery Flow** - Automated discovery process with shadow API detection
3. **Prediction Generation Flow** - AI-enhanced failure prediction workflow
4. **Natural Language Query Flow** - Query processing with LLM integration
5. **Metrics Collection Flow** - Real-time metrics gathering and storage
6. **Rate Limit Policy Application Flow** - Policy creation and enforcement
7. **Optimization Recommendation Flow** - Performance analysis and recommendations

### Data Persistence
- **Data Persistence Architecture** - OpenSearch indices, repositories, and lifecycle management

**Use Cases**:
- Understanding data flow patterns
- Debugging integration issues
- Performance optimization
- API design and integration

---

## Deployment Architecture

**File**: [`deployment-architecture.md`](deployment-architecture.md)

Comprehensive deployment views for different environments:

### Environment Diagrams
1. **Docker Compose Development Environment** - Local development setup
2. **Kubernetes Production Deployment** - Production-ready K8s architecture with:
   - Ingress Layer
   - Frontend, Backend, Gateway Tiers
   - Data Tier (OpenSearch StatefulSet)
   - Optional MCP Tier
   - Configuration (ConfigMaps, Secrets)
   - Storage (PVCs)
   - Monitoring (Prometheus, Grafana)

### Advanced Architectures
3. **High Availability Architecture** - Multi-AZ deployment with:
   - Load balancing across availability zones
   - OpenSearch cluster replication
   - Shared services (Redis, Message Queue)
   - Persistent storage strategy

4. **Network Architecture** - Complete network topology showing:
   - Public Internet layer
   - DMZ/Edge Network (WAF, Load Balancer, CDN)
   - Application Network (Frontend, Backend, Gateway subnets)
   - Data Network (Database, Cache subnets)
   - Management Network (Bastion, Monitoring)

5. **Security Architecture** - Security layers including:
   - Network Security (Firewall, NSG, VPN)
   - Application Security (TLS, mTLS, Auth, RBAC)
   - Data Security (Encryption in transit/rest, Key Management)
   - Compliance & Audit (Audit logging, FIPS 140-3, Vulnerability scanning)

6. **Scaling Strategy** - Horizontal Pod Autoscaler configuration
7. **Disaster Recovery Architecture** - Multi-region DR with RTO/RPO targets

**Use Cases**:
- Deployment planning
- Infrastructure provisioning
- Security compliance
- Disaster recovery planning
- Capacity planning

---

## MCP Architecture

**File**: [`mcp-architecture.md`](mcp-architecture.md)

Detailed MCP (Model Context Protocol) server architecture for AI agent integration:

### MCP Components
1. **MCP Server Architecture Overview** - Complete MCP ecosystem
2. **Thin Wrapper Pattern** - Before/After refactoring comparison
3. **Discovery Server Architecture** - API discovery via MCP
4. **Metrics Server Architecture** - Metrics collection via MCP
5. **Optimization Server Architecture** - Optimization operations via MCP

### Implementation Details
6. **MCP Communication Flow** - Sequence diagram showing AI Agent → MCP → Backend flow
7. **MCP Backend Client Architecture** - HTTP client implementation
8. **MCP Health Check Architecture** - Health monitoring system
9. **MCP Error Handling Flow** - Comprehensive error handling strategy
10. **MCP Configuration & Environment** - Environment variables and settings
11. **MCP Integration with AI Agents** - Bob IDE and Claude Desktop integration

**Use Cases**:
- Understanding MCP server design
- Integrating with AI development tools
- Debugging MCP issues
- Extending MCP functionality

---

## Workflow Diagrams

**File**: [`workflow-diagrams.md`](workflow-diagrams.md)

Visual representations of key user stories and workflows:

### User Story Workflows
1. **API Discovery & Shadow API Detection** - Complete discovery workflow
2. **Predictive Failure Analysis** - AI-enhanced prediction generation
3. **Natural Language Query Processing** - Query understanding and response generation
4. **Performance Optimization Recommendations** - Optimization analysis workflow
5. **Intelligent Rate Limiting** - Rate limit policy creation and application
6. **Security Vulnerability Scanning** - Automated security scanning process
7. **Metrics Collection & Aggregation** - Real-time metrics gathering
8. **Gateway Registration & Management** - Gateway onboarding process

**Use Cases**:
- Understanding business processes
- User story implementation
- Feature development
- Testing and validation
- User documentation

---

## How to Use These Diagrams

### Viewing in GitHub
All diagrams use Mermaid syntax and render automatically in GitHub markdown files. Simply open any `.md` file in this directory on GitHub to view the diagrams.

### Viewing in VS Code
Install the **Markdown Preview Mermaid Support** extension:
```bash
code --install-extension bierner.markdown-mermaid
```

Then open any diagram file and use the markdown preview (Ctrl+Shift+V or Cmd+Shift+V).

### Viewing in Other Tools
- **draw.io**: Copy Mermaid code and use draw.io's Mermaid import feature
- **Excalidraw**: Use Mermaid to Excalidraw converters
- **PlantUML**: Convert Mermaid to PlantUML using online converters
- **Documentation Sites**: Most modern documentation tools (MkDocs, Docusaurus, GitBook) support Mermaid

### Exporting Diagrams
Use the Mermaid CLI to export diagrams to PNG, SVG, or PDF:

```bash
# Install Mermaid CLI
npm install -g @mermaid-js/mermaid-cli

# Export to PNG
mmdc -i system-architecture.md -o system-architecture.png

# Export to SVG
mmdc -i data-flow.md -o data-flow.svg

# Export to PDF
mmdc -i deployment-architecture.md -o deployment-architecture.pdf
```

### Editing Diagrams
1. **Online Editor**: Use [Mermaid Live Editor](https://mermaid.live/) for real-time preview
2. **VS Code**: Edit directly with preview using the Mermaid extension
3. **IntelliJ/WebStorm**: Built-in Mermaid support in markdown files

### Diagram Syntax Reference
- [Mermaid Documentation](https://mermaid.js.org/)
- [Flowchart Syntax](https://mermaid.js.org/syntax/flowchart.html)
- [Sequence Diagram Syntax](https://mermaid.js.org/syntax/sequenceDiagram.html)
- [C4 Diagram Syntax](https://mermaid.js.org/syntax/c4.html)

---

## Diagram Maintenance

### When to Update Diagrams
- **Architecture Changes**: Update when system architecture changes
- **New Features**: Add workflow diagrams for new user stories
- **Deployment Changes**: Update deployment diagrams for infrastructure changes
- **Integration Changes**: Update MCP diagrams when adding new MCP servers

### Diagram Standards
- Use consistent color schemes across diagrams
- Follow C4 model conventions for architecture diagrams
- Include clear labels and descriptions
- Keep diagrams focused and avoid overcrowding
- Use subgraphs to group related components
- Add notes for important clarifications

### Contributing
When adding new diagrams:
1. Follow existing naming conventions
2. Use Mermaid syntax for consistency
3. Add diagram to appropriate file or create new file if needed
4. Update this README with diagram description
5. Test rendering in GitHub and VS Code
6. Update main documentation files with references

---

## Quick Reference

| Diagram Type | File | Best For |
|--------------|------|----------|
| System Overview | `system-architecture.md` | Understanding overall design |
| Data Flows | `data-flow.md` | Tracing data through system |
| Deployment | `deployment-architecture.md` | Infrastructure planning |
| MCP Integration | `mcp-architecture.md` | AI agent integration |
| User Workflows | `workflow-diagrams.md` | Feature implementation |

---

## Related Documentation

- [Architecture Documentation](../architecture.md) - Detailed architecture description
- [MCP Architecture](../mcp-architecture.md) - MCP server architecture details
- [Engineering Overview](../engineering.md) - Engineering documentation
- [Business Context](../business-context.md) - User stories and requirements
- [API Reference](../api-reference.md) - REST API documentation
- [Deployment Guide](../deployment.md) - Deployment instructions

---

**Last Updated**: 2026-03-13  
**Version**: 1.0.0  
**Maintained By**: API Intelligence Plane Team