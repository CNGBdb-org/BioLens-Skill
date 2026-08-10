#!/usr/bin/env bash
# Flatten this cima/ skill package into an Agent skills directory.
# Agents expect: <dest>/<skill-name>/SKILL.md (one level under skills/).
#
# Usage (run from this directory):
#   ./install-to-agent.sh <destination-skills-dir>
#   ./install-to-agent.sh --agent <name> [project-root]
#   ./install-to-agent.sh --agent <name> --global
#
# Agent aliases (project-level unless --global):
#   cursor       -> <root>/.cursor/skills          | ~/.cursor/skills
#   claude       -> <root>/.claude/skills          | ~/.claude/skills
#   codex        -> <root>/.agents/skills          | ~/.codex/skills
#   antigravity  -> <root>/.agents/skills          | ~/.gemini/antigravity/skills
#   gemini       -> <root>/.agents/skills          | ~/.gemini/skills
#   opencode     -> <root>/.agents/skills          | ~/.config/opencode/skills
#   windsurf     -> <root>/.windsurf/skills        | ~/.codeium/windsurf/skills
#   copilot      -> <root>/.agents/skills          | ~/.copilot/skills
#
# Examples:
#   ./install-to-agent.sh --agent cursor
#   ./install-to-agent.sh --agent claude /path/to/project
#   ./install-to-agent.sh --agent cursor --global
#   ./install-to-agent.sh /path/to/project/.claude/skills
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"

usage() {
  sed -n '2,35p' "$0" | sed 's/^# \{0,1\}//'
  exit 2
}

resolve_agent_dest() {
  local agent="$1"
  local scope="$2"   # project | global
  local project="${3:-.}"
  case "$agent" in
    cursor)
      if [[ "$scope" == global ]]; then echo "$HOME/.cursor/skills"
      else echo "$project/.cursor/skills"; fi
      ;;
    claude|claude-code)
      if [[ "$scope" == global ]]; then echo "$HOME/.claude/skills"
      else echo "$project/.claude/skills"; fi
      ;;
    codex)
      if [[ "$scope" == global ]]; then echo "$HOME/.codex/skills"
      else echo "$project/.agents/skills"; fi
      ;;
    antigravity)
      if [[ "$scope" == global ]]; then echo "$HOME/.gemini/antigravity/skills"
      else echo "$project/.agents/skills"; fi
      ;;
    gemini|gemini-cli)
      if [[ "$scope" == global ]]; then echo "$HOME/.gemini/skills"
      else echo "$project/.agents/skills"; fi
      ;;
    opencode)
      if [[ "$scope" == global ]]; then echo "$HOME/.config/opencode/skills"
      else echo "$project/.agents/skills"; fi
      ;;
    windsurf)
      if [[ "$scope" == global ]]; then echo "$HOME/.codeium/windsurf/skills"
      else echo "$project/.windsurf/skills"; fi
      ;;
    copilot|github-copilot)
      if [[ "$scope" == global ]]; then echo "$HOME/.copilot/skills"
      else echo "$project/.agents/skills"; fi
      ;;
    *)
      echo "Unknown agent: $agent" >&2
      echo "Supported: cursor claude codex antigravity gemini opencode windsurf copilot" >&2
      exit 2
      ;;
  esac
}

DEST=""
AGENT=""
SCOPE="project"
PROJECT="."
POSITIONAL=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage ;;
    --agent|-a)
      [[ $# -ge 2 ]] || usage
      AGENT="$2"
      shift 2
      ;;
    --global|-g)
      SCOPE="global"
      shift
      ;;
    --project|-p)
      [[ $# -ge 2 ]] || usage
      PROJECT="$2"
      shift 2
      ;;
    --category|-c)
      # Compatibility no-op: this package is cima-only.
      [[ $# -ge 2 ]] || usage
      shift 2
      ;;
    -*)
      echo "Unknown option: $1" >&2
      usage
      ;;
    *)
      POSITIONAL+=("$1")
      shift
      ;;
  esac
done

if [[ -n "$AGENT" ]]; then
  if [[ ${#POSITIONAL[@]} -ge 1 ]]; then
    PROJECT="${POSITIONAL[0]}"
  fi
  DEST="$(resolve_agent_dest "$AGENT" "$SCOPE" "$(cd "$PROJECT" && pwd)")"
elif [[ ${#POSITIONAL[@]} -ge 1 ]]; then
  DEST="${POSITIONAL[0]}"
else
  usage
fi

mkdir -p "$DEST"

count=0
while IFS= read -r skill_md; do
  [[ -n "$skill_md" ]] || continue
  skill_dir="$(dirname "$skill_md")"
  name="$(basename "$skill_dir")"
  target="$DEST/$name"
  if [[ -e "$target" || -L "$target" ]]; then
    rm -rf "$target"
  fi
  ln -s "$skill_dir" "$target"
  echo "link $name -> $skill_dir"
  count=$((count + 1))
done < <(find "$ROOT" -mindepth 2 -maxdepth 2 -name SKILL.md | sort)

if [[ "$count" -eq 0 ]]; then
  echo "No SKILL.md found under $ROOT (expected <name>/SKILL.md)" >&2
  exit 1
fi

if [[ -f "$ROOT/requirements.txt" ]]; then
  dst="$DEST/requirements.txt"
  if [[ -e "$dst" || -L "$dst" ]]; then
    rm -rf "$dst"
  fi
  ln -s "$ROOT/requirements.txt" "$dst"
  echo "link requirements.txt"
fi

echo "Done. Linked $count skill(s) into $DEST"
