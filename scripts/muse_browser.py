"""SnapGen Muse AI: real-browser, zero-credit-only preflight and one-shot attempt.

Usage (in ai-content-agent project root):
  python scripts/muse_browser.py --pack workspace/projects/<id>/muse --scene scene_01
  python scripts/muse_browser.py --pack ... --scene scene_01 --generate

The first command does not click Generate. Both launch an isolated, persistent
Chrome profile and halt when Muse AI is not actually selected and explicitly
priced at ZERO. Never uses undocumented SnapGen APIs, steals Chrome cookies,
logs in on behalf of the user, bypasses a paywall, or enables paid models.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from providers.video.snapgen_muse import SITE, BLOCKED, validate_zero_price, sha256


def selected_model_controls(page) -> list[str]:
    """Don't confuse an unselected model menu option with an active model."""
    out = []
    selectors = (
        "select option:checked",
        "[role=combobox]",
        "[role=radio][aria-checked=true]",
        "[data-state=active]",
        "[aria-selected=true]",
        "button[aria-pressed=true]",
    )
    for selector in selectors:
        for element in page.locator(selector).all():
            try:
                if not element.is_visible():
                    continue
                t = element.inner_text(timeout=400).strip()
                if t:
                    out.append(" ".join(t.split())[:180])
            except Exception:
                continue
    return out


def require_form_evidence(page, seconds: int, resolution: str) -> tuple[str, str]:
    selected = selected_model_controls(page)
    active_muse = [v for v in selected if re.search(r"\bmuse\s*(?:ai)?\b", v, re.I)]
    if len(active_muse) != 1:
        raise RuntimeError("Muse AI is not unambiguously selected. Current active controls: " + repr(selected[:12]))
    # Fail closed when the site changed its form or settings aren't exposed.
    active = " ".join(selected)
    checks = [resolution in active, "9:16" in active,
              bool(re.search(rf"(?<!\d){seconds}\s*(?:s|sec|seconds)\b", active, re.I))]
    if not all(checks):
        raise RuntimeError("Requested resolution/aspect/duration not verified in active form controls")
    return active_muse[0], active


def get_prompt_field(page):
    elements = page.locator("textarea:visible, [contenteditable=true]:visible")
    if elements.count() != 1:
        raise RuntimeError("SnapGen prompt editor is missing/ambiguous")
    return elements.first


