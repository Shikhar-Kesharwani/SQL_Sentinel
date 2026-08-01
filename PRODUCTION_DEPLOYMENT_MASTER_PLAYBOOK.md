PRODUCTION DEPLOYMENT MASTER PLAYBOOK
A Universal, Reusable Deployment & DevOps Playbook for Full-Stack Software Projects

Paste this document into any future project as a standing reference for an AI coding assistant (Claude Code, Cursor, Codex, Gemini CLI, etc.) or a human engineer. It governs how the project gets deployed, secured, monitored, and scaled — never how the application looks or behaves.

Table of Contents
1. Introduction
2. Production Deployment Philosophy
3. Project Structure
4. Environment Variables
5. Cloud Native Deployment
6. Docker Deployment
7. Database Best Practices
8. Object Storage
9. Redis
10. Background Workers
11. Security
12. Logging
13. Monitoring
14. Performance
15. CI/CD
16. README Template
17. Deployment Architecture Diagrams
18. Interview Talking Points
19. Production Checklist
20. Common Deployment Mistakes
21. Troubleshooting Guide
22. Scaling Strategy

1. Introduction
1.1 What this document is
This playbook is a deployment operating manual, not a design document. It exists to answer one question, repeatedly, across every project you ever ship: "How do I take working application code and make it run safely, reliably, and cheaply in production — without touching what the application does?"
It is written to be pasted at the start of a new project's deployment phase, read by either a human or an AI coding assistant, and followed mechanically. Every chapter is self-contained enough to be referenced individually ("go implement chapter 11") without re-reading the whole document.

1.2 What this document is not
This is not:
- A UI/UX guide
- A system design document for the application's business logic
- A framework tutorial
- A one-time deployment log for a specific project
If a task involves changing what a button does, how a page looks, what data a form collects, or how a feature behaves — that task does not belong in this playbook. Redirect it to normal feature development. This playbook only activates once the application already works and the question becomes "how do we ship it."

1.3 Who should use this
- AI coding assistants operating in agentic mode on a repository, told to "productionize this" or "deploy this."
- Solo developers and students building portfolio projects who want production-grade deployment without production-grade headcount.
- Small teams who don't yet have a dedicated DevOps/SRE hire and need a repeatable standard.

1.4 How to use this document
- Read Chapter 2 (Philosophy) and the Critical Preservation Rules below before touching anything.
- Read Chapter 3 to understand how the repository should be organized for deployment.
- Pick one deployment architecture from Chapter 5 (Cloud Native) or Chapter 6 (Docker) — or implement both, since the application code doesn't change between them.
- Work top-to-bottom through Chapters 7–15, implementing each concern (database, storage, caching, security, logging, monitoring, performance, CI/CD) incrementally, committing after each.
- Use Chapter 19 as a final gate before calling anything "production ready."
- Keep Chapters 20–22 as ongoing references — mistakes to avoid, a debugging companion, and a map of how the deployment should evolve as the project grows.

1.5 Critical Preservation Rules (read this first, every time)
This is the single most important section in the entire document. It overrides every other instruction if there is ever a conflict.
The deployed application must look, feel, and behave exactly as it did before deployment work began.
Concretely: an AI assistant or engineer working from this playbook may only touch deployment, infrastructure, security, performance, scalability, reliability, monitoring, logging, CI/CD, and documentation. It may never touch the UI, UX, layout, styling, branding, routing, page structure, business logic, API contracts, or feature set — because none of those are deployment concerns, and changing them while "just deploying" silently rewrites the product without anyone deciding to.
If, in the course of deployment work, a change to application code genuinely becomes unavoidable (for example: a hardcoded localhost URL must become an environment variable, or a missing /health route must be added for the orchestrator to function), the following procedure is mandatory before writing a single line:
- State what the change is, precisely.
- State why it's required — what breaks in production without it.
- State the benefit of making the change.
- State the risk of making the change.
- State the alternative(s) considered, including "do nothing and accept X limitation."
Only then make the smallest possible backward-compatible change — never a rewrite, never a "while I'm in here" improvement, never a refactor of surrounding code.
A useful gut check: if a proposed change would be visible to an end user looking at the running application, it is very likely out of scope. If it's only visible in logs, infrastructure config, or a terminal, it's very likely in scope.

1.6 Applicability - What to Include vs. Skip
Not every chapter in this playbook applies to every project. Implementing infrastructure a project doesn't need is its own kind of production risk - it adds attack surface, cost, and operational burden with no corresponding benefit. Before starting work, classify each chapter using the table below and skip anything the project has no genuine requirement for.

Chapter | Status | Applies when... | Safe to skip when...
--- | --- | --- | ---
1-4 (Intro, Philosophy, Structure, Env Vars) | Always required | Every project, no exceptions | Never - these are the foundation everything else sits on
5 (Cloud Native) | Conditional - pick 5 or 6 | The project will run on managed platforms (Vercel, Render, Railway, Neon, etc.) | The project is exclusively self-hosted via Docker
6 (Docker) | Conditional - pick 5 or 6 | The project needs self-hosted or full-control deployment | The project is exclusively cloud-native/managed
7 (Database) | Always required | The project has any persistent data store | Never - nearly every real application has a database
8 (Object Storage) | Conditional | The project accepts file/image/document uploads or generates downloadable files | No user-generated or stored files exist anywhere in the app
9 (Redis) | Conditional | The project needs caching, rate limiting, server-side sessions, or a job queue | The project has low traffic, uses stateless JWTs only, and has no background jobs
10 (Background Workers) | Conditional | The project has slow, unreliable, or deferrable work (email, PDF generation, third-party API calls) | Every operation the app performs is fast and safe to do synchronously in the request cycle
11 (Security) | Always required | Every project accepting any network traffic | Never - baseline security headers, input handling, and secret hygiene apply universally
12 (Logging) | Always required | Every project | Never - even a small project needs structured logs to debug production issues
13 (Monitoring) | Always required (Sentry/health checks); metrics conditional | Error tracking and health checks: always. Full Prometheus-style metrics: once traffic/team size justifies a dashboard | Metrics collection can be deferred for a solo portfolio project with minimal traffic
14 (Performance) | Conditional, by sub-topic | Compression and caching: nearly always cheap and worth it. Image optimization: only if the app serves images. Code splitting/bundle analysis: only if the frontend bundle is large enough to matter | A tiny app with no images and a small bundle can defer most of this chapter
15 (CI/CD) | Always required | Every project with more than a single manual deploy expected | Never - even solo projects benefit from automated lint/test/build gates
16 (README Template) | Always required | Every project | Never - documentation is not optional
17 (Diagrams) | Conditional | Onboarding a team, or documenting for an interview/portfolio audience | A private solo project with no other stakeholders can skip formal diagrams, though they remain good practice
18 (Interview Talking Points) | Conditional | The project is a portfolio piece or the deployment will be discussed in an interview/review setting | Purely internal production systems with no such audience
19 (Production Checklist) | Always required | Before any real production launch | Never - this is the final gate, always run it
20-21 (Mistakes, Troubleshooting) | Always required as reference | Every project, as an ongoing reference | Never - keep both available even if not actively read line by line
22 (Scaling Strategy) | Conditional, by stage | Only the stage matching the project's current size applies actively; later stages are read for awareness, not implemented early | Never implement Stage 3/4 tooling (multi-region, sharding, IaC) for a Stage 1 portfolio project - that is premature complexity, not thoroughness

The governing rule: when a chapter's trigger condition genuinely doesn't exist in the project, skip that chapter's implementation entirely rather than adding the infrastructure "just in case." When in doubt, apply the same procedure as any other necessary change (Section 1.5) - state what's being skipped and why, so the decision is visible and reviewable, not silent.

2. Production Deployment Philosophy
2.1 Deployment is a separate concern from development
The application should be deployable because it was built to a set of portable conventions (environment-based config, statelessness, health endpoints) — not because deployment work reshapes the application to fit a particular platform. Good deployment work is almost always additive: new config files, new scripts, new infrastructure definitions, sitting alongside application code without invading it.

2.2 Boring technology first
Production systems should default to the most boring, well-documented, widely-supported option at every layer unless there's a concrete reason not to: managed Postgres over a self-hosted database cluster, a standard reverse proxy over a custom one, established CI/CD platforms over bespoke pipelines. Novelty is a cost paid in incident response, not a feature.

2.3 Twelve-Factor as a baseline, not a religion
This playbook borrows heavily from the Twelve-Factor App methodology: config in the environment, strict separation of build/release/run stages, stateless processes, disposability, dev/prod parity. These principles are treated as strong defaults. Deviating from them is allowed when justified (see the change procedure in 1.5), not forbidden outright.

2.4 Everything reproducible, nothing tribal
A deployment that only works because one engineer remembers a manual step is a production incident waiting to happen. Every step in this playbook should end up codified: in a Dockerfile, in a CI workflow, in an infrastructure-as-code file, or in the README — never only in someone's memory.

2.5 Fail loud, fail early
Prefer configuration that fails at build time or startup time over configuration that fails silently at runtime under load. A missing environment variable should crash the container on boot with a clear error message, not undefined-propagate through the app until a user hits a broken feature.

2.6 Security and observability are not "later" tasks
They are treated in this playbook as first-class chapters (11–13), not appendices. A project without structured logs, health checks, and basic secret hygiene is not "done, minus polish" — it is not production ready, full stop.

2.7 Two architectures, one codebase
This playbook standardizes on supporting both a fully managed cloud-native deployment and a self-hosted Docker Compose deployment from the same application code. This is deliberate: it forces the application to be genuinely portable (no platform-specific lock-in baked into business logic), it gives you a cheap/managed option and a full-control option for different project stages, and it's an excellent way to demonstrate platform-engineering competence in a portfolio or interview setting.

3. Project Structure
3.1 Guiding principle
Deployment artifacts live in clearly separated, predictable locations, distinct from application source. Nothing about deployment tooling should require hunting through src/ to find it, and nothing about deployment tooling should live inside src/.

