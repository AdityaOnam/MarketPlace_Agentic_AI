"""page_type and archetype labelling. Reference: procedure.md §3 tables.

Public functions: `classify_page_type(url, title, json_ld_types)`,
`classify_archetype(pages, inventory, hints=None) -> (label, confidence)` and
`classify_archetype_detailed(...)`, which also returns the evidence that decided it.

Why this replaced the first version (2026-09-12, D-035). An 84-site run against the shipped classifier returned `unknown`
for 51 sites and `brochure` for 28 -- and most of those 28 were wrong (ebay.com, etsy.com,
booking.com are not five-page brochure sites). The shipped rules read only the
inventory's page_type proportions, so when discovery was starved they had nothing to
read, and the `total <= 5 -> brochure` fallback turned "we barely looked" into a label.

Design: additive evidence, not a rule cascade
--------------------------------------------
A first-match cascade decides by *ordering*: whichever rule sits earlier wins no matter
how much contrary evidence sits later. A blind 40-site hold-out showed exactly that (a
shop with a blog became news because the news rule came first; a personal blog became
news because the personal rule came last). So each archetype now accumulates weighted
evidence from five independent families, counter-evidence subtracts, and the top score
wins only with a margin (`_Evidence`, `_decide`):

  identity     4-6  who runs the site: org JSON-LD types on home/about, TLD, commerce or
                    docs platform generators, docs./wiki hosts, Person with no Organization
  structure    <=4  what the inventory is made of -- proportions on the *inventory*
                    (discovered + same-origin links on fetched pages), never the sample;
                    article share is capped at 3 so a blog section is evidence, not a verdict
  affordances  2-4  what the site invites: cart, pricing/trial/demo, order/menu/locations,
                    post-a-job / become-a-seller, donate
  content      <=2  what fetched pages are, discounted when the inventory does not back it
                    (the static sample is stratified by page type and over-represents small
                    sections such as /docs/)
  vocabulary   <=3  weighted keyword sets over titles/descriptions/visible text/raw HTML/
                    robots.txt paths/sitemap names, core-term gated; carries a JS-shell
                    homepage alone only when very strong

Counter-evidence is explicit: commerce identity subtracts from news/saas/personal, pricing
or software identity from news/personal/docs, institutional identity from news/saas,
"author is a Person with no Organization" from news, third-party listings from saas.
Confidence is derived from evidence strength and margin (0.55-0.90), not assigned per rule.
`unknown` is returned for insufficient evidence *and* for a near-tie ("ambiguous: A vs
B"), with both sides in the reason.

Archetypes: the original six plus `reference` (encyclopaedia/wiki/health reference),
`institutional` (university, government, foundation, NGO, open-source project),
`marketplace` (third-party inventory: listings, classifieds, job boards, travel, creator
platforms) and `personal` (an individual's site) -- which the analysers already knew
(`PERSONAL_ARCHETYPES`) but no rule ever produced. Downstream only COMMERCIAL_ARCHETYPES
and PERSONAL_ARCHETYPES change behaviour, so the new labels are safe.

Other changes: broader page_type URL rules (plural products/items, /dp/ /itm/ /ip/,
/cp/<slug>/<id>, category, blog|news|articles -> article, tutorials|kb|sdk -> docs,
docs./developer./kb./wiki. hosts); 200-but-really-a-bot-wall pages are dropped before any
rule (`_BLOCK_PAGE_RE`); optional `hints` (robots.txt text, sitemap URLs) feed the
sitemap-name and vocabulary evidence. No hostnames or site-specific strings anywhere; the
calibration corpora were 84 + 90 sites and the hold-out 40, and every rule is a general
signal, not a fix for a domain.
"""
from __future__ import annotations

import os
import re
from urllib.parse import urlparse

# --------------------------------------------------------------------------------------
# page_type
# --------------------------------------------------------------------------------------

# Ordered most-specific-first so the first match wins ties per the "more specific label"
# rule. Every path rule is anchored to a path segment unless the token is unambiguous.
_PATH_TITLE_RULES: list[tuple[str, re.Pattern]] = [
    ("login", re.compile(r"login|signin|sign-in|signup|sign-up|/account(s)?(/|$)|register|/auth(/|$)|password", re.I)),
    ("legal", re.compile(r"privacy|/terms|cookie|/legal|imprint|impressum|/tos(/|$)|accessibility-statement", re.I)),
    ("faq", re.compile(r"\bfaq(s)?\b|frequently-asked", re.I)),
    # Segment-anchored (2026-09-12, fresh-list run): unanchored `pricing` matched a tech-news
    # site's article slugs (/news/gpu-pricing-...) and made it saas_marketing -- the same
    # defect v1 fixed for `plans` in Stage C.
    ("pricing", re.compile(r"/(pricing|plans|fees|compare-plans|pricing-plans|plans-and-pricing)(/|$|\?)|/pricing-|-(pricing|fees)(/|$)", re.I)),
    # Segment-anchored: unanchored `api|guide|reference` matched half of a real engineering
    # blog's article slugs (Stage B', 2026-09-04). Tutorials / learn / wiki / kb are added
    # because tutorial sites (w3schools, geeksforgeeks, tutorialspoint) are documentation in
    # everything but name.
    ("documentation", re.compile(
        r"/(docs?|documentation|api|apis|reference|manual|handbook|guides?|tutorials?|"
        r"how-to|howto|kb|knowledge-?base|help-?center|developers?|dev|sdk|cli|getting-started|"
        r"quickstart|en/latest|en/stable|en/[0-9.]+|[0-9]+/library|specs?|specification|"
        r"functions?|commands?|methods?|configuration|installation|troubleshooting|changelog|release-notes)(/|$)", re.I)),
    ("contact", re.compile(r"contact|/support(/|$)|get-in-touch|customer-service", re.I)),
    ("about", re.compile(r"/about|/company(/|$)|who-we-are|/team(/|$)|/mission(/|$)|/our-story|/leadership", re.I)),
    # Category before product: `/collections/x` is a listing, `/collections/x/products/y` is
    # the product, and the more specific product rule must not swallow the listing.
    # Single-letter shortcuts are only accepted with a numeric tail (`/p/12345`): bare `/c/`
    # is the C language on w3schools, `/b/` is a blog on plenty of sites.
    ("product", re.compile(
        r"/(products?|items?|shop|dp|itm|ip|listing|sku|pd|product-detail|prod)(/|$)|/p/[^/]*\d", re.I)),
    ("category", re.compile(
        r"/(collections?|categor(y|ies)|store|browse|catalog|catalogue|departments?|brands?|"
        r"shop-by|all-products|new-arrivals)(/|$)|/cp/[^/]+/\d+", re.I)),
    ("article", re.compile(
        r"/(blog|blogs|news|articles?|posts?|stories|story|press|press-releases?|newsroom|"
        r"magazine|editorial|opinion|insights?|journal|updates?|entertainment|politics|"
        r"business|sports?|world|tech|health|lifestyle|science|culture|travel)(/|$)", re.I)),
]

_PRICING_TITLE_RE = re.compile(r"^\s*pricing\b|pricing (&|and) plans|plans (&|and) pricing|pricing plans|compare plans", re.I)
_DATE_IN_PATH_RE = re.compile(r"/(19|20)\d{2}[/-](0?[1-9]|1[0-2])([/-]|$)")

# Hostname prefixes that decide the *whole host* is documentation. A `docs.` subdomain has
# no other plausible purpose; treating every URL on it as `other` because the path lacks
# `/docs/` was why docs.python.org and docs.djangoproject.com were `unknown`.
# Narrow on purpose: `api.` and `help.` hosts serve whole ordering sites and support portals
# (api.dominos.co.in is Domino's India's entire storefront).
_DOC_HOST_RE = re.compile(r"^(docs?|documentation|developers?|kb|wiki|manual)\.", re.I)
_WIKI_HOST_RE = re.compile(r"^(wiki|[a-z]{2,3})\.wikipedia\.|^wiki\.", re.I)