def run(pack_path: Path, scene_id: str, generate: bool, *, headless: bool = False) -> dict:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("Install optional Playwright browser package") from exc
    base = Path(pack_path).resolve()
    manifest = json.loads((base / "muse_manifest.json").read_text(encoding="utf-8"))
    scenes = [x for x in manifest["scenes"] if x["scene_id"] == scene_id]
    if len(scenes) != 1:
        raise RuntimeError("Unknown scene id")
    scene = scenes[0]
    if scene.get("generation_blocker"):
        raise RuntimeError(f"Scene requires authentic UI/product reference: {scene_id}")
    text = (base / scene["prompt_file"]).read_text(encoding="utf-8")
    if not text.strip() or len(text) > 6000:
        raise RuntimeError("Prompt absent/too long")
    receipt_file = base / "receipts" / f"{scene_id}.json"
    if receipt_file.is_file():
        past = json.loads(receipt_file.read_text(encoding="utf-8"))
        if past.get("attempted"):
            raise RuntimeError("Previously attempted scene; don't double-charge/double-submit")
    with sync_playwright() as pw:
        chrome = (Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
                  if sys.platform == "win32" else None)
        if chrome and not chrome.is_file():
            chrome = None
        context = pw.chromium.launch_persistent_context(
            str(ROOT / "workspace" / "browser_profiles" / "snapgen_muse"),
            executable_path=str(chrome) if chrome else None,
            headless=headless, accept_downloads=True,
            viewport={"width": 1366, "height": 900})
        try:
            page = context.pages[0] if context.pages else context.new_page()
            page.goto(SITE.rstrip("/") + "/studio/", wait_until="domcontentloaded", timeout=45000)
            # No automatic clicking through login, consent, billing or unknown menu.
            # A separate --setup command handles manual authorization.
            page.wait_for_timeout(2500)
            if not page.url.startswith(SITE):
                raise RuntimeError("Browser left trusted SnapGen origin")
            editor = get_prompt_field(page)
            editor.fill(text)
            page.wait_for_timeout(400)
            active_muse, _ = require_form_evidence(
                page, scene["seconds"], scene["resolution"])
            body = page.locator("body").inner_text(timeout=4000)
            quote = validate_zero_price(
                body, selected_model=active_muse,
                resolution=scene["resolution"],
                aspect=scene["aspect"], seconds=scene["seconds"])
            photo = base / "receipts" / f"{scene_id}_price.png"
            page.screenshot(path=str(photo), full_page=False)
            receipt = {**quote, "site": page.url, "scene_id": scene_id,
                       "prompt_sha256": sha256(base / scene["prompt_file"]),
                       "price_screenshot": str(photo),
                       "attempted": False,
                       "mp4_delivered": False}
            if generate:
                button = page.get_by_role("button", name=re.compile(r"^Generate(?:\s+Video)?$", re.I))
                if button.count() != 1 or not button.is_enabled():
                    raise RuntimeError("Generate button ambiguous or disabled")
                # Re-check all values immediately before submission.
                active_muse, _ = require_form_evidence(
                    page, scene["seconds"], scene["resolution"])
                validate_zero_price(page.locator("body").inner_text(timeout=3000),
                                    selected_model=active_muse,
                                    resolution=scene["resolution"],
                                    aspect=scene["aspect"], seconds=scene["seconds"])
                receipt["attempted"] = True
                receipt["status"] = "ATTEMPTED_STATUS_UNKNOWN"
                receipt["attempted_at"] = datetime.now(timezone.utc).isoformat()
                receipt_file.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
                try:
                    button.click(timeout=12000)
                    page.wait_for_timeout(1700)
                    if BLOCKED.search(page.locator("body").inner_text(timeout=4000)):
                        receipt["status"] = "BLOCKED_BY_FREE_ACCESS_NOTICE"
                    else:
                        receipt["status"] = "SUBMITTED_AWAITING_MP4"
                except Exception as exc:
                    receipt["status"] = "UNKNOWN_OUTCOME_DO_NOT_RETRY"
                    receipt["error_type"] = type(exc).__name__
                    raise
                finally:
                    receipt_file.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
            else:
                receipt["status"] = "PRICE_CHECK_ONLY_NO_GENERATION"
                receipt_file.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
            return receipt
        finally:
            context.close()


def setup_profile():
    """One-time private login window; no passwords enter the chat or script."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        chrome = (Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
                  if sys.platform == "win32" else None)
        # A clean dedicated profile avoids accessing a user's browser secrets.
        context = pw.chromium.launch_persistent_context(
            str(ROOT / "workspace" / "browser_profiles" / "snapgen_muse"),
            executable_path=str(chrome) if chrome and chrome.is_file() else None,
            headless=False, viewport={"width": 1366, "height": 900})
        try:
            page = context.pages[0] if context.pages else context.new_page()
            page.goto(SITE, wait_until="domcontentloaded", timeout=45000)
            print("Log into SnapGen in this Chrome window. When done, press Enter in the terminal.", flush=True)
            try:
                input()
            except EOFError:
                raise RuntimeError("Interactive login requires an open terminal (not background execution)")
            print("Browser profile saved. No generation was started.", flush=True)
        finally:
            context.close()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pack", type=Path)
    p.add_argument("--scene")
    p.add_argument("--generate", action="store_true")
    p.add_argument("--headless", action="store_true")
    p.add_argument("--setup", action="store_true", help="one-time sign in to isolated Chrome profile")
    args = p.parse_args()
    if args.setup:
        if args.generate or args.headless:
            raise RuntimeError("Login setup must be visible and may not generate")
        setup_profile()
        return
    if not args.pack or not args.scene:
        p.error("--pack and --scene are required unless --setup is used")
    print(json.dumps(run(args.pack, args.scene, args.generate,
                         headless=args.headless), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()