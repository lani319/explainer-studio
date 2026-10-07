#!/usr/bin/env sh
# Rebuild skills/explainer/engine/vendor/three.bundle.js — three.js + the model loaders as ONE classic script.
# Classic, not an ES module: Chrome refuses module scripts on file:// pages, and episodes open from disk.
set -e
VERSION="${1:-0.186.1}"
OUT="$(cd "$(dirname "$0")/.." && pwd)/skills/explainer/engine/vendor"
TMPDIR="$(mktemp -d)"
cd "$TMPDIR"
npm init -y >/dev/null
npm install --silent "three@$VERSION" esbuild
cat > entry.js <<'JS'
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { STLLoader } from "three/examples/jsm/loaders/STLLoader.js";
import { OBJLoader } from "three/examples/jsm/loaders/OBJLoader.js";
window.THREE = Object.assign({}, THREE, { GLTFLoader, STLLoader, OBJLoader });
JS
npx esbuild entry.js --bundle --format=iife --minify --legal-comments=none --outfile=three.bundle.js
{ printf '/* three.js %s with GLTFLoader, STLLoader, OBJLoader — MIT License, see LICENSE-three.txt */\n' "$VERSION"; cat three.bundle.js; } > "$OUT/three.bundle.js"
cp node_modules/three/LICENSE "$OUT/LICENSE-three.txt"
echo "wrote $OUT/three.bundle.js"