3.2 Reference layout
project-root/
├── apps/                 # or frontend/ + backend/ if not a monorepo
│   ├── frontend/
│   │   ├── src/
│   │   ├── public/
│   │   ├── Dockerfile
│   │   ├── .env.example
│   │   └── package.json
│   └── backend/
│       ├── src/
│       ├── Dockerfile
│       ├── .env.example
│       └── package.json
├── infra/
│   ├── docker/
│   │   ├── docker-compose.yml
│   │   ├── docker-compose.prod.yml
│   │   ├── nginx/
│   │   │   └── default.conf
│   │   └── .env.example
│   ├── cloud/
│   │   ├── vercel.json
│   │   ├── render.yaml
│   │   └── terraform/    # optional, if IaC is used
│   └── scripts/
│       ├── migrate.sh
│       ├── backup-db.sh
│       ├── restore-db.sh
│       └── seed.sh
├── .github/
│   └── workflows/
│       ├── ci.yml
│       ├── deploy-frontend.yml
│       └── deploy-backend.yml
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DEPLOYMENT.md
│   ├── TROUBLESHOOTING.md
│   └── RUNBOOK.md
├── PRODUCTION_DEPLOYMENT_MASTER_PLAYBOOK.md
├── docker-compose.yml    # symlink or thin wrapper, if preferred at root
├── .env.example
├── .gitignore
└── README.md

3.3 Rules for this structure
- .env files are never committed. Only .env.example files with placeholder values are committed. This is enforced in .gitignore and re-verified in CI (see Chapter 15).
- Every service that gets containerized owns its own Dockerfile, colocated with its source, not centralized in infra/. Compose files reference them by relative path.
- infra/ owns orchestration, not application logic. If a script in infra/scripts/ needs to embed business logic beyond "run this migration tool" or "call this backup command," that's a sign the logic belongs in the application instead.
- docs/ is deployment/ops documentation, separate from any product or API documentation that already exists elsewhere in the repo.
- Monorepo vs. polyrepo doesn't change any of the above — only the path depth.

3.4 What never moves
Nothing in this chapter implies restructuring src/. If an existing project has a different but coherent structure, deployment tooling adapts to fit alongside it — the reference layout above is a default for new projects, not a mandate to reorganize existing ones. Reorganizing source code is an application change and falls under the Critical Preservation Rules in Chapter 1.

4. Environment Variables
4.1 The core rule
Nothing environment-specific is ever hardcoded. Not a database URL, not an API key, not a port number, not a feature flag, not a third-party service endpoint. If a value differs — or could plausibly ever differ — between local development, staging, and production, it belongs in an environment variable.

4.2 Naming conventions
Convention | Example | Notes
--- | --- | ---
SCREAMING_SNAKE_CASE | DATABASE_URL | Universal standard across virtually every runtime
Prefix by concern | REDIS_URL, S3_BUCKET_NAME | Groups related config, aids searchability
Public frontend vars get a framework-specific prefix | NEXT_PUBLIC_API_URL, VITE_API_URL | Required by most bundlers to expose vars to client-side code — anything without this prefix must never leak to the browser bundle
No secrets in NEXT_PUBLIC_* / VITE_* ever | — | These are compiled into the client bundle and are publicly readable

4.3 Required files
File | Committed? | Purpose
--- | --- | ---
.env | No | Actual local secrets, gitignored
.env.example | Yes | Every variable name the app needs, with placeholder or dummy values, documented inline
.env.production | No | Never committed; production secrets live in the hosting platform's secret manager, not in a file
.env.test | Optional, yes | Safe to commit if it only contains non-sensitive test fixtures

4.4 .env.example template
# ---- App ----
NODE_ENV=development
PORT=4000

# ---- Database ----
DATABASE_URL=postgresql://user:password@localhost:5432/appdb

# ---- Redis ----
REDIS_URL=redis://localhost:6379

# ---- Auth ----
JWT_SECRET=replace_with_a_long_random_string
JWT_EXPIRES_IN=15m
REFRESH_TOKEN_SECRET=replace_with_a_different_long_random_string

# ---- OAuth (example: Google) ----
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

# ---- Object Storage ----
S3_ENDPOINT=
S3_BUCKET_NAME=
S3_ACCESS_KEY_ID=
S3_SECRET_ACCESS_KEY=
S3_REGION=auto

# ---- Monitoring ----
SENTRY_DSN=

# ---- Frontend-exposed (safe for browser) ----
NEXT_PUBLIC_API_URL=http://localhost:4000

4.5 Validation at startup
Environment variables should be validated once, at process boot, and the process should refuse to start if a required variable is missing or malformed — not fail later, mid-request, with a confusing stack trace. A small schema-validated config module accomplishes this cheaply:

```ts
// config/env.ts
import { z } from "zod";

const envSchema = z.object({
  NODE_ENV: z.enum(["development", "test", "production"]),
  PORT: z.coerce.number().default(4000),
  DATABASE_URL: z.string().url(),
  REDIS_URL: z.string().url(),
  JWT_SECRET: z.string().min(32, "JWT_SECRET must be at least 32 characters"),
});

const parsed = envSchema.safeParse(process.env);
if (!parsed.success) {
  console.error("Invalid environment configuration:");
  console.error(parsed.error.flatten().fieldErrors);
  process.exit(1);
}
export const env = parsed.data;
```
This is deployment tooling, not business logic — it is safe to add even under the Critical Preservation Rules, because it changes how config is loaded, not what the application does.

4.6 Secrets management by platform
Platform | Where secrets live
--- | ---
Vercel | Project -> Settings -> Environment Variables (scoped per environment: Production/Preview/Development)
Render / Railway | Service -> Environment tab, or a linked secret group
Docker Compose (self-hosted) | A gitignored .env file next to docker-compose.yml, referenced via env_file:
Kubernetes | Secret objects, ideally sourced from an external secrets manager (Vault, AWS Secrets Manager, Doppler) rather than committed manifests
GitHub Actions | Repository or environment-scoped Encrypted Secrets, never plaintext in workflow YAML

4.7 Rotation and hygiene
- Rotate JWT_SECRET, database passwords, and third-party API keys on a schedule (e.g., every 90 days) and immediately on suspected compromise or offboarding of anyone with access.
- Never log environment variables, even at debug level. A single accidental console.log(process.env) in a shared logging sink is a common real-world leak vector.
- Use distinct secrets per environment. A staging leak should never compromise production.

5. Cloud Native Deployment
5.1 Overview
The cloud-native architecture deploys each concern to a managed platform purpose-built for it, wired together over the network rather than colocated on one machine. It trades some cost and a bit of network latency between services for near-zero infrastructure maintenance.

+-------------+       +--------------+       +-----------------+
|   Vercel    |-----> |   Render/    |-----> | Neon / Supabase |
| (Frontend)  |       |   Railway    |       |   (Postgres)    |
|             |       |  (Backend)   |       |                 |
+-------------+       +--------------+       +-----------------+
                             |
                             v
                      +-----------------+
                      | Cloudflare R2 / |
                      | Supabase Storage|
                      +-----------------+

5.2 Frontend -> Vercel
Vercel is the default choice for frontend hosting because it handles CDN distribution, image optimization, preview deployments per pull request, and zero-config builds for most major frameworks (Next.js, Vite, React, Svelte, Astro) out of the box.

Minimum required setup:
- Connect the GitHub repository in the Vercel dashboard, or deploy via CLI (vercel --prod).
- Set the Root Directory if the frontend lives in a subfolder (e.g., apps/frontend).
- Add all NEXT_PUBLIC_* / VITE_* environment variables under Project Settings, scoped correctly per environment.
- Set the build command and output directory explicitly if the framework preset doesn't auto-detect correctly.
- Enable Preview Deployments for pull requests — this is close to free and catches integration issues before merge.

infra/cloud/vercel.json (only needed for non-default behavior):
```json
{
  "framework": "nextjs",
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "X-Frame-Options", "value": "DENY" },
        { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" }
      ]
    }
  ]
}
```

5.3 Backend -> Render or Railway
Both platforms offer managed container hosting with git-push (or GitHub Actions-triggered) deploys, without needing to hand-roll Kubernetes or EC2 management.

Criteria | Render | Railway
--- | --- | ---
Pricing model | Per-service, predictable | Usage-based, can be cheaper at low traffic
Native cron jobs | Yes | Yes
Native background workers | Yes (separate service type) | Yes
Zero-downtime deploys | Yes, on paid tiers | Yes
Built-in managed Postgres | Yes | Yes
Preview environments | Yes | Yes

Either is a reasonable default; pick one and be consistent. A minimal render.yaml (Render's infrastructure-as-code format) for a Node backend:

```yaml
services:
  - type: web
    name: backend-api
    env: node
    plan: starter
    buildCommand: npm ci && npm run build
    startCommand: npm run start
    healthCheckPath: /health
    envVars:
      - key: NODE_ENV
        value: production
      - key: DATABASE_URL
        fromDatabase:
          name: app-db
          property: connectionString
      - key: JWT_SECRET
        sync: false # set manually in dashboard, not in this file
```

5.4 Database -> Neon / Supabase / MongoDB Atlas
Option | Best for | Notes
--- | --- | ---
Neon | Postgres, serverless scale-to-zero, branching per PR | Excellent for variable-traffic apps; database branching mirrors git branching
Supabase | Postgres + auth + storage + realtime as a bundle | Good when you want fewer moving parts, not just a database
MongoDB Atlas | Document-model data, existing Mongo codebases | Free tier (M0) is sufficient for early-stage projects

In all three cases: enable automated daily backups, enable connection pooling (see Chapter 7.1), and restrict network access to known origins where the platform supports IP allow-listing.

5.5 Storage -> Cloudflare R2 / Supabase Storage
Covered in depth in Chapter 8. At the infrastructure level, the only cloud-native-specific decision is: object storage is never the application server's local filesystem, because most cloud-native compute (Vercel functions, Render's ephemeral containers) has no durable local disk. Files written locally will vanish on the next deploy or restart.

