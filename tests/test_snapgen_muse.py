import importlib.util
import json
from pathlib import Path
import pytest

SRC = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("snapgen_muse", SRC / "src/providers/video/snapgen_muse.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_zero_only_with_selected_muse_and_exact_settings():
    r = mod.validate_zero_price("This generation will cost: 0 Credits per video", selected_model="Muse AI Video",
                                resolution="720p", aspect="9:16", seconds=6)
    assert r["price"] == 0 and r["status"] == "ZERO_QUOTE_VERIFIED"


@pytest.mark.parametrize("text", [
    "Remaining credits: 0", "This generation will cost: 1 Credits per video",
    "This generation will cost: 0 Credits per video\nThis generation will cost: 5 Credits per video",
    "This generation will cost: 0.5 Credits per video",
    "This generation will cost: 0 Credits per video. Muse AI temporarily unavailable for free users",
    "This generation will cost: 0 Credits per video. Upgrade to continue",
])
def test_price_and_access_fails_closed(text):
    with pytest.raises(RuntimeError, match="Blocked"):
        mod.validate_zero_price(text, selected_model="Muse AI Video",
                                resolution="720p", aspect="9:16", seconds=6)


def test_veo_must_not_be_mislabeled_muse():
    with pytest.raises(RuntimeError, match="not Muse"):
        mod.validate_zero_price("0 Credits per video", selected_model="Veo 3.1 Fast",
                                resolution="720p", aspect="9:16", seconds=6)


def test_muse_plan_8_scenes_and_factual_refs(tmp_path):
    source = SRC / "docs/tv_comparison_8_scenes.json"
    result = mod.prepare(source, tmp_path / "muse")
    assert result["scene_count"] == 8
    assert result["total_seconds"] == 48
    assert result["live_zero_cost_confirmed"] is False
    assert (tmp_path / "muse" / "prompts/scene_03.txt").is_file()
    assert result["scenes"][3]["generation_blocker"] == "REQUIRES_AUTHENTIC_PRODUCT_REFERENCE"
    assert "настоящие разъёмы" in (tmp_path / "muse" / "prompts/scene_05.txt").read_text()


def test_missing_mp4_never_allowed_to_telegram(tmp_path):
    root = tmp_path / "muse"
    mod.prepare(SRC / "docs/tv_comparison_8_scenes.json", root)
    report = mod.inspect(root)
    assert report["qa_status"] == "AWAITING_REMOTE_SEMANTIC_QA"
    assert report["ready_for_telegram"] is False
    assert all(item["technical_status"] == "FAIL" for item in report["scenes"])
    with pytest.raises(RuntimeError):
        mod.check_remote_evidence(root)


def test_aspect_resolution_and_fps_enforced():
    bad = {"width": 256, "height": 448, "fps": 4.5, "duration": 6.0,
           "bps": 400000, "bytes": 3_000_000}
    problems = mod.quality_gate(bad, 6)
    assert len(problems) >= 3
    good = {"width": 720, "height": 1280, "fps": 25, "duration": 6.03,
            "bps": 1_500_000, "bytes": 3_000_000}
    assert mod.quality_gate(good, 6) == []


def test_invalid_plan_timeline_rejected(tmp_path):
    plan = json.loads((SRC / "docs/tv_comparison_8_scenes.json").read_text())
    plan["scenes"][1]["start_seconds"] = 10
    src = tmp_path / "bad.json"
    src.write_text(json.dumps(plan), encoding="utf-8")
    with pytest.raises(ValueError, match="overlaps/gaps"):
        mod.prepare(src, tmp_path / "pack")

def test_muse_dedicated_route_and_price_quote_not_generic_studio():
    assert mod.MUSE_URL == "https://snapgen.ai/app/video-gen/muse"
    with pytest.raises(RuntimeError, match="zero-credit quote"):
        mod.validate_zero_price("0 Credits per video", selected_model="Muse AI Video",
                                resolution="720p", aspect="9:16", seconds=6)


def test_remote_qa_forbid_same_mp4_reused_for_all_scenes(tmp_path, monkeypatch):
    pack = tmp_path / "pack"
    mod.prepare(SRC / "docs/tv_comparison_8_scenes.json", pack)
    pack.joinpath("qa", "remote_semantic_report.json").write_text(
        json.dumps({"scenes": [{"scene_id": f"scene_{i:02d}", "source_sha256": "identical"}
                               for i in range(1, 9)]}))
    def fake_inspect(pack, ffprobe="ffprobe"):
        return {"scenes": [{"scene_id": f"scene_{i:02d}",
                             "technical_status": "PASS",
                             "probe": {"sha256": "identical"}} for i in range(1, 9)]}
    monkeypatch.setattr(mod, "inspect", fake_inspect)
    with pytest.raises(RuntimeError, match="Repeated source video"):
        mod.check_remote_evidence(pack)


def test_reference_is_hashed_and_tampering_blocks_video_qa(tmp_path):
    plan = SRC / "docs/tv_comparison_8_scenes.json"
    root = tmp_path / "muse"
    (root / "references").mkdir(parents=True)
    for name in ("authentic_tv_menu.png", "authentic_tv_ports.png",
                 "authentic_connection_diagram.png", "authentic_model_comparison.png"):
        (root / "references" / name).write_bytes(b"initial-test-reference")
    result = mod.prepare(plan, root)
    assert not any(x["generation_blocker"] for x in result["scenes"])
    assert result["scenes"][3]["reference_sha256"]
    (root / "references" / "authentic_tv_menu.png").write_bytes(b"tampered")
    report = mod.inspect(root)
    scene4 = report["scenes"][3]
    assert scene4["technical_status"] == "FAIL"
    assert "Reference modified since scene plan creation" in scene4["problems"]


def test_reference_path_cannot_escape_references_folder(tmp_path):
    obj = json.loads((SRC / "docs/tv_comparison_8_scenes.json").read_text())
    obj["scenes"][3]["reference_file"] = "../private.png"
    p = tmp_path / "plan.json"
    p.write_text(json.dumps(obj), encoding="utf8")
    with pytest.raises(ValueError, match="safe path"):
        mod.prepare(p, tmp_path / "pack")


def test_temporal_motion_measure_rejects_static_25fps_frames(monkeypatch, tmp_path):
    class Proc:
        returncode = 0
        def __init__(self, value):
            self.stdout = bytes([value]) * (96 * 170)
    counter = iter([Proc(80), Proc(80), Proc(80)])
    monkeypatch.setattr(mod.subprocess, "run", lambda *a, **kw: next(counter))
    assert mod.temporal_motion_score(tmp_path / "static.mp4", seconds=6) == 0
    counter = iter([Proc(80), Proc(95), Proc(120)])
    monkeypatch.setattr(mod.subprocess, "run", lambda *a, **kw: next(counter))
    assert mod.temporal_motion_score(tmp_path / "moving.mp4", seconds=6) == 25
