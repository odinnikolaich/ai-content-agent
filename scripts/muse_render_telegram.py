"""Assemble only verified, genuine Muse clips; optionally deliver to Telegram.

IMPORTANT: no stock substitution, no repeated photo zoom, no fabricated QAs.
The render deliberately fails unless all clips have real remote semantic QA,
video streams pass native resolution/FPS checks, and individually approved
Russian narration segments match the exact script text.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from providers.video.snapgen_muse import check_remote_evidence, probe_video, sha256


def commands(args: list[str], *, timeout: int = 600, cwd: Path | None = None) -> str:
    p = subprocess.run([str(x) for x in args], text=True, capture_output=True,
                       cwd=cwd, timeout=timeout)
    if p.returncode:
        raise RuntimeError(f"FFmpeg failed ({p.returncode}): {p.stderr[-1200:]}")
    return p.stdout


def stamp(t: float) -> str:
    cs = round(t * 100)
    h, cs = divmod(cs, 360_000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02}:{s:02}.{cs:02}"


def phrases(text: str, limit: int = 30) -> list[str]:
    if "\\" in text or "{" in text or "}" in text or "\n" in text:
        raise RuntimeError("Unsafe/invalid subtitle text")
    result, buf = [], []
    for word in text.split():
        if len(word) > limit:
            raise RuntimeError("Word wider than subtitle safe area")
        test = " ".join([*buf, word])
        if len(test) > limit and buf:
            result.append(" ".join(buf))
            buf = []
        buf.append(word)
        if word.endswith((".", "?", "!")):
            result.append(" ".join(buf))
            buf = []
    if buf:
        result.append(" ".join(buf))
    if " ".join(result) != " ".join(text.split()):
        raise RuntimeError("Subtitle content differs from TTS transcript")
    return result


def subtitle_ass(text: str, voice_duration: float, full_duration: float, out: Path) -> dict:
    rows = phrases(text)
    weights = [sum(max(1, len(w)) for w in x.split()) for x in rows]
    if not weights or voice_duration < 0.5:
        raise RuntimeError("No audible speech duration")
    factor = voice_duration / sum(weights)
    header = [
        "[Script Info]", "Title: Verbatim narration (not raw Whisper guesses)",
        "ScriptType: v4.00+", "PlayResX: 720", "PlayResY: 1280",
        "WrapStyle: 2", "ScaledBorderAndShadow: yes", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: Clean,Arial,28,&H00FFFFFF,&H00FFFFFF,&H80000000,&H80000000,-1,0,0,0,100,100,0,0,1,2,0,2,40,40,132,1",
        "", "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
    ]
    cursor = 0.08
    max_cue = 0
    for phrase, weight in zip(rows, weights):
        end = min(voice_duration + 0.08, cursor + weight * factor)
        if end <= cursor + 0.08 or end - cursor > 2.5:
            raise RuntimeError("Caption timing unsuitable; adjust script / word alignment")
        header.append(f"Dialogue: 0,{stamp(cursor)},{stamp(end)},Clean,,0,0,0,,{phrase}")
        max_cue = max(max_cue, len(phrase))
        cursor = end
    if cursor > full_duration + 0.01:
        raise RuntimeError("Caption extends outside scene")
    out.write_text("\n".join(header) + "\n", encoding="utf-8-sig")
    return {"number_of_cues": len(rows), "max_characters": max_cue,
            "text_source": "EXACT_TTS_NARRATION", "timing": "CHARACTER_ESTIMATE_VERIFY_BEFORE_PUBLISH"}


def voice_info(pack: Path, row: dict, ffprobe: str) -> tuple[Path, float]:
    speech = pack / "voice" / f'{row["scene_id"]}.mp3'
    receipt = speech.with_suffix(".json")
    if not speech.is_file() or not receipt.is_file():
        raise RuntimeError(f"Approved Russian voice missing: {row['scene_id']}")
    r = json.loads(receipt.read_text(encoding="utf-8"))
    text_hash = hashlib.sha256(row["narration"].encode("utf-8")).hexdigest()
    if r.get("narration_sha256") != text_hash or not r.get("human_audio_approved"):
        raise RuntimeError(f"Speech not verified to match transcript: {row['scene_id']}")
    if r.get("audio_sha256") != sha256(speech):
        raise RuntimeError(f"Speech audio modified after QA: {row['scene_id']}")
    # Audio-only MP3 probe via ffprobe uses format stream rather than video.
    p = commands([ffprobe, "-v", "error", "-show_entries", "format=duration",
                  "-of", "default=noprint_wrappers=1:nokey=1", speech], timeout=25)
    dur = float(p.strip())
    if not .8 <= dur <= row["seconds"] - .15:
        raise RuntimeError(f"Voice exceeds {row['seconds']}s scene: {row['scene_id']}={dur}")
    return speech, dur


def assemble(pack: Path, output: Path, *, ffmpeg: str = "ffmpeg", ffprobe: str = "ffprobe") -> dict:
    pack = Path(pack)
    validation = check_remote_evidence(pack)
    manifest = json.loads((pack / "muse_manifest.json").read_text(encoding="utf-8"))
    if validation["count"] != len(manifest["scenes"]):
        raise RuntimeError("Not all scenes inspected")
    staging = pack / "montage"
    staging.mkdir(exist_ok=True)
    parts = []
    captions = []
    for i, row in enumerate(manifest["scenes"], 1):
        source = pack / row["import_file"]
        speech, voice_duration = voice_info(pack, row, ffprobe)
        ass = staging / f'scene_{i:02d}.ass'
        caption_qa = subtitle_ass(row["narration"], voice_duration, row["seconds"], ass)
        captions.append(caption_qa)
        part = staging / f'scene_{i:02d}.mp4'
        # Windows path with ffmpeg libass: resolve relative to staging via cwd.
        video_filter = ("scale=720:1280:force_original_aspect_ratio=increase,"
                        "crop=720:1280,setsar=1,"
                        "fps=25,format=yuv420p,"
                        f"subtitles=scene_{i:02d}.ass")
        commands([ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
                  "-i", source.resolve(), "-i", speech.resolve(),
                  "-filter_complex", f"[0:v]{video_filter}[v];[1:a]aresample=48000,apad[a]",
                  "-map", "[v]", "-map", "[a]",
                  "-t", row["seconds"], "-c:v", "libx264",
                  "-preset", "veryfast", "-crf", "20", "-threads", "2",
                  "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                  "-ar", "48000", "-ac", "1", "-movflags", "+faststart", part],
                 timeout=600, cwd=staging)
        # Preserve original camera footage, never still-frame-pad a short source.
        stats = probe_video(part, ffprobe=ffprobe)
        if abs(stats["duration"] - row["seconds"]) > .1:
            raise RuntimeError("Short or malformed video segment")
        parts.append(part)
    concat_file = staging / "clips.txt"
    concat_file.write_text("".join("file '" + p.name + "'\n" for p in parts), encoding="utf-8")
    output.parent.mkdir(parents=True, exist_ok=True)
    commands([ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
              "-f", "concat", "-safe", "0", "-i", concat_file,
              "-c", "copy", "-movflags", "+faststart", output.resolve()],
             cwd=staging, timeout=100)
    final_stats = probe_video(output, ffprobe)
    if not 43 <= final_stats["duration"] <= 60:
        raise RuntimeError("Final 43–60s duration QA failed")
    audit = {"status": "TECHNICAL_PASS_EDITORIAL_PREVIEW",
             "semantics": "PASSED_PER_CLIP_REMOTE_QA",
             "audio": "Human-approved Russian speech receipts",
             "captions": captions,
             "narration_timing": "ESTIMATED_WITHIN_SCENE",
             "human_final_preview_required": True,
             "final_mp4": str(output), "stats": final_stats, "created_at": datetime.now(timezone.utc).isoformat()}
    (pack / "qa" / "final_qa_report.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    return audit


async def send_telegram(pack: Path, output: Path, *, env_path: Path) -> dict:
    qa_file = pack / "qa" / "final_qa_report.json"
    if not qa_file.is_file():
        raise RuntimeError("No final QA report")
    qa = json.loads(qa_file.read_text(encoding="utf-8"))
    if qa.get("status") != "TECHNICAL_PASS_EDITORIAL_PREVIEW":
        raise RuntimeError("Final QA not approved")
    if qa["stats"]["sha256"] != sha256(output):
        raise RuntimeError("Video changed since final QA")
    receipt_path = pack / "telegram_receipt.json"
    if receipt_path.is_file():
        raise RuntimeError("Already delivered: avoid duplicate Telegram posts")
    import dotenv
    from telegram import Bot
    values = dotenv.dotenv_values(env_path)
    token = str(values.get("TELEGRAM_BOT_TOKEN") or "").strip()
    chat_id = str(values.get("TELEGRAM_DELIVERY_CHAT_ID") or "").strip()
    if not token or not re.fullmatch(r"\d{5,16}", chat_id):
        raise RuntimeError("Missing verified Telegram credentials/recipient")
    async with Bot(token) as bot:
        with output.open("rb") as f:
            result = await bot.send_video(
                chat_id=int(chat_id), video=f, width=720, height=1280,
                caption=("Muse AI — предварительный технический тест. "
                         "Проверьте качество, озвучку и соответствие каждой сцены тексту. "
                         "Не публиковать без финальной редакторской проверки."),
                supports_streaming=True, connect_timeout=60, read_timeout=250, write_timeout=250)
    if not result or not result.video or str(result.chat.id) != chat_id:
        raise RuntimeError("Telegram did not confirm upload")
    receipt = {"status": "TELEGRAM_PREVIEW_DELIVERED", "message_id": result.message_id,
               "chat_id": result.chat.id, "sha256": sha256(output),
               "sent_at": datetime.now(timezone.utc).isoformat()}
    receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    return receipt


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pack", type=Path, required=True)
    ap.add_argument("--output", type=Path, default=ROOT / "output" / "muse_ai_test.mp4")
    ap.add_argument("--send", action="store_true")
    ap.add_argument("--env", type=Path, default=ROOT / ".env")
    args = ap.parse_args()
    audit = assemble(args.pack, args.output)
    print(json.dumps(audit, ensure_ascii=False, indent=2))
    if args.send:
        result = asyncio.run(send_telegram(args.pack, args.output, env_path=args.env))
        print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()