5.6 DNS
- Point the apex domain (example.com) and/or www subdomain at Vercel via the DNS records Vercel provides (typically an A record to Vercel's IP or a CNAME for www).
- Point an api. subdomain at the backend host (Render/Railway provide a CNAME target).
- Set a low TTL (e.g., 300s) while first configuring DNS, then raise it once stable, to make mistakes cheap to fix during setup.
- Verify propagation with dig example.com or nslookup before assuming a record is live — DNS caches lie for a while.

5.7 HTTPS
Both Vercel and Render/Railway provision and renew TLS certificates automatically via Let's Encrypt once DNS is correctly pointed at them. There is normally no manual certificate management in the cloud-native path. The only action required is: never serve mixed content (an HTTPS page loading an http:// resource) and always redirect http:// to https:// — both platforms do this by default, but it's worth confirming with curl -I http://yourdomain.com and checking for a redirect to https://.

5.8 CI/CD
Covered fully in Chapter 15. In the cloud-native path, CI/CD is largely handled by the platforms' native git integration (push to main -> auto-deploy), with GitHub Actions layered on top for checks that must pass before that deploy is allowed to happen (lint, type-check, test, build validation).

5.9 Health Checks
Every backend service must expose at minimum:
- GET /health -> 200 OK, { "status": "ok" } (liveness: is the process running?)
- GET /ready -> 200 OK, { "status": "ready" } (readiness: can it serve traffic - DB reachable, etc.)

Render, Railway, and most orchestrators poll a configured health check path and will restart or stop routing traffic to an instance that fails it repeatedly. See Chapter 13.2 for the full liveness/readiness distinction and example implementation.

6. Docker Deployment
6.1 Overview
The Docker architecture runs every service — frontend, backend, database, cache, workers, reverse proxy — as containers on a single host or a small cluster of hosts you control. It trades managed-platform convenience for full control over the runtime, no vendor lock-in, and predictable flat hosting costs regardless of traffic.

                      +---------------------+
Internet ----------->| Nginx (reverse      |
                     | proxy, TLS term)     |
                     +----------+----------+
                                |
          +-----------------+-----------------+
          |                                   |
  +-------v-------+                  +--------v-------+
  |   Frontend    |                  |    Backend     |
  |   Container   |                  |   Container    |
  +---------------+                  +--------+-------+
                                              |
           +-------------------------+------------------------+
           |                         |                        |
   +-------v-------+        +---------v--------+      +---------v--------+
   |   Postgres    |        |       Redis      |      |      Worker      |
   |   Container   |        |     Container    |      |    Container     |
   +---------------+        +-------------------+      +------------------+

6.2 Dockerfiles
Principles: multi-stage builds, non-root users, minimal base images, and layer caching that puts rarely-changing steps (dependency installation) before frequently-changing steps (copying source code).

Backend Dockerfile (Node.js example):
```dockerfile
# ---- Base ----
FROM node:20-alpine AS base
WORKDIR /app

# ---- Dependencies ----
FROM base AS deps
COPY package.json package-lock.json ./
RUN npm ci --omit=dev

# ---- Build ----
FROM base AS build
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# ---- Production ----
FROM base AS production
ENV NODE_ENV=production
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
COPY --from=deps /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist
COPY package.json ./
USER appuser
EXPOSE 4000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:4000/health || exit 1
CMD ["node", "dist/index.js"]
```

Frontend Dockerfile (Next.js example, standalone output):
```dockerfile
FROM node:20-alpine AS base
WORKDIR /app

FROM base AS deps
COPY package.json package-lock.json ./
RUN npm ci

FROM base AS build
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM base AS production
ENV NODE_ENV=production
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
COPY --from=build /app/public ./public
COPY --from=build /app/.next/standalone ./
COPY --from=build /app/.next/static ./.next/static
USER appuser
EXPOSE 3000
CMD ["node", "server.js"]
```

Rules for every Dockerfile in the project:
- Pin base image versions (node:20-alpine, never bare node:latest) — floating tags break reproducibility.
- Always run as a non-root user in the final stage.
- Always include a HEALTHCHECK instruction so docker ps and orchestrators can see container health directly.
- .dockerignore must exclude node_modules, .git, .env, and build artifacts, mirroring .gitignore closely.

6.3 Docker Compose
infra/docker/docker-compose.yml (base, shared across environments):
```yaml
version: "3.9"

services:
  frontend:
    build:
      context: ../../apps/frontend
      dockerfile: Dockerfile
    restart: unless-stopped
    depends_on:
      backend:
        condition: service_healthy
    networks:
      - app-network

  backend:
    build:
      context: ../../apps/backend
      dockerfile: Dockerfile
    restart: unless-stopped
    env_file:
      - .env
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "wget", "--spider", "-q", "http://localhost:4000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s
    networks:
      - app-network

  postgres:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - app-network

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: ["redis-server", "--appendonly", "yes"]
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - app-network

  worker:
    build:
      context: ../../apps/backend
      dockerfile: Dockerfile
    command: ["node", "dist/worker.js"]
    restart: unless-stopped
    env_file:
      - .env
    depends_on:
      redis:
        condition: service_healthy
      postgres:
        condition: service_healthy
    networks:
      - app-network

  nginx:
    image: nginx:1.27-alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/default.conf:/etc/nginx/conf.d/default.conf:ro
      - ./nginx/certs:/etc/nginx/certs:ro
    depends_on:
      - frontend
      - backend
    networks:
      - app-network

networks:
  app-network:
    driver: bridge

volumes:
  postgres-data:
  redis-data:
```

docker-compose.prod.yml (override, applied with -f docker-compose.yml -f docker-compose.prod.yml):
```yaml
version: "3.9"

services:
  backend:
    deploy:
      resources:
        limits:
          cpus: "1.0"
          memory: 512M
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
  
  frontend:
    deploy:
      resources:
        limits:
          cpus: "0.5"
          memory: 256M
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

  postgres:
    deploy:
      resources:
        limits:
          memory: 1G
```

6.4 Networks
All services communicate over a single user-defined bridge network (app-network), never the Docker default bridge. User-defined networks give containers DNS resolution by service name (backend can reach Postgres at postgres:5432, no IP addresses required) and isolate the stack from other unrelated containers on the host. Only nginx publishes ports to the host; every other service is reachable exclusively through the internal network — the database and backend are never directly exposed to the internet.

6.5 Volumes
Volume | Mounted by | Why it's persistent
--- | --- | ---
postgres-data | postgres | Database files must survive container restarts and rebuilds
redis-data | redis | AOF persistence file, survives restarts (optional if Redis is used purely as an ephemeral cache)
nginx/certs (bind mount) | nginx | TLS certificates, managed outside the container lifecycle

Named volumes (postgres-data, redis-data) are managed by Docker and persist across docker compose down (but not docker compose down -v, which is destructive and should never be run casually in production). Bind mounts (./nginx/...) are used for config that's edited on the host and needs to be visible to both.

6.6 Reverse Proxy
infra/docker/nginx/default.conf:
```nginx
upstream frontend_upstream {
    server frontend:3000;
}
upstream backend_upstream {
    server backend:4000;
}

server {
    listen 80;
    server_name example.com www.example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name example.com www.example.com;

    ssl_certificate /etc/nginx/certs/fullchain.pem;
    ssl_certificate_key /etc/nginx/certs/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    client_max_body_size 20M;

    gzip on;
    gzip_types text/plain application/json application/javascript text/css;

    location /api/ {
        proxy_pass http://backend_upstream/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        proxy_pass http://frontend_upstream;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
TLS certificates in a self-hosted setup are typically obtained via Certbot (Let's Encrypt) running as a sidecar container or a host cron job that renews certificates and reloads Nginx (nginx -s reload) on renewal — this avoids downtime from a full container restart.

6.7 Health Checks
Every service in the compose file above declares a healthcheck:. This matters for two reasons: depends_on: condition: service_healthy prevents the backend from starting before Postgres is actually ready to accept connections (not just "the container started," which is a common source of race-condition crashes on docker compose up), and docker ps surfaces per-container health status directly for quick debugging.

6.8 Persistent Storage
Beyond database and cache volumes, if the application accepts file uploads and is not using external object storage (Chapter 8), uploaded files must be written to a named volume, never the container's writable layer:
```yaml
  backend:
    volumes:
      - uploads-data:/app/uploads
```
Writing to the container's own filesystem without a volume means every file is lost the moment the container is recreated. In production, external object storage (R2/S3-compatible) is still strongly preferred over a local volume, because a local volume ties uploaded data to a single host and complicates any future move to multiple backend replicas.

6.9 Logging
Docker's default json-file logging driver is sufficient for small deployments, with max-size and max-file limits set (as shown in 6.3) to prevent unbounded disk growth from log files. For anything beyond a single-host deployment, ship container logs to a centralized destination (see Chapter 12) using a log shipper such as Vector, Fluent Bit, or the platform-native driver for your cloud provider, rather than relying on docker logs as the only access path.

7. Database Best Practices
7.1 Connection Pooling
Every production application connects to the database through a connection pool, never opening a fresh connection per request. Opening and tearing down a raw TCP + auth handshake per request is slow and exhausts the database's max-connections limit quickly under load — especially in serverless environments where each function invocation could otherwise open its own connection.

Environment | Pooling approach
--- | ---
Long-running backend (Docker/Render/Railway) | In-process pool via the ORM/driver (e.g., Prisma's built-in pool, pg.Pool), sized to roughly (core_count * 2) + effective_spindle_count as a starting heuristic, then tuned under load
Serverless functions (Vercel functions, Lambda) | An external pooler such as PgBouncer or the platform's built-in pooler (Neon's pooled connection string, Supabase's Supavisor) is mandatory — otherwise concurrent invocations can open hundreds of direct connections in seconds

Example pooled connection setup (Prisma):
```ts
// prisma/client.ts
import { PrismaClient } from "@prisma/client";

const globalForPrisma = global as unknown as { prisma: PrismaClient };

export const prisma =
  globalForPrisma.prisma ||
  new PrismaClient({
    log: process.env.NODE_ENV === "development" ? ["query", "warn", "error"] : ["error"],
  });

if (process.env.NODE_ENV !== "production") globalForPrisma.prisma = prisma;
```
The globalForPrisma pattern prevents hot-reload in development from spawning a new pool on every file save.

7.2 Migrations
Migrations are version-controlled, ordered, and applied identically across every environment. Never manually edit a production schema through a GUI or ad-hoc SQL — every schema change ships as a migration file, reviewed in the same pull request as the code that depends on it.

```bash
# Prisma example
npx prisma migrate dev --name add_user_email_index  # local: create + apply
npx prisma migrate deploy                           # staging/production: apply only, never generates new ones
```
migrate deploy (apply-only, no schema drift detection prompts) is the command that belongs in CI/CD — never migrate dev, which can prompt interactively or reset data.

7.3 Rollback
Every migration should have a clear rollback path before it ships:
- Additive changes (new column, new table, new index) are trivially safe and rarely need a real rollback beyond re-deploying the prior code version.
- Destructive changes (dropping a column, renaming a table) should be split into multiple deploys: (1) stop using the old column in code, deploy, (2) confirm stability, (3) drop the column in a follow-up migration. This is the "expand and contract" pattern — it avoids a single migration that can't be safely undone.
- Keep a tested restore-db.sh (7.5) as the rollback of last resort for anything a forward-fix can't address quickly.

7.4 Backup
```bash
#!/usr/bin/env bash
# infra/scripts/backup-db.sh
set -euo pipefail

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="backup_${TIMESTAMP}.sql.gz"

pg_dump "$DATABASE_URL" | gzip > "/backups/${BACKUP_FILE}"

# Upload to object storage for off-host durability
aws s3 cp "/backups/${BACKUP_FILE}" "s3://${BACKUP_BUCKET}/db-backups/${BACKUP_FILE}" \
  --endpoint-url "${S3_ENDPOINT}"

echo "Backup complete: ${BACKUP_FILE}"
```
- Run this on a schedule (cron on a self-hosted box, or a GitHub Actions scheduled workflow, or the managed platform's native automated backups).
- Test restores regularly. A backup that has never been restored is not a verified backup — it's an assumption.
- Retain backups on a tiered schedule: e.g., daily for 7 days, weekly for 4 weeks, monthly for 6 months — adjust to the project's actual recovery point objective (RPO).

7.5 Restore
```bash
#!/usr/bin/env bash
# infra/scripts/restore-db.sh
set -euo pipefail

BACKUP_FILE="$1"
if [ -z "$BACKUP_FILE" ]; then
  echo "Usage: ./restore-db.sh <backup_file.sql.gz>"
  exit 1
fi

echo "WARNING: this will overwrite the target database. Press Ctrl+C to abort."
sleep 5

gunzip -c "$BACKUP_FILE" | psql "$DATABASE_URL"

echo "Restore complete."
```
Restore scripts should always include a confirmation delay or explicit --yes flag requirement — a restore is a destructive, irreversible action against the target database.

7.6 Indexes
- Index every foreign key column and every column used in a WHERE, ORDER BY, or JOIN clause on a table expected to grow beyond a few thousand rows.
- Use EXPLAIN ANALYZE to confirm an index is actually being used before assuming it helps — an unused index still costs write performance and storage.
- Composite indexes should list columns in the order they're filtered/sorted, most selective first, matching actual query patterns.
- Avoid over-indexing: every index slows down INSERT/UPDATE/DELETE on that table, so index deliberately, not defensively.

7.7 Constraints
Push data integrity into the database schema wherever practical, rather than relying solely on application-level validation:
```sql
ALTER TABLE users ADD CONSTRAINT email_unique UNIQUE (email),
                  ADD CONSTRAINT email_not_empty CHECK (char_length(email) > 0);
ALTER TABLE orders ADD CONSTRAINT fk_orders_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
```
Application-level validation is still necessary for good UX (fast, specific error messages) — but the database constraint is the final backstop against bad data getting in through a bug, a race condition, or a direct script.

7.8 Seed Scripts
```ts
// prisma/seed.ts
async function main() {
  await prisma.user.upsert({
    where: { email: "admin@example.com" },
    update: {},
    create: {
      email: "admin@example.com",
      name: "Admin",
      role: "ADMIN",
    },
  });
}
main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
```
Seed scripts use upsert (or equivalent idempotent logic), never plain insert, so they're safe to re-run without creating duplicates. Seed scripts populate reference/lookup data and local dev fixtures — they never run automatically against production as part of a deploy.

8. Object Storage
8.1 Why not the local filesystem
Covered briefly in 6.8: in any environment where compute is ephemeral, horizontally scaled, or serverless, the local filesystem is not durable storage. Object storage (S3-compatible) is the default for any user-uploaded or generated file — images, PDFs, exports, avatars.

8.2 Cloudflare R2
R2 is S3-API-compatible with zero egress fees, which makes it the default recommendation for most projects over raw S3, particularly anything serving files directly to end users at any real volume.

```ts
// lib/storage.ts
import { S3Client, PutObjectCommand, GetObjectCommand } from "@aws-sdk/client-s3";
import { getSignedUrl } from "@aws-sdk/s3-request-presigner";

const s3 = new S3Client({
  region: "auto",
  endpoint: process.env.S3_ENDPOINT,
  credentials: {
    accessKeyId: process.env.S3_ACCESS_KEY_ID!,
    secretAccessKey: process.env.S3_SECRET_ACCESS_KEY!,
  },
});

export async function uploadFile(key: string, body: Buffer, contentType: string) {
  await s3.send(
    new PutObjectCommand({
      Bucket: process.env.S3_BUCKET_NAME,
      Key: key,
      Body: body,
      ContentType: contentType,
    })
  );
}

export async function getSignedDownloadUrl(key: string, expiresInSeconds = 3600) {
  const command = new GetObjectCommand({
    Bucket: process.env.S3_BUCKET_NAME,
    Key: key
  });
  return getSignedUrl(s3, command, { expiresIn: expiresInSeconds });
}
```

8.3 Supabase Storage
For projects already using Supabase for auth/database, Supabase Storage avoids introducing a second vendor and integrates with Supabase's row-level security policies to control access at the bucket/object level using the same auth already in place.
```ts
const { data, error } = await supabase.storage
  .from("avatars")
  .upload(`${userId}/profile.png`, file, { upsert: true });
```

8.4 Signed URLs
Files are never uploaded through the application server when avoidable, and are never served from a public bucket for anything containing user data. The standard pattern:
1. Client requests a signed upload URL from the backend (backend generates it, doesn't proxy the file bytes).
2. Client uploads directly to R2/S3/Supabase using that signed URL.
3. Backend stores only the resulting object key/reference in the database.
4. When the file needs to be read, the backend generates a short-lived signed download URL on request, rather than exposing a permanently public link.

This keeps large file transfers off the application server entirely (saving bandwidth and memory) and ensures access control is enforced at generation time, not baked into a permanent public URL.

8.5 Upload Security
- Validate file type by content (magic-byte sniffing), not just the client-supplied Content-Type header or file extension, which are trivially spoofable.
- Enforce a maximum file size both client-side (fast UX feedback) and server-side (actual security boundary) — never trust the client-side check alone.
- Generate the storage key server-side (e.g., a UUID), never trust a client-supplied filename or path directly, to prevent path traversal and overwrite attacks.
- Set signed URL expiry as short as the use case allows — minutes for one-time downloads, longer only when genuinely needed.
- Scan uploads for malware where the application accepts files from untrusted users at any meaningful scale (e.g., via ClamAV or a managed scanning API).

9. Redis
9.1 Caching
Redis sits in front of expensive, repeatable reads — not as a replacement for the database, but as a layer that absorbs read traffic for data that doesn't need to be fetched fresh on every request.

```ts
async function getUserProfile(userId: string) {
  const cacheKey = `user:profile:${userId}`;
  const cached = await redis.get(cacheKey);
  if (cached) return JSON.parse(cached);

  const profile = await prisma.user.findUnique({ where: { id: userId } });
  await redis.set(cacheKey, JSON.stringify(profile), "EX", 300); // 5 min TTL
  return profile;
}
```
Always set a TTL. An unbounded cache is a slow memory leak and a future source of stale-data bugs. Invalidate explicitly on writes to the same entity where staleness would be user-visible and unacceptable, rather than relying on TTL alone for data that changes often.

9.2 Rate Limiting
```ts
import { Ratelimit } from "@upstash/ratelimit";
import { Redis } from "@upstash/redis";

const ratelimit = new Ratelimit({
  redis: Redis.fromEnv(),
  limiter: Ratelimit.slidingWindow(100, "60 s"),
});

export async function rateLimitMiddleware(req, res, next) {
  const identifier = req.ip;
  const { success, limit, remaining } = await ratelimit.limit(identifier);
  
  res.setHeader("X-RateLimit-Limit", limit);
  res.setHeader("X-RateLimit-Remaining", remaining);
  
  if (!success) {
    return res.status(429).json({ error: "Too many requests" });
  }
  next();
}
```
A sliding-window algorithm backed by Redis is preferred over in-memory rate limiting because it works correctly across multiple backend replicas — in-memory counters are per-process and silently stop working the moment the app scales past one instance.

9.3 Sessions
For applications using server-side sessions (as opposed to stateless JWTs), Redis is the standard session store because it makes sessions available to every backend replica, unlike in-memory session stores which break horizontal scaling.

```ts
app.use(
  session({
    store: new RedisStore({ client: redisClient }),
    secret: process.env.SESSION_SECRET,
    resave: false,
    saveUninitialized: false,
    cookie: { secure: true, httpOnly: true, sameSite: "lax", maxAge: 86400000 },
  })
);
```

9.4 Queues
Redis-backed queues (via BullMQ or similar) decouple slow or unreliable work — sending email, generating a PDF, calling a third-party API — from the request/response cycle, so a user isn't left waiting on something that could fail or take seconds.

```ts
import { Queue } from "bullmq";
export const emailQueue = new Queue("email", { connection: redisConnection });

// Enqueue from a request handler — returns immediately
await emailQueue.add("welcome-email", { userId: user.id });
```
See Chapter 10 for the worker side of this pattern.

10. Background Workers
10.1 Why workers exist
Anything that is slow, unreliable (depends on a third-party API), or not needed synchronously for the response the user is waiting on belongs in a background job, processed by a separate worker process — not inline in the request handler.

```ts
// worker.ts
import { Worker } from "bullmq";

const emailWorker = new Worker(
  "email",
  async (job) => {
    if (job.name === "welcome-email") {
      await sendEmail(job.data.userId);
    }
  },
  { connection: redisConnection, concurrency: 5 }
);
```
The worker runs as its own container/process/service (see the worker service in the Compose file, 6.3, or a separate Render "Background Worker" service type) — sharing code with the backend, but deployed and scaled independently of it.

10.2 Retry Logic
```ts
await emailQueue.add(
  "welcome-email",
  { userId: user.id },
  { 
    attempts: 5, 
    backoff: { type: "exponential", delay: 2000 },
  }
);
```
Exponential backoff prevents a struggling downstream service (e.g., a flaky email provider) from being hammered with immediate retries, which tends to make outages worse, not better. Not every failure should be retried identically — a 400 Bad Request from a third-party API indicates a permanent problem with the job's data and should not retry the same way a 503 Service Unavailable should.

10.3 Dead Letter Queue
Jobs that exhaust their retry attempts move to a dead letter queue (DLQ) rather than vanishing silently:

```ts
emailWorker.on("failed", async (job, err) => {
  if (job.attemptsMade >= job.opts.attempts) {
    await deadLetterQueue.add("failed-email", { originalJob: job.data, error: err.message });
    logger.error({ jobId: job.id, err }, "Job moved to dead letter queue");
  }
});
```
The DLQ is monitored (alerting, or a periodic manual review) so permanently failing jobs are visible and actionable, rather than silently dropped — a failure mode that's easy to miss until a user notices a welcome email that never arrived.

10.4 Idempotency
Any job (or API endpoint) that could plausibly be retried, redelivered, or double-submitted must be safe to run more than once with the same input and produce the same end state — this is idempotency, and it is a hard requirement for anything using at-least-once delivery queues.

```ts
async function processPayment(job) {
  const { paymentIntentId } = job.data;
  const existing = await prisma.payment.findUnique({ where: { paymentIntentId } });
  if (existing?.status === "completed") {
    return; // already processed, safe no-op
  }
  // ... process payment, then record it keyed by paymentIntentId
}
```
The general pattern: derive a deterministic idempotency key from the operation (a payment intent ID, a webhook event ID, a combination of user + action + timestamp bucket), check for prior completion before doing the work, and record completion atomically with the side effect where possible.

11. Security
11.1 Helmet
Helmet sets a battery of security-related HTTP headers with sane defaults, closing off a long list of well-known low-effort attack vectors in one line:
```ts
import helmet from "helmet";
app.use(helmet());
```
This alone sets X-Content-Type-Options, X-Frame-Options, Strict-Transport-Security, and several others. It should be one of the first middleware registered, before routes.

11.2 CSP (Content Security Policy)
A default-deny CSP restricts which origins scripts, styles, images, and connections can load from, which is the strongest available mitigation against XSS actually executing even if an injection point exists:
```ts
app.use(
  helmet.contentSecurityPolicy({
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      imgSrc: ["'self'", "data:", "https://*.r2.dev"],
      connectSrc: ["'self'", process.env.API_URL],
      frameAncestors: ["'none'"],
    },
  })
);
```
Roll this out in Content-Security-Policy-Report-Only mode first against real production traffic, review violation reports, then switch to enforcing mode — a CSP that's too strict silently breaks legitimate functionality (a font that fails to load, an embedded widget that stops rendering) if deployed directly to enforcing mode without validation.

11.3 HSTS
```ts
app.use(
  helmet.hsts({
    maxAge: 63072000, // 2 years
    includeSubDomains: true,
    preload: true,
  })
);
```
HSTS instructs browsers to never attempt an http:// connection to this domain again, closing the window for an SSL-stripping downgrade attack on the first request. Only enable preload once genuinely confident every subdomain supports HTTPS — submission to the HSTS preload list is difficult to reverse.

11.4 JWT
```ts
import jwt from "jsonwebtoken";

