# GitHub Pages Deployment Instructions

**Project**: Physical AI & Humanoid Robotics Textbook
**Repository**: https://github.com/Mehreen676/Physical-AI--humanoid-robotics-book.git
**Live URL**: https://mehreen676.github.io/Physical-AI--humanoid-robotics-book/
**Created**: 2025-12-27

---

## Quick Start: Copy-Paste Commands

Execute these commands in order from your terminal/command prompt:

### Step 1: Install Dependencies

```bash
cd front-end
npm install
```

Expected output: `added X packages in X seconds`

---

### Step 2: Build Locally

```bash
npm run build
```

Expected output:
```
[1/2] Validating imports...
[2/2] Building static site...
✔ Generated build files.
```

---

### Step 3: Test Locally (Optional but Recommended)

```bash
npm run start
```

Then open browser at: `http://localhost:3000/Physical-AI--humanoid-robotics-book/`

Verify:
- [ ] Landing page shows warm cream background
- [ ] Text is dark brown, headings are olive green
- [ ] Accents are soft orange
- [ ] Dark mode toggle works
- [ ] All sidebar links load chapters without 404

Press `Ctrl+C` in terminal to stop local server when done.

---

### Step 4: Commit All Changes

```bash
cd ..
git add .
git commit -m "Feature 008: Deploy to GitHub Pages with gh-pages package"
git push origin main
```

Expected output:
```
[main XXXXXXX] Feature 008: Deploy to GitHub Pages
 X file changed, X insertions(+)
```

---

### Step 5: Deploy to GitHub Pages

```bash
cd front-end
npm run deploy
```

Expected output:
```
> gh-pages -d build

Published
```

**Wait 2-5 minutes for GitHub Pages to rebuild.**

---

### Step 6: Enable GitHub Pages in Repository Settings

1. Go to: https://github.com/Mehreen676/Physical-AI--humanoid-robotics-book
2. Click **Settings** tab
3. Click **Pages** in left sidebar
4. Under "Build and deployment":
   - **Source**: Select "Deploy from a branch"
   - **Branch**: Select `gh-pages`
   - **Folder**: Select `/ (root)`
5. Click **Save**

Expected: Green checkmark with message "Your site is published at https://mehreen676.github.io/Physical-AI--humanoid-robotics-book/"

---

### Step 7: Verify Live Deployment

Open browser and visit: **https://mehreen676.github.io/Physical-AI--humanoid-robotics-book/**

Verify:
- [ ] Page loads with warm cream background
- [ ] All text and colors visible correctly
- [ ] Dark mode toggle works
- [ ] Click sidebar links - all chapters load without 404
- [ ] Mobile responsive (open DevTools, check 375px width)
- [ ] Footer shows "Created by Mehreen Asghar Ali..."

---

## Detailed Step-by-Step Commands

### Install gh-pages Package (if not already installed)

```bash
cd front-end
npm install --save-dev gh-pages
```

### Update package.json deploy script (ALREADY DONE)

The deploy script is already configured in `front-end/package.json`:

```json
{
  "scripts": {
    "deploy": "gh-pages -d build"
  },
  "devDependencies": {
    "gh-pages": "^5.0.0"
  }
}
```

### Full Deployment Sequence

```bash
# Navigate to repository root
cd /path/to/text-book

# Navigate to front-end directory
cd front-end

# Install dependencies (one-time only)
npm install

# Build static site
npm run build

# Optional: Test locally before deploying
npm run start
# (Open http://localhost:3000/Physical-AI--humanoid-robotics-book/ in browser)
# (Press Ctrl+C to stop)

# Go back to repo root
cd ..

# Commit all changes
git add .
git commit -m "Feature 008: Deploy to GitHub Pages"
git push origin main

# Deploy to GitHub Pages
cd front-end
npm run deploy
```

---

## Verification Commands

### Verify gh-pages Package Installed

```bash
cd front-end
npm list gh-pages
```

Should output: `gh-pages@5.0.0` or similar version ≥4.0.0

### Verify build Directory Created

```bash
ls -la build/
# or on Windows:
dir build
```

Should show: `Physical-AI--humanoid-robotics-book/` directory and other files

### Verify Site is Live

```bash
curl -I https://mehreen676.github.io/Physical-AI--humanoid-robotics-book/
```

