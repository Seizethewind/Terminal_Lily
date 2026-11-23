#!/data/data/com.termux/files/usr/bin/bash
# Sets up Lily_Ai 0.1, the local fallback model (Gemma 4 through Ollama). Run from the repo folder.
# Usage: bash scripts/setup_local_ai.sh [gemma4:e2b|gemma4:e4b]   (default gemma4:e2b)
set -e
TAG="${1:-gemma4:e2b}"
NAME="lily_ai:0.1"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
export OLLAMA_MODELS="$HERE/data/models"   # the same folder Lily uses when she starts Ollama
mkdir -p "$OLLAMA_MODELS"

if ! command -v ollama >/dev/null; then
    echo "Installing ollama (pkg)..."
    pkg install -y ollama
fi

echo "Starting ollama for the setup..."
ollama serve >/dev/null 2>&1 &
SERVER=$!
trap 'kill $SERVER 2>/dev/null' EXIT
for _ in $(seq 1 30); do
    ollama list >/dev/null 2>&1 && break
    sleep 1
done

echo "Downloading $TAG (several GB, needs Wi-Fi and free space)..."
ollama pull "$TAG"
sed "s|^FROM .*|FROM $TAG|" "$HERE/config/local_ai/Modelfile" > "$HERE/data/Modelfile.local"
ollama create "$NAME" -f "$HERE/data/Modelfile.local"
rm -f "$HERE/data/Modelfile.local"
echo "Done. Lily_Ai 0.1 is the model '$NAME'. Test it: ollama run $NAME"
echo "Lily uses it by herself only when the router fails or there is no internet."
