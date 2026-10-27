"""Fail-closed SnapGen/Muse AI scene handoff for ai-content-agent.

No undocumented third-party API or fabricated quota. The browser extension never
uses a credit balance as evidence that a generation is free: the live quote must
be exactly zero immediately before submitting. Successful clicks are not videos.

Use 'prepare' to make 8 evidence-linked 6s shots and 'inspect' to probe imports.
Browser operations are deliberately opt-in, with screenshots and receipts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SITE = "https://snapgen.ai/"
# This is the dedicated Muse page; generic Studio mostly lists Veo/Grok.
MUSE_URL = "https://snapgen.ai/app/video-gen/muse"
VALID_DURATIONS = {4, 6, 8}
VALID_RESOLUTIONS = {"720p", "1080p"}
MIN_NATIVE_FPS = 24.0
MIN_NATIVE_SIZE = (720, 1280)
MIN_VIDEO_BITRATE = 500_000
PRICE = re.compile(r"\bthis\s+generation\s+will\s+cost\s*:?\s*(\d+(?:[.,]\d+)?)\s*credits\s+per\s+video\b", re.I)
BLOCKED = re.compile(r"temporarily\s+unavailable\s+for\s+free|only\s+for\s+premium|subscribe\s+to\s+generate|upgrade\s+to\s+(?:generate|continue)|model\s+maintenance", re.I)


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(file: Path) -> str:
    with file.open("rb") as f:
        h = hashlib.sha256()
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
        return h.hexdigest()


def safe_id(s: Any) -> str:
    item = str(s)
    if not re.fullmatch(r"scene_\d{2,3}", item):
        raise ValueError(f"Invalid scene_id: {item!r}")
    return item


def validate_zero_price(page_text: str, *, selected_model: str,
                        resolution: str, aspect: str, seconds: int) -> dict:
    """Recheck actual selected model, form settings and visible quote each time."""
    if not re.search(r"\bmuse\s*(?:ai)?\b", selected_model, re.I):
        raise RuntimeError("Blocked: active selected model is not Muse AI")
    if resolution not in VALID_RESOLUTIONS or aspect != "9:16" or seconds not in VALID_DURATIONS:
        raise RuntimeError("Blocked: invalid duration, resolution or aspect")
    if BLOCKED.search(page_text):
        raise RuntimeError("Blocked: paywall, free quota or model maintenance")
    offers = [float(x.replace(",", ".")) for x in PRICE.findall(page_text)]
    if not offers or len(offers) != 1 or offers[0] != 0.0:
        raise RuntimeError(f"Blocked: no unambiguous live zero-credit quote: {offers}")
    return {"model": selected_model, "price": 0, "credits": "0 Credits per video",
            "resolution": resolution, "aspect": aspect, "seconds": seconds,
            "checked_at": utc(), "status": "ZERO_QUOTE_VERIFIED"}


def prepare(plan_path: Path, pack_path: Path) -> dict:
    """Create one prompt per scene; facts without reference are blocked."""
    src = Path(plan_path)
    data = json.loads(src.read_text(encoding="utf-8"))
    scenes = data.get("scenes") or data.get("scene_plan", {}).get("scenes")
    if not isinstance(scenes, list) or not 6 <= len(scenes) <= 12:
        raise ValueError("Expected 6–12 authored scenes")
    base = Path(pack_path)
    for directory in ("prompts", "imports", "receipts", "qa", "references"):
        (base / directory).mkdir(parents=True, exist_ok=True)
    output = []
    seen = set()
    expected_start = 0.0
    for index, scene in enumerate(scenes, start=1):
        sid = safe_id(scene.get("scene_id", f"scene_{index:02d}"))
        if sid in seen:
            raise ValueError(f"Duplicate scene: {sid}")
        seen.add(sid)
        start, end = float(scene["start_seconds"]), float(scene["end_seconds"])
        if not (math.isfinite(start) and math.isfinite(end) and abs(start - expected_start) < 0.02):
            raise ValueError(f"Scene {sid} overlaps/gaps previous scene")
        seconds = int(round(end - start))
        if seconds not in VALID_DURATIONS or abs((end-start)-seconds) > 0.02:
            raise ValueError(f"Scene {sid} length must be 4, 6 or 8 seconds")
        expected_start = end
        narration = str(scene.get("narration") or scene.get("spoken_text") or "").strip()
        direction = str(scene.get("visual_direction") or "").strip()
        must_show = list(scene.get("must_show") or [])
        if not narration or not direction or not must_show:
            raise ValueError(f"Scene {sid} lacks narration, direction or visual contract")
        # A shot of a stranger pressing a remote is not enough to demonstrate
        # apps, port labels, meaningful image comparison, or model specifications.
        needs_real_reference = bool(scene.get("requires_verified_reference"))
        reference = str(scene.get("reference_file") or "").strip()
        if reference and (
                ".." in Path(reference).parts or Path(reference).is_absolute()
                or Path(reference).parts[:1] != ("references",)
                or Path(reference).suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}):
            raise ValueError("Reference must be a safe path within references/")
        real_reference = (base / reference) if reference else None
        if needs_real_reference and (not real_reference or not real_reference.is_file()):
            # Preparation is still useful. Mark generation blocked instead of
            # hallucinating UI labels and product port details.
            block = "REQUIRES_AUTHENTIC_PRODUCT_REFERENCE"
        else:
            block = None
        prompt = (
            f"Photorealistic live-action shot, genuine temporal motion, "
            f"portrait 9:16, {seconds} seconds, 720p or higher.\n"
            f"Scene: {direction}\n"
            f"VISIBLE REQUIRED EVIDENCE: {'; '.join(map(str, must_show))}.\n"
            "The action MUST be independently visible on the subject, not "
            "merely camera panning or zooming across one still photograph. "
            "No unrelated people pressing TV remotes, no invented brand names, "
            "no fake application UI or technical port labels, no watermarks, "
            "no captions rendered within generated image. "
            "If the scene depends on a real menu or product port panel, "
            "match the provided verified reference exactly; do not invent features."
        )
        (base / "prompts" / f"{sid}.txt").write_text(prompt, encoding="utf-8")
        output.append({"scene_id": sid, "narration": narration,
                       "start_seconds": start, "end_seconds": end,
                       "seconds": seconds, "resolution": "720p", "aspect": "9:16",
                       "must_show": must_show, "forbidden": scene.get("forbidden") or [],
                       "requires_verified_reference": needs_real_reference,
                       "reference_file": reference or None,
                       "reference_sha256": sha256(real_reference) if real_reference and real_reference.is_file() else None,
                       "generation_blocker": block,
                       "prompt_file": f"prompts/{sid}.txt",
                       "import_file": f"imports/{sid}.mp4"})
    if not 43 <= expected_start <= 60:
        raise ValueError(f"Total {expected_start}s outside 43–60s")
    manifest = {"provider": "snapgen_muse", "site": SITE,
                "model": "Muse AI Video (only if explicitly selected and free)",
                "model_available_now": False, "live_zero_cost_confirmed": False,
                "browser_generation_submitted": False,
                "status": "PROMPTS_PREPARED_NO_GENERATION",
                "source_plan_sha256": sha256(src),
                "scene_count": len(output), "total_seconds": expected_start,
                "scenes": output, "created_at": utc()}
    (base / "muse_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def probe_video(path: Path, ffprobe: str = "ffprobe") -> dict:
    file = Path(path)
    if not file.is_file() or file.stat().st_size < 500_000:
        raise RuntimeError("Video file missing, undersized or incomplete")
    res = subprocess.run([ffprobe, "-v", "error", "-show_streams", "-show_format",
                          "-of", "json", str(file)], capture_output=True,
                         text=True, timeout=35)
    if res.returncode:
        raise RuntimeError(f"FFprobe error: {res.stderr[-300:]}")
    data = json.loads(res.stdout)
    v = next((x for x in data.get("streams", []) if x.get("codec_type") == "video"), None)
    if not v:
        raise RuntimeError("No video stream")
    fraction = str(v.get("avg_frame_rate") or "0/1").split("/")
    fps = float(fraction[0]) / max(float(fraction[1]) if len(fraction) > 1 else 1.0, .00001)
    dur = float(v.get("duration") or data.get("format", {}).get("duration") or 0)
    bps = int(v.get("bit_rate") or data.get("format", {}).get("bit_rate") or 0)
    return {"width": int(v["width"]), "height": int(v["height"]),
            "fps": round(fps, 3), "duration": round(dur, 3),
            "bps": bps, "bytes": file.stat().st_size, "sha256": sha256(file)}


def quality_gate(stats: dict, expected_duration: int) -> list[str]:
    problems = []
    w, h = stats["width"], stats["height"]
    if w < MIN_NATIVE_SIZE[0] or h < MIN_NATIVE_SIZE[1]:
        problems.append(f"Native {w}x{h} below 720x1280")
    if w <= 0 or h <= 0 or abs((w / h) - (9/16)) > .03:
        problems.append("Wrong aspect ratio")
    if stats["fps"] < MIN_NATIVE_FPS:
        problems.append("Actual source below 24 fps")
    if stats["bps"] < MIN_VIDEO_BITRATE:
        problems.append("Insufficient native video bitrate")
    if stats["duration"] + .2 < expected_duration:
        problems.append("Missing motion seconds; do not pad by freezing last frame")
    if stats["duration"] > expected_duration + 1.0:
        problems.append("Unexpected video duration")
    return problems


def inspect(pack: Path, ffprobe: str = "ffprobe") -> dict:
    root = Path(pack)
    manifest = json.loads((root / "muse_manifest.json").read_text(encoding="utf-8"))
    results = []
    for row in manifest["scenes"]:
        source = root / row["import_file"]
        reasons = []
        stats = None
        if row["generation_blocker"]:
            reasons.append(row["generation_blocker"])
        if row["requires_verified_reference"]:
            ref_path = root / str(row["reference_file"] or "")
            if not ref_path.is_file():
                reasons.append("Verified product/menu/ports reference missing")
            elif sha256(ref_path) != row.get("reference_sha256"):
                reasons.append("Reference modified since scene plan creation")
        try:
            stats = probe_video(source, ffprobe)
            reasons.extend(quality_gate(stats, int(row["seconds"])))
        except (OSError, RuntimeError, ValueError, KeyError) as exc:
            reasons.append(str(exc))
        # Syntactic media checks do not confirm correct product, action or
        # absence of model watermark; those need actual semantic inspection.
        results.append({"scene_id": row["scene_id"],
                        "technical_status": "FAIL" if reasons else "PASS",
                        "semantic_status": "UNVERIFIED", "product_identity": "UNVERIFIED",
                        "subject_motion": "UNVERIFIED", "watermark": "UNVERIFIED",
                        "problems": reasons, "probe": stats})
    qa = {"provider": "snapgen_muse", "qa_status": "AWAITING_REMOTE_SEMANTIC_QA",
          "publication_approved": False, "ready_for_telegram": False,
          "tested_at": utc(), "scenes": results}
    (root / "qa" / "native_quality_report.json").write_text(
        json.dumps(qa, ensure_ascii=False, indent=2), encoding="utf-8")
    return qa


def check_remote_evidence(pack: Path) -> dict:
    """Strict semantic gate: reject synthetic/empty/historical PASS reports."""
    root = Path(pack)
    media_qa = inspect(root)
    if any(s["technical_status"] != "PASS" for s in media_qa["scenes"]):
        raise RuntimeError("Not every imported scene passed native media QA")
    evid = root / "qa" / "remote_semantic_report.json"
    if not evid.is_file():
        raise RuntimeError("Remote content QA has not inspected the actual clips")
    data = json.loads(evid.read_text(encoding="utf-8"))
    proofs = data.get("scenes", [])
    if not isinstance(proofs, list) or len(proofs) != len(media_qa["scenes"]):
        raise RuntimeError("Remote QA must contain one proof for each source MP4")
    lookup = {x["scene_id"]: x for x in proofs}
    if len(lookup) != len(proofs):
        raise RuntimeError("Remote QA duplicate scene identities")
    hashes = [s["probe"]["sha256"] for s in media_qa["scenes"]]
    if len(set(hashes)) != len(hashes):
        raise RuntimeError("Repeated source video: scenes must be visually independent")
    required = ("shows_must_show", "real_subject_motion", "product_identity_preserved",
                "visible_watermark_absent", "unrelated_action_absent", "accurate_real_menu_ports")
    for row in media_qa["scenes"]:
        sid = row["scene_id"]
        proof = lookup.get(sid)
        if not proof or proof.get("source_sha256") != row["probe"]["sha256"]:
            raise RuntimeError(f"Scene {sid} lacks matching actual MP4 evidence")
        if proof.get("status") != "PASS" or float(proof.get("score") or 0) < 85:
            raise RuntimeError(f"Scene {sid} failed remote content inspection")
        if not all(proof.get(item) is True for item in required):
            raise RuntimeError(f"Scene {sid}: visual claims not supported")
    return {"status": "SCENES_VERIFIED", "count": len(media_qa["scenes"])}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("prepare")
    a.add_argument("--plan", type=Path, required=True)
    a.add_argument("--pack", type=Path, required=True)
    b = sub.add_parser("inspect")
    b.add_argument("--pack", type=Path, required=True)
    c = sub.add_parser("verified")
    c.add_argument("--pack", type=Path, required=True)
    arg = parser.parse_args()
    result = (prepare(arg.plan, arg.pack) if arg.cmd == "prepare" else
              inspect(arg.pack) if arg.cmd == "inspect" else
              check_remote_evidence(arg.pack))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()