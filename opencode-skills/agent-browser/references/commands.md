# Command Index

> **Do not treat this file as the command reference.** As of agent-browser
> 0.39.x the authoritative, version-matched references are:

```bash
agent-browser --help                    # full command + flag reference
agent-browser <command> --help          # per-command details
agent-browser skills get core --full    # version-matched usage guide + templates
```

Why: this file used to duplicate the full 0.27.0 command list and rotted on
every CLI upgrade. The CLI help and built-in skills always match your
installed version. This index only maps *tasks* to *commands*.

## Task → Command Map

| Task | Start with |
|------|-----------|
| Navigate / interact | `open`, `click`, `fill`, `type`, `press`, `select`, `check`, `hover`, `scroll`, `drag`, `upload`, `download` |
| Read the page | `snapshot [-i]`, `read`, `get text/html/value/attr/title/url/count/box/styles` |
| Verify state | `is visible/enabled/checked`, `get url`, `wait --text/--url/--load/--fn` |
| Locate stubborn elements | `find role/text/label/placeholder/testid/first/last/nth` |
| Screenshots / PDF | `screenshot [--full/--annotate]`, `pdf` |
| Visual / URL diffs | `diff snapshot`, `diff screenshot --baseline <img>`, `diff url <u1> <u2>` |
| Cookies / storage | `cookies get/set/clear`, `cookies set --curl <file>`, `storage local/session` |
| Network mocking / inspection | `network route/unroute/requests/har` |
| Emulation | `set viewport/device/geo/offline/headers/credentials/media` |
| Tabs / iframes / frames | `tab`, `frame` |
| Debugging | `console`, `errors`, `highlight`, `inspect`, `trace start/stop`, `profiler start/stop` |
| Recording | `record start/stop` (`.webm`/`.mp4`) |
| Performance / a11y | `vitals`, `a11y` |
| React introspection | `react tree/inspect/renders/suspense` (needs `--enable react-devtools`) |
| SPA navigation | `pushstate <url>` |
| Sessions / auth | `session id/info/list`, `auth save/login/list/show/delete`, `--restore`, `--state` |
| Bulk work | `batch [--bail] "cmd" "cmd"` |
| Live streaming | `stream enable/disable/status` |
| Cloud / alternative browsers | `-p ios/browserbase/browserless/agentcore/...`, `--engine lightpanda/obscura` |
| AI chat mode | `chat "instruction"` (needs `AI_GATEWAY_API_KEY`) |
| Observability | `dashboard start/stop` |
| Maintenance | `install`, `upgrade`, `doctor [--fix]`, `skills list/get/path` |

## Historical note

Version 0.27.0 → 0.39.1 additions captured in the map above: `read`, `is`,
`download`, `pdf`, `mouse`, `set`, `storage`, `diff`, `a11y`, `batch`,
`stream`, `chat`, `dashboard`, `plugin`, `confirm/deny`, `connect`,
`upgrade`, `session`, `mcp`, webmcp, trace/profiler, iOS provider,
`--pin-tab`, `--allowed-domains`, `--engine`, config-file support, and the
`--restore` family replacing legacy `--session-name`.
