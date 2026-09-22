<p align="center">
  <a href="https://tracepath.dev"><strong>TracePath</strong></a>
</p>

<p align="center">
  <a href="https://github.com/bsisduck/skills/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License"></a>
  <a href="https://tracepath.dev/product/agent-skills"><img src="https://img.shields.io/badge/docs-agent--skills-7c3aed.svg" alt="Docs"></a>
  <a href="https://github.com/bsisduck/skills/actions"><img src="https://img.shields.io/github/actions/workflow/status/bsisduck/skills/ci.yml?branch=main" alt="CI"></a>
</p>

# TracePath Agent Skills

Agent skills that let AI coding agents (Claude Code, Cursor, and anything that reads SKILL.md) set up and operate [TracePath](https://tracepath.dev) observability: instrument a project, then debug production issues down to root cause.

TracePath is an open-source error tracking and observability platform — [self-host](https://docs.tracepath.dev/server/docker-compose) it or use [TracePath Cloud](https://cloud.tracepath.dev). Skills are plain Markdown, MIT-licensed, no marketplace lock-in.

> Source of truth: the skills live in the [`skills/` directory](https://github.com/bsisduck/tracepath/tree/main/skills) of the main [TracePath monorepo](https://github.com/bsisduck/tracepath) (where they are generated from CLI knowledge by `cli/tools/skillgen`). This repo mirrors them for standalone distribution and install.

## Skills

| Skill | Purpose |
|---|---|
| [`tracepath-setup`](skills/tracepath-setup/SKILL.md) | Analyze and instrument repositories for TracePath observability — plans the project map, creates projects via setup tokens, then integrates backends (OpenTelemetry), frontends (`@tracepath/*` SDKs), mobile and Kubernetes. Use when the user wants to add, migrate, or verify TracePath monitoring. |
| [`tracepath`](skills/tracepath/SKILL.md) | Operate a TracePath instance through the `tracepath` CLI — log in, query exceptions, logs, endpoints and metrics, debug production issues to root cause, and diagnose latency. Invoke as `/tracepath <subcommand>`. |

The `tracepath-setup` skill ships with companion reference files it reads at runtime: [`frontend-js.md`](skills/tracepath-setup/frontend-js.md), [`ai-agent.md`](skills/tracepath-setup/ai-agent.md), [`data-model.md`](skills/tracepath-setup/data-model.md), [`performance.md`](skills/tracepath/performance.md), [`kubernetes.md`](skills/tracepath-setup/kubernetes.md), [`flutter.md`](skills/tracepath-setup/flutter.md), [`android.md`](skills/tracepath-setup/android.md), [`ios.md`](skills/tracepath-setup/ios.md), [`dashboard-project-setup.md`](skills/tracepath-setup/dashboard-project-setup.md).

## Install

### Claude Code (plugin marketplace)

This repo is a `.claude-plugin` marketplace. Add it and install the `tracepath` plugin (both skills bundled as one plugin):

```
/plugin marketplace add bsisduck/skills
/plugin install tracepath@bsisduck-skills
```

Or add the marketplace path to `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "tracepath": {
      "source": "github",
      "repo": "bsisduck/skills"
    }
  }
}
```

### Manual (any agent that reads SKILL.md)

Copy (or symlink) the skill directories into your agent's skills folder:

```bash
git clone https://github.com/bsisduck/skills.git
mkdir -p ~/.claude/skills
cp -r skills/tracepath skills/tracepath-setup ~/.claude/skills/
```

For Cursor and other tools, point your skills directory at the clone, or copy individual `SKILL.md` files where your tool reads them.

## Validate locally

```bash
# frontmatter + companion-file references in every SKILL.md
python3 .github/scripts/validate_frontmatter.py

# markdown link lint (pinned to a compatible version)
npx markdown-link-check@3.13.0 --config .github/markdown-link-check.json skills/*/SKILL.md
```

## Repository layout

```
skills/
├── skills/
│   ├── tracepath-setup/     # instrumentation + setup skill (+ reference docs)
│   └── tracepath/           # CLI operation / debugging skill (+ performance.md)
├── .claude-plugin/          # plugin + marketplace manifests
├── .github/workflows/ci.yml # lint: YAML, frontmatter, markdown checks
├── marketplace.json         # (see .claude-plugin/)
└── LICENSE
```

## Links

- [TracePath](https://tracepath.dev) — main product site
- [Documentation](https://docs.tracepath.dev)
- [Main monorepo](https://github.com/bsisduck/tracepath)
- [js-client SDKs](https://github.com/bsisduck/js-client)
- [OTel Agent](https://github.com/bsisduck/tracepath-otel-agent)

## License

MIT — see [LICENSE](LICENSE). Upstream work © dusanstanojeviccs (Traceway).

## Contributing

`main` is protected: all changes go through pull requests. README changes, new skills and doc fixes welcome via PR; CI (frontmatter + manifest + link checks) must pass.
