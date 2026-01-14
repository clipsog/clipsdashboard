# Push to GitHub - Step by Step

## Option 1: If Repository Doesn't Exist Yet

1. Go to: https://github.com/new
2. Repository name: `clipsdashboard`
3. Make it **Private** (recommended for API keys)
4. **Don't** check "Initialize with README"
5. Click "Create repository"

## Option 2: Push Using GitHub CLI (Easiest)

If you have GitHub CLI installed:

```bash
cd "/Users/duboisca/Desktop/LitoStream/kick/smmfollows-bot"
gh auth login
git push -u origin main
```

## Option 3: Push Using Personal Access Token

1. Go to: https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Name it: "Render Deployment"
4. Select scopes: `repo` (full control)
5. Click "Generate token"
6. Copy the token

Then run:

```bash
cd "/Users/duboisca/Desktop/LitoStream/kick/smmfollows-bot"
git remote set-url origin https://<YOUR_TOKEN>@github.com/clipsog/clipsdashboard.git
git push -u origin main
```

Replace `<YOUR_TOKEN>` with your actual token.

## Option 4: Use SSH (If you have SSH keys set up)

```bash
cd "/Users/duboisca/Desktop/LitoStream/kick/smmfollows-bot"
git remote set-url origin git@github.com:clipsog/clipsdashboard.git
git push -u origin main
```

## After Successful Push

Once pushed, go to Render and deploy:
1. https://dashboard.render.com
2. New + → Web Service
3. Connect GitHub
4. Select `clipsog/clipsdashboard`
5. Create Web Service
