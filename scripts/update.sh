#!/data/data/com.termux/files/usr/bin/bash
# Update Terminal_Lily from GitHub. Run it from anywhere: bash ~/Terminal_Lily/scripts/update.sh
# It only fast-forwards, so it never overwrites or merges your own edits.
set -e
cd "$(dirname "$0")/.."

[ -d .git ] || { echo "This folder is not a git clone, so it cannot update itself."; exit 1; }
command -v git >/dev/null || { echo "git is missing. Run: pkg install git"; exit 1; }

if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  echo "You have local changes. Update stops so it cannot overwrite them:"
  git status --short --untracked-files=no
  echo "Save them first (git stash), then run this again."
  exit 1
fi

before=$(git rev-parse HEAD)
git pull --ff-only
after=$(git rev-parse HEAD)

if [ "$before" = "$after" ]; then
  echo "Already up to date."
  exit 0
fi

echo; echo "What changed:"
git log --oneline "$before..$after" | head -15

# Only reinstall Python packages when the list changed.
if ! git diff --quiet "$before" "$after" -- requirements.txt; then
  echo; echo "requirements.txt changed, installing packages..."
  pip install -r requirements.txt
fi

[ -f .env ] || { cp .env.example .env; echo "Created .env from .env.example: edit it."; }
echo; echo "Updated. Restart Lily (/exit, then python main.py) to use the new version."
