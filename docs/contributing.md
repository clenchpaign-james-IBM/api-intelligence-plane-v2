# Contributing Guidelines: API Intelligence Plane

**Version**: 1.0.0  
**Last Updated**: 2026-03-12

Thank you for your interest in contributing to the API Intelligence Plane! This document provides guidelines and best practices for contributing to the project.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Project Structure](#project-structure)
5. [Coding Standards](#coding-standards)
6. [Testing Guidelines](#testing-guidelines)
7. [Commit Guidelines](#commit-guidelines)
8. [Pull Request Process](#pull-request-process)
9. [Documentation](#documentation)
10. [Community](#community)

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors, regardless of experience level, gender identity, sexual orientation, disability, personal appearance, body size, race, ethnicity, age, religion, or nationality.

### Expected Behavior

- Be respectful and considerate
- Welcome newcomers and help them get started
- Provide constructive feedback
- Focus on what is best for the community
- Show empathy towards other community members

### Unacceptable Behavior

- Harassment, discrimination, or offensive comments
- Personal attacks or trolling
- Publishing others' private information
- Any conduct that could reasonably be considered inappropriate

### Reporting

If you experience or witness unacceptable behavior, please report it to support@api-intelligence-plane.com.

---

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- Git installed and configured
- Docker and Docker Compose installed
- Python 3.11+ for backend development
- Node.js 18+ for frontend development
- Java 17+ for demo gateway development
- A GitHub account

### Finding Issues to Work On

1. **Good First Issues**: Look for issues labeled `good-first-issue`
2. **Help Wanted**: Check issues labeled `help-wanted`
3. **Bug Reports**: Issues labeled `bug` are always welcome
4. **Feature Requests**: Issues labeled `enhancement`

### Claiming an Issue

1. Comment on the issue expressing your interest
2. Wait for maintainer approval before starting work
3. Ask questions if anything is unclear

---

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/api-intelligence-plane-v2.git
cd api-intelligence-plane-v2

# Add upstream remote
git remote add upstream https://github.com/original/api-intelligence-plane-v2.git
```

### 2. Create a Branch

```bash
# Create a feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/bug-description
```

### 3. Set Up Development Environment

```bash
# Copy environment configuration
cp .env.example .env

# Start development services
docker-compose up -d

# Initialize OpenSearch
docker-compose exec backend python scripts/init_opensearch.py
```

### 4. Verify Setup

```bash
# Check all services are running
docker-compose ps

# Test backend
curl http://localhost:8000/health

# Test frontend
curl http://localhost:3000
```

---

## Project Structure

```
api-intelligence-plane-v2/
├── backend/              # Python FastAPI backend
│   ├── app/
│   │   ├── api/         # REST API endpoints
│   │   ├── models/      # Pydantic models
│   │   ├── services/    # Business logic
│   │   ├── agents/      # LangChain/LangGraph agents
│   │   ├── adapters/    # Gateway adapters
│   │   ├── db/          # Database layer
│   │   └── scheduler/   # Background jobs
│   ├── tests/           # Tests
│   └── scripts/         # Utility scripts
├── frontend/            # React TypeScript frontend
│   └── src/
│       ├── components/  # React components
│       ├── pages/       # Page components
│       ├── services/    # API clients
│       └── hooks/       # Custom hooks
├── mcp-servers/         # MCP servers (optional)
├── gateway/        # Java Spring Boot gateway
├── docs/                # Documentation
└── specs/               # Feature specifications
```

---

## Coding Standards

### Python (Backend & MCP Servers)

#### Style Guide

- **Formatter**: Black (line length: 100)
- **Import Sorting**: isort (profile: black)
- **Linter**: flake8 (max-line-length: 100)
- **Type Checking**: mypy (strict mode)

#### Running Code Quality Tools

```bash
cd backend

# Format code
black app/ tests/

# Sort imports
isort app/ tests/

# Lint code
flake8 app/ tests/

# Type check
mypy app/
```

#### Naming Conventions

```python
# Variables and functions: snake_case
user_count = 10
def calculate_metrics():
    pass

# Classes: PascalCase
class MetricsService:
    pass

# Constants: UPPER_SNAKE_CASE
MAX_RETRY_COUNT = 3

# Private methods: _leading_underscore
def _internal_helper():
    pass
```

#### Docstrings

Use Google-style docstrings:

```python
def process_metrics(api_id: str, start_time: datetime) -> List[Metric]:
    """
    Process metrics for a specific API.
    
    Args:
        api_id: The API identifier
        start_time: Start time for metrics collection
        
    Returns:
        List of processed metrics
        
    Raises:
        ValueError: If api_id is invalid
        MetricsError: If metrics processing fails
    """
    pass
```

### TypeScript/JavaScript (Frontend)

#### Style Guide

- **Formatter**: Prettier (semi: false, singleQuote: true)
- **Linter**: ESLint (extends: recommended, typescript-eslint)
- **Style Guide**: Airbnb TypeScript

#### Running Code Quality Tools

```bash
cd frontend

# Format code
npm run format

# Lint code
npm run lint

# Type check
npm run type-check
```

#### Naming Conventions

```typescript
// Variables and functions: camelCase
const userCount = 10;
function calculateMetrics() {}

// Components and classes: PascalCase
function MetricsCard() {}
class ApiService {}

// Constants: UPPER_SNAKE_CASE
const MAX_RETRY_COUNT = 3;

// Interfaces: PascalCase with 'I' prefix (optional)
interface IMetric {}
// Or without prefix
interface Metric {}

// Types: PascalCase
type MetricData = {
  value: number;
  timestamp: string;
};
```

#### Component Structure

```typescript
import React from 'react';

interface MetricsCardProps {
  apiId: string;
  metrics: Metric[];
}

/**
 * Displays API metrics in a card format
 */
export function MetricsCard({ apiId, metrics }: MetricsCardProps) {
  // Component logic
  return (
    <div className="metrics-card">
      {/* Component JSX */}
    </div>
  );
}
```

### Java (Gateway)

#### Style Guide

- **Style Guide**: Google Java Style Guide
- **Formatter**: Spring Java Format

#### Naming Conventions

```java
// Variables and methods: camelCase
int userCount = 10;
public void calculateMetrics() {}

// Classes: PascalCase
public class MetricsService {}

// Constants: UPPER_SNAKE_CASE
public static final int MAX_RETRY_COUNT = 3;

// Packages: lowercase
package com.example.gateway.service;
```

---

## Testing Guidelines

### Backend Testing

#### Integration Tests (Required)

```python
# tests/integration/test_metrics_service.py
import pytest
from app.services.metrics_service import MetricsService

@pytest.mark.asyncio
async def test_collect_metrics_integration():
    """Test metrics collection with real OpenSearch."""
    service = MetricsService()
    metrics = await service.collect_metrics(api_id="test-api")
    
    assert len(metrics) > 0
    assert metrics[0].api_id == "test-api"
```

#### End-to-End Tests (Required)

```python
# tests/e2e/test_prediction_workflow.py
import pytest
from app.services.prediction_service import PredictionService

@pytest.mark.asyncio
async def test_prediction_workflow_e2e():
    """Test complete prediction generation workflow."""
    # Setup
    service = PredictionService()
    
    # Execute
    predictions = await service.generate_predictions_for_api(api_id="test-api")
    
    # Verify
    assert len(predictions) > 0
    assert predictions[0].confidence_score > 0.7
```

#### Running Tests

```bash
cd backend

# Run all tests
pytest

# Run specific test file
pytest tests/integration/test_metrics_service.py

# Run with coverage
pytest --cov=app --cov-report=html

# Run E2E tests only
pytest tests/e2e/
```

### Frontend Testing

```bash
cd frontend

# Run tests
npm test

# Run with coverage
npm run test:coverage

# Run in watch mode
npm test -- --watch
```

### Test Coverage

- **Integration Tests**: Required for all services
- **E2E Tests**: Required for user stories
- **Unit Tests**: Not required per project specification
- **Coverage Target**: Focus on integration and E2E coverage

---

## Commit Guidelines

### Commit Message Format

Follow the Conventional Commits specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

#### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

#### Examples

```bash
# Feature
git commit -m "feat(predictions): add AI-enhanced prediction generation"

# Bug fix
git commit -m "fix(metrics): resolve race condition in metrics collection"

# Documentation
git commit -m "docs(api): update API reference with new endpoints"

# Multiple lines
git commit -m "feat(optimization): implement caching recommendations

- Add Redis caching analysis
- Calculate cache hit rate improvements
- Generate implementation steps

Closes #123"
```

### Commit Best Practices

1. **Atomic Commits**: One logical change per commit
2. **Clear Messages**: Describe what and why, not how
3. **Reference Issues**: Include issue numbers when applicable
4. **Sign Commits**: Use GPG signing for verified commits

---

## Pull Request Process

### Before Submitting

1. **Update from upstream**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run tests**:
   ```bash
   # Backend
   cd backend && pytest
   
   # Frontend
   cd frontend && npm test
   ```

3. **Run code quality checks**:
   ```bash
   # Backend
   cd backend
   black app/ tests/
   isort app/ tests/
   flake8 app/ tests/
   mypy app/
   
   # Frontend
   cd frontend
   npm run lint
   npm run format
   ```

4. **Update documentation** if needed

### Creating a Pull Request

1. **Push your branch**:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create PR on GitHub**:
   - Use a clear, descriptive title
   - Fill out the PR template completely
   - Link related issues
   - Add screenshots for UI changes
   - Request reviews from maintainers

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Related Issues
Closes #123

## Testing
- [ ] Integration tests added/updated
- [ ] E2E tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests pass locally
```

### Review Process

1. **Automated Checks**: CI/CD pipeline runs automatically
2. **Code Review**: At least one maintainer review required
3. **Address Feedback**: Make requested changes
4. **Approval**: Maintainer approves PR
5. **Merge**: Maintainer merges PR

### After Merge

1. **Delete branch**:
   ```bash
   git branch -d feature/your-feature-name
   git push origin --delete feature/your-feature-name
   ```

2. **Update local main**:
   ```bash
   git checkout main
   git pull upstream main
   ```

---

## Documentation

### When to Update Documentation

- Adding new features
- Changing existing functionality
- Fixing bugs that affect usage
- Adding new configuration options
- Updating dependencies

### Documentation Types

1. **Code Comments**: Explain complex logic
2. **Docstrings**: Document functions and classes
3. **API Documentation**: Update API reference
4. **User Guides**: Update deployment or usage guides
5. **Architecture Docs**: Update for architectural changes

### Documentation Standards

- Use clear, concise language
- Include code examples
- Keep documentation up-to-date with code
- Use proper markdown formatting
- Add diagrams for complex concepts

---

## Component-Specific Guidelines

### Backend Development

#### Adding a New Service

1. Create service class in `backend/app/services/`
2. Add Pydantic models in `backend/app/models/`
3. Create repository in `backend/app/db/repositories/`
4. Add API endpoints in `backend/app/api/v1/`
5. Write integration tests
6. Update API documentation

#### Adding a New Agent

1. Create agent class in `backend/app/agents/`
2. Implement LangGraph workflow
3. Add LLM service integration
4. Create fallback logic
5. Write integration tests
6. Document agent behavior

### Frontend Development

#### Adding a New Page

1. Create page component in `frontend/src/pages/`
2. Add route in `App.tsx`
3. Create necessary components
4. Add API service methods
5. Implement error handling
6. Add loading states

#### Adding a New Component

1. Create component in `frontend/src/components/`
2. Define TypeScript interfaces
3. Implement component logic
4. Add styling with Tailwind CSS
5. Write component tests
6. Document props and usage

### MCP Server Development

#### Adding a New MCP Tool

1. Define tool in MCP server file
2. Implement tool logic (delegate to backend)
3. Add input validation
4. Document tool parameters
5. Test with MCP client
6. Update MCP documentation

---

## Community

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and discussions
- **Discord**: Real-time chat and community support
- **Email**: support@api-intelligence-plane.com

### Getting Help

1. **Check Documentation**: Review existing docs first
2. **Search Issues**: Look for similar issues
3. **Ask Questions**: Use GitHub Discussions
4. **Join Discord**: Get real-time help

### Recognition

Contributors are recognized in:
- README.md contributors section
- Release notes
- Project documentation

---

## Release Process

### Versioning

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

1. Update version numbers
2. Update CHANGELOG.md
3. Run full test suite
4. Build and test Docker images
5. Create release tag
6. Publish release notes
7. Deploy to production

---

## Additional Resources

- [Architecture Documentation](./architecture.md)
- [API Reference](./api-reference.md)
- [Deployment Guide](./deployment.md)
- [AI Setup Guide](./ai-setup.md)

---

## Questions?

If you have questions about contributing, please:

1. Check this guide first
2. Search existing issues and discussions
3. Ask in GitHub Discussions
4. Join our Discord community
5. Email support@api-intelligence-plane.com

Thank you for contributing to API Intelligence Plane! 🚀