function signAccessToken(userId: string) {
  return jwt.sign({ sub: userId }, process.env.JWT_SECRET, {
    expiresIn: "15m",
    algorithm: "HS256",
  });
}

function verifyAccessToken(token: string) {
  return jwt.verify(token, process.env.JWT_SECRET, { algorithms: ["HS256"] });
}
```
- Explicitly whitelist the algorithm on verify (algorithms: ["HS256"]) — failing to do so is a known class of vulnerability where an attacker forges a token using the none algorithm or switches to an asymmetric algorithm the server doesn't expect.
- Keep access tokens short-lived (minutes, not days) and pair with a longer-lived refresh token that's stored more defensively (httpOnly cookie, rotated on use).
- Never store sensitive data in the JWT payload — it's signed, not encrypted, and is trivially decodable by anyone holding the token.

11.5 OAuth
- Always use the Authorization Code flow with PKCE, even for confidential clients — it is the current best practice across the OAuth 2.1 draft and effectively supersedes the older implicit flow, which should not be used for new projects.
- Validate the state parameter on callback to prevent CSRF against the OAuth flow itself.
- Request the minimum necessary scopes — broad scope requests both increase blast radius on token compromise and reduce user trust at the consent screen.

11.6 Cookies
```ts
res.cookie("refreshToken", token, {
  httpOnly: true,
  secure: true,
  sameSite: "strict",
  maxAge: 7 * 24 * 60 * 60 * 1000,
  path: "/api/auth/refresh",
});
```

Flag | Purpose
--- | ---
httpOnly | Inaccessible to JavaScript, mitigates token theft via XSS
secure | Only sent over HTTPS
sameSite: strict (or lax if cross-site flows require it) | Mitigates CSRF
Scoped path | Limits the cookie to routes that actually need it

11.7 CORS
```ts
import cors from "cors";

