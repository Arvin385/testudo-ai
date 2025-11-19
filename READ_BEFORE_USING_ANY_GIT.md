# Testudo AI — Git Branching Guide

This document explains how the Testudo AI team will collaborate using a simple, consistent Git branching strategy. Following this guide ensures smooth teamwork, clean code integration, and minimal merge conflicts.

---

## Branch Overview

We use two main branches for the entire project:

| Branch | Purpose |
|:-------|:---------|
| `main` | Contains stable, production-ready code |
| `dev`  | Used for integrating new features before merging to `main` |

Each subteam will create long-lived subteam branches and short-lived feature branches from `dev` for their specific tools or modules.

---

## Workflow Overview

The general flow of work is:

```
(feature branches) --> <subteam branch> --> dev --> main
```
At the beginning of the project, each team will make their own branch from dev, named after their subteam.

Subteams branch from their subteam branch, work on their features, and merge back into the subteam branch when complete.

When teams want to update the main project with all of their recent new features, they'll create a pull request from their subteam branch to `dev` and add Arvin, Farhan, Swathi, or Rohan as a reviewer. 

The core team will merge this branch back into dev, test that no changes broke any features, and merge `dev` back into `main` after testing is complete. 

---

## Example: Creating and Working on a Feature Branch

If your subteam is developing the Transit Tool:

### 1. Create Your Subteam Branch
Subteams start from the latest `dev` branch:

```bash
git checkout dev
git pull origin dev
git checkout -b scheduler
```

This creates a new branch for your subteam’s work. 

If the command line interface scares you, follow this tutorial: https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-and-deleting-branches-within-your-repository
Your source branch for this should be `dev`. 

---

### 2. Create Your Feature Branch
When making new features, subteam members start from their subteam's branch:

```bash
git checkout dev
git pull origin dev
git checkout -b scheduler-scraping-tool
```

This creates a new branch for your individual work. Make sure you name your branch aptly as "<subteam-name>-feature/<feature-name>" or one of the other naming conventions down below.

Making the branch works the same here as in Step 1, just note your source branch for this should be your subteam's branch, NOT `dev`. 

---

### 3. Make Changes and Commit Often
As you write code and test locally, commit frequently:

```bash
git add .
git commit -m "Add basic transit data fetcher"
git push origin scheduler-feature/scraping-tool
```

To stay up to date with others’ work:

```bash
git pull origin dev
git merge dev
```

Use GitHub Desktop (HIGHLY RECOMMENDED) or Visual Studio Code if you don't want to deal with the Git CLI.

---

### 4 Open a Pull Request in your subteam (PR)
When your feature is working and tested, open a **PR** to merge your branch into your subteam's branch:

```
scheduler-feature/scraping-tool → scheduler
```
Make a PR:
- On how to make a PR: https://www.youtube.com/watch?v=nCKdihvneS0
- Write a clear PR title and description.  
- Confirm with your subteam that it is OK to merge back into your subteam's branch
Merge your code back:
- Once you ALL agree, merge into your subteam branch AT YOUR OWN RISK
- Ask for help if you want someone with Git experience to show you how to merge branches.
Cleaning Up:
- Go back to the GitHub website, open the pull requests tab, and go to the closed group.
- Scroll down to the bottom and select delete branch.
- This doesn't delete the code entirely... just makes everything less cluttered. You can restore it later if needed.

### 5. Open a Pull Request to dev (PR)
When your feature is working and tested, open a **PR** to merge your branch into dev:

```
scheduler → dev
```

- ONLY follow the steps for making a PR from above.
- Open the PR on GitHub, and tap on reviewers. Select Arvin, Farhan (DarksharkThe1st), Swathi, or Rohan's name.  
- Ping one of the four of us on discord, and we will review and merge as needed for you.

---

### 5. Integration and Release
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
| Feature | `<subteam_name>-feature/<name>` | `scheduler-feature/scraping-tool` |
| Fix | `<subteam-name>-fix/<name>` | `scheduler-fix/schedule-display` |
| Experimental (optional) | `scheduler-exp/<name>` | `scheduler-exp/auto-scheduling` |

Branch names should be lowercase, short, and descriptive.

---

## Best Practices

- Commit often. Small, frequent commits make collaboration smoother.  
- Merge often. Avoid long-lived branches that are hard to reconcile later.  
- Write clear commit messages. Example: `Add endpoint for dining menu data`.  
- Review PRs carefully. Reviews are part of how we learn and maintain quality.  
- Never push directly to `main`. Always go through `dev` and subteam branches.

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
scheduling              dining-tool                                <---- subteam branch
   │                      |    |                                   <---- branch
feature_name         feature1  feature2
   |                    |        |                                 <---- merge
scheduling              dining-tool
   └──────────────→ dev ←────┘                                     <---- merge            
            merge & test
```

---

## Summary

- Subteams begin from subteam branches, sourced from `dev`.
- Work happens on feature branches created from your subteam branch.  
- Merge early and often to avoid large, messy updates.  
- The core team keeps `main` stable.  
- Communicate regularly with your subteam to coordinate merges and reviews.
