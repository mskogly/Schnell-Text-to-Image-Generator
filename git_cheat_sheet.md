# Git Cheat Sheet for `Schnell-Text-to-Image-Generator`

Your project is already set up with Git! Here is a simple guide to using it.

## Setup for this new location
Since we moved out of Dropbox, you need to recreate the virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Daily Workflow

### 1. Check what changed
See which files you have modified:
```bash
git status
```

### 2. Save your changes (Stage & Commit)
When you are happy with your work:
```bash
# Add all modified files
git add .

# Save them with a message
git commit -m "Describe what you did here"
```

### 3. Upload to GitHub
To back up your code to the cloud:
```bash
git push
```

### 4. Download from GitHub (on another machine)
To get the latest changes you pushed from elsewhere:
```bash
git pull
```

## Why Git is better than Dropbox here
- **Ignores `venv`**: Dropbox syncs your virtual environment, which breaks when moving between computers. Git ignores it.
- **History**: You can undo changes easily.
