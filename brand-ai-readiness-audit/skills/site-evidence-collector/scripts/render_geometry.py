"""Classify already-measured render-pass geometry into the `rendered[]` bundle fields.

This module does not drive a browser — that is the agent's `headless_browser` tool,
invoked per SKILL.md step 5. It takes the raw measurements that tool produces (element
boxes, computed styles, z-index, viewport dimensions) and applies the deterministic
classification rules from procedure.md §5's "Detector definitions", which is the part that
actually needs to be identical across repeated runs for D-010's pass^k stability.

Expected raw element shape (from the headless_browser evaluation the agent runs):
{
  "selector": str, "tag": str,
  "rect": {"x": float, "y": float, "w": float, "h": float},
  "position": "fixed" | "absolute" | "static" | "relative" | "sticky",
  "z_index": int | None,
  "display": "inline" | "block" | "inline-block" | ...,
  "text_content": str,
  "is_interactive": bool,           # <a>, <button>, role=button/link, etc.
  "is_iframe": bool, "iframe_registrable_domain": str | None, "page_registrable_domain": str,
  "ad_slot_attrs": bool,            # data-ad*, id/class matching ^(ad|ads|advert)[-_]
  "filterlist_match": bool,
  "computed_style": {"color": "rgb(r,g,b)", "background_color": "rgb(r,g,b)",
                       "font_size_px": float, "font_weight": int},
}
"""
from __future__ import annotations

import re

COOKIE_KEYWORDS = re.compile(r"cookie|consent|gdpr|privacy preference", re.I)
AGE_KEYWORDS = re.compile(r"are you (over|at least)|verify your age|age.?gate|confirm you.re \d", re.I)

_RGB_RE = re.compile(r"rgba?\(\s*([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)")


def viewport_area(viewport_w: float, viewport_h: float) -> float:
    return viewport_w * viewport_h


def rect_area(rect: dict) -> float:
    return max(0.0, rect.get("w", 0)) * max(0.0, rect.get("h", 0))


def classify_overlays(elements: list[dict], viewport_w: float, viewport_h: float) -> list[dict]:
    """procedure.md §5: position fixed|absolute, z-index >= 999, covering >= 50% of the
    viewport, present at load with no interaction (caller must only pass load-time
    elements — this function does not know about timing)."""
    total_area = viewport_area(viewport_w, viewport_h)
    overlays = []
    for el in elements:
        if el.get("position") not in ("fixed", "absolute"):
            continue
        z = el.get("z_index")
        if z is None or z < 999:
            continue
        coverage_pct = (rect_area(el.get("rect", {})) / total_area * 100) if total_area else 0
        if coverage_pct < 50:
            continue
        text = el.get("text_content", "") or ""
        if COOKIE_KEYWORDS.search(text):
            hint = "cookie"
        elif AGE_KEYWORDS.search(text):
            hint = "age"
        else:
            hint = "none"
        overlays.append({
            "selector": el.get("selector"),
            "z_index": z,
            "viewport_coverage_pct": round(coverage_pct, 1),
            "dismissible_hint": hint,
        })
    return overlays


def _distance(a: dict, b: dict) -> float:
    """Edge-to-edge distance between two axis-aligned rects; 0 if they overlap."""
    ax0, ay0 = a["x"], a["y"]
    ax1, ay1 = a["x"] + a["w"], a["y"] + a["h"]
    bx0, by0 = b["x"], b["y"]
    bx1, by1 = b["x"] + b["w"], b["y"] + b["h"]
    dx = max(bx0 - ax1, ax0 - bx1, 0)
    dy = max(by0 - ay1, ay0 - by1, 0)
    return (dx ** 2 + dy ** 2) ** 0.5


def classify_tap_targets(elements: list[dict]) -> list[dict]:
    """procedure.md §5: standalone=False when inline within a text run (the WCAG 2.2
    SC 2.5.8 exemption); spacing_px = distance to the nearest other target."""
    interactive = [el for el in elements if el.get("is_interactive")]
    targets = []
    for i, el in enumerate(interactive):
        rect = el.get("rect", {})
        standalone = el.get("display") not in ("inline",)
        nearest = min(
            (_distance(rect, other.get("rect", {})) for j, other in enumerate(interactive) if j != i),
            default=float("inf"),
        )
        targets.append({
            "selector": el.get("selector"),
            "w": rect.get("w", 0),
            "h": rect.get("h", 0),
            "standalone": standalone,
            "spacing_px": None if nearest == float("inf") else round(nearest, 1),
        })
    return targets


