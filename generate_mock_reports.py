import json
import random
from datetime import datetime

websites_data = [
    ("shein.com", "Dynamic e-commerce, product listings, filters, images, mobile interactions"),
    ("temu.com", "Highly dynamic marketplace pages and dense interactive UI"),
    ("aliexpress.com", "Large product catalog, filters, dynamic content and scripts"),
    ("wayfair.com", "Product-heavy pages, filters, images and navigation"),
    ("walmart.com", "Large navigation structure, product pages, forms and dynamic UI"),
    ("ebay.com", "Search, filters, product listings and dynamic content"),
    ("etsy.com", "Image-heavy listings, seller identity and search/filter interactions"),
    ("newegg.com", "Dense product comparison and filtering interfaces"),
    ("homedepot.com", "Complex navigation, search, filters and product content"),
    ("lowes.com", "Product navigation, filters, forms and dynamic content"),
    ("cnn.com", "Ad-heavy, dynamic news pages and dense navigation"),
    ("forbes.com", "Heavy pages, advertisements and dynamically loaded articles"),
    ("foxnews.com", "Dense navigation, advertising and media modules"),
    ("usatoday.com", "Dynamic content, advertising and article modules"),
    ("dailymail.co.uk", "Very dense pages, advertisements, images and links"),
    ("the-sun.com", "Dense articles, advertisements, media and navigation"),
    ("weather.com", "Highly dynamic content, scripts, advertisements and modules"),
    ("tripadvisor.com", "Reviews, dynamic widgets, filters and interactive content"),
    ("expedia.com", "Complex search forms and dynamically generated results"),
    ("kayak.com", "Dynamic search, filters and client-side rendering"),
    ("skyscanner.net", "Search forms, dynamic results and filters"),
    ("booking.com", "Complex forms, dynamic inventory and filtering"),
    ("indeed.com", "Job search, filters, listings and dynamic UI"),
    ("glassdoor.com", "Dynamic content, forms and interactive pages"),
    ("linkedin.com", "Highly dynamic content feed and interactive controls"),
    ("ziprecruiter.com", "Job search, filtering, forms and listings"),
    ("zillow.com", "Map-heavy interface, dynamic listings and filters"),
    ("realtor.com", "Search forms, maps, filters and listing cards"),
    ("redfin.com", "Interactive maps, dynamic listings and filters"),
    ("apartments.com", "Search/filter controls and dynamic listing content"),
    ("webmd.com", "Content-heavy pages, advertisements and navigation"),
    ("healthline.com", "Article-heavy pages, advertisements and images"),
    ("medicalnewstoday.com", "Content-heavy pages, advertisements and article modules"),
    ("verywellhealth.com", "Article pages, navigation and media"),
    ("drugs.com", "Large reference corpus, navigation and entity information"),
    ("w3schools.com", "Large documentation corpus and interactive examples"),
    ("tutorialspoint.com", "Large content corpus and dense navigation"),
    ("geeksforgeeks.org", "Dense content, advertisements, navigation and code blocks"),
    ("javatpoint.com", "Large documentation corpus and navigation"),
    ("craigslist.org", "Older/minimal markup, forms, links and inconsistent structure"),
    ("yellowpages.com", "Large directory, search/forms and business identity"),
    ("superpages.com", "Directory structure, links and business identity"),
    ("mapquest.com", "Dynamic maps, search and forms"),
    ("manta.com", "Business directory and entity-identity testing"),
    ("britannica.com", "Large content corpus, navigation and structured articles"),
    ("fandom.com", "Dynamic content, advertisements and navigation"),
    ("quora.com", "Dynamic content, interactive modules and identity signals"),
    ("medium.com", "Dynamic publishing pages and author identity"),
    ("substack.com", "Publisher/author identity and dynamic content"),
    ("mcdonalds.com", "Location search, menus and dynamic modules"),
    ("dominos.com", "Ordering forms, location selection and dynamic UI"),
    ("tacobell.com", "Menu interactions and ordering flows"),
    ("chipotle.com", "Ordering, menus, location and forms"),
    ("doordash.com", "Dynamic search, location, listings and interactive UI"),
    ("paypal.com", "Forms, account-related flows and dynamic UI"),
    ("robinhood.com", "App-like dynamic UI, charts and interaction"),
    ("coinbase.com", "Dynamic pricing, forms and app-like pages"),
    ("fidelity.com", "Complex navigation, forms and dense content"),
    ("nerdwallet.com", "Content, calculators, forms and advertisements"),
    ("salesforce.com", "Large marketing pages, forms and scripts"),
    ("hubspot.com", "Marketing content, forms and dynamic modules"),
    ("zendesk.com", "Documentation, product content and navigation"),
    ("notion.so", "App-like navigation and client-side content"),
    ("canva.com", "Highly interactive app and dynamic pages"),
    ("shopify.com", "E-commerce platform pages, forms and dynamic content"),
    ("wordpress.com", "Dynamic publishing pages, navigation and forms"),
    ("wix.com", "Client-side rendering and dynamic website-builder pages"),
    ("squarespace.com", "Dynamic marketing pages, forms and scripts"),
    ("weebly.com", "Builder generated pages, forms and scripts"),
    ("adrianroselli.com", "Accessibility focused real-world site useful for engagement testing"),
    ("w3.org", "Useful accessibility-defect case"),
    ("lanecc.edu", "Useful accessibility-defect case"),
    ("project2025.org", "Useful document-language/accessibility case"),
    ("web.dev", "Useful accessibility-defect case"),
    ("gohugo.io", "Strong documentation/static site baseline and control"),
    ("docs.python.org", "Structured documentation and crawlability control"),
    ("docs.djangoproject.com", "Structured documentation, navigation and links"),
    ("developer.mozilla.org", "Large structured documentation corpus"),
    ("github.com", "Large, complex site useful for crawl/render/entity testing"),
    ("wikipedia.org", "Huge structured corpus and strong internal linking"),
    ("mozilla.org", "Organizational identity and structured content"),
    ("python.org", "Clear organization/entity and documentation structure"),
    ("nasa.gov", "Large government/science content corpus"),
    ("mit.edu", "Institutional identity and content-rich baseline")
]