app.use(
  cors({
    origin: process.env.ALLOWED_ORIGINS?.split(",") ?? [],
    credentials: true,
    methods: ["GET", "POST", "PUT", "PATCH", "DELETE"],
  })
);
```
origin: "*" is never used on any endpoint that accepts credentials or handles authenticated requests. The allowed-origins list is explicit and environment-driven, so staging and production don't accidentally share trust.

11.8 Rate Limiting
See Chapter 9.2 for the Redis-backed implementation. At minimum, apply stricter limits to authentication endpoints (/login, /register, /forgot-password) than to general API traffic, since these are the endpoints most valuable to brute-force or credential-stuffing attacks.

11.9 CSRF
For any cookie-based session authentication (not needed for pure Bearer-token/JWT-in-header APIs, which are inherently not vulnerable to classic CSRF), issue and validate a CSRF token on state-changing requests:
```ts
import csrf from "csurf";
app.use(csrf({ cookie: { httpOnly: true, sameSite: "strict" } }));

app.use((req, res, next) => {
  res.locals.csrfToken = req.csrfToken();
  next();
});
```
Combined with sameSite: strict cookies (11.6), this provides layered defense — sameSite alone is often sufficient against modern browsers but shouldn't be the only control for a sensitive application.

11.10 XSS
- Never render unsanitized user input as raw HTML. Frameworks like React/Vue escape output by default — the danger is specifically in bypasses like dangerouslySetInnerHTML or v-html, which must go through a sanitizer (e.g., DOMPurify) if user content is ever involved.
- The CSP in 11.2 is the second line of defense, limiting what an injected script could even do if one slipped through.
- Sanitize on output, not just on input — input sanitization alone is fragile because the same data might be rendered in multiple contexts (HTML, attribute, URL, JS string) each with different escaping needs.

11.11 SQL Injection
Use parameterized queries / an ORM's query builder exclusively. Never string-concatenate user input into raw SQL.
```ts
// Safe (parameterized, via ORM)
await prisma.user.findMany({ where: { email: userInput } });

// Safe (parameterized, raw query)
await prisma.$queryRaw`SELECT * FROM users WHERE email = ${userInput}`;

// NEVER do this
await prisma.$queryRawUnsafe(`SELECT * FROM users WHERE email = '${userInput}'`);
```
If a raw query is genuinely unavoidable, it must use the driver's parameter binding ($1, ?, or tagged templates that auto-escape), never manual string interpolation of user input.

11.12 Secrets
- Secrets live in environment variables sourced from a platform secret manager (Chapter 4.6), never committed to git — including in commit history, which means a leaked secret must be rotated, not just deleted in a follow-up commit.
- Add a pre-commit or CI secret-scanning step (e.g., gitleaks, truffleHog) to catch accidental commits before they reach a shared branch.
- Different secrets per environment (dev/staging/production) — a compromised staging key should never grant access to production data.

12. Logging
12.1 Structured Logs
Every production log line is emitted as structured data, not a free-text string — this is what makes logs searchable, filterable, and aggregable at scale instead of being grep-fodder.

```ts
import pino from "pino";

export const logger = pino({
  level: process.env.LOG_LEVEL || "info",
  formatters: {
    level: (label) => ({ level: label }),
  },
  timestamp: pino.stdTimeFunctions.isoTime,
});

logger.info({ userId, orderId, amount }, "Order created");
```
Never console.log in production code paths — it produces unstructured output that's difficult to query and typically bypasses log-level filtering entirely.

12.2 JSON
```json
{
  "level": "info",
  "time": "2026-08-01T09:15:32.104Z",
  "requestId": "3f9d2b1e-...",
  "userId": "usr_8213",
  "orderId": "ord_4471",
  "amount": 4200,
  "msg": "Order created"
}
```
JSON-formatted logs are the universal input format for essentially every log aggregation platform (Datadog, Grafana Loki, CloudWatch Logs Insights, Better Stack), which is why structured loggers default to it in production mode while often pretty-printing to the console in development for human readability.

12.3 Correlation IDs
A correlation ID (or trace ID) is generated once per incoming request and threaded through every log line, every downstream service call, and every queued job that originates from that request — so a single ID can be used to reconstruct the full path of one user action across a distributed system.

```ts
import { randomUUID } from "crypto";

app.use((req, res, next) => {
  req.correlationId = req.headers["x-correlation-id"] || randomUUID();
  res.setHeader("x-correlation-id", req.correlationId);
  next();
});
```
When enqueuing a background job from within a request, the correlation ID is passed along as part of the job payload so the worker's logs can be tied back to the originating request.

12.4 Request IDs
Distinct from a correlation ID (which can span multiple services), a request ID identifies one specific HTTP request/response cycle and is logged at minimum on entry (method, path, IP) and exit (status code, duration):

```ts
app.use((req, res, next) => {
  const start = Date.now();
  res.on("finish", () => {
    logger.info(
      {
        requestId: req.correlationId,
        method: req.method,
        path: req.path,
        status: res.statusCode,
        durationMs: Date.now() - start,
      },
      "Request completed"
    );
  });
  next();
});
```
This single middleware, applied globally, gives a complete access log with timing for every endpoint without instrumenting each route individually.

13. Monitoring
13.1 Sentry
Sentry (or an equivalent error-tracking platform) captures unhandled exceptions with full stack traces, request context, and user context, and groups recurring errors so a spike is visible immediately rather than discovered from a user complaint.

```ts
import * as Sentry from "@sentry/node";

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  environment: process.env.NODE_ENV,
  tracesSampleRate: process.env.NODE_ENV === "production" ? 0.1 : 1.0,
});

