1. Reframe Hotpass as “research-first”, not just “refine spreadsheets”

Hotpass today says: “refines messy spreadsheets into a governed single source of truth” and points to profiles, GE, POPIA, Prefect, OTEL, and a Streamlit dashboard. That’s already a structured, observable pipeline. We just need to teach that pipeline to: 1. run adaptive research loops, 2. do relationship/identity reasoning, 3. decide when to stop, and 4. let agents drive the whole thing. ￼

So: no second repo, no bolt-on integration — only new packages under src/hotpass/... that are called from the existing CLI (uv run hotpass ...) and exposed via your existing AGENTS.md. ￼

⸻

2. Build an Adaptive Research Orchestrator inside Hotpass

Add a new module, e.g. src/hotpass/research/orchestrator.py, that runs this exact sequence: 1. Local/authority pass
• Look in ./data, ./dist, and historical runs for the same entity.
• Hit any authority/registry/directories defined in the profile (this is important because the current README already says “configurable profiles tailor validation rules, mappings, and terminology to your sector”; we just extend the schema to include authority_sources:). ￼ 2. OSS-first web extraction
• Try OSS tools first (Playwright headless → trafilatura/readability-lxml → unstructured/pdfplumber) to get page content, not Firecrawl. That keeps you vendor-neutral and OSS-first. (We just added this to your UPGRADE.md.)
• Only if this fails → go to 3. 3. Hotpass Native Crawl (Scrapy + Playwright)
• Run a first-party crawler built into Hotpass using Scrapy (focused spider, domain-limited) with a per-domain concurrency cap. Scrapy is OSS, Python, and built for focused/broad crawls. citeturn0search12turn0search18
• When the target is JavaScript-heavy, route requests through Playwright via scrapy-playwright or an equivalent Playwright middleware so pages are rendered before extraction. This is the current, actively maintained pattern for JS-heavy sites. citeturn0search1turn0search2
• Apply time-/scope-limits so the crawler does not DOS a site; emit crawl status and warnings back to the orchestrator so the UI and agents can show progress.
• If the crawler hits robots.txt, 429, or anti-bot signals, drop back to OSS deterministic extraction and mark the attempt in provenance.
• If the native crawler reports robots/limits → drop back to OSS again. 4. Backfill pass
• If field still null or fails GE → mark as backfillable (the profile says which fields can be backfilled), and run the above again with a looser goal.
• Write full provenance (source, method, timestamp, confidence) to the row. 5. Stop condition
• Only after all 4 steps fail → return low confidence.

That whole thing lives in Hotpass, not in a side project.

⸻

3. Add relationship / entity mapping right in Hotpass

You wanted intelligent relationship mapping and deductive techniques. We can do that with OSS tools.
• Add src/hotpass/identity/graph.py that:
• builds a mini entity graph from current dataset + authority lookups,
• adds nodes/edges when the native crawler or the OSS fetchers find “parent company”, “training centre”, “campus”, “licence #…”.
• For disambiguation, call Splink (UK MoJ is literally using Splink in production for fast, probabilistic record linkage). Splink is OSS, Pythonic, and 2025 versions are fast enough to run on batch/linkage workloads. ￼
• Feed that result back to the research orchestrator so it can say: “we didn’t find this school, but three linked entities all say the phone number is X → confidence ↑”.
• Wire all this through profiles so a profile can say:

identity:
match_on: [name, licence_number, geo]
resolver: splink
backfill_from_related: true

This keeps the “profile-driven” promise in your README. ￼

⸻

4. Agent-native control, using only Hotpass’ own CLI + MCP

You already have AGENTS.md in the repo. Use it. ￼

Add/ensure these MCP tools (all wrappers around your CLI):
• hotpass.refine
• hotpass.enrich (now calls the adaptive research orchestrator above)
• hotpass.plan.research (new)
• hotpass.explain_provenance
• hotpass.qa
and log them to ./.hotpass/mcp-audit.log (we added that hardening step) so operators can see what the agents are doing.

Then, add rate-limited fetchers:
• For every remote step, wrap it with Prefect 3’s concurrency/rate limit blocks so even “autopilot” runs can’t hammer remote sites or the Playwright pool.
• Use crawler job status (Scrapy signals / your own job store) to back off or queue when you see 429/5xx or robots.txt denials; surface these in the Streamlit dashboard for operators.

This gives you: “agents can control everything, but they can’t burn our credits”.

⸻

5. UI: live spreadsheet, human-in-the-loop, using what you have

Your README already says: “Streamlit dashboard” as one of the surfaces. Great — keep that. But add a grid. ￼
• Mount AG Grid or Handsontable inside Streamlit (both have Streamlit wrappers; Handsontable 15 has better Excel-like editing). That’s OSS-aligned. ￼
• Stream rows as they’re refined/enriched:
• Grey = pending
• Green = refined
• Blue = refined + local research
• Orange = refined + remote research
• Red = backfilled / low confidence
• Add a “Run adaptive research again” button per row → calls hotpass.plan.research with a bigger budget.
• Show crawler warnings (if any) inline for transparency — thanks to the better status.
• Keep human-in-the-loop by requiring approval for:
• overwriting user-edited cells,
• switching allow_network from false to true,
• merging entities when Splink score is below, say, 0.92. (This matches the UK MoJ guidance to keep humans in the loop for borderline matches.) ￼

No watercrawl needed — it’s all Hotpass + OSS.

⸻

6. Exports

Add to your CLI (and MCP mirror):

uv run hotpass refine ... --export xlsx,csv,pipe
uv run hotpass enrich ... --export xlsx,csv,pipe

Internally:
• .xlsx → pandas + openpyxl
• .csv → df.to_csv(index=False)
• pipe-delimited → df.to_csv(sep="|", index=False)

This is totally consistent with the existing CLI pattern in README. ￼

⸻

7. Final frontier-grade guarantees (Hotpass-only)
   1. Single system of record: everything is in this repo — profiles, orchestrator, identity graph, MCP server. No watercrawl. ￼
   2. Adaptive research: planner exhausts OSS → authority → Hotpass native crawl (Scrapy+Playwright) → relationship expansion before returning low confidence. (Scrapy is well suited for focused and broad crawls and scrapy-playwright handles JS-heavy sites.) citeturn0search12turn0search1
   3. Relationship-aware validation: Splink-style probabilistic linkage to raise/lower confidence across linked rows. ￼
   4. Agent-monitored: MCP tools are narrow, logged, rate-limited, and respect env flags.
   5. Human-in-the-loop UI: Streamlit + grid + provenance badges; operators can pause, fix, or re-run any row.
   6. OSS-first: trafilatura / Playwright / unstructured / Scrapy before any third-party crawler; Soda/dbt/whylogs alongside GE if you want to extend. (This is in your patched UPGRADE.md.)

