#!/bin/bash

# ============================================
# init-semantic-latex.sh
# One-click setup for semantic-release LaTeX
# ============================================

set -e

echo "🚀 Initializing Semantic Release for LaTeX Project"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 found"
        return 0
    else
        echo -e "${RED}✗${NC} $1 not found"
        return 1
    fi
}

echo ""
echo "📋 Checking prerequisites..."
MISSING_DEPS=0

check_command git || MISSING_DEPS=1
check_command node || MISSING_DEPS=1
check_command npm || MISSING_DEPS=1
check_command pdflatex || MISSING_DEPS=1
check_command bibtex || MISSING_DEPS=1

# Optional but recommended
echo ""
echo "📦 Checking optional tools..."
check_command latexpand || echo -e "${YELLOW}  → Install with: tlmgr install latexpand${NC}"
check_command latexdiff || echo -e "${YELLOW}  → Install with: tlmgr install latexdiff${NC}"

if [ $MISSING_DEPS -eq 1 ]; then
    echo ""
    echo -e "${RED}❌ Missing required dependencies. Please install them first.${NC}"
    exit 1
fi

echo ""
echo "✅ All required dependencies found!"
echo ""

# Confirm before proceeding
read -p "This will create/modify files in your project. Continue? (y/N) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

# Create directory structure
echo ""
echo "📁 Creating directory structure..."
mkdir -p scripts
mkdir -p .github/workflows

# Create package.json
echo "📄 Creating package.json..."
cat > package.json << 'EOF'
{
  "name": "latex-document-release",
  "version": "0.0.0-development",
  "description": "Automated LaTeX document versioning with semantic-release",
  "private": true,
  "scripts": {
    "build": "./scripts/build.sh",
    "build:diff": "./scripts/build-diff.sh",
    "test": "./scripts/validate.sh",
    "semantic-release": "semantic-release"
  },
  "devDependencies": {
    "@semantic-release/changelog": "^6.0.3",
    "@semantic-release/exec": "^6.0.3",
    "@semantic-release/git": "^10.0.1",
    "@semantic-release/github": "^9.2.6",
    "@commitlint/cli": "^18.4.3",
    "@commitlint/config-conventional": "^18.4.3",
    "husky": "^8.0.3",
    "semantic-release": "^22.0.12"
  }
}
EOF

# Create .releaserc.js
echo "📄 Creating .releaserc.js..."
cat > .releaserc.js << 'EOF'
module.exports = {
  branches: ['main', 'master'],
  plugins: [
    ['@semantic-release/commit-analyzer', {
      preset: 'conventionalcommits',
      releaseRules: [
        {type: 'feat', release: 'minor'},
        {type: 'fix', release: 'patch'},
        {type: 'docs', release: 'patch'},
        {type: 'style', release: 'patch'},
        {type: 'refactor', release: 'patch'},
        {breaking: true, release: 'major'}
      ]
    }],
    '@semantic-release/release-notes-generator',
    ['@semantic-release/changelog', {
      changelogFile: 'CHANGELOG.md'
    }],
    ['@semantic-release/exec', {
      prepareCmd: './scripts/prepare-release.sh ${nextRelease.version} ${lastRelease.version}'
    }],
    ['@semantic-release/github', {
      assets: [
        {path: 'dist/main.pdf', name: 'document-${nextRelease.version}.pdf'},
        {path: 'dist/main_expanded.tex', name: 'source-${nextRelease.version}.tex'},
        {path: 'dist/main.bbl', name: 'bibliography-${nextRelease.version}.bbl'},
        {path: 'dist/diff.pdf', name: 'diff-${lastRelease.version}-to-${nextRelease.version}.pdf'}
      ]
    }],
    ['@semantic-release/git', {
      assets: ['CHANGELOG.md', 'package.json'],
      message: 'chore(release): ${nextRelease.version} [skip ci]'
    }]
  ]
};
EOF

# Create commitlint.config.js
echo "📄 Creating commitlint.config.js..."
cat > commitlint.config.js << 'EOF'
module.exports = {
  extends: ['@commitlint/config-conventional']
};
EOF

# Create build.sh
echo "📄 Creating scripts/build.sh..."
cat > scripts/build.sh << 'EOF'
#!/bin/bash
set -e
MAIN_FILE="${MAIN_FILE:-main}"
BUILD_DIR="build"
DIST_DIR="dist"

echo "🔨 Building LaTeX document..."
mkdir -p "$BUILD_DIR" "$DIST_DIR"

# Copy files to build directory
cp -r *.tex "$BUILD_DIR/" 2>/dev/null || true
cp -r *.bib "$BUILD_DIR/" 2>/dev/null || true
cp -r *.cls "$BUILD_DIR/" 2>/dev/null || true
cp -r *.sty "$BUILD_DIR/" 2>/dev/null || true
cp -r figures "$BUILD_DIR/" 2>/dev/null || true
cp -r chapters "$BUILD_DIR/" 2>/dev/null || true

cd "$BUILD_DIR"

