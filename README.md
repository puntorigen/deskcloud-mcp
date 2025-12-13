# DeskCloud Platform (Private)

> ⚠️ **Private Repository** - This repo contains premium features and business logic.

## Overview

This is the private monorepo for DeskCloud, containing:
- Premium features (Connect Agent, video recording, custom images)
- Next.js frontend (landing page + dashboard)
- Infrastructure configurations

## Structure

```
deskcloud-platform/
├── core/                   # Git subtree from puntorigen/deskcloud-mcp
├── frontend/               # Next.js app (Vercel)
├── backend-premium/        # Premium API extensions (Render.com)
├── connect-agent/          # Desktop client app
├── infrastructure/         # Terraform/Docker configs
└── docs/plans/             # Planning documents
```

## Getting Started

### 1. Set up the core subtree

```bash
# Add the open source repo as a subtree
git subtree add --prefix=core https://github.com/puntorigen/deskcloud-mcp.git main --squash
```

### 2. Pull updates from open source

```bash
git subtree pull --prefix=core https://github.com/puntorigen/deskcloud-mcp.git main --squash
```

### 3. Push fixes back to open source (if applicable)

```bash
git subtree push --prefix=core https://github.com/puntorigen/deskcloud-mcp.git main
```

## Plan Documents

All planning documents are in `docs/plans/`:

| Document | Description |
|----------|-------------|
| `MASTER_ROADMAP.md` | Start here - project overview and roadmap |
| `nextjs_landing_dashboard.md` | Frontend + auth + dashboard |
| `remote_agent_client.md` | Connect Agent (control your PCs) |
| `multi_os_support.md` | Raspberry Pi, Android, Windows |
| `session_video_recording.md` | Video recording feature |
| `custom_image_builder.md` | Custom Docker images |
| `opensource_release_checklist.md` | Open source release process |

## Environments

| Environment | Frontend | Backend |
|-------------|----------|---------|
| Production | deskcloud.app (Vercel) | api.deskcloud.app (Render) |
| Staging | staging.deskcloud.app | api-staging.deskcloud.app |

## Related Repositories

- **Open Source Core**: [puntorigen/deskcloud-mcp](https://github.com/puntorigen/deskcloud-mcp)
