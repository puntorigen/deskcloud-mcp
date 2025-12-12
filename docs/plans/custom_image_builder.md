# Custom Image Builder Feature Plan

> ⚠️ **Start Here**: Read [`MASTER_ROADMAP.md`](./MASTER_ROADMAP.md) first for project context and overview.

> **DeskCloud Premium Feature**  
> **Status:** Planning  
> **Created:** December 2025  
> **Tier:** Team ($99/mo) and Enterprise  
> **Priority**: 🟢 Low - Phase 10 (after Video Recording)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Problem Statement](#problem-statement)
3. [Use Cases](#use-cases)
4. [Feature Tiers](#feature-tiers)
5. [Technical Architecture](#technical-architecture)
6. [Implementation Phases](#implementation-phases)
7. [Database Schema](#database-schema)
8. [API Specification](#api-specification)
9. [Dashboard UI/UX](#dashboard-uiux)
10. [Security Considerations](#security-considerations)
11. [Infrastructure Requirements](#infrastructure-requirements)
12. [Cost Analysis](#cost-analysis)
13. [Success Metrics](#success-metrics)
14. [Timeline](#timeline)
15. [Risks and Mitigations](#risks-and-mitigations)
16. [Related Plans](#related-plans)

---

## Executive Summary

### Vision

Enable DeskCloud users to create **custom Docker images** with pre-installed tools, languages, and configurations. Users can then spawn AI-powered desktop sessions using these custom environments, dramatically reducing setup time and ensuring consistency across sessions.

### Value Proposition

| User Pain Point | DeskCloud Solution |
|-----------------|-------------------|
| "I waste 10 minutes installing tools every session" | Pre-built custom image, ready in seconds |
| "My team members have different environments" | Shared image templates, consistent setup |
| "I need specific browser versions for testing" | Curated templates with version pinning |
| "Enterprise needs approved software only" | BYOI with security scanning |

### Industry Precedent

| Platform | Approach |
|----------|----------|
| GitHub Codespaces | `devcontainer.json` |
| Gitpod | `devcontainer.json` + `.gitpod.yml` |
| Google Cloud Workstations | Custom Dockerfiles |
| AWS Cloud9 | AMI customization |

---

## Problem Statement

### Current Limitation

DeskCloud sessions currently use a **single default image** with:
- Ubuntu 22.04 base
- Standard desktop environment (XFCE)
- Basic tools (browsers, terminals)

### User Needs

1. **Developers:** Need specific language runtimes, IDEs, CLI tools
2. **QA Engineers:** Need specific browser versions, testing frameworks
3. **Data Scientists:** Need Python environments, Jupyter, ML libraries
4. **Enterprises:** Need approved software, security agents, VPN clients

### Market Opportunity

- Custom environments are a **high-value differentiator**
- Justifies premium pricing (compute + storage costs)
- Creates **stickiness** (users invest in configuration)
- Enables **enterprise sales** (compliance, standardization)

---

## Use Cases

### Use Case 1: Frontend Developer

```yaml
name: "Frontend Dev Environment"
base: ubuntu-22.04
tools:
  - vscode
  - nodejs-20
  - chrome
  - firefox
packages:
  - pnpm
  - yarn
scripts:
  - "pnpm install -g create-next-app"
```

**Outcome:** Developer opens session, VS Code ready with Node.js, can start coding immediately.

---

### Use Case 2: Selenium QA Engineer

```yaml
name: "Browser Testing Suite"
base: ubuntu-22.04
tools:
  - chrome-120
  - firefox-121
  - python-3.12
packages:
  - selenium
  - playwright
  - pytest
```

**Outcome:** QA engineer has exact browser versions for regression testing.

---

### Use Case 3: Data Science Team

```yaml
name: "ML Workstation"
base: ubuntu-22.04
tools:
  - python-3.11
  - jupyter
  - vscode
packages:
  - numpy
  - pandas
  - scikit-learn
  - pytorch
  - tensorflow
```

**Outcome:** Data scientist has full ML stack ready, consistent across team.

---

### Use Case 4: Enterprise Compliance

```yaml
name: "Acme Corp Approved"
base: company-base-image
tools:
  - approved-browser
  - company-vpn
  - security-agent
audit:
  - cis-benchmark
  - company-policy
```

**Outcome:** Enterprise has compliant, auditable environments.

---

## Feature Tiers

### Tier Breakdown

```
┌────────────────────────────────────────────────────────────────┐
│                        FREE TIER                               │
├────────────────────────────────────────────────────────────────┤
│  • Default DeskCloud image only                                │
│  • No customization                                            │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│                      PRO TIER ($29/mo)                         │
├────────────────────────────────────────────────────────────────┤
│  • Choose from 5 curated templates:                            │
│    - Web Developer (Node + Python + Browsers)                  │
│    - Python Data Science                                       │
│    - Java Enterprise                                           │
│    - DevOps Tooling                                            │
│    - Browser Testing                                           │
│  • Cannot customize templates                                  │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│                     TEAM TIER ($99/mo)                         │
├────────────────────────────────────────────────────────────────┤
│  • All Pro templates                                           │
│  • ⭐ Custom Image Builder:                                    │
│    - Visual recipe configurator                                │
│    - devcontainer.json support                                 │
│    - Custom apt/pip/npm packages                               │
│    - Post-install scripts (sandboxed)                          │
│  • 5 custom images per account                                 │
│  • Build logs and history                                      │
│  • Share images with team members                              │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│                   ENTERPRISE TIER (Custom)                     │
├────────────────────────────────────────────────────────────────┤
│  • All Team features                                           │
│  • ⭐ Bring Your Own Image (BYOI):                             │
│    - Import from any registry                                  │
│    - Private registry integration                              │
│    - Air-gapped environment support                            │
│  • ⭐ Private Image Registry:                                  │
│    - Dedicated namespace                                       │
│    - Access controls                                           │
│    - Image signing                                             │
│  • ⭐ Security & Compliance:                                   │
│    - Automated vulnerability scanning (Trivy)                  │
│    - CIS benchmark validation                                  │
│    - Approval workflows                                        │
│    - Audit logs                                                │
│  • Unlimited custom images                                     │
│  • Priority build queue                                        │
│  • Dedicated support                                           │
└────────────────────────────────────────────────────────────────┘
```

---

## Technical Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         DASHBOARD                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │    Recipe    │  │    Build     │  │   Session    │          │
│  │ Configurator │→ │   Monitor    │→ │   Launcher   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────────┬────────────────────────────────────┘
                             │ API
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       API GATEWAY                               │
│  POST /images          - Create image build                     │
│  GET  /images          - List user images                       │
│  GET  /images/:id      - Get image details                      │
│  DELETE /images/:id    - Delete image                           │
│  GET  /images/:id/logs - Stream build logs                      │
│  POST /images/validate - Validate BYOI image                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     BUILD ORCHESTRATOR                          │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Job Queue   │→ │   Builder    │→ │   Registry   │          │
│  │  (Redis/SQS) │  │   Workers    │  │    Push      │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                           │                                     │
│                    ┌──────┴──────┐                              │
│                    ▼             ▼                              │
│             ┌──────────┐  ┌──────────┐                          │
│             │ Docker   │  │ Kaniko   │                          │
│             │ BuildKit │  │ (K8s)    │                          │
│             └──────────┘  └──────────┘                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      IMAGE REGISTRY                             │
│                                                                 │
│  registry.deskcloud.app/                                        │
│  ├── templates/           # Curated templates (Pro)             │
│  │   ├── web-developer:latest                                   │
│  │   ├── data-science:latest                                    │
│  │   └── ...                                                    │
│  ├── users/               # Custom images (Team)                │
│  │   ├── user123/                                               │
│  │   │   ├── my-env:v1                                          │
│  │   │   └── my-env:v2                                          │
│  │   └── user456/                                               │
│  └── enterprise/          # BYOI validated (Enterprise)         │
│      └── acme-corp/                                             │
│          └── approved-image:v1                                  │
│                                                                 │
│  Options:                                                       │
│  • Harbor (self-hosted)                                         │
│  • AWS ECR                                                      │
│  • Google Artifact Registry                                     │
│  • Cloudflare R2 + Distribution                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Component Details

#### 1. Recipe Configurator (Dashboard)

Visual UI for defining environment:

```typescript
interface ImageRecipe {
  name: string;
  description?: string;
  base: BaseImage;
  tools: Tool[];
  packages: {
    apt?: string[];
    pip?: string[];
    npm?: string[];
    cargo?: string[];
  };
  scripts?: {
    postInstall?: string;  // Max 1000 chars, sandboxed
  };
  environment?: Record<string, string>;
}

type BaseImage = 
  | 'ubuntu-22.04'
  | 'ubuntu-24.04'
  | 'debian-12';

type Tool =
  | 'vscode'
  | 'nodejs-18' | 'nodejs-20' | 'nodejs-22'
  | 'python-3.10' | 'python-3.11' | 'python-3.12'
  | 'go-1.21' | 'go-1.22'
  | 'rust-stable'
  | 'java-17' | 'java-21'
  | 'chrome' | 'chrome-120' | 'chrome-121'
  | 'firefox' | 'firefox-120' | 'firefox-121'
  | 'docker'
  | 'kubectl'
  | 'terraform'
  | 'jupyter';
```

#### 2. Dockerfile Generator

Transforms recipe into Dockerfile:

```python
# app/premium/images/generator.py

class DockerfileGenerator:
    def generate(self, recipe: ImageRecipe) -> str:
        lines = [
            f"FROM deskcloud/base:{recipe.base}",
            "",
            "# Curated tools",
        ]
        
        for tool in recipe.tools:
            lines.append(f"RUN /opt/deskcloud/install-tool.sh {tool}")
        
        if recipe.packages.apt:
            apt_list = " ".join(recipe.packages.apt)
            lines.append(f"RUN apt-get update && apt-get install -y {apt_list}")
        
        if recipe.packages.pip:
            pip_list = " ".join(recipe.packages.pip)
            lines.append(f"RUN pip install {pip_list}")
        
        if recipe.packages.npm:
            npm_list = " ".join(recipe.packages.npm)
            lines.append(f"RUN npm install -g {npm_list}")
        
        if recipe.scripts and recipe.scripts.postInstall:
            # Sandboxed execution
            lines.append(f'RUN /opt/deskcloud/sandbox.sh "{recipe.scripts.postInstall}"')
        
        if recipe.environment:
            for key, value in recipe.environment.items():
                lines.append(f"ENV {key}={value}")
        
        lines.append("")
        lines.append("# DeskCloud session entrypoint")
        lines.append("ENTRYPOINT ['/opt/deskcloud/entrypoint.sh']")
        
        return "\n".join(lines)
```

#### 3. Build Worker

Executes builds in isolated environment:

```python
# app/premium/images/builder.py

class ImageBuilder:
    def __init__(self, registry_url: str, build_backend: str = "docker"):
        self.registry_url = registry_url
        self.build_backend = build_backend  # "docker" | "kaniko" | "buildkit"
    
    async def build(self, job: BuildJob) -> BuildResult:
        # Generate Dockerfile
        dockerfile = DockerfileGenerator().generate(job.recipe)
        
        # Create build context
        context = await self._create_context(dockerfile, job)
        
        # Execute build
        if self.build_backend == "docker":
            result = await self._build_with_docker(context, job)
        elif self.build_backend == "kaniko":
            result = await self._build_with_kaniko(context, job)
        
        # Push to registry
        if result.success:
            await self._push_to_registry(result.image_id, job.target_tag)
        
        # Security scan
        if job.scan_enabled:
            scan_result = await self._security_scan(job.target_tag)
            result.vulnerabilities = scan_result.vulnerabilities
        
        return result
    
    async def _build_with_docker(self, context: BuildContext, job: BuildJob) -> BuildResult:
        """Build using Docker BuildKit"""
        cmd = [
            "docker", "build",
            "--progress=plain",
            "--cache-from", f"{self.registry_url}/cache/{job.user_id}",
            "--cache-to", f"type=registry,ref={self.registry_url}/cache/{job.user_id}",
            "-t", job.target_tag,
            context.path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )
        
        # Stream logs
        async for line in process.stdout:
            await job.log_stream.write(line.decode())
        
        await process.wait()
        
        return BuildResult(
            success=process.returncode == 0,
            image_id=job.target_tag if process.returncode == 0 else None
        )
```

#### 4. devcontainer.json Support

Parse standard devcontainer format:

```python
# app/premium/images/devcontainer.py

class DevContainerParser:
    def parse(self, content: str) -> ImageRecipe:
        config = json.loads(content)
        
        recipe = ImageRecipe(
            name=config.get("name", "Custom Environment"),
            base=self._map_image(config.get("image", "ubuntu-22.04")),
            tools=[],
            packages={}
        )
        
        # Map features to tools
        for feature, options in config.get("features", {}).items():
            tool = self._map_feature_to_tool(feature)
            if tool:
                recipe.tools.append(tool)
        
        # Map customizations
        if "customizations" in config:
            vscode = config["customizations"].get("vscode", {})
            # Could pre-install extensions, etc.
        
        # Post-create command
        if "postCreateCommand" in config:
            recipe.scripts = {
                "postInstall": config["postCreateCommand"]
            }
        
        return recipe
    
    def _map_feature_to_tool(self, feature: str) -> Optional[str]:
        """Map devcontainer features to DeskCloud tools"""
        mapping = {
            "ghcr.io/devcontainers/features/node:1": "nodejs-20",
            "ghcr.io/devcontainers/features/python:1": "python-3.12",
            "ghcr.io/devcontainers/features/go:1": "go-1.22",
            "ghcr.io/devcontainers/features/docker-in-docker:2": "docker",
        }
        return mapping.get(feature)
```

---

## Implementation Phases

### Phase 1: Foundation (Week 1-2)

**Goal:** Core infrastructure for image building

- [ ] Database schema for images and builds
- [ ] Basic API endpoints (CRUD for images)
- [ ] Job queue setup (Redis or SQS)
- [ ] Docker BuildKit integration
- [ ] Registry setup (Harbor or ECR)
- [ ] Build logs streaming (WebSocket)

**Deliverables:**
- Can create image from Dockerfile via API
- Logs stream in real-time
- Image pushed to registry

---

### Phase 2: Recipe System (Week 3-4)

**Goal:** Visual recipe builder for Team tier

- [ ] Recipe schema and validation
- [ ] Dockerfile generator from recipes
- [ ] Curated tool catalog (20+ tools)
- [ ] Package allowlist system
- [ ] Dashboard UI: Recipe configurator
- [ ] Dashboard UI: Build status monitor

**Deliverables:**
- Users can visually create recipes
- Recipes build into images
- UI shows build progress

---

### Phase 3: Curated Templates (Week 5)

**Goal:** Pro tier templates

- [ ] Create 5 curated templates
- [ ] Template metadata and descriptions
- [ ] Template selection UI
- [ ] Auto-update mechanism for templates
- [ ] Template versioning

**Templates:**
1. Web Developer (Node + Python + Chrome)
2. Python Data Science (Python + Jupyter + ML libs)
3. Java Enterprise (Java + Maven + IDE tools)
4. DevOps Tooling (Docker + K8s + Terraform)
5. Browser Testing (Chrome + Firefox + Selenium)

---

### Phase 4: DevContainer Support (Week 6)

**Goal:** Import devcontainer.json

- [ ] DevContainer parser
- [ ] Feature mapping to tools
- [ ] Import from GitHub repo
- [ ] Import from file upload
- [ ] Validation and preview

**Deliverables:**
- Paste devcontainer.json, get DeskCloud image
- Import from GitHub URL

---

### Phase 5: Caching & Performance (Week 7)

**Goal:** Fast rebuilds

- [ ] Layer caching strategy
- [ ] Per-user cache namespaces
- [ ] Cache warming for common layers
- [ ] Build time analytics
- [ ] Parallel builds (queue management)

**Target:** Rebuild with minor changes < 60 seconds

---

### Phase 6: Security & BYOI (Week 8-9)

**Goal:** Enterprise features

- [ ] Trivy integration for vulnerability scanning
- [ ] Scan reports in dashboard
- [ ] BYOI validation pipeline
- [ ] Image requirements checker
- [ ] Approval workflow (admin approval for images)
- [ ] Audit logging

**Deliverables:**
- Security scan on every build
- Enterprise can import external images
- Full audit trail

---

### Phase 7: Private Registry (Week 10)

**Goal:** Enterprise isolation

- [ ] Per-organization namespaces
- [ ] Access control (who can pull)
- [ ] Image signing (Cosign)
- [ ] Private registry federation
- [ ] Air-gapped deployment docs

---

## Database Schema

### SQLModel Definitions

```python
# app/db/models.py (additions for image builder)

from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON
import uuid

def generate_image_uuid() -> str:
    return f"img_{uuid.uuid4().hex[:12]}"

def generate_build_uuid() -> str:
    return f"bld_{uuid.uuid4().hex[:12]}"


class ImageTemplate(SQLModel, table=True):
    """Curated templates (Pro tier)"""
    __tablename__ = "image_templates"
    
    id: str = Field(default_factory=generate_image_uuid, primary_key=True)
    name: str = Field(index=True)
    slug: str = Field(unique=True, index=True)  # e.g., "web-developer"
    description: str
    category: str  # "development", "testing", "data-science"
    
    # Recipe stored as JSON
    recipe: dict = Field(sa_column=Column(JSON))
    
    # Registry info
    registry_tag: str  # e.g., "registry.deskcloud.app/templates/web-developer:v2"
    
    # Metadata
    version: str = Field(default="1.0.0")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CustomImage(SQLModel, table=True):
    """User-created images (Team tier)"""
    __tablename__ = "custom_images"
    
    id: str = Field(default_factory=generate_image_uuid, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    organization_id: Optional[str] = Field(foreign_key="organizations.id", index=True)
    
    name: str
    description: Optional[str]
    
    # Recipe definition
    recipe: dict = Field(sa_column=Column(JSON))
    
    # Or devcontainer.json source
    devcontainer_json: Optional[str] = None
    source_repo: Optional[str] = None  # GitHub URL if imported
    
    # Registry info
    registry_tag: Optional[str] = None  # Set after successful build
    
    # Status
    status: str = Field(default="pending")  # pending, building, ready, failed
    
    # Sharing
    is_shared_with_team: bool = Field(default=False)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_built_at: Optional[datetime] = None
    
    # Relationships
    user: "User" = Relationship(back_populates="custom_images")
    builds: List["ImageBuild"] = Relationship(back_populates="image")


class ImageBuild(SQLModel, table=True):
    """Build job records"""
    __tablename__ = "image_builds"
    
    id: str = Field(default_factory=generate_build_uuid, primary_key=True)
    image_id: str = Field(foreign_key="custom_images.id", index=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    
    # Build info
    version: str  # e.g., "v3"
    dockerfile: str  # Generated Dockerfile content
    
    # Status
    status: str = Field(default="queued")  # queued, building, pushing, scanning, completed, failed
    
    # Results
    registry_tag: Optional[str] = None
    image_size_bytes: Optional[int] = None
    build_duration_seconds: Optional[int] = None
    
    # Logs
    logs_url: Optional[str] = None  # S3/R2 URL for full logs
    error_message: Optional[str] = None
    
    # Security scan results
    scan_status: Optional[str] = None  # pending, passed, failed, skipped
    vulnerabilities: Optional[dict] = Field(sa_column=Column(JSON))  # {critical: 0, high: 2, ...}
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Relationships
    image: CustomImage = Relationship(back_populates="builds")


class BYOIImage(SQLModel, table=True):
    """Enterprise Bring Your Own Image"""
    __tablename__ = "byoi_images"
    
    id: str = Field(default_factory=generate_image_uuid, primary_key=True)
    organization_id: str = Field(foreign_key="organizations.id", index=True)
    submitted_by_user_id: str = Field(foreign_key="users.id")
    
    name: str
    description: Optional[str]
    
    # Source
    source_registry: str  # e.g., "ghcr.io"
    source_tag: str  # e.g., "mycompany/custom-env:v1"
    
    # Validation
    validation_status: str = Field(default="pending")  # pending, validating, approved, rejected
    validation_errors: Optional[List[str]] = Field(sa_column=Column(JSON))
    
    # Security
    scan_status: Optional[str] = None
    vulnerabilities: Optional[dict] = Field(sa_column=Column(JSON))
    
    # Approval workflow
    approved_by_user_id: Optional[str] = Field(foreign_key="users.id")
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    
    # Internal registry (after validation)
    internal_tag: Optional[str] = None  # Our cached copy
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

### Session Model Update

```python
# Update Session model to support custom images

class Session(SQLModel, table=True):
    # ... existing fields ...
    
    # Image selection
    image_type: str = Field(default="default")  # default, template, custom, byoi
    image_id: Optional[str] = None  # Reference to template/custom/byoi
    image_tag: Optional[str] = None  # Resolved registry tag
```

---

## API Specification

### Image Templates (Pro+)

```yaml
# GET /api/v1/images/templates
# List available curated templates

Response 200:
  templates:
    - id: "tpl_webdev01"
      slug: "web-developer"
      name: "Web Developer"
      description: "Node.js, Python, and modern browsers"
      category: "development"
      tools: ["nodejs-20", "python-3.12", "chrome", "vscode"]
      version: "2.1.0"
    - id: "tpl_datasci01"
      slug: "data-science"
      name: "Python Data Science"
      ...
```

### Custom Images (Team+)

```yaml
# POST /api/v1/images
# Create a new custom image

Request:
  name: "My Frontend Environment"
  description: "For React development"
  recipe:
    base: "ubuntu-22.04"
    tools: ["nodejs-20", "vscode", "chrome"]
    packages:
      npm: ["pnpm", "create-next-app"]
    scripts:
      postInstall: "pnpm setup"

Response 201:
  id: "img_abc123def456"
  name: "My Frontend Environment"
  status: "pending"
  created_at: "2025-12-10T10:00:00Z"

---

# GET /api/v1/images
# List user's custom images

Response 200:
  images:
    - id: "img_abc123def456"
      name: "My Frontend Environment"
      status: "ready"
      registry_tag: "registry.deskcloud.app/users/user123/my-frontend:v1"
      last_built_at: "2025-12-10T10:05:00Z"

---

# POST /api/v1/images/{id}/build
# Trigger a new build

Response 202:
  build_id: "bld_xyz789"
  status: "queued"
  position_in_queue: 3

---

# GET /api/v1/images/{id}/builds/{build_id}
# Get build status

Response 200:
  id: "bld_xyz789"
  status: "building"
  progress: 45
  current_step: "Installing npm packages"
  started_at: "2025-12-10T10:01:00Z"

---

# GET /api/v1/images/{id}/builds/{build_id}/logs
# Stream build logs (WebSocket or SSE)

WebSocket Message:
  {
    "type": "log",
    "timestamp": "2025-12-10T10:02:15Z",
    "line": "Step 4/12 : RUN npm install -g pnpm"
  }

---

# DELETE /api/v1/images/{id}
# Delete custom image

Response 204: (no content)
```

### DevContainer Import

```yaml
# POST /api/v1/images/import/devcontainer
# Import from devcontainer.json

Request:
  # Option 1: Direct JSON
  devcontainer_json: |
    {
      "name": "Node.js",
      "image": "mcr.microsoft.com/devcontainers/javascript-node:20",
      "features": {
        "ghcr.io/devcontainers/features/python:1": {}
      },
      "postCreateCommand": "npm install"
    }
  
  # Option 2: GitHub URL
  github_url: "https://github.com/user/repo"
  branch: "main"
  path: ".devcontainer/devcontainer.json"

Response 200:
  parsed_recipe:
    name: "Node.js"
    base: "ubuntu-22.04"
    tools: ["nodejs-20", "python-3.12"]
    scripts:
      postInstall: "npm install"
  warnings:
    - "Feature 'ghcr.io/devcontainers/features/docker-in-docker' not supported"
  
  # User can then POST /api/v1/images with this recipe
```

### BYOI (Enterprise)

```yaml
# POST /api/v1/images/byoi
# Submit external image for validation

Request:
  name: "Acme Corp Standard"
  source_registry: "ghcr.io"
  source_tag: "acmecorp/dev-env:v1"
  pull_credentials:  # Optional, encrypted
    username: "bot"
    password: "token"

Response 202:
  id: "byoi_xyz123"
  validation_status: "pending"
  message: "Image queued for validation and security scan"

---

# GET /api/v1/images/byoi/{id}
# Check validation status

Response 200:
  id: "byoi_xyz123"
  validation_status: "approved"
  scan_status: "passed"
  vulnerabilities:
    critical: 0
    high: 0
    medium: 3
    low: 12
  internal_tag: "registry.deskcloud.app/enterprise/acmecorp/dev-env:v1"
```

---

## Dashboard UI/UX

### Recipe Configurator

```
┌─────────────────────────────────────────────────────────────────┐
│  Create Custom Image                                     [Save] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Name: [My Development Environment          ]                   │
│                                                                 │
│  Base Image:                                                    │
│  ┌─────────────────────────────────────────┐                    │
│  │ ○ Ubuntu 22.04 LTS (Recommended)        │                    │
│  │ ○ Ubuntu 24.04 LTS                      │                    │
│  │ ○ Debian 12                             │                    │
│  └─────────────────────────────────────────┘                    │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  Development Tools:                                             │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ [✓] VS Code Server                                      │    │
│  │ [✓] Node.js     [v20 LTS ▼]                            │    │
│  │ [✓] Python      [v3.12 ▼]                              │    │
│  │ [ ] Go          [v1.22 ▼]                              │    │
│  │ [ ] Rust        [stable ▼]                             │    │
│  │ [ ] Java        [v21 LTS ▼]                            │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  Browsers:                                                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ [✓] Chrome      [latest ▼]                             │    │
│  │ [ ] Firefox     [latest ▼]                             │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  Additional Packages:                                           │
│                                                                 │
│  apt:  [ffmpeg, imagemagick, jq                    ] [+ Add]    │
│  pip:  [requests, pandas                           ] [+ Add]    │
│  npm:  [pnpm, typescript                           ] [+ Add]    │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  Post-Install Script (optional):                                │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ pnpm setup                                              │    │
│  │ echo "export EDITOR=code" >> ~/.bashrc                  │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│  ⚠️ Script runs in sandboxed environment (max 60 seconds)      │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  Estimated build time: ~3 minutes                               │
│  Estimated image size: ~2.1 GB                                  │
│                                                                 │
│                              [Cancel]  [Build Image]            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Build Progress

```
┌─────────────────────────────────────────────────────────────────┐
│  Building: My Development Environment                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Status: Building                                               │
│  ████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 45%            │
│                                                                 │
│  Steps:                                                         │
│  ✅ Step 1/8: Pull base image                    (12s)          │
│  ✅ Step 2/8: Install VS Code Server             (45s)          │
│  ✅ Step 3/8: Install Node.js 20                 (23s)          │
│  🔄 Step 4/8: Install Python 3.12                (running...)   │
│  ⏳ Step 5/8: Install Chrome                                    │
│  ⏳ Step 6/8: Install apt packages                              │
│  ⏳ Step 7/8: Install pip packages                              │
│  ⏳ Step 8/8: Run post-install script                           │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  Build Logs:                                        [Full logs] │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ [10:02:15] Step 4/8 : RUN /opt/deskcloud/install...     │    │
│  │ [10:02:16] Downloading Python 3.12.1...                 │    │
│  │ [10:02:18] Extracting...                                │    │
│  │ [10:02:22] Installing pip...                            │    │
│  │ [10:02:24] ✓ Python 3.12.1 installed                    │    │
│  │ █                                                       │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│                                               [Cancel Build]    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Image Library

```
┌─────────────────────────────────────────────────────────────────┐
│  My Images                                    [+ Create Image]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ 🐳 My Development Environment                    [Ready] │  │
│  │    Node.js 20, Python 3.12, Chrome, VS Code              │  │
│  │    Last built: 2 hours ago • 2.1 GB • v3                 │  │
│  │                                                          │  │
│  │    [Use in Session]  [Rebuild]  [Edit]  [Delete]        │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ 🐳 Selenium Testing                            [Building] │  │
│  │    Chrome 120, Firefox 121, Python 3.12, Playwright      │  │
│  │    Building... 67% • Started 2 min ago                   │  │
│  │                                                          │  │
│  │    [View Progress]  [Cancel]                             │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ 🐳 Data Science Workbench                       [Failed] │  │
│  │    Python 3.11, Jupyter, PyTorch                         │  │
│  │    Failed: pip install timeout • 1 hour ago              │  │
│  │                                                          │  │
│  │    [View Logs]  [Retry Build]  [Edit]  [Delete]         │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  Usage: 3 of 5 custom images                                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Security Considerations

### 1. Dockerfile Generation Safety

```python
# Allowlist approach for packages

ALLOWED_APT_PACKAGES = {
    "ffmpeg", "imagemagick", "jq", "curl", "wget", "git",
    "build-essential", "cmake", "pkg-config", ...
}

BLOCKED_APT_PACKAGES = {
    "sudo", "passwd", "login", "ssh", ...
}

def validate_apt_packages(packages: List[str]) -> ValidationResult:
    blocked = [p for p in packages if p in BLOCKED_APT_PACKAGES]
    unknown = [p for p in packages if p not in ALLOWED_APT_PACKAGES]
    
    if blocked:
        return ValidationResult(valid=False, error=f"Blocked packages: {blocked}")
    if unknown:
        return ValidationResult(valid=False, error=f"Unknown packages: {unknown}")
    
    return ValidationResult(valid=True)
```

### 2. Post-Install Script Sandboxing

```python
# Sandbox configuration for user scripts

SCRIPT_LIMITS = {
    "max_duration_seconds": 60,
    "max_memory_mb": 512,
    "max_file_size_mb": 100,
    "network_access": False,
    "filesystem": "read-only except /home/user",
}

# Use bubblewrap or similar for isolation
async def run_sandboxed_script(script: str) -> ScriptResult:
    cmd = [
        "bwrap",
        "--ro-bind", "/", "/",
        "--tmpfs", "/tmp",
        "--dev", "/dev",
        "--proc", "/proc",
        "--unshare-net",  # No network
        "--die-with-parent",
        "/bin/bash", "-c", script
    ]
    # ... execute with timeout
```

### 3. BYOI Validation

```python
# Validation checks for external images

class BYOIValidator:
    async def validate(self, image_tag: str) -> ValidationResult:
        errors = []
        
        # 1. Pull image
        try:
            await self._pull_image(image_tag)
        except Exception as e:
            return ValidationResult(valid=False, error=f"Cannot pull: {e}")
        
        # 2. Check required files
        required_files = [
            "/opt/deskcloud/entrypoint.sh",
            "/usr/bin/Xvfb",
            "/usr/bin/x11vnc",
        ]
        for f in required_files:
            if not await self._file_exists(image_tag, f):
                errors.append(f"Missing required file: {f}")
        
        # 3. Check for dangerous configurations
        inspect = await self._inspect_image(image_tag)
        if inspect.user == "root":
            errors.append("Image runs as root (not allowed)")
        if "--privileged" in str(inspect.config):
            errors.append("Image requires privileged mode (not allowed)")
        
        # 4. Security scan
        scan = await self._run_trivy(image_tag)
        if scan.critical > 0:
            errors.append(f"Critical vulnerabilities found: {scan.critical}")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            scan_results=scan
        )
```

### 4. Registry Security

- **Namespace isolation:** Users can only push to their namespace
- **Pull restrictions:** Images only pullable by owner or shared team
- **Signed images:** Optional image signing with Cosign (Enterprise)
- **Scan on push:** All images scanned before becoming available

---

## Infrastructure Requirements

### Build Infrastructure

| Component | Development | Production |
|-----------|-------------|------------|
| Build Workers | 1x local Docker | 3x dedicated VMs |
| Registry | Local Harbor | AWS ECR / Harbor cluster |
| Job Queue | Redis (single) | Redis Cluster / SQS |
| Log Storage | Local filesystem | S3 / Cloudflare R2 |
| Cache Storage | Local Docker cache | Shared BuildKit cache |

### Estimated Resources per Build

| Resource | Estimate |
|----------|----------|
| CPU | 2-4 cores for 3-5 minutes |
| Memory | 4-8 GB |
| Disk I/O | 2-5 GB read/write |
| Network | 500MB - 2GB download |

### Registry Storage

| Tier | Images | Estimated Storage |
|------|--------|-------------------|
| Pro (templates only) | 5 templates | ~10 GB (shared) |
| Team (5 custom) | 5 per user × avg 2GB | ~10 GB per user |
| Enterprise | Unlimited | ~50+ GB per org |

---

## Cost Analysis

### Build Costs

| Provider | Build Cost | Notes |
|----------|------------|-------|
| Self-hosted VM | ~$0.02/build | $50/mo VM, ~2500 builds |
| Docker Build Cloud | $0.02/min | ~$0.06/build avg |
| AWS CodeBuild | $0.005/min | ~$0.015/build |
| GitHub Actions | Free/2000min | Then $0.008/min |

### Storage Costs

| Provider | Cost | Notes |
|----------|------|-------|
| AWS ECR | $0.10/GB/mo | + $0.09/GB transfer |
| Harbor (self-hosted) | ~$0.02/GB/mo | S3 backend |
| Cloudflare R2 | $0.015/GB/mo | No egress fees |

### Estimated Monthly Costs by Tier

| Scenario | Team (10 users) | Enterprise (50 users) |
|----------|-----------------|----------------------|
| Builds | 100/mo × $0.05 = $5 | 500/mo × $0.05 = $25 |
| Storage | 100 GB × $0.02 = $2 | 500 GB × $0.02 = $10 |
| Registry | $50 (managed) | $100 (HA cluster) |
| **Total** | ~$57/mo | ~$135/mo |

### Pricing Justification

| Tier | Price | Cost | Margin |
|------|-------|------|--------|
| Team $99/mo | $99 | ~$6/user | 94% gross |
| Enterprise custom | $500+/mo | ~$15-30/org | 94%+ |

---

## Success Metrics

### Adoption Metrics

| Metric | Target (6 months) |
|--------|-------------------|
| Team tier upgrades | 20% of Pro users upgrade for custom images |
| Custom images created | 3+ per Team user |
| Template usage (Pro) | 60% of Pro sessions use templates |

### Engagement Metrics

| Metric | Target |
|--------|--------|
| Build success rate | > 95% |
| Avg build time | < 4 minutes |
| Session start time (custom) | < 30 seconds (cached) |
| Rebuild frequency | 1-2 per image per week |

### Revenue Metrics

| Metric | Target |
|--------|--------|
| MRR from custom images | 30% of total MRR |
| Team tier conversion | 10% of Pro → Team |
| Enterprise pipeline | 3+ in negotiation |

---

## Timeline

```
Week 1-2:   Foundation
            ├── Database schema
            ├── Basic API
            ├── Job queue
            └── Docker BuildKit integration

Week 3-4:   Recipe System
            ├── Recipe schema
            ├── Dockerfile generator
            ├── Tool catalog
            └── Dashboard UI

Week 5:     Templates
            ├── Create 5 templates
            ├── Template management
            └── Pro tier integration

Week 6:     DevContainer
            ├── Parser
            ├── GitHub import
            └── Validation UI

Week 7:     Performance
            ├── Layer caching
            ├── Build analytics
            └── Optimization

Week 8-9:   Security/BYOI
            ├── Trivy integration
            ├── BYOI validation
            └── Approval workflow

Week 10:    Private Registry
            ├── Namespace isolation
            ├── Access control
            └── Documentation

─────────────────────────────────────────────
Total: 10 weeks from start
Dependencies: Dashboard + Auth must exist first
```

---

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Build failures frustrate users | Medium | High | Detailed error messages, suggested fixes, retry button |
| Build queue congestion | Medium | Medium | Priority queue for paid tiers, auto-scaling workers |
| Security vulnerability in user image | Low | Critical | Mandatory Trivy scanning, blocked package list |
| Registry storage costs explode | Low | Medium | Image retention policies, compression, dedup |
| Users abuse build resources | Low | Medium | Rate limits, build time limits, cost monitoring |
| Complex UI scares users | Medium | Medium | Start with templates, progressive disclosure |

---

## Related Plans

- [Next.js Landing & Dashboard](./nextjs_landing_dashboard.md) - Dashboard implementation
- [Session Video Recording](./session_video_recording.md) - Another premium feature
- [Multi-OS Support](./multi_os_support.md) - Extended image support for Android, Windows, Pi
- [Remote Agent Client](./remote_agent_client.md) - Control user's own computers (no custom images needed)
- Backend Auth & Users - Required before this feature

---

## Appendix A: Tool Catalog (Initial)

```yaml
# /config/tool_catalog.yaml

categories:
  editors:
    - id: vscode
      name: "VS Code Server"
      version: "latest"
      install_script: "/opt/deskcloud/tools/install-vscode.sh"
      size_mb: 350

  languages:
    - id: nodejs-18
      name: "Node.js 18 LTS"
      version: "18.19.0"
    - id: nodejs-20
      name: "Node.js 20 LTS"
      version: "20.10.0"
    - id: nodejs-22
      name: "Node.js 22"
      version: "22.0.0"
    - id: python-3.10
      name: "Python 3.10"
      version: "3.10.13"
    - id: python-3.11
      name: "Python 3.11"
      version: "3.11.7"
    - id: python-3.12
      name: "Python 3.12"
      version: "3.12.1"
    - id: go-1.21
      name: "Go 1.21"
      version: "1.21.5"
    - id: go-1.22
      name: "Go 1.22"
      version: "1.22.0"
    - id: rust-stable
      name: "Rust (stable)"
      version: "1.75.0"
    - id: java-17
      name: "Java 17 LTS"
      version: "17.0.9"
    - id: java-21
      name: "Java 21 LTS"
      version: "21.0.1"

  browsers:
    - id: chrome
      name: "Google Chrome (latest)"
      version: "latest"
    - id: chrome-120
      name: "Google Chrome 120"
      version: "120.0.6099.109"
    - id: chrome-119
      name: "Google Chrome 119"
      version: "119.0.6045.199"
    - id: firefox
      name: "Mozilla Firefox (latest)"
      version: "latest"
    - id: firefox-121
      name: "Mozilla Firefox 121"
      version: "121.0"

  devops:
    - id: docker
      name: "Docker CLI + Compose"
      version: "24.0.7"
    - id: kubectl
      name: "kubectl"
      version: "1.29.0"
    - id: terraform
      name: "Terraform"
      version: "1.6.6"
    - id: aws-cli
      name: "AWS CLI v2"
      version: "2.15.0"
    - id: gcloud
      name: "Google Cloud CLI"
      version: "458.0.0"

  data-science:
    - id: jupyter
      name: "JupyterLab"
      version: "4.0.9"
    - id: conda
      name: "Miniconda"
      version: "latest"
```

---

## Appendix B: Example devcontainer.json Mapping

```json
// Input: .devcontainer/devcontainer.json
{
  "name": "Node.js & TypeScript",
  "image": "mcr.microsoft.com/devcontainers/javascript-node:20",
  "features": {
    "ghcr.io/devcontainers/features/python:1": {
      "version": "3.12"
    },
    "ghcr.io/devcontainers/features/docker-in-docker:2": {}
  },
  "customizations": {
    "vscode": {
      "extensions": [
        "dbaeumer.vscode-eslint",
        "esbenp.prettier-vscode"
      ]
    }
  },
  "postCreateCommand": "npm install",
  "forwardPorts": [3000]
}

// Output: DeskCloud Recipe
{
  "name": "Node.js & TypeScript",
  "base": "ubuntu-22.04",
  "tools": [
    "nodejs-20",
    "python-3.12",
    "docker",
    "vscode"
  ],
  "packages": {},
  "scripts": {
    "postInstall": "npm install"
  },
  "warnings": [
    "VS Code extensions will need to be installed manually in session",
    "Port forwarding handled automatically by DeskCloud"
  ]
}
```

---

*Document Version: 1.0*  
*Last Updated: December 2025*
