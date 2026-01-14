# Push Code to GitHub - Quick Steps

## Step 1: Get Your Personal Access Token

1. Go to: **https://github.com/settings/tokens**
2. Click **"Generate new token"** → **"Generate new token (classic)"**
3. Name: `Render Deployment`
4. Expiration: Choose your preference (90 days, 1 year, etc.)
5. Select scope: ✅ **`repo`** (Full control of private repositories)
6. Click **"Generate token"**
7. **COPY THE TOKEN** - You won't see it again!

## Step 2: Push Your Code

Run these commands in your terminal:

```bash
cd "/Users/duboisca/Desktop/LitoStream/kick/smmfollows-bot"

# Replace YOUR_TOKEN_HERE with the token you copied
git remote set-url origin https://YOUR_TOKEN_HERE@github.com/clipsog/clipsdashboard.git

# Now push
git push -u origin main
```

**Example:**
If your token is `ghp_abc123xyz456`, the command would be:
```bash
git remote set-url origin https://ghp_abc123xyz456@github.com/clipsog/clipsdashboard.git
```

## Step 3: Verify

After pushing, check: https://github.com/clipsog/clipsdashboard

You should see all your files there!

## Next: Deploy to Render

Once the code is on GitHub:
1. Go to: https://dashboard.render.com
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub account
4. Select repository: `clipsog/clipsdashboard`
5. Render will auto-detect `render.yaml`
6. Click **"Create Web Service"**

That's it! 🚀