possible_findings = [
    {
        "title": "Missing JSON-LD structured data",
        "severity": "high",
        "evidence_template": "Crawled pages on {site} based on characteristics: {desc}. Missing schema.org markup.",
        "suggested_action": {
            "summary": "Add relevant JSON-LD structured data to improve off-site discoverability.",
            "priority": "high"
        }
    },
    {
        "title": "Potential bounce factor on mobile",
        "severity": "medium",
        "evidence_template": "Analyzed interaction footprint for {desc}. Time to interactive is high.",
        "suggested_action": {
            "summary": "Optimize main thread scripts to improve on-site engagement.",
            "priority": "medium"
        }
    },
    {
        "title": "Inaccessible semantic HTML",
        "severity": "critical",
        "evidence_template": "Detected non-semantic elements overriding core accessibility structure on {site}.",
        "suggested_action": {
            "summary": "Replace presentational div spans with standard HTML5 semantic elements.",
            "priority": "high"
        }
    },
    {
        "title": "Low contrast ratios on key content",
        "severity": "medium",
        "evidence_template": "Contrast on text related to '{desc}' falls below WCAG AA thresholds.",
        "suggested_action": {
            "summary": "Adjust foreground/background color combinations to meet 4.5:1 ratio.",
            "priority": "medium"
        }
    },
    {
        "title": "Broken internal links",
        "severity": "low",
        "evidence_template": "Found 3 broken internal links while parsing {site}.",
        "suggested_action": {
            "summary": "Fix or remove broken internal links to prevent negative SEO impact.",
            "priority": "low"
        }
    },
    {
        "title": "Missing meta description tags",
        "severity": "high",
        "evidence_template": "Homepage and 4 subpages lack meta description tags.",
        "suggested_action": {
            "summary": "Add unique, descriptive meta descriptions to all key pages.",
            "priority": "high"
        }
    }
]

reports = []
random.seed(42) # For reproducibility

for site, desc in websites_data:
    num_findings = random.randint(1, 6)
    selected_findings = random.sample(possible_findings, num_findings)
    
    findings = []
    summary_counts = {"total_findings": num_findings, "critical": 0, "high": 0, "medium": 0, "low": 0}
    
    for i, base_finding in enumerate(selected_findings):
        severity = base_finding["severity"]
        summary_counts[severity] += 1
        
        finding = {
            "id": f"F-{i+1:03}",
            "title": base_finding["title"],
            "severity": severity,
            "evidence": base_finding["evidence_template"].format(site=site, desc=desc),
            "suggested_action": base_finding["suggested_action"]
        }
        findings.append(finding)
    
    # Remove 'low' from summary if it's 0 to match schema style, but plan didn't restrict to 3 severities
    if summary_counts["low"] == 0:
        del summary_counts["low"]
        
    report = {
        "site": site,
        "audited_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "description_context": desc,
        "summary": summary_counts,
        "findings": findings
    }
    reports.append(report)

with open("mock_reports.json", "w") as f:
    json.dump(reports, f, indent=2)

print("Generated mock_reports.json with randomized findings.")
