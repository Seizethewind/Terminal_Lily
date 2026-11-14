#!/data/data/com.termux/files/usr/bin/bash
# One-command setup for Terminal_Lily on Termux. Run from the repo folder.
set -e
pkg update -y
pkg install -y python git
pip install -r requirements.txt
[ -f .env ] || cp .env.example .env
echo "Done. Edit .env, then start Lily with: python main.py"