Should show: `HTTP/2 200 OK`

### Verify gh-pages Branch Exists

```bash
git branch -a
```

Should show: `remotes/origin/gh-pages`

---

## Troubleshooting

### Error: "gh-pages command not found"

**Solution**: Install gh-pages package

```bash
cd front-end
npm install --save-dev gh-pages
```

### Error: "build directory not found"

**Solution**: Run build command first

```bash
cd front-end
npm run build
```

### Error: "Authentication failed" during push/deploy

**Solution**: Check GitHub credentials or use personal access token

```bash
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

Or generate GitHub personal access token: https://github.com/settings/tokens

### Site shows 404 error

**Possible Causes**:
1. GitHub Pages not enabled in settings
2. gh-pages branch not created yet (happens after first deploy)
3. Website still building (wait 2-5 minutes)
4. Browser cache (hard refresh: Ctrl+Shift+Delete)

**Solution**:
- Verify Settings → Pages shows "Published"
- Check Branches tab for `gh-pages` branch
- Wait 5 minutes and try again
- Hard refresh browser (Ctrl+Shift+Delete in Chrome)

### Colors not showing

**Solution**: Hard refresh browser

```
Chrome/Edge: Ctrl+Shift+Delete
Firefox: Ctrl+Shift+Delete or Ctrl+F5
Safari: Cmd+Shift+Delete
```

If still broken after hard refresh:
1. Check browser console (F12) for CSS 404 errors
2. Rebuild and redeploy:
   ```bash
   cd front-end
   npm run build
   cd ..
   git add .
   git commit -m "Rebuild"
   git push
   cd front-end
   npm run deploy
   ```

### Dark mode not working

**Solution**: Clear browser localStorage and hard refresh

```
F12 → Application tab → LocalStorage → Delete all entries
Then: Ctrl+Shift+Delete (hard refresh)
```

---

## Performance Verification

### Run Lighthouse Audit on Live Site

1. Open https://mehreen676.github.io/Physical-AI--humanoid-robotics-book/
2. Press F12 (DevTools)
3. Click **Lighthouse** tab
4. Click **Analyze page load**
5. Check results:
   - Performance: Should be ≥85/100
   - Accessibility: Should be ≥90/100
   - Largest Contentful Paint (LCP): Should be <2 seconds

### Check Mobile Responsiveness

1. Open https://mehreen676.github.io/Physical-AI--humanoid-robotics-book/
2. Press F12 (DevTools)
3. Click **Toggle device toolbar** (Ctrl+Shift+M)
4. Test widths: 375px (mobile), 768px (tablet), 1024px (desktop)
5. Verify layout adapts without overflow or broken elements

---

## Rollback (Revert Deployment)

If deployment has issues and you need to roll back:

```bash
# Check gh-pages branch history
git log remotes/origin/gh-pages -5

# Revert to previous commit on gh-pages
git reset --soft remotes/origin/gh-pages~1

# Or manually revert and redeploy
git checkout gh-pages
git revert HEAD
git push origin gh-pages
git checkout main
```

---

## Next Steps

1. ✅ Share live URL with judges: https://mehreen676.github.io/Physical-AI--humanoid-robotics-book/
2. Monitor feedback from judges
3. If issues found, fix in main branch and redeploy with:
   ```bash
   npm run build && npm run deploy
   ```

---

## Summary

| Step | Command | Expected Result |
|------|---------|-----------------|
| 1 | `cd front-end && npm install` | Dependencies installed |
| 2 | `npm run build` | build/ directory created |
| 3 | `npm run start` | Local server at :3000 |
| 4 | `git add . && git commit && git push` | Pushed to main |
| 5 | `npm run deploy` | Deployed to gh-pages |
| 6 | Enable Pages in Settings | GitHub Pages enabled |
| 7 | Visit live URL | Site live and working |

---

**For detailed documentation, see**:
- `specs/008-github-pages-deployment/spec.md` - Full specification
- `specs/008-github-pages-deployment/plan.md` - Implementation architecture
- `specs/008-github-pages-deployment/quickstart.md` - Detailed walkthrough
- `specs/008-github-pages-deployment/tasks.md` - All 59 implementation tasks

---

**Created**: 2025-12-27
**Feature**: 008-github-pages-deployment
**Status**: DEPLOYMENT READY ✅