# Compile PDF
pdflatex -interaction=nonstopmode "$MAIN_FILE.tex" || true
bibtex "$MAIN_FILE" || true
pdflatex -interaction=nonstopmode "$MAIN_FILE.tex" || true
pdflatex -interaction=nonstopmode "$MAIN_FILE.tex"

# Generate expanded TeX
if command -v latexpand &> /dev/null; then
    latexpand --keep-comments --expand-bbl "$MAIN_FILE.tex" > "$MAIN_FILE"_expanded.tex
else
    cp "$MAIN_FILE.tex" "$MAIN_FILE"_expanded.tex
fi

# Copy to dist
cd ..
cp "$BUILD_DIR/$MAIN_FILE.pdf" "$DIST_DIR/"
cp "$BUILD_DIR/$MAIN_FILE.bbl" "$DIST_DIR/" 2>/dev/null || touch "$DIST_DIR/$MAIN_FILE.bbl"
cp "$BUILD_DIR/$MAIN_FILE"_expanded.tex "$DIST_DIR/"

echo "✅ Build complete!"
EOF

# Create prepare-release.sh
echo "📄 Creating scripts/prepare-release.sh..."
cat > scripts/prepare-release.sh << 'EOF'
#!/bin/bash
set -e
NEXT_VERSION=$1
LAST_VERSION=$2

echo "📦 Preparing release v$NEXT_VERSION..."
mkdir -p dist

# Build main document
./scripts/build.sh

# Generate diff if previous version exists
if [ -n "$LAST_VERSION" ] && [ "$LAST_VERSION" != "null" ]; then
    echo "📊 Generating diff from v$LAST_VERSION..."
    # Download previous version and generate diff
    # (Implementation depends on your setup)
fi

echo "✅ Release prepared!"
EOF

# Create validate.sh
echo "📄 Creating scripts/validate.sh..."
cat > scripts/validate.sh << 'EOF'
#!/bin/bash
set -e
echo "✔️ Validating LaTeX project..."

MAIN_FILE="${MAIN_FILE:-main}"
if [ ! -f "$MAIN_FILE.tex" ]; then
    echo "❌ $MAIN_FILE.tex not found"
    exit 1
fi

echo "✅ Validation complete"
EOF

# Create GitHub Actions workflow
echo "📄 Creating .github/workflows/release.yml..."
cat > .github/workflows/release.yml << 'EOF'
name: Semantic Release

on:
  push:
    branches: [main, master]
  workflow_dispatch:

permissions:
  contents: write
  issues: write
  pull-requests: write

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - uses: xu-cheng/latex-action@v3
        with:
          root_file: main.tex
          extra_packages: |
            latexpand
            latexdiff

      - run: npm ci
      - run: npm test
      - run: npx semantic-release
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
EOF

# Make scripts executable
echo "🔧 Making scripts executable..."
chmod +x scripts/*.sh

# Update .gitignore
echo "📄 Updating .gitignore..."
cat >> .gitignore << 'EOF'

# Semantic Release
node_modules/
dist/
build/
*.log

# LaTeX
*.aux
*.bbl
*.blg
*.out
*.toc
*.synctex.gz
EOF

# Install npm packages
echo ""
echo "📦 Installing npm packages..."
npm install

# Setup git hooks
echo "🔧 Setting up git hooks..."
npx husky install
npx husky add .git/hooks/commit-msg 'npx --no -- commitlint --edit "$1"'

# Create sample files if they don't exist
if [ ! -f main.tex ]; then
    echo "📄 Creating sample main.tex..."
    cat > main.tex << 'EOF'
\documentclass{article}
\usepackage{hyperref}

\title{My Document}
\author{Author Name}
\date{\today}

\begin{document}
\maketitle

\section{Introduction}
This is a sample document with semantic versioning.

\bibliographystyle{plain}
\bibliography{references}

\end{document}
EOF
fi

if [ ! -f references.bib ]; then
    echo "📄 Creating sample references.bib..."
    cat > references.bib << 'EOF'
@article{sample2024,
  title={Sample Article},
  author={Author, A.},
  journal={Journal Name},
  year={2024}
}
EOF
fi

# Final instructions
echo ""
echo "=================================================="
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "📝 Next steps:"
echo ""
echo "1. Test the build:"
echo "   npm run build"
echo ""
echo "2. Make your first conventional commit:"
echo "   git add ."
echo "   git commit -m \"feat: initial semantic release setup\""
echo ""
echo "3. Push to trigger automatic release:"
echo "   git push origin main"
echo ""
echo "📚 Commit message format:"
echo "   feat: new feature → minor version bump"
echo "   fix: bug fix → patch version bump"
echo "   feat!: breaking change → major version bump"
echo ""
echo "🔍 For more info, see README.md"
echo "=================================================="

# Offer to create initial commit
echo ""
read -p "Create initial commit? (y/N) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git add .
    git commit -m "feat: add semantic release for LaTeX documents

- Automated versioning based on commits
- PDF and diff generation
- GitHub releases with assets
- Changelog generation"
    echo -e "${GREEN}✅ Initial commit created!${NC}"
    echo "Push to GitHub to trigger the first release:"
    echo "  git push origin main"
fi
