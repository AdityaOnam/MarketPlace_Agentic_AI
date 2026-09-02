# Audit report schema

The entrypoint emits exactly one JSON object. Fields marked **required** are
the contest floor; the rest are this marketplace's additions.

## Top level

| Field | Type | Req | Notes |
|---|---|---|---|
| `site` | string | ✅ | Bare host, e.g. `example.com`. No scheme, no trailing slash. |
| `audited_at` | string | ✅ | UTC ISO-8601 with `Z`, e.g. `2026-09-20T14:32:00Z`. |
| `summary` | object | ✅ | Counts by severity. |
| `findings` | array | ✅ | May be empty. Never `null`. |
| `scope` | object | — | What was actually inspected — makes evidence auditable. |

### `summary`

| Field | Type | Req |
|---|---|---|
| `total_findings` | int | ✅ |
| `critical` / `high` / `medium` / `low` / `info` | int | ✅ (may be `0`) |

Invariant: the five severity counts must sum to `total_findings`.

### `scope` (recommended)

```json
"scope": {
  "pages_crawled": 8,
  "urls": ["https://example.com/", "https://example.com/about"],
  "robots_respected": true,
  "checks_run": ["crawl-access", "structured-data", "entity", "engagement"],
  "checks_not_assessed": [],
  "duration_seconds": 41
}
```

## A finding

| Field | Type | Req | Notes |
|---|---|---|---|
| `id` | string | ✅ | `F-001`, sequential in final sort order. |
| `title` | string | ✅ | What is wrong, in plain language. No jargon-only titles. |
| `severity` | enum | ✅ | `critical` \| `high` \| `medium` \| `low` \| `info` |
| `evidence` | string | ✅ | **Observed facts only** — counts, URLs, status codes, quoted markup. Never a restatement of the title. |
| `suggested_action` | object | ✅ | See below. |
| `category` | enum | — | `discoverability` \| `engagement` |
| `check_id` | string | — | Stable id of the check that fired, e.g. `CR-04`. |
| `confidence` | enum | — | `high` \| `medium` \| `low` |
| `affected_urls` | string[] | — | Up to 5 concrete examples. |
| `proactive` | bool | — | `true` = recommendation without a detected defect. |

### `suggested_action`

| Field | Type | Req | Notes |
|---|---|---|---|
| `summary` | string | ✅ | One sentence: what to change. |
| `priority` | enum | ✅ | `critical` \| `high` \| `medium` \| `low` |
| `mechanism` | string | — | *Why* this fixes it — the causal chain. |
| `steps` | string[] | — | Concrete, ordered, copy-pasteable where possible. |
| `effort` | enum | — | `low` \| `medium` \| `high` |
| `verify` | string | — | How the owner confirms the fix worked. |

## Evidence rules

Evidence is the difference between an audit and a guess.

- ✅ `"7/8 sampled pages returned 200 but rendered <100 words without JS; /pricing had 41 words in raw HTML vs 612 after render."`
- ❌ `"The site relies too heavily on JavaScript."` — no observation.
- If a check could not run, do **not** invent a finding. Add the check to
  `scope.checks_not_assessed` instead.

## Full example

```json
{
  "site": "example.com",
  "audited_at": "2026-09-20T14:32:00Z",
  "scope": {
    "pages_crawled": 8,
    "robots_respected": true,
    "checks_not_assessed": [],
    "duration_seconds": 44
  },
  "summary": {
    "total_findings": 3,
    "critical": 0, "high": 1, "medium": 1, "low": 0, "info": 1
  },
  "findings": [
    {
      "id": "F-001",
      "check_id": "SD-01",
      "category": "discoverability",
      "title": "No structured data anywhere on the site",
      "severity": "high",
      "confidence": "high",
      "evidence": "8/8 sampled pages contain zero <script type=\"application/ld+json\"> blocks and no microdata/RDFa attributes. Sampled: /, /about, /pricing, /contact, /blog.",
      "affected_urls": ["https://example.com/", "https://example.com/pricing"],
      "suggested_action": {
        "summary": "Add Organization JSON-LD sitewide and a page-type schema on each template.",
        "priority": "high",
        "mechanism": "Assistants extract entity attributes from typed key/value markup far more reliably than from prose. Without it, name, logo, and sameAs links must be inferred, so the brand is often skipped or conflated with a similarly named entity.",
        "steps": [
          "Add one Organization block in the sitewide <head> with name, url, logo, description and sameAs[] pointing to official social/Wikidata profiles.",
          "Add Product/Offer on product templates, Article on posts, FAQPage on FAQs.",
          "Keep every value identical to the visible on-page text.",
          "Validate with Google's Rich Results Test and schema.org validator."
        ],
        "effort": "medium",
        "verify": "Re-fetch each template; each returns >=1 valid JSON-LD block that parses and matches visible copy."
      }
    }
  ]
}
```
