# Corpus selection rule and seal declaration

Written **2026-09-04, before any site was audited**, per `PLAN.md` §10 Stage A′. Its
purpose is to fix the selection rule in place while it is still impossible for a result to
influence it.

D-017 cut the pinned sampling frames (Tranco, Common Crawl) as bureaucracy at n=54. The
honest replacement is not a smaller frame — it is writing down the rule and admitting what
it costs, which is what this file is.

## What the sample is, and is not

The corpus is **hand-picked under the rule below**. It is not a random draw from a frame.
Therefore every number computed from it estimates performance **on a sample we chose**, and
none of them is a population rate. That sentence is attached to the numbers wherever they
are reported, not stored here.

## Selection rule

1. **Archetype is the primary stratum**, because `archetype` is an input to the suppression
   rules — a wrong label activates guards written for a different kind of site, so its
   errors propagate rather than staying local. Dev is 4 per archetype; held-out is 2 per
   archetype.
2. **Popularity is the secondary stratum**, recorded per row as head / mid / tail, balanced
   within archetype but not enforced.
3. **A site is eligible only if the audit can do its work on it**, per `OFFICIALS-QA.md`
   §2.2 — the graders committed to using sites that do not block the agent, so a site that
   blocks is not representative of the grading condition. A blocking site is **rejected and
   logged**, never worked around: no UA spoofing, no retry around a 403.
4. **Bias is declared, not corrected.** The candidate pool skews toward sites this project's
   authors already know, which skews toward technically well-built ones. The visible
   consequence is that **measured recall will be optimistic if defects are rarer here than
   on the open web, and measured precision pessimistic if these sites are cleaner than
   average**. Recorded here rather than argued away.
5. **Language and geography quotas** (`CORPUS.md` §1): dev carries 5 non-English sites
   across 3 languages including one non-Latin script (Japanese). This meets the ≥2-language
   and ≥1-non-Latin-script floors and is one short of nothing — the 60-site version's ≥12
   was scaled down with the corpus.

## Negative-control construction

15 sites, 2 per dimension across the 7 check families with the most false-positive
exposure, plus one spare on `offsite_identity`. Each row names the dimension it is curated
clean on and why.

**This set is a screen, not a measurement** (`EVALS.md` §3). It reports counts. A firing
*inside* a site's curated dimension is a hard defect; a firing *outside* it is an
unlabelled finding and goes to the adjudication queue, because these sites were never
verified clean on anything else.

**A row is curated only on evidence that was fetched, never on reputation.** D-020 is the
reason: two of the original 12 rows were written from an assumption about a well-known
site's markup, and one of them had zero JSON-LD at all. So the construction rule for a
dimension is: fetch the homepage first, read the specific evidence the dimension's checks
read, and only then write the row. A candidate that cannot be verified that way is rejected
and logged below, not softened into a weaker `why_clean` string.

`offsite_identity` (added 2026-09-04, **D-026**) is the seventh dimension: `CHK-D-025`
(no declared anchors), `CHK-D-026` (declared anchors that don't resolve), `CHK-D-027`
(self-inconsistent identity attributes). Its two rows were selected by pre-screening
candidate homepages for an `Organization`/`Corporation` JSON-LD block carrying a non-empty
`sameAs`, then running the full live audit and reading `anchors.results[]` before the row
was written. The pre-screen is the load-bearing step. **14 well-known candidates were
probed; 3 were unreachable, 8 of the 11 remaining declared no `sameAs` anywhere on the
homepage, and 3 qualified.** The eight negatives include sites any reputation-based
curation would have picked without checking: `www.theguardian.com`, `www.redhat.com`,
`www.khanacademy.org` and `www.nature.com` emit no `application/ld+json` on the homepage
at all, and `www.bbc.co.uk`, `www.wired.com` and `www.britannica.com` emit a block with no
anchors in it. The dimension is scarcer in the wild than its name suggests — worth knowing
before `CHK-D-025`'s firing rate on the dev corpus is interpreted, and a second
demonstration of D-020's lesson at a 8-in-11 rate.

All three qualifying candidates were kept, making this the one dimension with a spare:
`stripe.com` (12 declared anchors incl. Wikipedia, Wikidata and Crunchbase — one, Crunchbase,
403s to `resolved: null`), `about.gitlab.com` (Wikipedia plus six official social profiles,
6/6 resolve 200) and `www.docker.com` (GitHub plus five social profiles in `sameAs`, plus two
outbound profile links the collector picked up; 8/8 resolve 200). Docker is the weakest of
the three as a *knowledge-base* anchor case — it declares no Wikipedia or Wikidata entry —
which is exactly why it is useful as the spare: if one of the other two rows has to be
retired, the dimension still has a row whose anchors all resolve, and `CHK-D-025`'s low bar
(any one resolvable anchor passes) is what it is meant to test.

## Held-out seal

`harness/corpus/heldout.csv` was written on **2026-09-04, before the harness had produced a
single result**, and is sealed until Stage F.

- **3 looks total**, logged in `holdout-log.md`.
- Any inspection beyond the aggregate metric converts that site to dev, permanently.
- **Held-out is excluded from the Stage B′ archetype-accuracy pass.** `CORPUS.md` §6 said
  "all 54 sites"; that would have spent a look before the set was ever used for its
  purpose. B′ runs on dev + negative + adversarial (42 sites). Corrected in `CORPUS.md`.

Sealing before the harness exists is the only defence available against the failure mode a
hand-picked held-out set is prone to: choosing, without meaning to, the sites we expect to
do well on. It cannot be argued away afterwards, only pre-empted.

## Rejection log

Sites removed from the candidate pool, with the reason. Populated as runs discover them —
a site is rejected only on observed behaviour, never on expectation.

| Site | Set | Reason |
| --- | --- | --- |
| `www.theguardian.com` | negative (`offsite_identity`) | Homepage renders 0 `application/ld+json` blocks. No declared anchors to be clean on |
| `www.redhat.com` | negative (`offsite_identity`) | Same — 0 JSON-LD blocks on the homepage after redirect to `/en` |
| `www.nature.com` | negative (`offsite_identity`) | Same — 0 JSON-LD blocks |
| `www.khanacademy.org` | negative (`offsite_identity`) | Same — 0 JSON-LD blocks |
| `www.bbc.co.uk` | negative (`offsite_identity`) | One `CollectionPage` block, no `sameAs`, no Organization entity |
| `www.wired.com` | negative (`offsite_identity`) | `Organization` + `WebSite` blocks present, `sameAs` absent from both |
| `www.britannica.com` | negative (`offsite_identity`) | One `WebSite` block with no `name` and no `sameAs` |
| `www.rei.com` | negative (`offsite_identity`) | 403 to the harness UA. Rule 3: a blocking site is rejected, never worked around |
| `www.mayoclinic.org` | negative (`offsite_identity`) | 403 to the harness UA. Rule 3 |
| `www.patagonia.com` | negative (`offsite_identity`) | Homepage returns 404 to the harness UA |
| `www.ted.com` | negative (`offsite_identity`) | Connection failed at the transport layer; no status returned |
| `gitlab.com` | negative (`offsite_identity`) | Not a rejection of the site — it redirects cross-host to `about.gitlab.com`, which is the row that was added instead |
