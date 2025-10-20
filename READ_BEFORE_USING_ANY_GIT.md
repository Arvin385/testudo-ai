# Testudo AI — Git Branching Guide

This guide explains how we’ll collaborate efficiently as a large team using Git branching best practices.  
Our goals are:  
- Keep things simple and organized  
- Encourage fast iteration and teamwork  
- Maintain stable code in our main branch  

---

## Branch Overview

We use two main branches for the whole project:

| Branch | Purpose |
|:-------|:---------|
| `main` | Always contains stable, production-ready code |
| `dev`  | Integrates all new features before merging to `main` |

Subteams will create short-lived feature branches off `dev` to work on specific tools or modules.

---

## Workflow Overview

Here’s the basic flow for all development work:

```
(feature branches) --> dev --> main
```

Subteams branch from `dev`, work on their feature, merge back when complete.  
The core team handles merging `dev` → `main` after full testing.

---

## Example: Creating and Working on a Feature Branch

Let’s say your subteam is developing the Transit Tool.

### 1. Create a Branch
Always branch off the latest `dev`:
```bash
git checkout dev
git pull origin dev
git checkout -b feature/transit-tool
```

This creates a new branch named `feature/transit-tool`.

---

### 2. Make Changes and Commit Often
Write your code, test it locally, and commit frequently:
```bash
git add .
git commit -m "Add basic transit data fetcher"
git push origin feature/transit-tool
```

Keep your branch up to date with `dev`:
```bash
git pull origin dev
git merge dev
```

---

### 3. Open a Pull Request (PR)
When your feature works and is tested, open a PR to merge:
```
feature/transit-tool → dev
```

- Include a clear title and description of what your branch adds or fixes.  
- Ask another member to review your code.  

Once approved, merge into `dev`.

---

### 4. Integration and Release
After all teams have tested their modules:
1. Core team merges `dev` → `main`.
2. Everyone pulls the latest `main`:
   ```bash
   git checkout main
   git pull origin main
   ```

---

## Branch Naming Conventions

| Type | Format | Example |
|:-----|:--------|:--------|
| Feature | `feature/<name>` | `feature/dining-api` |
| Fix | `fix/<name>` | `fix/schedule-display` |
| Experimental (optional) | `exp/<name>` | `exp/voice-test` |

Keep branch names lowercase and descriptive.

---

## Best Practices

- Commit often — smaller commits are easier to debug and review.  
- Merge often — avoid letting branches get stale.  
- Write clear commit messages (e.g., “Add dining hall API integration”).  
- Review each other’s PRs for quality and shared learning.  
- Never push directly to `main` — all work flows through `dev`.  

---

## Visual Overview

```
          ┌─────────────┐
          │   main      │  ← stable production code
          └─────▲───────┘
                │
         ┌──────┴───────┐
         │     dev       │  ← integration branch
         └───▲────▲──────┘
             │    │
   ┌─────────┘    └─────────┐
   │                        │
feature/scheduling-api   feature/dining-tool
   │                        │
   └──────────────→ dev ←────┘
            merge & test
```

---

## Summary

- Work happens on feature branches from `dev`.  
- Merge early, merge often.  
- Core team ensures `main` stays stable.  
- Communicate — your subteam lead coordinates merges and reviews.
