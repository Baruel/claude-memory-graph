---
name: claude-memory-graph
description: Visualize Claude Code's memories as an interactive graph. Builds one self-contained HTML file from every memory in ~/.claude/projects/*/memory, grouped by workspace, with [[links]] as edges, search, type filters and a detail panel. Use when the user asks to see, visualize, map or graph their Claude memories, wants to know what Claude remembers about them or their projects, or wants to refresh the graph after editing or cleaning up memories.
---

# Claude memory graph

The skill draws an interactive map of everything Claude Code remembers, across every project. Each memory is a node. Memories cluster around their project, and projects sit inside workspace regions. `[[links]]` between memories become edges.

## Build

Run the builder that sits next to this file (Python 3.8+, stdlib only):

```bash
python3 -I <this skill's directory>/build.py <output.html>
```

For a typical install that is:

```bash
python3 -I ~/.claude/skills/claude-memory-graph/build.py ~/claude-memory-graph.html
```

- If the user named an output path, use theirs. Otherwise pick a place they can easily open, and tell them the full path.
- Options: `--root` points at a different projects dir (by default `$CLAUDE_CONFIG_DIR/projects` or `~/.claude/projects`). `--home` sets the home path used to shorten labels.
- The builder prints `N memories, N links, N dangling, N projects, N workspaces -> path`. Report those numbers.
- It asserts that node ids are unique and that every edge points at a real node. If an assertion fails, report the error. Don't hand over a broken file.

Open the file in a browser for the user if your environment allows it (`open` on macOS, `xdg-open` on Linux). If a sandbox blocks that, give them the command to run.

## How it reads memories

- **Nodes:** every `*.md` in each `<projects>/<dir>/memory/` except `MEMORY.md`. Temporary session dirs (`-private-…`, `-tmp-…`, `-var-folders-…`) are skipped.
- **Fields:** frontmatter `name`, `description` and `type`, whether top-level or nested under `metadata:`. A missing `type` shows as `unknown`.
- **Edges:** `[[target]]` in a memory's body. A link resolves by `name`, then by filename, and prefers the same project. Links that don't resolve are counted as "dangling".
- **Projects:** a dir's name is its working directory with every non-alphanumeric character replaced by `-`. The builder strips the home prefix and one container folder (`Projects`, `code`, `src`, `repos`, …), so `-Users-ana-Projects-acme-api` becomes `acme-api`. The home dir itself is `home`.
- **Workspaces:** a project joins the workspace of the shortest other project whose label prefixes it at a `-`, so `acme-api` and `acme-web` both join `acme`. Projects with no parent dir form their own workspace.

## Using the page

- Hover a node for its name and date. Click one for its description, file path and links in both directions.
- Search opens a results list in the side panel, grouped by workspace and showing a snippet of each description. Enter opens the first result. Clicking a result centers it and shows its details, with "← results" to go back.
- The theme menu offers Auto (follows the system light/dark setting), Paper, Ink, Blueprint, Neon and Print. The choice is remembered in that browser.
- The type chips toggle memory types.
- Click a workspace or project in the legend to toggle it. Alt-click shows only that one.
- Drag to pan, scroll to zoom, and drag nodes to move them. Esc closes the panel.

## Rules

- The page is read-only and never changes memories.
- The HTML embeds every memory's name and description. Tell the user that before they share it, and never commit it to a public repo.
- The output is a single offline file with no network requests. Keep it that way if you change the template.
- To add a theme, add a `:root[data-theme="…"]` token block to the template's CSS and an entry to its `THEMES` array. The canvas reads the same tokens.
