# Testudo AI — Git Branching Guide

This document explains how the Testudo AI team will collaborate using a simple, consistent Git branching strategy. Following this guide ensures smooth teamwork, clean code integration, and minimal merge conflicts.

---

## Branch Overview

We use two main branches for the entire project:

| Branch | Purpose |
|:-------|:---------|
| `main` | Contains stable, production-ready code |
| `dev`  | Used for integrating new features before merging to `main` |

Each subteam will create short-lived feature branches from `dev` for their specific tools or modules.

---

## Workflow Overview

The general flow of work is:

```
(feature branches) --> dev --> main
```

Subteams branch from `dev`, work on their features, and merge back when complete.  
The core team merges `dev` into `main` once testing is complete.

---

## Example: Creating and Working on a Feature Branch

If your subteam is developing the Transit Tool:

### 1. Create a Branch
Always start from the latest `dev` branch:

```bash
git checkout dev
git pull origin dev
git checkout -b feature/transit-tool
```

This creates a new branch for your subteam’s work.

---

### 2. Make Changes and Commit Often
As you write code and test locally, commit frequently:

```bash
git add .
git commit -m "Add basic transit data fetcher"
git push origin feature/transit-tool
```

To stay up to date with others’ work:

```bash
git pull origin dev
git merge dev
```

---

### 3. Open a Pull Request (PR)
When your feature is working and tested, open a **PR** to merge your branch into `dev`:

```
feature/transit-tool → dev
```

- Write a clear PR title and description.  
- Request a review from your subteam lead or another member.  
- Once approved, merge into `dev`.

---

### 4. Integration and Release
After all subteams’ modules are tested and verified:
1. The core team merges `dev` into `main`.
2. Everyone pulls the latest stable version:

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

Branch names should be lowercase, short, and descriptive.

---

## Best Practices

- Commit often. Small, frequent commits make collaboration smoother.  
- Merge often. Avoid long-lived branches that are hard to reconcile later.  
- Write clear commit messages. Example: `Add endpoint for dining menu data`.  
- Review PRs carefully. Reviews are part of how we learn and maintain quality.  
- Never push directly to `main`. Always go through `dev` and feature branches.

---

## Visual Overview

```
          ┌─────────────┐
          │   main      │  ← stable production code
          └─────▲───────┘
                │                                                  <--- branch
         ┌──────┴───────┐
         │     dev       │  ← integration branch
         └───▲────▲──────┘
             │    │                                                <---- branch
   ┌─────────┘    └─────────┐
   │                        │
scheduling-api          dining-tool      
   │                      |    |                                   <---- branch
feature_name         feature1  feature2
   |                    |        |                                 <---- merge
scheduling-api          dining-tool
   └──────────────→ dev ←────┘                                     <---- merge            
            merge & test
```

---

## Summary

- Work happens on feature branches created from `dev`.  
- Merge early and often to avoid large, messy updates.  
- The core team keeps `main` stable.  
- Communicate regularly with your subteam to coordinate merges and reviews.