app.use(Sentry.Handlers.requestHandler());
// ... routes ...
app.use(Sentry.Handlers.errorHandler());
```
Set tracesSampleRate well below 1.0 in production for any meaningfully trafficked application — full tracing on every request is expensive and rarely necessary once the system is understood.

13.2 Health / Readiness / Liveness
These three checks answer different questions and should not be conflated into one endpoint:

Check | Question it answers | Failure response
--- | --- | ---
Liveness (/health) | "Is the process alive and not deadlocked?" | Orchestrator restarts the container
Readiness (/ready) | "Can this instance currently serve traffic?" | Orchestrator stops routing traffic to it, but does not restart it
Health (general/legacy) | Often used as a catch-all synonym for liveness in simpler setups | —

```ts
app.get("/health", (req, res) => {
  res.status(200).json({ status: "ok" });
});

app.get("/ready", async (req, res) => {
  try {
    await prisma.$queryRaw`SELECT 1`;
    await redis.ping();
    res.status(200).json({ status: "ready" });
  } catch (err) {
    res.status(503).json({ status: "not ready", error: err.message });
  }
});
```
The distinction matters operationally: if the database is briefly unreachable, the correct response is "stop sending this instance traffic" (readiness failure), not "kill and restart the process" (liveness failure) — restarting doesn't fix a database outage and just adds churn.

13.3 Metrics
Expose application-level metrics (request counts, latency histograms, queue depth, error rates) in a format a metrics platform can scrape, typically Prometheus-compatible:

```ts
import client from "prom-client";

const httpRequestDuration = new client.Histogram({
  name: "http_request_duration_seconds",
  help: "Duration of HTTP requests in seconds",
  labelNames: ["method", "route", "status_code"],
});

app.get("/metrics", async (req, res) => {
  res.set("Content-Type", client.register.contentType);
  res.end(await client.register.metrics());
});
```
At minimum, track: request rate, error rate, p50/p95/p99 latency, and (if applicable) queue depth and worker throughput. These four are enough to build a meaningful dashboard and set sane alert thresholds without over-instrumenting on day one.

14. Performance
14.1 Compression
```ts
import compression from "compression";
app.use(compression());
```
Gzip/Brotli compression on text-based responses (JSON, HTML, CSS, JS) typically cuts payload size by 60–80% for minimal CPU cost, and is one of the highest-leverage, lowest-effort performance wins available.

14.2 Image Optimization
- Serve images in modern formats (WebP/AVIF) with fallback, at the resolution actually needed for the display context — never a full-resolution source image scaled down purely in CSS.
- Next.js's built-in <Image> component (or an equivalent for other frameworks) handles resizing, format negotiation, and lazy loading automatically.
- Store only the original in object storage; generate resized/format-converted variants on demand or at upload time via a transform pipeline (Cloudflare Images, Supabase Image Transformations, or a custom Sharp-based worker job).

14.3 Code Splitting
- Route-based code splitting (automatic in Next.js, configurable via React.lazy + dynamic import() elsewhere) ensures users download only the JavaScript needed for the page they're on, not the entire application bundle upfront.
- Dynamically import heavy, rarely-used components (rich text editors, charting libraries, PDF viewers) rather than including them in the main bundle.

14.4 Caching
Layered caching, from closest to the user to furthest:

Layer | Example | TTL guidance
--- | --- | ---
Browser cache | Cache-Control headers on static assets | Long (1 year) for hashed/fingerprinted filenames
CDN edge cache | Vercel Edge Network, Cloudflare | Minutes to hours for semi-dynamic content
Application cache | Redis (Chapter 9.1) | Seconds to minutes for per-entity data
Database query cache | ORM-level or materialized views | Depends on data volatility

```ts
res.setHeader("Cache-Control", "public, max-age=31536000, immutable"); // fingerprinted static asset
res.setHeader("Cache-Control", "private, max-age=60"); // per-user, short-lived
```

14.5 Lazy Loading
```jsx
const RichTextEditor = React.lazy(() => import("./RichTextEditor"));

<Suspense fallback={<Spinner />}>
  <RichTextEditor />
</Suspense>
```
Applies to below-the-fold images (loading="lazy" natively in HTML), non-critical third-party scripts (loaded after first paint), and any component not needed for initial render.

14.6 Bundle Analysis
```bash
# Next.js
ANALYZE=true npm run build

# Vite
npx vite-bundle-visualizer
```
Run a bundle analyzer before every major release, or wire it into CI as an informational (non-blocking) step that flags a significant size regression. It's far cheaper to catch a 400KB dependency accidentally included in the client bundle in review than after users start complaining about load time.

15. CI/CD
15.1 GitHub Actions — CI pipeline
.github/workflows/ci.yml:
```yaml
name: CI
on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  lint-and-typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: "npm"
      - run: npm ci
      - run: npm run lint
      - run: npm run typecheck

  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_db
        ports: ["5432:5432"]
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: "npm"
      - run: npm ci
      - run: npx prisma migrate deploy
        env:
          DATABASE_URL: postgresql://postgres:test@localhost:5432/test_db
      - run: npm run test
        env:
          DATABASE_URL: postgresql://postgres:test@localhost:5432/test_db

  build:
    runs-on: ubuntu-latest
    needs: [lint-and-typecheck, test]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: "npm"
      - run: npm ci
      - run: npm run build

  secret-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: gitleaks/gitleaks-action@v2
```

15.2 Deployment Pipeline
.github/workflows/deploy-backend.yml:
```yaml
name: Deploy Backend
on:
  push:
    branches: [main]
    paths:
      - "apps/backend/**"

jobs:
  deploy:
    runs-on: ubuntu-latest
    needs: []
    steps:
      - uses: actions/checkout@v4
      - name: Run CI checks
        uses: ./.github/workflows/ci.yml
      - name: Deploy to Render
        run: |
          curl -X POST "${{ secrets.RENDER_DEPLOY_HOOK_URL }}"
      - name: Wait for health check
        run: |
          for i in {1..30}; do
            STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://api.example.com/health)
            if [ "$STATUS" = "200" ]; then
              echo "Service healthy"
              exit 0
            fi
            sleep 10
          done
          echo "Health check failed after deploy"
          exit 1
```
Deployment only proceeds after CI checks pass, and the workflow verifies the health endpoint post-deploy before considering the deployment successful — a deploy that "succeeds" but leaves an unhealthy service running is effectively a silent outage.

15.3 Rollback
Automated rollback-on-failure, for platforms that keep prior deployments addressable:
```yaml
      - name: Rollback on failed health check
        if: failure()
        run: |
          curl -X POST "${{ secrets.RENDER_ROLLBACK_HOOK_URL }}"
```
For Docker-based self-hosted deploys, rollback means redeploying the previous known-good image tag:
```bash
docker compose pull backend:previous-stable
docker compose up -d backend
```
This is why images should always be tagged with a commit SHA or version number in addition to latest — latest alone gives nothing to roll back to.

15.4 Testing, Lint, Type Checking, Build Validation
All four gate every merge to main and every deploy, in this order (fastest/cheapest first, so failures are caught early without wasting CI minutes on slower steps):
1. Lint — catches style and common-bug patterns in seconds.
2. Type check — catches an entire class of runtime errors before execution.
3. Test — unit and integration tests against a real (ephemeral) database, as shown in 15.1.
4. Build — confirms the production build actually compiles; a project can pass lint/typecheck/test and still fail to build due to environment-specific issues.

None of these are optional for "small" projects — the cost of running them is seconds to minutes; the cost of skipping them is a production incident discovered by a user.

16. README Template
Every project ships a root README.md following this structure. It is deployment/operations-facing first, marketing-facing second — a new engineer (or an AI assistant picking up the project cold) should be able to get a local environment running and understand the deployment model within five minutes of reading it.

```markdown
# Project Name
One-paragraph description of what this application does.

## Tech Stack
- Frontend: [framework]
- Backend: [framework/runtime]
- Database: [PostgreSQL / etc., ORM used]
- Cache/Queue: Redis
- Storage: Cloudflare R2
- Deployment: Vercel (frontend) + Render (backend) | Docker Compose (self-hosted)

## Local Development
### Prerequisites
- Node.js 20+
- Docker (for local Postgres/Redis)

### Setup
\`\`\`bash
git clone <repo-url>
cd project-name
cp .env.example .env
# fill in local values
docker compose up -d postgres redis
npm install
npx prisma migrate dev
npm run dev
\`\`\`

## Environment Variables
See `.env.example` for the full list.
Required for local development: `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`.

## Deployment
### Cloud Native
See `docs/DEPLOYMENT.md` § Cloud Native.

### Docker Compose (self-hosted)
\`\`\`bash
cp infra/docker/.env.example infra/docker/.env
# fill in production values
docker compose -f infra/docker/docker-compose.yml -f infra/docker/docker-compose.prod.yml up -d
\`\`\`

## Scripts
| Command | Purpose |
|---|---|
| `npm run dev` | Start local dev server |
| `npm run build` | Production build |
| `npm run test` | Run test suite |
| `npx prisma migrate dev` | Create + apply a migration locally |
| `./infra/scripts/backup-db.sh` | Backup production database |

## Architecture
See `docs/ARCHITECTURE.md`.

## Troubleshooting
See `docs/TROUBLESHOOTING.md` or Chapter 21 of the deployment playbook.

## License
[License name]
```

