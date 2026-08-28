# Failure Mode Test Report — frontend-design-orchestrator (Iteration 1, Round 1)

**Tester**: 辛特助 (阿辛)
**Date**: 2026-08-03
**Skill version tested**: SKILL.md with new §"Failure Handling（失败模式与兜底）" section (lines 255–289)
**Scope**: Guidance clarity test only. No DESIGN.md produced. No skill files modified.

---

## Failure Mode A — Ambiguous intent (2+ workflow match)

**User prompt under test**:
> "帮我 review 一下这个 dashboard 的设计，顺便让它看起来像 Linear 的风格"

**Workflows matched**: 2
1. **Tertiary Workflow — Design Review** (triggered by "review 一下这个 dashboard 的设计")
2. **Primary Workflow — Generate DESIGN.md, Style Reference variant** (triggered by "看起来像 Linear 的风格" — a Style Reference per Primary Workflow Step 1, lines 30–32)

### Rule quote (verbatim from SKILL.md, lines 261–263)

From the Failure Handling table, Section 1 "Ambiguous intent → route correctly", Row 1:

> | User request matches 2+ workflows (e.g. "review my design and make it look like Linear") | Ask ONE clarifying question: "Do you want a design REVIEW first, or a new spec with Linear-style guidance?" | Default to Primary workflow (generate spec) — it produces the most actionable output |

### Action taken per the rule

Applied the **first-line fix**:

Output a single clarifying question, copying the skill's template verbatim:

> "Do you want a design REVIEW of the existing dashboard first, or a new spec with Linear-style guidance?"

**PAUSE** here, per Junior Designer Mode (SKILL.md line 46: "Wait for user confirmation before Step 4").

If the user does not disambiguate, the **fallback** rule applies: default to the Primary Workflow. That means:
- Treat "Linear" as a Style Reference (vibe, layout, interaction only — no hex/logo scraping per line 31)
- Treat the existing dashboard as observed context for the spec, even if no file/URL is provided (caveat below)

### Was the guidance clear and actionable?

**Mostly yes.** The rule provides:
- A canonical example sentence that maps directly onto the test prompt ("review my design and make it look like Linear")
- A copy-paste-ready clarifying question
- A deterministic default if the user is silent

### Gaps identified

1. **No timeout/wait guidance.** The rule says "ask one question and pause" but does not specify how long to wait. In an interactive session, a non-responsive user could stall the agent indefinitely. **Severity: minor** — operationally awkward, not blocking.
2. **The fallback (Primary Workflow) still has hidden ambiguity.** If the user fails to disambiguate AND the dashboard is not attached, the default-to-Primary path proceeds without an observed source of truth. Linear becomes the sole design input. The rule does not flag this residual gap. **Severity: moderate** — produces a valid but decontextualized spec.
3. **No explicit "also check if the dashboard is attached" step.** The Tertiary Workflow's Step 1 (line 59) is "Load Document." If the user's first prompt includes "review this dashboard" with no attachment, the clarifying question should *also* ask for the file/URL. The current rule's question template does not include this. **Severity: moderate** — easy to fix in the next iteration.

---

## Failure Mode B — Missing brand assets (Specific Brand route, no inputs)

**User prompt under test**:
> "按照我们公司的品牌规范给我出一个 landing page 的设计规范"
> Follow-up: "Do you have brand guidelines, a repo, or a canonical URL?" → "没有，就是类似 Apple 那种干净的风格"

**Original route**: Specific Brand (Primary Workflow Step 2, lines 33–42 — Brand Asset Protocol is MANDATORY).
**Reality**: User has no guidelines, no repo, no URL, no canonical site. They have only a vibe reference (Apple).

### Rule quote (verbatim from SKILL.md, line 270)

From the Failure Handling table, Section 2 "Missing assets → degrade, don't invent", Row 1:

> | **Specific Brand** route: user has no guidelines / repo / canonical URL | Switch to **Style Reference** route; document the switch in the DESIGN.md assumptions section | Ask for ONE reference product ("Which product's design do you admire?") and use it as vibe source only |

### Action taken per the rule

Applied the **first-line fix — route switch + document**:

1. **Route switch**: Specific Brand → Style Reference. The user's "Apple" mention becomes the Style Reference.
2. **Document the switch in the assumptions section** of the upcoming Drafting block (Junior Designer Mode, lines 43–46). Stated text:
   > "Assumption: User originally requested a Specific Brand route ('公司品牌规范') but confirmed no guidelines / repo / canonical URL are available. Per Failure Handling §2, switched to Style Reference route using Apple as the vibe source. Constraint: vibe, layout patterns, and interaction style only — no hex codes, no logo, no proprietary assets extracted (per Primary Workflow Step 1, lines 30–32). All brand-derived tokens will be labeled `Confidence: LOW` (per Step 4)."

3. **Continue with Primary Workflow** from Step 3 (Junior Designer Mode drafting), now operating in Style Reference mode.

**Did NOT ask "which product do you admire?"** — because the user already volunteered one (Apple). The fallback question would only fire if the user had no reference at all either. The skill's rule does not state this explicitly, but it is the only reading consistent with "don't ask what was just answered."

### Was the guidance clear and actionable?

**Yes.** The rule provides:
- A precise trigger condition ("user has no guidelines / repo / canonical URL")
- A deterministic route switch (Specific Brand → Style Reference)
- A documentation requirement (write into assumptions)
- A fallback for the next failure mode (no reference product either)
- A discipline constraint ("vibe source only") that prevents the highest-risk anti-pattern in this scenario: scraping Apple's actual hex values

### Gaps identified

1. **Rule does not say "use the user's volunteered reference without re-asking."** The fallback line ("Ask for ONE reference product") could be misread as mandatory in every case. An agent could re-ask "which product do you admire?" after the user just said "Apple." **Severity: minor** — recoverable from context, but adds friction.
2. **Rule does not call out the "well-known brand" trap.** Apple HIG is publicly documented. The "vibe source only" constraint is the right discipline, but the rule should explicitly state: "A well-known reference brand is still Style Reference — never extract the reference's actual design tokens." **Severity: moderate** — the most likely real-world failure mode this rule needs to prevent.
3. **Documentation timing is implicit.** The rule says "document the switch in the DESIGN.md assumptions section," but the assumptions section is created at Step 3 of the Primary Workflow. If the agent is in early clarification, it must remember to surface the switch at the right time. Not a contradiction, but the rule could be tightened: "Document the switch in the FIRST Drafting block." **Severity: minor.**

---

## Cross-cutting observations

- The Failure Handling section is **composable**: both test cases use the table format, both first-line fixes are non-destructive (route switch, clarifying question), and the fallbacks degrade to "default" rather than "fail."
- The section's opening principle (line 257) is operationalized cleanly: "When execution hits a wall, escalate BEFORE guessing. Every workflow has a fallback." Both test cases follow this discipline.
- The "Escalation rule" at line 289 ("STOP and report — never fabricate brand data, URLs, or repo contents") would have been a third line of defense if my first-line fixes had failed. It is correctly placed and unambiguous.

## Verdict on the new section

The Failure Handling section **passes** both tests as a guidance document. The two matched rules were findable, quotable, and actionable. Identified gaps are improvements for the next iteration, not failures in the current version.

**Recommended improvements for iteration 2** (in priority order):
1. Add a "well-known reference brand" clause to §2 row 1 fallback to lock down the Apple/Linear/Vercel extraction trap.
2. In §1 row 1, expand the clarifying-question template to also ask for the design asset (file/URL/screenshot) when the user's request implies review.
3. Add a default wait-timeout or "ask once, then default" rule to §1 row 1.
4. Make explicit: if the user has already volunteered a reference product in the same prompt, skip the "ask for one" fallback.

---

*End of report.*
