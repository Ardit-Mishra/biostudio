# Pushing BioStudio to GitHub

Step-by-step instructions for pushing this repository to GitHub.

---

## Prerequisites

1. A GitHub account ([github.com](https://github.com))
2. Git installed locally (`git --version`)
3. A **Personal Access Token (PAT)** with `repo` scope

### Creating a Personal Access Token

1. Go to **GitHub → Settings → Developer Settings → Personal Access Tokens → Tokens (classic)**
2. Click **Generate new token (classic)**
3. Select the `repo` scope (full control of private repositories)
4. Copy the token — you will not see it again

---

## First-Time Setup

### 1. Create the GitHub Repository

1. Go to [github.com/new](https://github.com/new)
2. Repository name: `biostudio`
3. Description: `AI-Powered Molecular Intelligence Platform for Educational Drug Discovery`
4. Visibility: Public (or Private)
5. **Do not** initialize with README, .gitignore, or license (they already exist locally)
6. Click **Create repository**

### 2. Initialize and Push

```bash
git init
git add .
git commit -m "Initial commit: BioStudio v1.2.0"

git remote add origin https://github.com/Ardit-Mishra/biostudio.git

git branch -M main
git push -u origin main
```

When prompted for a password, use your **Personal Access Token** (not your GitHub password).

---

## Subsequent Pushes

```bash
git add .
git commit -m "Description of changes"
git push origin main
```

---

## Using PAT in the Remote URL (Optional)

To avoid entering credentials each time:

```bash
git remote set-url origin https://<YOUR_PAT>@github.com/Ardit-Mishra/biostudio.git
```

Replace `<YOUR_PAT>` with your actual token. Keep this URL private.

---

## Verifying the Push

After pushing, confirm at: [https://github.com/Ardit-Mishra/biostudio](https://github.com/Ardit-Mishra/biostudio)

Check that:
- README.md renders correctly on the repository page
- CITATION.cff is recognized by GitHub (shows citation widget in sidebar)
- .gitignore is preventing local environment folders from being tracked
- License badge and links in README point to the correct repository

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `remote: Permission denied` | Verify PAT has `repo` scope and is not expired |
| `fatal: remote origin already exists` | Run `git remote set-url origin <URL>` instead of `git remote add` |
| Large files rejected | Check `.gitignore` is excluding `.cache/`, `.pythonlibs/`, model files |
| Branch name mismatch | Use `git branch -M main` to rename default branch |