17. Deployment Architecture Diagrams
17.1 Cloud Native — Full Request Flow
```text
      ┌────────────────────┐
      │        User        │
      └──────────┬───────────┘
                 │ HTTPS
                 ▼
 ┌──────────────────────────────┐
 │     Vercel Edge Network      │
 │(Frontend, CDN, static assets)│
 └──────────────┬───────────────┘
                │ API calls (fetch)
                ▼
 ┌──────────────────────────────┐
 │       Render / Railway       │
 │    (Backend API service)     │
 └───────┬───────────┬───────────┘
         │           │
   ┌──────────┘    └──────────┐
   ▼                          ▼
 ┌─────────────────────┐  ┌─────────────────────┐
 │   Neon / Supabase   │  │    Cloudflare R2    │
 │ (Postgres, pooled)  │  │   (Object Storage)  │
 └─────────────────────┘  └─────────────────────┘
         │
         ▼
 ┌─────────────────────┐
 │    Managed Redis    │
 │   (Upstash, etc.)   │
 └─────────────────────┘
```

17.2 Docker — Full Request Flow
```text
      ┌────────────────────┐
      │        User        │
      └──────────┬───────────┘
                 │ HTTPS (443)
                 ▼
 ┌──────────────────────────────┐
 │    Nginx (reverse proxy,     │
 │    TLS termination, gzip)    │
 └──────┬───────────────┬────────┘
        │               │ /api/
      / ──────┘       └──────
        ▼               ▼
 ┌───────────────────┐ ┌───────────────────┐
 │ Frontend Container│ │ Backend Container │
 └───────────────────┘ └─────────┬─────────┘
                                 │
     ┌──────────────────────────┼──────────────────────────┐
     ▼                          ▼                          ▼
 ┌───────────────────┐  ┌───────────────────┐      ┌───────────────────┐
 │ Postgres Container│  │  Redis Container  │      │ Worker Container  │
 │(postgres-data vol)│  │ (redis-data vol)  │      │(shares backend code)│
 └───────────────────┘  └───────────────────┘      └───────────────────┘
 All containers on a single user-defined bridge network ("app-network").
 Only Nginx publishes ports to the host.
```

17.3 CI/CD Pipeline Flow
```text
git push ──▶ GitHub Actions triggered
                    │
       ┌────────────┼────────────┐
       ▼            ▼            ▼
     Lint       Type Check      Test
       │            │            │
       └────────────┼────────────┘
                    ▼
                  Build
                    │
                    ▼
               Secret Scan
                    │
                    ▼
            All checks passed? ──No──▶ Block merge / deploy
                    │ Yes
                    ▼
            Deploy to platform
                    │
                    ▼
         Post-deploy health check
                    │
          ┌──────────┴──────────┐
          ▼                     ▼
       Healthy              Unhealthy
          │                     │
          ▼                     ▼
 Deployment complete     Automatic rollback
```

18. Interview Talking Points
This chapter exists to help you explain the decisions embedded in this playbook, not just implement them — useful when a project built from this playbook comes up in a technical interview or design review. Each entry is deliberately terse; expand on whichever ones map to your actual project.

18.1 Why this architecture over another
The core answer for almost every choice in this document: each decision optimizes for the fewest moving parts an early-stage team has to operate, without foreclosing the option to scale later. Managed services (Neon, Render, Vercel) are chosen over self-managed infrastructure specifically because operational burden has a real cost — every self-hosted piece of infrastructure is something that pages you at 2 a.m. The Docker path exists in parallel precisely so that "no vendor lock-in" is still available when control matters more than convenience.

18.2 Tradeoffs
Every choice in this playbook has a corresponding cost, and being able to name it is the difference between "I copied a template" and "I understand what I built":
- Managed Postgres vs. self-hosted: less control over tuning and version upgrades, in exchange for automated backups, failover, and no OS-patching burden.
- Cloud-native vs. Docker: cloud-native is faster to ship and requires less ops knowledge, but costs scale with usage and some platform lock-in is unavoidable; Docker is more portable and often cheaper at scale, but the team now owns patching, orchestration, and uptime.
- JWT vs. server-side sessions: JWTs scale statelessly across replicas with no shared session store, but can't be invalidated before expiry without extra infrastructure (a revocation list); sessions can be revoked instantly but require a shared store (Redis) to scale horizontally.
- Synchronous vs. queued background work: queuing adds infrastructure (Redis, a worker process) and eventual-consistency complexity, but keeps request latency low and makes slow/unreliable operations retryable independent of the user's request.

18.3 Scaling
Explain scaling as a sequence of bottlenecks removed in order, not a single leap: first the application tier is scaled horizontally (more backend replicas behind a load balancer, trivial once the app is stateless per Chapter 2.3), then the database read path is scaled (read replicas, then connection pooling tuning, then caching via Redis to absorb repeat reads), then the database write path (usually the last and hardest bottleneck — sharding, or moving hot tables to a purpose-built store), and background work is scaled independently by adding worker replicas since queues decouple that tier already.

18.4 Docker networking
Explain that containers on a user-defined bridge network get automatic DNS resolution by service name — the backend reaches Postgres at the hostname postgres, not an IP address, because Docker runs an embedded DNS server for the network. This is also why only necessary ports are published to the host: everything else communicates over the internal network, invisible from outside the host entirely, which is a real security boundary, not just tidiness.

18.5 Managed databases
Explain what "managed" actually buys: automated backups and point-in-time recovery, automatic minor-version patching, failover handling, and often connection pooling built in (Neon, Supabase). The tradeoff is reduced access to low-level tuning (custom postgresql.conf settings are often restricted) and a recurring cost that scales with usage rather than a fixed server bill.

18.6 Environment variables
Explain the twelve-factor rationale directly: identical build artifacts should run unmodified across dev/staging/production, differing only in configuration injected at runtime — this is what makes "works on my machine" a solvable problem rather than a permanent hazard, and what makes CI able to test the exact artifact that later gets deployed.

18.7 CI/CD
Explain the pipeline as a series of increasingly expensive gates, each one filtering out a class of problem before it reaches the next, more costly stage — lint and type errors caught in seconds locally or in CI, logic errors caught by tests before merge, and integration/runtime errors caught by a post-deploy health check before real traffic is fully cut over.

18.8 Reverse proxy
Explain why Nginx sits in front of the application in the Docker architecture: it centralizes TLS termination (one place to manage certificates, not one per service), enables running multiple services behind one public IP/port 443 via path- or host-based routing, and provides a layer for response caching, gzip, and basic rate limiting without adding that logic to every backend service individually.

