---
description: "REST API development standards: RESTful conventions, versioning, validation, OpenAPI. Use when building or modifying API endpoints, routes, or controllers."
---

# REST API Development

- Follow RESTful conventions: proper HTTP verbs, status codes, resource naming
- Use plural nouns for resource endpoints (`/users`, not `/user`)
- Version APIs via URL path (`/v1/`) or headers
- Return consistent response structures with proper error payloads
- Implement rate limiting and authentication on all public endpoints
- Validate request payloads with schemas (JSON Schema, Pydantic, Zod, etc.)
- Document APIs with OpenAPI/Swagger