_NON_PAGE_EXT_RE = re.compile(
    r"\.(png|jpe?g|gif|webp|svg|ico|bmp|avif|heic|"
    r"css|js|mjs|json|xml|"
    r"pdf|docx?|xlsx?|pptx?|csv|"
    r"woff2?|ttf|eot|otf|"
    r"mp3|mp4|webm|mov|avi|wav|ogg|"
    r"zip|gz|tar|rar)$", re.I
)

_PRODUCT_TYPES = {"product", "offer", "aggregateoffer", "productgroup", "individualproduct", "productmodel", "vehicle"}
_ARTICLE_TYPES = {"article", "blogposting", "newsarticle", "report", "scholarlyarticle",
                  "liveblogposting", "opinionnewsarticle", "reviewnewsarticle", "analysisnewsarticle",
                  "backgroundnewsarticle", "socialmediaposting", "medicalscholarlyarticle"}
_DOC_TYPES = {"techarticle", "apireference", "howto"}
# `Question`/`Answer` deliberately absent: every FAQPage block nests them, and they made
# github.com and paypal.com "reference" in the first 84-site run.
_REFERENCE_PAGE_TYPES = {"medicalwebpage", "medicalcondition", "drug", "definedterm", "definedtermset", "qapage"}
# A page that calls itself a tutorial / reference / manual in its <title> is documentation
# whatever its URL looks like -- w3schools, tutorialspoint and geeksforgeeks all do this.
# `how to`, `examples` and bare `api` were here and matched a fundraising site's charity
# pages (fresh-list run); only words a page uses to call *itself* documentation remain.
_DOC_TITLE_RE = re.compile(r"\b(tutorials?|documentation|docs|manual|handbook|api reference|cheat ?sheet|syntax|user guide|developer guide|getting started|quick ?start)\b|\breference\b(?! (guide|desk))", re.I)
_DOC_SITE_DESC_RE = re.compile(r"\b(tutorials?|documentation|learn to code|programming (tutorials?|reference)|reference (guide|manual))\b", re.I)


def _norm_types(types) -> set[str]:
    """Flatten JSON-LD @type values to lowercase bare names. Accepts a str, a list, a
    nested list, `schema:Product`, or `https://schema.org/Product`."""
    out: set[str] = set()
    stack = [types]
    while stack:
        t = stack.pop()
        if t is None:
            continue
        if isinstance(t, (list, tuple, set)):
            stack.extend(t)
            continue
        if not isinstance(t, str):
            continue
        t = t.strip().rstrip("/")
        t = t.rsplit("/", 1)[-1].rsplit(":", 1)[-1].rsplit("#", 1)[-1]
        if t:
            out.add(t.lower())
    return out


def classify_page_type(url: str, title: str | None, json_ld_types: list[str]) -> str:
    parsed = urlparse(url)
    path = parsed.path or "/"
    host = (parsed.netloc or "").lower()
    title = title or ""

    if path == "/" or path == "":
        return "home"

    if _NON_PAGE_EXT_RE.search(path):
        return "asset"

    types_lower = _norm_types(json_ld_types)
    if types_lower & _PRODUCT_TYPES:
        return "product"
    if types_lower & _ARTICLE_TYPES:
        return "article"
    if types_lower & _DOC_TYPES:
        return "documentation"
    if "faqpage" in types_lower:
        return "faq"
    if "collectionpage" in types_lower or "itemlist" in types_lower:
        return "category"

    for label, pattern in _PATH_TITLE_RULES:
        if pattern.search(path):
            return label
        if label == "pricing":
            if _PRICING_TITLE_RE.search(title):
                return label
        elif label not in ("product", "category", "article", "documentation") and pattern.search(title):
            return label

    if _DATE_IN_PATH_RE.search(path):
        return "article"

    # Wikipedia-style `/wiki/<Term>` is reference, which downstream is closest to
    # documentation; a docs.* host makes every otherwise-unlabelled path documentation.
    if re.search(r"/wiki/", path, re.I) or _WIKI_HOST_RE.search(host):
        return "documentation"
    if _DOC_HOST_RE.search(host):
        return "documentation"

    return "other"


# --------------------------------------------------------------------------------------
# archetype -- per-page signal extraction
# --------------------------------------------------------------------------------------