18.9 HTTPS
Explain the mechanics briefly: TLS certificates are issued by a certificate authority (Let's Encrypt, free and automated) and proven valid via a domain-ownership challenge (HTTP-01 or DNS-01), then presented by the server during the TLS handshake so the client can verify it's talking to the real server and encrypt the connection — and why HSTS (11.3) closes the remaining gap of a user's very first request potentially going out over plain HTTP before the redirect happens.

18.10 Health checks
Explain the liveness/readiness distinction from 13.2 concretely with an example: a backend instance whose database connection just dropped is still "alive" (the process hasn't crashed) but not "ready" (it can't serve most requests correctly) — conflating the two into one check either causes unnecessary restarts (killing a process that would recover once the DB reconnects) or, worse, keeps routing traffic to an instance that can't actually serve it.

18.11 Monitoring
Explain the difference between error tracking (Sentry — "what broke, and for whom") and metrics (Prometheus-style — "what's the aggregate system behavior over time") as complementary, not redundant: error tracking answers "what happened," metrics answer "is this getting better or worse," and a mature setup uses metrics to detect a problem exists and error tracking to diagnose exactly what it is.

18.12 Migrations
Explain migrations as the single source of truth for schema history, and the reason migrate deploy (apply-only) is used in CI/production rather than migrate dev (which can create new migrations interactively): production should never generate schema changes on its own — every schema change is authored, reviewed, and tested in advance, then applied deterministically.

18.13 Redis
Explain Redis's role across four distinct use cases in this playbook — cache, rate limiter, session store, and queue backend — and why one piece of infrastructure can serve all four: Redis is fast, in-memory, and supports the data structures (sorted sets for rate limiting, simple key-value with TTL for caching/sessions, lists/streams for queues) each pattern needs, without requiring four separate systems.

18.14 Object storage
Explain why files never touch the application server directly in the recommended pattern (8.4): a signed URL lets the client upload straight to R2/S3, which means large file transfers don't consume application server memory or bandwidth, and the backend's only job is authorization (deciding whether this user is allowed to get a signed URL) rather than being a data pipe.

18.15 Persistent volumes
Explain the core distinction: a container's own filesystem is ephemeral and destroyed on recreation, while a Docker volume is a separate, durable storage unit that outlives the container's lifecycle and can be reattached to a replacement container — this is what makes it safe to redeploy a database container (rebuild the image, e.g., for a version bump) without losing the actual data.

19. Production Checklist
Use this as the final gate before calling a deployment "production ready." Every item should be checked against the actual running system, not just the code.

Environment & Configuration
[ ] All secrets are in environment variables, none committed to git (verified via gitleaks or equivalent)
[ ] .env.example is complete and up to date with every variable the app needs
[ ] Environment variables are validated at process startup (Chapter 4.5)
[ ] Distinct secrets exist per environment (dev/staging/production)
[ ] NODE_ENV=production is correctly set in the production environment

Database
[ ] Connection pooling is configured (in-process pool or external pooler for serverless)
[ ] All migrations applied via migrate deploy, matching what's in version control
[ ] Automated daily backups are running and verified
[ ] A restore has actually been tested at least once, not just assumed to work
[ ] Indexes exist on foreign keys and frequently-queried columns
[ ] Constraints (unique, foreign key, check) are enforced at the schema level

Storage
[ ] Uploaded files go to object storage, not local disk (or a persistent volume if genuinely self-hosted only)
[ ] Signed URLs are used for upload/download, not permanently public links, for anything user-specific
[ ] File type is validated server-side by content, not just extension/header
[ ] Max file size is enforced server-side

Security
[ ] Helmet (or equivalent security headers) is applied
[ ] CSP is configured and tested in report-only mode before enforcing
[ ] HSTS is enabled
[ ] JWT verification explicitly whitelists the signing algorithm
[ ] Cookies use httpOnly, secure, and an appropriate sameSite setting
[ ] CORS origin list is explicit, never * on credentialed endpoints
[ ] Rate limiting is applied, with stricter limits on auth endpoints
[ ] CSRF protection is in place for any cookie-based session auth
[ ] All database queries are parameterized; no raw string interpolation of user input
[ ] Dependency vulnerability scan has been run (npm audit, Dependabot, or Snyk)

Logging & Monitoring
[ ] Logs are structured JSON, not free-text console.log
[ ] Correlation/request IDs are threaded through logs
[ ] Error tracking (Sentry or equivalent) is wired up and tested with a deliberate test error
[ ] /health (liveness) and /ready (readiness) endpoints exist and are correctly distinguished
[ ] Basic metrics (request rate, error rate, latency percentiles) are exposed or collected

Performance
[ ] Response compression is enabled
[ ] Static assets are served with long-lived, immutable cache headers
[ ] Images are optimized and served in modern formats
[ ] Bundle size has been checked with an analyzer, no unexpectedly large dependencies

CI/CD
[ ] Lint, type check, test, and build all run and block merge on failure
[ ] Secret scanning runs in CI
[ ] Deployment includes a post-deploy health check before being considered successful
[ ] A rollback path exists and has been documented (and ideally tested)

Documentation
[ ] README follows the template in Chapter 16 and is current
[ ] docs/ARCHITECTURE.md reflects the actual deployed architecture
[ ] docs/DEPLOYMENT.md has step-by-step instructions a new team member could follow cold

Final Sign-off
[ ] The application has been smoke-tested end-to-end against the actual production URL, not just localhost
[ ] DNS resolves correctly and HTTPS is enforced (no mixed content, http:// redirects to https://)
[ ] Someone other than the original deployer has reviewed this checklist

20. Common Deployment Mistakes
Mistake | Why it happens | How to avoid it
--- | --- | ---
Hardcoding localhost URLs | Copy-pasted from local dev without thinking about environments | Every URL/host/port comes from an environment variable, validated at startup (Ch. 4)
Committing .env | Forgetting to gitignore it before the first commit | Add .env to .gitignore in the very first commit of the project, before any secrets exist
No connection pooling in serverless | Works fine locally with one connection, breaks under concurrent invocations | Always use a pooler (PgBouncer, Neon pooled connection string) for serverless (Ch. 7.1)
Treating container filesystem as persistent | Local dev never restarts the container, so the bug doesn't surface until production | Always use named volumes or external object storage for anything that must survive a restart (Ch. 6.8, 8.1)
Running docker compose down -v casually | Muscle memory from cleaning up dev environments | Never use -v against a production compose stack; document this explicitly for the team
No health check distinction (liveness vs. readiness) | Simpler to write one /health endpoint | Implement both; understand what each failure mode should trigger (Ch. 13.2)
CORS: origin: "*" left in from local dev | Convenient during initial development, forgotten before shipping | Explicit origin allowlist from an environment variable, checked in CI or code review
Skipping migration rollback planning | Migrations "just work" until one doesn't | Use the expand-and-contract pattern for destructive changes (Ch. 7.3)
No retry/idempotency on background jobs | Works fine in testing where nothing actually fails or retries | Design every job to be safely re-runnable from the start (Ch. 10.2, 10.4)
Logging secrets accidentally | A debug console.log(req.body) or console.log(process.env) left in | Structured logger with explicit field allowlisting; never log entire request/env objects
Deploying without a post-deploy health check | Deployment "succeeds" (build completed) even if the app crashes on boot | Gate deployment success on an actual health check response, not just build completion (Ch. 15.2)
No rate limiting on auth endpoints | Rate limiting added generically, auth endpoints treated the same as everything else | Apply stricter, dedicated limits to login/register/password-reset (Ch. 11.8)
Ignoring bundle size until it's a problem | No visibility into what's shipped to the client | Run a bundle analyzer regularly, not just when performance complaints arrive (Ch. 14.6)
Single point of failure on the reverse proxy | Nginx runs as one container with no redundancy plan | Acceptable for early-stage projects; document it as a known limitation and plan for it in Ch. 22's later stages
Redesigning the app "while deploying" | Deployment work exposes visible rough edges in the UI, tempting to "just fix it" | Follow the Critical Preservation Rules (Ch. 1.5) — flag it, don't silently fix it

21. Troubleshooting Guide
21.1 "It works locally but not in production"
- Diff environment variables between local and production — this is the cause more often than not.
- Check NODE_ENV is actually set to production in the deployed environment.
- Confirm the production build (npm run build then run the built output) works locally — some bugs only appear in the optimized/minified build, not npm run dev.
- Check for case-sensitivity issues in imports — most local dev filesystems (macOS, Windows) are case-insensitive; most production Linux containers are not.

21.2 Database connection errors under load
- Check current connection count against the database's max connections limit.
- Confirm pooling is actually configured (Ch. 7.1) — a common failure is having a pooler installed but the app still connecting directly.
- Check for connection leaks — connections opened but never released, often from a query that throws before finally/disconnect runs.

21.3 Container won't start / crash-loops
- docker logs <container> — read the actual error, don't guess.
- Check the HEALTHCHECK and startup order — is it trying to connect to a dependency (Postgres, Redis) that isn't ready yet? Confirm depends_on: condition: service_healthy is set (Ch. 6.7).
- Confirm all required environment variables are present in the container's actual environment (docker exec <container> env), not just in .env.example.

21.4 Deploy succeeds but site shows old version
- Check CDN/browser caching — hard refresh, or check Cache-Control headers on the deployed asset.
- Confirm the deploy actually targeted the branch/commit expected — check the platform's deploy log for the commit SHA.
- For Docker: confirm the image was actually rebuilt (docker compose build --no-cache) and not served from a stale cached layer.

21.5 High latency / slow responses
- Check database query performance first — EXPLAIN ANALYZE the slowest endpoints' queries.
- Check whether Redis caching (Ch. 9.1) is actually being hit, or silently missing on every request.
- Check for N+1 query patterns — a loop issuing one query per item instead of one batched query.
- Check external API calls in the request path — anything not cached or backgrounded (Ch. 10) that's waiting on a third party.

21.6 SSL/TLS certificate errors
- Confirm DNS actually points at the expected target (dig/nslookup) — certificate provisioning fails silently if DNS isn't correctly resolved yet.
- For self-hosted: check Certbot logs for renewal failures and confirm the renewal hook actually reloads Nginx.
- Check certificate expiry directly: openssl s_client -connect example.com:443 -servername example.com | openssl x509 -noout -dates.

21.7 CORS errors in the browser console
- Confirm the requesting origin is in the backend's allowlist exactly (including protocol and port — http://localhost:3000 and https://localhost:3000 are different origins).
- Check whether the request includes credentials (credentials: "include" client-side) and whether the server sets Access-Control-Allow-Credentials: true — the two must match, and origin: "*" is invalid with credentials enabled.

21.8 Background jobs stuck or not processing
- Confirm the worker process/container is actually running, not just the queue producer.
- Check Redis connectivity from the worker specifically — a queue can accept new jobs while the worker consuming them is disconnected.
- Check the dead letter queue (Ch. 10.3) — jobs may be failing and exhausting retries silently if no one's watching it.

22. Scaling Strategy
22.1 Stage 1 — Portfolio
- Profile: Single developer, low/no real traffic, cost-sensitive, optimizing for demonstrating competence.
- Cloud-native architecture (Ch. 5) on free/hobby tiers throughout: Vercel (frontend), Render/Railway free tier (backend), Neon/Supabase free tier (database).
- Single backend instance, no horizontal scaling needed.
- Basic monitoring (Sentry free tier) is sufficient; full metrics infrastructure is likely overkill.
- Docker Compose setup still worth building and documented (Ch. 6) — it's a strong differentiator in a portfolio even if never deployed to a real server, and demonstrates the same skills the cloud path does.

22.2 Stage 2 — Startup MVP
- Profile: Early real users, still small team, needs to move fast without accumulating dangerous technical debt.
- Move off free tiers to paid starter tiers for reliability (no cold starts, real backup SLAs).
- Add Redis for caching and session/rate-limiting if not already present.
- Add background workers for anything user-facing that touches a third-party API (email, payments, notifications) — reliability starts mattering once real users depend on it.
- CI/CD gates (Ch. 15) become non-negotiable at this stage if they weren't already.
- Start tracking the four core metrics (Ch. 13.3): request rate, error rate, latency percentiles, queue depth.

22.3 Stage 3 — Production
- Profile: Meaningful traffic, uptime matters to the business, multiple engineers touching the codebase.
- Horizontal scaling of the backend tier (multiple replicas behind a load balancer) — this is where statelessness (sessions in Redis, not in-process; Ch. 9.3) stops being optional.
- Database read replicas if read traffic is the bottleneck; connection pooling tuning becomes an active, monitored concern rather than a set-and-forget default.
- Full observability stack: structured logs shipped to a central aggregator, dashboards built on the metrics from Ch. 13.3, on-call alerting on error rate and latency thresholds.
- Staging environment that mirrors production configuration, used for pre-release validation, not just local testing.
- Formal incident response process — the troubleshooting guide (Ch. 21) becomes the seed of a real runbook.

22.4 Stage 4 — Enterprise
- Profile: High availability requirements, compliance obligations, large or multiple engineering teams.
- Multi-region deployment for latency and disaster recovery, with the database's replication topology explicitly designed for it (not just multiple app regions pointed at one database region).
- Database write-path scaling: sharding, or splitting hot tables into purpose-built stores, once a single primary can no longer absorb write load.
- Formal SLAs, with monitoring and alerting designed around them specifically (error budgets, not just "did it error").
- Security posture matures beyond Chapter 11's baseline: regular penetration testing, SOC 2 or equivalent compliance processes, dedicated secrets management infrastructure (Vault or a cloud provider's equivalent) rather than platform-native env var storage.
- Infrastructure-as-code (Terraform or equivalent) becomes mandatory rather than optional — manual dashboard configuration doesn't scale to multiple environments and multiple regions managed by multiple teams.

22.5 The throughline
At every stage, the same rule from Chapter 1.5 applies: the application doesn't change because the deployment scaled. What changes is entirely infrastructure — more replicas, more caching layers, more observability, more automation around the same twelve-factor-compliant, environment-configured, stateless application this playbook describes from Stage 1 onward. That portability is the entire point of building it this way from the start.
