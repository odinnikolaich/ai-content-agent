"""Create the actual Russian voice from scene narration; verify before montage.

Use --generate to create gTTS / edge-tts speech samples, then --approve only
AFTER listening to the output. A technical TTS success is not good-quality
speech, especially if model names are mispronounced.
"""
from __future__ import annotations
import argparse
import asyncio
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from providers.video.snapgen_muse import sha256


def output_for(pack: Path, scene: dict):
    p = pack / "voice" / f"{scene['scene_id']}.mp3"
    p.parent.mkdir(exist_ok=True)
    return p


async def generate(pack: Path, scene: dict, provider: str):
    dest = output_for(pack, scene)
    dest.unlink(missing_ok=True)
    if provider == "gtts":
        from gtts import gTTS
        # One independent TTS request per 4/6/8s scene; never time-stretch.
        await asyncio.to_thread(gTTS(scene["narration"], lang="ru", slow=False).save, str(dest))
    elif provider == "edge":
        import edge_tts
        await edge_tts.Communicate(scene["narration"], voice="ru-RU-DmitryNeural", rate="+0%").save(str(dest))
    else:
        raise ValueError("Use 'gtts' or 'edge'")
    if not dest.is_file() or dest.stat().st_size < 1500:
        raise RuntimeError(f"Empty TTS MP3: {scene['scene_id']}")
    receipt = {
        "provider": provider,
        "scene_id": scene["scene_id"],
        "narration_sha256": hashlib.sha256(scene["narration"].encode("utf-8")).hexdigest(),
        "audio_sha256": sha256(dest),
        "human_audio_approved": False,
        "status": "GENERATED_AWAITING_LISTENING_REVIEW",
    }
    dest.with_suffix(".json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    return dest


def approve(pack: Path, scene: dict):
    dest = output_for(pack, scene)
    receipt_file = dest.with_suffix(".json")
    if not receipt_file.exists() or not dest.exists():
        raise RuntimeError("Cannot approve a missing generated sample")
    data = json.loads(receipt_file.read_text(encoding="utf-8"))
    if data.get("audio_sha256") != sha256(dest):
        raise RuntimeError("Audio changed since generation")
    if data.get("narration_sha256") != hashlib.sha256(scene["narration"].encode("utf-8")).hexdigest():
        raise RuntimeError("Audio was generated for different narration")
    data["human_audio_approved"] = True
    data["status"] = "LISTENED_AND_APPROVED_FOR_PREVIEW"
    receipt_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pack", type=Path, required=True)
    p.add_argument("--scene", default="all")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--generate", choices=["gtts", "edge"])
    g.add_argument("--approve", action="store_true")
    args = p.parse_args()
    manifest = json.loads((args.pack / "muse_manifest.json").read_text(encoding="utf-8"))
    scenes = [x for x in manifest["scenes"] if args.scene in ("all", x["scene_id"])]
    if not scenes:
        raise RuntimeError("Unknown scene")
    for scene in scenes:
        val = approve(args.pack, scene) if args.approve else asyncio.run(generate(args.pack, scene, args.generate))
        print(scene["scene_id"], val)

if __name__ == "__main__":
    main()