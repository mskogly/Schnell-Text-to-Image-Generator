# GitHub Setup for New Machine

Since this is a new machine, you need to configure Git and authenticate with GitHub.

## Step 1: Configure Git Identity

First, tell Git who you are:

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

Replace with your actual name and the email associated with your GitHub account.

## Step 2: Authenticate with GitHub

GitHub no longer accepts passwords for Git operations. You need to use either:

### Option A: Personal Access Token (Recommended for beginners)

1. Go to GitHub.com and log in
2. Click your profile picture → **Settings**
3. Scroll down to **Developer settings** (bottom of left sidebar)
4. Click **Personal access tokens** → **Tokens (classic)**
5. Click **Generate new token** → **Generate new token (classic)**
6. Give it a name like "MacBook Git Access"
7. Set expiration (recommend 90 days or No expiration)
8. Check the **repo** scope (this gives full control of private repositories)
9. Click **Generate token** at the bottom
10. **IMPORTANT**: Copy the token immediately (you won't see it again!)

When you run `git push`, use:
- Username: your GitHub username
- Password: paste the token (not your GitHub password)

### Option B: SSH Key (More secure, one-time setup)

1. Generate an SSH key:
```bash
ssh-keygen -t ed25519 -C "your.email@example.com"
```
Press Enter to accept default location, optionally add a passphrase.

2. Start the SSH agent and add your key:
```bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```

3. Copy your public key:
```bash
cat ~/.ssh/id_ed25519.pub
```

4. Add to GitHub:
   - Go to GitHub.com → Settings → SSH and GPG keys
   - Click **New SSH key**
   - Paste your public key
   - Click **Add SSH key**

5. Update your repository to use SSH:
```bash
git remote set-url origin git@github.com:mskogly/Schnell-Text-to-Image-Generator.git
```

## Step 3: Verify Setup

Test your connection:
```bash
# For HTTPS (Personal Access Token)
git push

# For SSH
ssh -T git@github.com
```

## Next Steps

Once authenticated, you can commit and push the git cheat sheet:
```bash
git add git_cheat_sheet.md
git commit -m "Add Git cheat sheet for project workflow"
git push
```
