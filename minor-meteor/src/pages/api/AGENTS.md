# AGENTS.md for minor-meteor/src/pages/api

## Purpose
- Define contracts for API endpoint handlers in the Astro project.

## Ownership
- Owner: Project maintainer (AR Khan)

## Local Contracts
- Contains TypeScript files that implement serverless API routes.

## Work Guidance
- Follow the `src/pages` AGENTS.md rules unless overridden.
- Each file should export a handler compatible with Astro's API runtime.
- Keep API logic isolated; avoid importing UI components.

## Verification
- API routes should respond correctly when tested locally (`npm run dev`) and after deployment.

## Child DOX Index
- No further child AGENTS.md files at this time.