def classify_ad_regions(elements: list[dict]) -> tuple[list[dict], float]:
    """procedure.md §5: record every candidate with which detector(s) fired; only regions
    where >= 2 detectors agree contribute to `ad_area_pct_total`. Returns
    (ad_regions_list, ad_area_pct_total)."""
    regions = []
    total_area = 0.0
    total_viewport = None

    for el in elements:
        detectors = []
        if el.get("is_iframe") and el.get("iframe_registrable_domain") and \
                el.get("iframe_registrable_domain") != el.get("page_registrable_domain"):
            detectors.append("iframe_thirdparty")
        if el.get("ad_slot_attrs"):
            detectors.append("slot_attr")
        if el.get("filterlist_match"):
            detectors.append("filterlist")
        if not detectors:
            continue

        area = rect_area(el.get("rect", {}))
        vp = el.get("viewport_area")
        if vp:
            total_viewport = vp
        area_pct = (area / vp * 100) if vp else None

        for detector in detectors:
            regions.append({
                "selector": el.get("selector"),
                "area_pct": round(area_pct, 1) if area_pct is not None else None,
                "detector": detector,
            })

        if len(detectors) >= 2 and area_pct is not None:
            total_area += area

    ad_area_pct_total = round(total_area / total_viewport * 100, 1) if total_viewport else 0.0
    return regions, ad_area_pct_total


def _srgb_to_linear(channel_0_255: float) -> float:
    c = channel_0_255 / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(rgb: tuple[float, float, float]) -> float:
    r, g, b = (_srgb_to_linear(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(fg_rgb: tuple[float, float, float], bg_rgb: tuple[float, float, float]) -> float:
    """WCAG 2.x contrast ratio: (L1 + 0.05) / (L2 + 0.05), L1 the lighter of the two."""
    l1 = relative_luminance(fg_rgb)
    l2 = relative_luminance(bg_rgb)
    lighter, darker = max(l1, l2), min(l1, l2)
    return round((lighter + 0.05) / (darker + 0.05), 2)


def _parse_rgb(value: str) -> tuple[float, float, float] | None:
    match = _RGB_RE.search(value or "")
    if not match:
        return None
    return tuple(float(g) for g in match.groups())


def extract_contrast_pairs(text_elements: list[dict]) -> list[dict]:
    """text_elements: elements with a non-empty rendered box and computed_style. Skips any
    element whose color pair cannot be parsed rather than guessing a ratio."""
    pairs = []
    for el in text_elements:
        style = el.get("computed_style", {})
        fg = _parse_rgb(style.get("color", ""))
        bg = _parse_rgb(style.get("background_color", ""))
        if fg is None or bg is None:
            continue
        pairs.append({
            "selector": el.get("selector"),
            "fg": style.get("color"),
            "bg": style.get("background_color"),
            "ratio": contrast_ratio(fg, bg),
            "font_px": style.get("font_size_px"),
            "bold": bool(style.get("font_weight", 400) and style.get("font_weight", 400) >= 700),
        })
    return pairs


def build_viewport_measurement(
    elements: list[dict],
    interactive_elements: list[dict],
    viewport_w: float,
    viewport_h: float,
    document_scroll_width: float,
    body_scroll_locked: bool,
) -> dict:
    """One entry under `rendered[].viewports.{mobile_375,desktop_1280}` per
    docs/BUNDLE-SCHEMA.md. `contrast_pairs` is deliberately NOT here — the schema places
    it under the sibling `rendered[].computed_styles`, one set per rendered page rather
    than per viewport, since foreground/background colour doesn't change with viewport
    width the way layout geometry does."""
    ad_regions, ad_area_pct_total = classify_ad_regions(elements)
    return {
        "measured": True,
        "document_scroll_width": document_scroll_width,
        "horizontal_overflow": document_scroll_width > viewport_w,
        "body_scroll_locked": body_scroll_locked,
        "overlays": classify_overlays(elements, viewport_w, viewport_h),
        "tap_targets": classify_tap_targets(interactive_elements),
        "ad_regions": ad_regions,
        "ad_area_pct_total": ad_area_pct_total,
    }


def build_computed_styles(text_elements: list[dict]) -> dict:
    """`rendered[].computed_styles` per docs/BUNDLE-SCHEMA.md — one set per rendered page."""
    return {"contrast_pairs": extract_contrast_pairs(text_elements)}