_GENERATOR_RE = re.compile(r'<meta[^>]+name=["\']generator["\'][^>]+content=["\']([^"\']+)', re.I)
_GENERATOR_RE_2 = re.compile(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']generator["\']', re.I)
_OG_TYPE_RE = re.compile(r'<meta[^>]+property=["\']og:type["\'][^>]+content=["\']([^"\']+)', re.I)
_OG_TYPE_RE_2 = re.compile(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:type["\']', re.I)

_ECOM_PLATFORM_RE = re.compile(
    r"shopify|woocommerce|magento|bigcommerce|prestashop|opencart|salesforce commerce|demandware|"
    r"shopware|squarespace commerce|wix stores|ecwid|volusion|3dcart|shift4shop", re.I)
_ECOM_HTML_RE = re.compile(
    r"cdn\.shopify\.com|Shopify\.theme|woocommerce|Magento_|/checkout/cart|add-to-cart|addToCart|"
    r"data-product-id|data-cart-count|cart-count|minicart|mini-cart", re.I)
_DOC_GENERATOR_RE = re.compile(
    r"sphinx|mkdocs|docusaurus|gitbook|vuepress|vitepress|readthedocs|docsify|jekyll.*docs|"
    r"just-the-docs|hugo.*(docsy|book|doks)|antora|slate|redoc|swagger|mintlify|readme\.io", re.I)
_EDITORIAL_GENERATOR_RE = re.compile(r"wordpress|ghost|substack|medium|blogger|typepad|arc publishing|newspack", re.I)

# `/checkout` alone is not a cart: shopify.com and stripe.com sell a product called Checkout.
# Matched against the full href so a cart on its own host (shoppingcart.aliexpress.com) counts.
_CART_LINK_RE = re.compile(r"/(cart|basket|bag|shopcart|shopping-?cart|checkout/cart)(/|$|\?)|//(shopping)?cart\.", re.I)
_CART_TEXT_RE = re.compile(r"\b(cart|basket|checkout|add to (cart|bag|basket)|buy now|shop now|shop all)\b", re.I)
_SAAS_TEXT_RE = re.compile(
    r"\b(free trial|start (your )?free|try (it )?(for )?free|try free|request a demo|book a demo|get a demo|"
    r"schedule a demo|watch demo|see pricing|view pricing|pricing|plans and pricing|"
    r"start for free|get started( for)? free|sign up( for)? free|open an account|create (a |your )?free account|"
    r"talk to sales|contact sales|download the app|get the app)\b", re.I)
_SAAS_LINK_RE = re.compile(r"/(pricing|plans|demo|request-demo|free-trial|trial|signup|sign-up|get-started|start-free)(/|$|\?)", re.I)
_LOCAL_TEXT_RE = re.compile(
    r"\b(order (online|now|ahead|delivery|pickup)|find a (store|location|restaurant|branch)|store locator|"
    r"locations?|our menu|view menu|menu|reservations?|book a table|opening hours|hours & locations|"
    r"directions|visit us|nearest)\b", re.I)
_LOCAL_LINK_RE = re.compile(r"/(locations?|store-?locator|find-a-store|restaurants?|menu|menus|order|reservations?|book|directions)(/|$|\?)", re.I)
_MARKETPLACE_LINK_RE = re.compile(
    r"/(jobs?|job-search|job-listings?|listings?|homes?|for-sale|for-rent|rentals?|apartments?|"
    r"hotels?|flights?|vacation-rentals?|cruises?|classifieds|salaries|post-ad|post-a-job|"
    r"leaderboard|marketplace)(/|$|\?)", re.I)
# JSON-LD that only a listings / aggregator site emits: search-result pages typed as such,
# job postings, flights and airports, real-estate listings. `Hotel` on its own is a local
# business; `Hotel` on every non-home page of a 500-URL site is a directory of hotels.
_MARKETPLACE_TYPES = {"searchresultspage", "jobposting", "flight", "airport", "trip", "touristdestination",
                      "realestatelisting", "apartment", "house", "singlefamilyresidence", "accommodation",
                      "lodgingreservation", "event", "eventseries"}
_MARKETPLACE_TEXT_RE = re.compile(
    r"\b(post (a |an |your )?(ad|job|listing)|browse (jobs|listings|homes|hotels|rentals)|find (jobs|homes|hotels|apartments|flights|a rental)|"
    r"search (jobs|homes|hotels|flights|listings|rentals)|write a review|list your (property|business|home)|"
    r"for sale|for rent|apply now|employers|hosts?|sellers?|become a (host|seller|driver|partner))\b", re.I)
_INSTITUTIONAL_LINK_RE = re.compile(
    r"/(admissions?|academics?|students?|faculty|alumni|campus|research|departments?|programs?|"
    r"donate|giving|foundation|grants?|missions?|agency|agencies|about-nasa|newsroom|press-room|"
    r"community|governance|board|volunteer|membership|get-involved|psf|our-work)(/|$|\?)", re.I)
_REFERENCE_LINK_RE = re.compile(
    r"/(wiki|encyclopedia|topic|topics|definition|dictionary|glossary|conditions?|diseases?|drugs?|"
    r"symptoms?|treatments?|medications?|health|nutrition|health-news|medical|vitamins|supplements|"
    r"calculators?|compare|ratings|facts|biography|science|history|questions?|answers?)(/|$|\?)", re.I)

_NEWS_ORG_TYPES = {"newsmediaorganization"}
_STORE_ORG_TYPES = {"onlinestore", "store", "wholesalestore", "departmentstore", "electronicsstore",
                    "clothingstore", "furniturestore", "homegoodsstore", "grocerystore",
                    "hardwarestore", "jewelrystore", "shoestore", "sportinggoodsstore", "toystore",
                    "bookstore", "petstore", "outletstore", "bikestore", "computerstore", "florist",
                    "gardenstore", "hobbyshop", "liquorstore", "mobilephonestore",
                    "moviegoodsstore", "musicstore", "officeequipmentstore", "paintingstore"}
_SAAS_ORG_TYPES = {"softwareapplication", "webapplication", "mobileapplication", "softwaresourcecode"}
_LOCAL_ORG_TYPES = {"localbusiness", "restaurant", "cafeorcoffeeshop", "barorpub", "bakery", "fastfoodrestaurant",
                    "foodestablishment", "hotel", "lodgingbusiness", "bedandbreakfast", "motel", "resort",
                    "dentist", "physician", "medicalclinic", "medicalbusiness", "hospital", "pharmacy",
                    "hairsalon", "beautysalon", "dayspa", "healthclub", "gym", "sportsclub",
                    "autorepair", "autodealer", "automotivebusiness", "gasstation", "carwash",
                    "realestateagent", "legalservice", "attorney", "notary", "accountingservice",
                    "financialservice", "insuranceagency", "bankorcreditunion",
                    "homeandconstructionbusiness", "plumber", "electrician", "roofingcontractor",
                    "hvacbusiness", "housepainter", "generalcontractor", "movingcompany", "locksmith",
                    "travelagency", "touristattraction", "museum", "library", "childcare", "animalshelter",
                    "veterinarycare", "petstore", "drycleaningorlaundry", "emergencyservice",
                    "entertainmentbusiness", "nightclub", "moviehouse", "amusementpark", "artgallery",
                    "shoppingcenter", "professionalservice", "employmentagency", "selfstorage",
                    "storagefacility", "tireshop", "winery", "brewery", "distillery"}
_INSTITUTIONAL_ORG_TYPES = {"educationalorganization", "collegeoruniversity", "school", "highschool",
                            "middleschool", "elementaryschool", "preschool", "governmentorganization",
                            "governmentoffice", "governmentservice", "ngo", "nonprofit", "foundation",
                            "researchorganization", "researchproject", "fundingagency", "library",
                            "museum", "politicalparty", "consortium"}
_PERSONAL_TYPES = {"person", "profilepage"}

# A 200 response that is really a bot wall. v1 counted these as fetched pages and then
# labelled the site from them ("Access Denied" -> brochure). They carry no evidence about
# the site at all and are dropped before any rule runs.
_BLOCK_PAGE_RE = re.compile(
    r"access denied|just a moment|attention required|are you a (human|robot)|verify you are human|"
    r"captcha|request blocked|request unsuccessful|403 forbidden|pardon our interruption|"
    r"enable javascript to run this app|enable cookies to continue|bot detection|unusual traffic|"
    r"security check|checking your browser|please wait while we verify|incapsula|perimeterx|"
    r"cloudflare ray id", re.I)

# --------------------------------------------------------------------------------------
# Vocabulary fallback. Weighted keyword sets per archetype, scored over the site's
# self-description (titles, meta descriptions), visible text, raw HTML (hydration data
# and i18n strings survive a JS shell), robots.txt Disallow paths and sitemap file names.
# Runs only after every structural rule has declined, needs a clear margin over the
# runner-up, and never exceeds 0.6 confidence. No site names, no host lists: the same
# table has to hold on a corpus this classifier has never seen. English-centric.
# --------------------------------------------------------------------------------------
_VOCAB: dict[str, list[tuple[str, float]]] = {
    "ecommerce": [
        (r"add[ -]to[ -](cart|bag|basket)|addtocart", 3), (r"\bcart\b|\bbasket\b", 1), (r"checkout", 1),
        (r"free shipping|free delivery", 2), (r"shop now|shop all|buy now", 2), (r"wish ?list", 1),
        (r"best ?sellers|new arrivals|top rated", 2), (r"shop by (category|brand|department)", 3),
        (r"in stock|out of stock", 2), (r"\bsku\b", 1), (r"coupons?|promo code", 1), (r"free returns|returns? policy", 1),
        (r"track (my |your )?order|order tracking", 2), (r"\bshopping\b", 1), (r"\bdeals?\b|\bsale\b|clearance", 1),
        (r"clothing|apparel|beauty|jewel(le)?ry|electronics|furniture|home (&|and) garden|appliances|footwear|accessories", 1),
    ],
    "marketplace": [
        (r"compare (prices|flights|hotels|rates|rentals)", 3), (r"\bflights?\b|airfare", 2), (r"\bhotels?\b", 2),
        (r"car (rental|hire)", 2), (r"\blistings?\b", 2), (r"homes? for sale|houses? for sale", 3), (r"for rent", 2),
        (r"apartments?", 1), (r"\bjobs?\b|job search|job listings", 1), (r"salar(y|ies)", 2), (r"post (a|an|your) (job|ad|listing)", 3),
        (r"classifieds", 3), (r"book now|book a (room|flight|table)", 1), (r"find (a |the |your )?(job|home|hotel|flight|deal|apartment|rental)", 3),
        (r"\bsellers?\b|\bbuyers?\b|\bhosts?\b", 1), (r"\brentals?\b|vacation rentals?", 2), (r"cruises?", 2), (r"marketplace", 2),
        (r"real estate|realtor|\bmls\b", 2), (r"employers?|recruiters?|candidates?", 1),
    ],
    "saas_marketing": [
        (r"free trial|try (it )?free|start (your )?free", 3), (r"(request|book|get|schedule|watch) a demo", 3), (r"\bpricing\b", 2),
        (r"\bplans\b", 1), (r"sign ?up|create (an|your) account", 1), (r"get started", 1), (r"\bplatform\b", 1),
        (r"integrations?", 2), (r"\bfeatures\b", 1), (r"enterprise", 1), (r"\bcrm\b", 2), (r"workflows?", 1),
        (r"\bsoftware\b", 1), (r"start for free|free forever|free plan", 3), (r"all-in-one", 1), (r"no credit card", 3),
        (r"design tool|website builder|email marketing|analytics|automation|collaboration|productivity|dashboard", 2),
        (r"talk to sales|contact sales", 2), (r"\bsaas\b|cloud-based", 2), (r"customers|trusted by", 1),
    ],
    "news_editorial": [
        (r"breaking news", 3), (r"latest news|top stories|top news", 2), (r"headlines", 2), (r"\bopinion\b|op-ed|editorial", 1),
        (r"newsletter", 1), (r"subscribe|subscription", 1), (r"journalists?|reporters?|correspondents?|columnists?", 2),
        (r"live updates|live blog", 3), (r"\bpolitics\b", 1), (r"world news|local news|national news", 2),
        (r"\bsports\b|entertainment|celebrity|showbiz", 0.5), (r"\d+ min read", 2), (r"newsroom", 2), (r"\bnews\b", 1),
        (r"published|updated (on|at)", 0.5), (r"exclusive|investigation", 1), (r"magazine|journal", 1),
    ],
    "documentation": [
        (r"documentation", 3), (r"tutorials?", 3), (r"api reference", 3), (r"\breference\b", 1), (r"getting started", 2),
        (r"install(ation)?", 1), (r"\bguides?\b", 1), (r"examples?", 1), (r"\bsyntax\b", 2), (r"changelog|release notes", 2),
        (r"cheat ?sheet", 2), (r"\bapi\b", 1), (r"\bsdk\b", 2), (r"\bcli\b", 1), (r"source code|open source|github", 1),
        (r"functions?|methods?|classes|parameters?|arguments?", 0.5), (r"learn to code|programming|coding", 2), (r"quick ?start", 2),
        (r"\bdocs\b", 3), (r"how[- ]to", 1), (r"exercises?|quiz(zes)?|certificates?", 1),
    ],
    "reference": [
        (r"encyclop(a)?edia", 3), (r"definitions?|dictionary|glossary|thesaurus", 2), (r"symptoms", 2), (r"treatments?", 2),
        (r"\bcauses\b", 1), (r"diagnosis", 2), (r"medically reviewed|fact[- ]checked|peer[- ]reviewed", 3),
        (r"health conditions|conditions a-z|drugs a-z", 2), (r"\bwiki\b", 2), (r"\bfacts\b", 1), (r"what is", 1),
        (r"biograph(y|ies)", 2), (r"drug interactions|side effects|dosage", 2), (r"forecast|radar", 1), (r"overview", 0.5),
        (r"topics?", 0.5), (r"\barticles\b", 0.5), (r"trusted (source|information)|expert", 1),
    ],
    "institutional": [
        (r"universit(y|ies)|college", 3), (r"admissions?", 3), (r"\bstudents?\b", 1), (r"faculty", 2), (r"\bcampus\b", 2),
        (r"\bresearch\b", 1), (r"government|federal|\bagency\b|ministry", 2), (r"official (website|site)", 2),
        (r"department of", 2), (r"foundation", 2), (r"non[- ]?profit|charity", 3), (r"\bdonate\b|donation", 2),
        (r"\bmission\b", 1), (r"alumni", 2), (r"academic", 2), (r"\bpolicy\b|public policy", 1), (r"\.gov\b", 2),
        (r"initiative|program(me)?s?", 0.5), (r"\bcommunity\b", 0.5), (r"grants?|funding", 1), (r"press release|newsroom", 0.5),
    ],
    "local_business": [
        (r"\bmenu\b", 2), (r"order online|order now|order ahead", 3), (r"\blocations?\b", 1), (r"find a (store|location|restaurant)|store locator", 3),
        (r"\bhours\b|opening hours|open now", 1), (r"directions", 2), (r"reservations?|book a table", 2), (r"delivery", 1),
        (r"pick ?up|curbside", 1), (r"near (you|me)|nearby", 2), (r"restaurants?", 2), (r"catering", 2), (r"franchise", 1),
        (r"pizza|burgers?|tacos?|coffee|bakery|grill|kitchen", 1), (r"dine[- ]in|drive[- ]thru|takeout|take-away", 2),
        (r"\b(salon|spa|clinic|dental|plumbing|roofing|auto repair)\b", 2), (r"visit us|come visit", 1),
    ],
}
_VOCAB_COMPILED = {k: [(re.compile(rx, re.I), w) for rx, w in v] for k, v in _VOCAB.items()}
# Ablation switch for evaluation: the vocabulary fallback is the most hand-tuned component,
# so a held-out run with it off shows how much of the coverage rests on it.
VOCAB_FALLBACK_ENABLED = os.environ.get("PAGE_CLASSIFIER_NO_VOCAB") != "1"
# A label's vocabulary only counts if at least one *core* term -- something that names the
# activity, not just the subject -- appears somewhere. A recipe site is full of "pizza",
# "menu" and "kitchen" (fresh-list run) but never says "order online" or "store locator".
_VOCAB_CORE = {k: re.compile(rx, re.I) for k, rx in {
    "ecommerce": r"add[ -]to[ -](cart|bag|basket)|addtocart|\bcart\b|checkout|free shipping|shop now|buy now|in stock|\bsku\b",
    "marketplace": r"\blistings?\b|\bjobs?\b|\bhotels?\b|\bflights?\b|for rent|for sale|\brentals?\b|classifieds|marketplace|apartments?|car (rental|hire)|salar(y|ies)",
    "saas_marketing": r"free trial|a demo|\bpricing\b|sign ?up|get started|\bplans\b|start for free|no credit card|integrations?",
    "news_editorial": r"\bnews\b|headlines|journalists?|reporters?|editor|subscribe|newsletter|breaking|live updates",
    "documentation": r"documentation|tutorials?|\bapi\b|\breference\b|\bdocs\b|install|getting started|\bsdk\b|\bcli\b",
    "reference": r"encyclop|definition|dictionary|glossary|symptoms|treatment|\bwiki\b|medically reviewed|\bfacts\b|biograph",
    "institutional": r"universit|college|government|federal|\bagency\b|foundation|non[- ]?profit|charity|\bdonate\b|official|\.gov\b|department of|admissions?",
    "local_business": r"order (online|now|ahead)|find a (store|location|restaurant)|store locator|opening hours|\bhours\b|directions|reservations?|book a table|near (you|me)|dine[- ]in|drive[- ]thru|takeout|curbside|catering",
}.items()}
_SITEMAP_NAME_HINTS = [
    ("ecommerce", re.compile(r"product|collection|categor|catalog|brand|store", re.I)),
    ("news_editorial", re.compile(r"news|article|post|blog|stor(y|ies)|editorial", re.I)),
    ("documentation", re.compile(r"docs?|documentation|tutorial|reference|guide", re.I)),
    ("marketplace", re.compile(r"job|listing|hotel|flight|rental|home|propert|classified", re.I)),
    ("reference", re.compile(r"wiki|condition|drug|topic|definition|encyclop", re.I)),
    ("local_business", re.compile(r"location|store-?locator|restaurant|menu", re.I)),
]


def _vocab_scores(sigs: list[dict], basis_paths: list[str], robots_txt: str | None, sitemap_urls: list[str] | None):
    """Per-archetype weighted keyword score. Sources and their multipliers:
    self-description (title + meta description + og) x4, visible main text x1, raw HTML
    x0.3 (JS bundles mention everything, so the per-keyword cap matters more than the
    weight), robots.txt Disallow paths x2, sitemap file names +3 each, inventory path
    tokens x0.5. Every keyword is capped per source so one repeated string cannot decide."""
    self_desc = " ".join(s["title"] + " " + s["meta_description"] for s in sigs)
    visible = " ".join((s.get("main_text") or "")[:20_000] for s in sigs)
    raw = " ".join((s.get("raw_head") or "") for s in sigs)
    robots_paths = " ".join(re.findall(r"^(?:dis)?allow:\s*(\S+)", robots_txt or "", re.I | re.M))
    robots_paths = re.sub(r"[/*$?=&_.-]+", " ", robots_paths)
    inv_tokens = " ".join(re.sub(r"[/_.-]+", " ", pth) for pth in basis_paths[:500])
    sources = [(self_desc, 4.0, 3), (visible, 1.0, 5), (raw, 0.3, 10), (robots_paths, 2.0, 5), (inv_tokens, 0.5, 10)]
    scores: dict[str, float] = {}
    terms: dict[str, list[str]] = {}
    for label, rules in _VOCAB_COMPILED.items():
        total = 0.0
        hits: dict[str, float] = {}
        for text, mult, cap in sources:
            if not text:
                continue
            for rx, w in rules:
                n = len(rx.findall(text))
                if n:
                    contrib = min(n, cap) * w * mult
                    total += contrib
                    key = rx.pattern[:18]
                    hits[key] = hits.get(key, 0) + contrib
        for u in sitemap_urls or []:
            name = u.rsplit("/", 1)[-1]
            for lab, rx in _SITEMAP_NAME_HINTS:
                if lab == label and rx.search(name):
                    total += 3.0
                    hits["sitemap:" + name[:20]] = hits.get("sitemap:" + name[:20], 0) + 3.0
        core = _VOCAB_CORE.get(label)
        if core is not None and not (core.search(self_desc) or core.search(visible) or core.search(raw) or core.search(robots_paths)):
            total = 0.0
            hits = {"(no core term)": 0.0}
        scores[label] = round(total, 1)
        terms[label] = [f"{k}x{v:.0f}" for k, v in sorted(hits.items(), key=lambda kv: -kv[1])[:4]]
    return scores, terms


def _walk_json(obj, depth=0):
    """Yield every dict nested inside a JSON-LD entry (bounded depth)."""
    if depth > 6:
        return
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from _walk_json(v, depth + 1)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk_json(v, depth + 1)


def _page_signals(p: dict) -> dict:
    """Normalise one page dict -- either the reduced shape the v1 driver built
    ({'page_type','json_ld_types','has_price','has_postal_address','primary_date'}) or a
    full `pages[]` bundle entry from extract_page -- into the signals the rules read."""
    sig = {
        "page_type": p.get("page_type", "other"),
        "url": p.get("url") or p.get("final_url") or "",
        "types": set(),
        "has_price": bool(p.get("has_price")),
        "has_postal_address": bool(p.get("has_postal_address")),
        "primary_date": p.get("primary_date"),
        "generator": "",
        "og_type": "",
        "ecom_html": False,
        "internal_links": [],       # (href, text)
        "link_texts": "",
        "internal_link_count": 0,
        "main_text_words": p.get("main_text_words"),
        "extraction_ok": p.get("extraction_ok", True),
        "title": p.get("title") or "",
        "meta_description": ((p.get("meta") or {}).get("description") or ""),
        "main_text": p.get("main_text") or "",
        "raw_head": "",
        "is_block_page": False,
        "authors": set(),
        "persons": set(),
        "outbound_profiles": len(p.get("outbound_profile_links") or []),
        "has_link_data": "links" in p,
    }

    if p.get("json_ld_types"):
        sig["types"] |= _norm_types(p["json_ld_types"])

    sd = p.get("structured_data") or {}
    for entry in sd.get("json_ld") or []:
        sig["types"] |= _norm_types(entry.get("type"))
        raw = entry.get("raw")
        if isinstance(raw, dict):
            for node in _walk_json(raw):
                ntypes = _norm_types(node.get("@type"))
                sig["types"] |= ntypes
                if ntypes & {"offer", "aggregateoffer"} or "price" in node or "lowPrice" in node or "priceCurrency" in node:
                    if any(k in node for k in ("price", "lowPrice", "highPrice", "priceCurrency", "priceSpecification")):
                        sig["has_price"] = True
                if "postaladdress" in ntypes or "streetAddress" in node or "addressLocality" in node:
                    sig["has_postal_address"] = True
                if "person" in ntypes and isinstance(node.get("name"), str):
                    sig["persons"].add(node["name"].strip().lower()[:60])
                author = node.get("author")
                for a in (author if isinstance(author, list) else [author]):
                    name = a.get("name") if isinstance(a, dict) else (a if isinstance(a, str) else None)
                    if name and isinstance(name, str):
                        sig["authors"].add(name.strip().lower()[:60])

    dates = p.get("dates") or {}
    if not sig["primary_date"]:
        sig["primary_date"] = (dates.get("meta_published") or dates.get("meta_modified")
                               or (dates.get("visible_dates") or [None])[0])
    if not sig["primary_date"]:
        m = _DATE_IN_PATH_RE.search(urlparse(sig["url"]).path or "")
        if m:
            sig["primary_date"] = m.group(0)

    raw_html = p.get("raw_html") or ""
    if raw_html:
        head = raw_html[:200_000]
        sig["raw_head"] = head
        # og:description / og:site_name are self-description too
        for m in re.finditer(r'<meta[^>]+property=["\']og:(description|site_name|title)["\'][^>]+content=["\']([^"\']{0,300})', head, re.I):
            sig["meta_description"] += " " + m.group(2)
        text_probe = sig["title"] + " " + re.sub(r"<[^>]+>", " ", re.sub(r"<script.*?</script>|<style.*?</style>", "", head[:30_000], flags=re.S | re.I))
        sig["is_block_page"] = bool(_BLOCK_PAGE_RE.search(text_probe)) and (sig["main_text_words"] or 0) < 80
        m = _GENERATOR_RE.search(head) or _GENERATOR_RE_2.search(head)
        sig["generator"] = m.group(1) if m else ""
        m = _OG_TYPE_RE.search(head) or _OG_TYPE_RE_2.search(head)
        sig["og_type"] = (m.group(1) if m else "").lower()
        sig["ecom_html"] = bool(_ECOM_HTML_RE.search(head))

    links = p.get("links") or []
    internal = [(l.get("href") or "", l.get("text") or l.get("aria_label") or "")
                for l in links if l.get("internal")]
    sig["internal_links"] = internal
    sig["internal_link_count"] = len({urlparse(h).path for h, _ in internal})
    sig["link_texts"] = " | ".join(t.strip() for _, t in internal if t and t.strip())[:50_000]
    return sig


def _virtual_inventory(inventory: list[dict], sigs: list[dict], cap: int = 500) -> list[dict]:
    """Union of the discovered inventory and the same-origin links on fetched pages, each
    labelled with classify_page_type. Deduplicated by (host, path) with fragments and
    queries dropped, so a nav link repeated on every fetched page counts once."""
    seen: set[tuple[str, str]] = set()
    out: list[dict] = []

    def add(url: str, page_type: str | None):
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https", ""):
            return
        key = (parsed.netloc.lower(), (parsed.path or "/").rstrip("/") or "/")
        if key in seen:
            return
        seen.add(key)
        out.append({"url": url, "page_type": page_type or classify_page_type(url, None, [])})

    for p in inventory or []:
        add(p.get("url", ""), p.get("page_type"))
    for s in sigs:
        for href, _ in s["internal_links"]:
            if len(out) >= cap:
                return out
            if href.startswith(("mailto:", "tel:", "javascript:")):
                continue
            add(href, None)
    return out


# --------------------------------------------------------------------------------------
# archetype -- rules
# --------------------------------------------------------------------------------------

class _Evidence:
    """Additive evidence ledger. Every signal adds (or subtracts) weight for one archetype
    and records why, so the decision is the *sum* of what was observed rather than the
    first rule that happened to match. Weights are the strength of the evidence family
    (identity 4-6 > affordance 2-4 > structure <= 4 > sampled content <= 2 > vocabulary <= 2),
    not per-site tuning."""

    def __init__(self):
        self.score: dict[str, float] = {k: 0.0 for k in _ARCHETYPES}
        self.notes: dict[str, list[str]] = {k: [] for k in _ARCHETYPES}

    def add(self, label: str, weight: float, note: str) -> None:
        if not weight:
            return
        self.score[label] += weight
        self.notes[label].append(f"{'+' if weight > 0 else ''}{weight:g} {note}")

    def ranked(self) -> list[tuple[str, float]]:
        return sorted(self.score.items(), key=lambda kv: -kv[1])


_ARCHETYPES = ("ecommerce", "saas_marketing", "news_editorial", "documentation", "local_business",
               "reference", "institutional", "marketplace", "personal")
_ORG_ENTITY_TYPES = {"organization", "corporation", "newsmediaorganization", "educationalorganization",
                     "governmentorganization", "ngo", "nonprofit", "onlinestore", "store", "localbusiness",
                     "sportsorganization", "medicalorganization", "collegeoruniversity", "school"}
_UGC_TYPES = {"interactioncounter", "userreview", "review", "socialmediaposting", "discussionforumposting", "comment"}
_USER_PATH_RE = re.compile(r"/(users?|members?|profiles?|u|@[^/]+|people|creators?|artists?|sellers?|shops?/[^/]+|portfolio/[^/]+)(/|$)", re.I)
_MARKET_CTA_RE = re.compile(r"\b(post (a|an|your) (job|ad|listing)|become a (seller|host|creator|partner|driver)|"
                            r"list your (property|business|home|space)|for (sellers|creators|employers|hosts|artists)|"
                            r"start selling|sell (your|on)|hire|apply now|find (a )?(freelancer|job|talent))\b", re.I)
_FIRST_PERSON_RE = re.compile(r"\b(i'?m|i am) an? \w+|\bmy (blog|notes|writing|work|garden|newsletter|projects|essays|site)\b|\babout me\b|\bmy name is\b|\bi write about\b|\bhi,? i'?m\b", re.I)
_DONATE_RE = re.compile(r"/(donate|donations?|give|giving|support-us|membership|volunteer)(/|$|\?)", re.I)


def _decide(ev: "_Evidence", min_score: float = 3.0, min_margin: float = 1.0) -> tuple[str, float, str]:
    ranked = ev.ranked()
    (top, top_s), (second, second_s) = ranked[0], ranked[1]
    why = "; ".join(ev.notes[top][:5])
    if top_s < min_score:
        return "unknown", 0.0, f"insufficient evidence: best {top} {top_s:.1f} (need {min_score:g}) [{why}]"
    margin = top_s - max(second_s, 0.0)
    if margin < min_margin:
        return "unknown", 0.0, (f"ambiguous: {top} {top_s:.1f} vs {second} {second_s:.1f} "
                               f"[{why}] vs [{'; '.join(ev.notes[second][:3])}]")
    # Confidence from evidence strength and separation, not from which rule fired:
    # strength saturates at 12 points, margin at 6.
    conf = 0.5 + 0.25 * min(top_s, 12.0) / 12.0 + 0.15 * min(margin, 6.0) / 6.0
    conf = round(max(0.55, min(0.9, conf)), 2)
    return top, conf, f"{top} {top_s:.1f} vs {second} {second_s:.1f}: {why}"


def classify_archetype_detailed(pages: list[dict], inventory: list[dict] | None = None,
                                hints: dict | None = None) -> tuple[str, float, str]:
    """Returns (archetype, confidence, reason).

    Evidence-scoring design (2026-09-12, replacing the first-match cascade after a blind
    40-site hold-out showed the cascade's ordering deciding sites the evidence did not):
    every archetype accumulates weighted evidence from five families -- identity,
    inventory structure, affordances, sampled content, vocabulary -- counter-evidence
    subtracts, and the top score wins only with a margin. Sampled-content signals are
    discounted when the inventory does not back them, because the static sample is
    stratified by page type and therefore over-represents small sections.

    `hints` is optional: {"robots_txt": str, "sitemap_urls": [str]} -- things the collector
    already has; they feed the sitemap-name and vocabulary evidence only."""
    if not pages:
        return "unknown", 0.0, "no_pages_fetched"
    hints = hints or {}

    sigs_all = [_page_signals(p) for p in pages]
    blocked = [s for s in sigs_all if s["is_block_page"]]
    sigs = [s for s in sigs_all if not s["is_block_page"]]
    if not sigs:
        return "unknown", 0.0, f"bot_blocked_page: {len(blocked)} fetched page(s) are access-denied/captcha walls, no evidence"
    home = next((s for s in sigs if s["page_type"] == "home"), sigs[0])
    all_types: set[str] = set().union(*(s["types"] for s in sigs))
    home_types = home["types"]
    home_about_types: set[str] = set().union(*(s["types"] for s in sigs if s["page_type"] in ("home", "about")))
    hosts = {urlparse(s["url"]).netloc.lower() for s in sigs if s["url"]}
    host = urlparse(home["url"]).netloc.lower() if home["url"] else (next(iter(hosts), "") if hosts else "")
    tld = host.rsplit(".", 1)[-1] if "." in host else ""

    # --- inventory (discovered + virtual), asset-free ---------------------------------
    basis = [p for p in _virtual_inventory(inventory or [], sigs) if p.get("page_type") != "asset"]
    total = len(basis)
    counts: dict[str, int] = {}
    for p in basis:
        counts[p["page_type"]] = counts.get(p["page_type"], 0) + 1
    product_count = counts.get("product", 0)
    category_count = counts.get("category", 0)
    article_count = counts.get("article", 0)
    has_pricing = counts.get("pricing", 0) > 0
    basis_paths = [urlparse(p["url"]).path or "/" for p in basis]
    share = lambda n: (n / total) if total else 0.0  # noqa: E731

    # --- fetched-page content signals -------------------------------------------------
    has_offer_price = any(s["has_price"] for s in sigs)
    has_postal_address = any(s["has_postal_address"] for s in sigs)
    content_sigs = [s for s in sigs if s["page_type"] not in ("home", "about", "contact", "legal", "login", "faq")]
    n_content = len(content_sigs)
    article_dates = {s["primary_date"] for s in sigs if s["page_type"] == "article" and s["primary_date"]}
    dated_pages = sum(1 for s in content_sigs if s["primary_date"])
    article_typed = sum(1 for s in content_sigs if s["types"] & _ARTICLE_TYPES or s["og_type"] == "article")
    generators = " ".join(s["generator"] for s in sigs if s["generator"])
    all_link_text = " | ".join(s["link_texts"] for s in sigs)
    uniq_hrefs = list({urlparse(h).path or "/": h for s in sigs for h, _ in s["internal_links"]}.values())
    uniq_paths = set(basis_paths) | {urlparse(h).path or "/" for h in uniq_hrefs}

    cart_links = sum(1 for h in uniq_hrefs if _CART_LINK_RE.search(h))
    cart_text = len(_CART_TEXT_RE.findall(all_link_text))
    saas_text = len(_SAAS_TEXT_RE.findall(all_link_text))
    saas_links = sum(1 for h in uniq_hrefs if _SAAS_LINK_RE.search(h))
    local_text = len(_LOCAL_TEXT_RE.findall(all_link_text))
    local_links = sum(1 for h in uniq_hrefs if _LOCAL_LINK_RE.search(h))
    market_links = sum(1 for path in uniq_paths if _MARKETPLACE_LINK_RE.search(path))
    market_text = len(_MARKETPLACE_TEXT_RE.findall(all_link_text)) + len(_MARKET_CTA_RE.findall(all_link_text))
    user_paths = sum(1 for path in uniq_paths if _USER_PATH_RE.search(path))
    inst_links = sum(1 for path in uniq_paths if _INSTITUTIONAL_LINK_RE.search(path))
    donate_links = sum(1 for path in uniq_paths if _DONATE_RE.search(path))
    ref_links = sum(1 for path in uniq_paths if _REFERENCE_LINK_RE.search(path))
    wiki_paths = sum(1 for path in basis_paths if re.search(r"^/wiki/", path, re.I))
    doc_count = max(0, counts.get("documentation", 0) - wiki_paths)  # /wiki/ is reference, not docs
    doc_titled = sum(1 for s in content_sigs if _DOC_TITLE_RE.search(s["title"]))
    home_declares_docs = bool(_DOC_SITE_DESC_RE.search(home["title"] + " " + home["meta_description"]))
    reference_pages = sum(1 for s in sigs if s["types"] & _REFERENCE_PAGE_TYPES)
    home_internal_links = home["internal_link_count"]

    is_news_org = bool(all_types & _NEWS_ORG_TYPES)
    is_store_org = bool(home_about_types & _STORE_ORG_TYPES)
    is_saas_org = bool(all_types & _SAAS_ORG_TYPES)
    is_institutional_org = bool(home_about_types & _INSTITUTIONAL_ORG_TYPES)
    is_institutional_tld = tld in ("edu", "gov", "mil") or bool(re.search(r"\.(edu|gov|ac|gc)\.[a-z]{2}$", host))
    home_local = bool(home_about_types & _LOCAL_ORG_TYPES)
    any_local = bool(all_types & _LOCAL_ORG_TYPES)
    org_entity = bool(all_types & _ORG_ENTITY_TYPES)
    person_entity = bool(all_types & _PERSONAL_TYPES)
    profile_page = "profilepage" in all_types or any(s["og_type"] == "profile" for s in sigs)
    authors = set().union(*(s["authors"] for s in sigs))
    single_author = len(authors) == 1 and sum(1 for s in content_sigs if s["authors"]) >= 2
    profile_links = sum(s["outbound_profiles"] for s in sigs if s["page_type"] in ("home", "about"))
    persons = set().union(*(s["persons"] for s in sigs))
    many_persons = len(persons) >= 4  # user profiles on a platform, not one person's site
    self_desc_home = " ".join(s["title"] + " " + s["meta_description"] + " " + (s["main_text"] or "")[:3000]
                              for s in sigs if s["page_type"] in ("home", "about"))
    first_person = len(_FIRST_PERSON_RE.findall(self_desc_home))
    ecom_platform = bool(_ECOM_PLATFORM_RE.search(generators))
    shop_cues = bool(cart_links or cart_text or is_store_org or ecom_platform or any(s["ecom_html"] for s in sigs))
    mostly_articles = n_content >= 3 and article_typed / n_content >= 0.6
    sitemap_names = [u.rsplit("/", 1)[-1] for u in (hints.get("sitemap_urls") or [])]

    ev = _Evidence()

    # ===== identity: who runs the site (strongest family) ==============================
    if ecom_platform:
        ev.add("ecommerce", 6, f"commerce platform generator ({generators.strip()[:30]})")
    if is_store_org:
        ev.add("ecommerce", 5, "Store/OnlineStore JSON-LD on home/about")
    if is_news_org:
        ev.add("news_editorial", 5, "NewsMediaOrganization JSON-LD")
    if is_saas_org:
        ev.add("saas_marketing", 4, "SoftwareApplication JSON-LD")
    if home_local:
        ev.add("local_business", 5, f"LocalBusiness-family JSON-LD on home/about ({', '.join(sorted(home_about_types & _LOCAL_ORG_TYPES))[:40]})")
    elif any_local:
        if total <= 60:
            ev.add("local_business", 3, "LocalBusiness-family JSON-LD on a small site")
        else:
            ev.add("marketplace", 3, "LocalBusiness-family JSON-LD on listing pages of a large site (directory)")
    if is_institutional_org:
        ev.add("institutional", 5, f"institutional JSON-LD ({', '.join(sorted(home_about_types & _INSTITUTIONAL_ORG_TYPES))[:40]})")
    if is_institutional_tld:
        ev.add("institutional", 4, f"institutional TLD ({host})")
    elif tld == "org":
        ev.add("institutional", 1, ".org")
    if _DOC_HOST_RE.search(host):
        ev.add("documentation", 5, f"documentation host ({host})")
    if _DOC_GENERATOR_RE.search(generators):
        ev.add("documentation", 5, f"documentation generator ({generators.strip()[:30]})")
    if _WIKI_HOST_RE.search(host):
        ev.add("reference", 5, "wiki host")
    if all_types & _MARKETPLACE_TYPES:
        ev.add("marketplace", 4, f"listing JSON-LD ({', '.join(sorted(all_types & _MARKETPLACE_TYPES))[:40]})")
    if all_types & _UGC_TYPES:
        ev.add("marketplace", 1.5, "user-generated-content JSON-LD (InteractionCounter/Review)")
    if reference_pages:
        ev.add("reference", 3 if reference_pages >= 2 else 2, f"reference JSON-LD on {reference_pages} page(s)")
    # personal: an individual's site. Person/ProfilePage identity, single authorship,
    # profile links, homepage Person -- and, decisively, no Organization entity anywhere.
    if many_persons:
        ev.add("marketplace", 2, f"{len(persons)} distinct Person entities (user profiles)")
    if person_entity and not org_entity and not many_persons:
        ev.add("personal", 3, "Person JSON-LD and no Organization entity")
        if profile_page:
            ev.add("personal", 2, "ProfilePage / og:type=profile")
        if home_types & _PERSONAL_TYPES:
            ev.add("personal", 2, "Person JSON-LD on the homepage")
        if single_author:
            ev.add("personal", 2, f"single author across articles ({next(iter(authors))[:30]})")
        if profile_links >= 2:
            ev.add("personal", 1, f"{profile_links} outbound profile links from home/about")
        if dated_pages >= 2 or article_count >= 3:
            ev.add("personal", 1, "blog-shaped")
    elif single_author and not org_entity and not (cart_links or has_pricing):
        ev.add("personal", 2, f"single author across articles, no Organization entity")
    if first_person and not org_entity and not many_persons and not (cart_links or has_pricing):
        ev.add("personal", min(3.0, 1.5 + 0.5 * first_person), f"first-person self-description on home/about ({first_person})")
        if profile_links >= 2:
            ev.add("personal", 1, f"{profile_links} outbound profile links")

    # ===== structure: what the inventory is made of (proportions on inventory only) =====
    if product_count + category_count >= 3:
        # a catalogue with no cart/store/platform evidence anywhere is structure only
        cap = 5.0 if shop_cues else 3.0
        ev.add("ecommerce", min(cap, 8 * share(product_count + category_count) + (1 if product_count >= 20 else 0)),
               f"catalogue paths product={product_count} category={category_count} of {total}" + ("" if shop_cues else " (no shop affordance seen)"))
    if doc_count >= 3:
        ev.add("documentation", min(4.0, 8 * share(doc_count)) + (1 if doc_count >= 10 else 0),
               f"documentation paths {doc_count}/{total}")
    if article_count >= 5:
        # capped at 3: a blog section is evidence, not a verdict -- identity outweighs it.
        ev.add("news_editorial", min(3.0, 6 * share(article_count)) + (0.5 if len(article_dates) >= 3 else 0),
               f"article paths {article_count}/{total}, {len(article_dates)} distinct dates")
    if wiki_paths >= 5:
        ev.add("reference", 4, f"/wiki/ paths ({wiki_paths})")
    if market_links >= 3:
        ev.add("marketplace", min(3.0, market_links / 4), f"listing-shaped paths ({market_links})")
    if user_paths >= 3:
        ev.add("marketplace", min(2.0, user_paths / 5), f"user/profile paths ({user_paths})")
    if inst_links >= 2:
        ev.add("institutional", min(2.0, inst_links / 4), f"institutional paths ({inst_links})")
    if ref_links >= 3:
        ev.add("reference", min(2.0, ref_links / 6), f"reference-shaped paths ({ref_links})")
    for lab, rx in _SITEMAP_NAME_HINTS:
        hits = [n for n in sitemap_names if rx.search(n)]
        if hits:
            ev.add(lab, min(2.0, 1.0 * len({re.sub(r"[\d_.-]+", "", h.lower()) for h in hits})), f"sitemap files {', '.join(hits[:3])[:50]}")
    if has_pricing:
        ev.add("saas_marketing", 2, "pricing page in inventory")

    # ===== affordances: what the site invites you to do ================================
    if cart_links:
        ev.add("ecommerce", 4, f"cart link ({cart_links})")
    elif cart_text >= 2:
        ev.add("ecommerce", 1.5, f"shop/cart CTA text ({cart_text})")
    if saas_text >= 2:
        ev.add("saas_marketing", 2 + (1 if saas_text >= 6 else 0), f"trial/demo/signup CTAs ({saas_text})")
    if saas_links >= 1:
        ev.add("saas_marketing", 1, f"trial/demo/pricing links ({saas_links})")
    if local_links >= 2 and local_text >= 2:
        ev.add("local_business", 3, f"menu/locations/order links ({local_links}) and CTAs ({local_text})")
    elif local_links >= 1 or local_text >= 3:
        ev.add("local_business", 1, "some menu/locations/order cues")
    if market_text >= 2:
        ev.add("marketplace", 2, f"marketplace CTAs ({market_text})")
    if donate_links:
        ev.add("institutional", 2.5, f"donate/membership/volunteer links ({donate_links})")
    if home_declares_docs:
        ev.add("documentation", 2, f"homepage declares docs/tutorials ({home['title'][:30]!r})")

    # ===== sampled content, discounted when the inventory does not back it ==============
    # (the static sample is stratified by page type; 4 fetched /docs/ pages say nothing
    # about a site whose inventory is 3% docs)
    def backed(page_share: float) -> float:
        return 1.0 if page_share >= 0.15 else (0.5 if page_share >= 0.05 else 0.25)

    if has_offer_price:
        ev.add("ecommerce", 2 if shop_cues else 1, "priced Offer JSON-LD on fetched pages")
    if article_typed >= 3 and dated_pages >= 2:
        ev.add("news_editorial", 2 * backed(share(article_count)), f"{article_typed} article-typed fetched pages with dates")
    if n_content >= 3 and doc_titled / n_content >= 0.5:
        unanimous = doc_titled == n_content and n_content >= 4
        ev.add("documentation", 3 * max(backed(share(doc_count)), 0.75 if unanimous else 0.0),
               f"{doc_titled}/{n_content} fetched pages titled tutorial/reference/docs")
    if has_postal_address and total <= 15 and not org_entity:
        ev.add("local_business", 1.5, "postal address on a small site")
    if _EDITORIAL_GENERATOR_RE.search(generators) and article_count >= 3:
        ev.add("news_editorial", 0.5, f"editorial CMS ({generators.strip()[:20]})")

    # ===== vocabulary (weak, core-term gated) ============================================
    if VOCAB_FALLBACK_ENABLED:
        # Vocabulary describes what text mentions, not necessarily who operates the site.
        # It therefore cannot, by itself, establish institutional or SaaS identity: those
        # labels affect downstream scope rules. Vocabulary remains a tie-breaker once an
        # independent identity, structure, or affordance signal exists.
        pre_vocab_scores = dict(ev.score)
        vscores, vterms = _vocab_scores(sigs, basis_paths, hints.get("robots_txt"), hints.get("sitemap_urls"))
        vr = sorted(vscores.items(), key=lambda kv: -kv[1])
        (vtop, vtop_s), (_, vsecond_s) = vr[0], vr[1]
        if vtop_s >= 12 and vtop_s >= 1.5 * max(vsecond_s, 1.0):
            if vtop not in {"institutional", "saas_marketing"} or pre_vocab_scores[vtop] > 0:
                ev.add(vtop, min(3.0, 1.0 + (vtop_s - 8) / 10), f"vocabulary {vtop_s:.0f} ({', '.join(vterms[vtop][:2])})")

    # ===== counter-evidence ===============================================================
    commerce_identity = ecom_platform or is_store_org or bool(cart_links)
    saas_identity = is_saas_org or (has_pricing and saas_text >= 2)
    inst_identity = is_institutional_org or is_institutional_tld
    if commerce_identity:
        ev.add("news_editorial", -2, "counter: commerce identity")
        ev.add("saas_marketing", -2, "counter: cart present")
        ev.add("personal", -2, "counter: commerce identity")
    if saas_identity:
        ev.add("news_editorial", -2, "counter: pricing/software identity")
        ev.add("documentation", -1.5 if share(doc_count) < 0.4 else 0, "counter: SaaS with a help/developer section")
        ev.add("personal", -2, "counter: pricing/software identity")
    if inst_identity:
        ev.add("news_editorial", -2, "counter: institutional identity")
        ev.add("saas_marketing", -1, "counter: institutional identity")
        ev.add("personal", -3, "counter: institutional identity")
    if person_entity and not org_entity:
        ev.add("news_editorial", -3, "counter: author is a Person with no Organization entity")
    if is_news_org:
        ev.add("personal", -4, "counter: NewsMediaOrganization")
    if mostly_articles and not is_saas_org and not has_pricing:
        ev.add("saas_marketing", -2, "counter: fetched pages are mostly articles")
    if local_links >= 2 or local_text >= 3:
        ev.add("institutional", -1.5, "counter: local-business affordances")
    if total > 60 and not home_local and any_local:
        ev.add("local_business", -2, "counter: large site, business entities only on listing pages")
    if market_text >= 2 or all_types & _MARKETPLACE_TYPES:
        ev.add("saas_marketing", -1.5, "counter: third-party listings / seller CTAs")
        ev.add("ecommerce", -1, "counter: third-party listings")
    if org_entity:
        ev.add("personal", -3, "counter: Organization entity present")

    label, conf, why = _decide(ev)
    if label != "unknown":
        return label, conf, why

    # ===== nothing decisive: honest fallbacks ==============================================
    if home["has_link_data"] and total <= 2 and home_internal_links == 0:
        return "unknown", 0.0, "homepage_no_links: JS shell or challenge page, nothing to classify"
    if total <= 5 and home_internal_links > 25:
        return "unknown", 0.0, f"discovery_starved: inventory={total}, homepage internal links={home_internal_links}"
    top_s = ev.ranked()[0][1]
    if total <= 8 and (home_internal_links or not home["has_link_data"]) and top_s < 2.5             and not (product_count or article_count >= 3 or doc_count):
        return "brochure", 0.6, f"small static site ({total} pages, {home_internal_links} homepage links), no structural evidence"
    return "unknown", 0.0, why


def classify_archetype(pages: list[dict], inventory: list[dict] | None = None,
                       hints: dict | None = None) -> tuple[str, float]:
    """Same contract as page_classifier.classify_archetype (`hints` is optional, see above)."""
    label, conf, _ = classify_archetype_detailed(pages, inventory, hints)
    return label, conf
