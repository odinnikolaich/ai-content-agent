from pathlib import Path
from core.models import ContentRequest,ResearchResult,ResearchSource
from core.serialization import from_dict,from_json,to_dict,to_json,write_json,read_json
def test_dataclass_roundtrip():
    r=ContentRequest(project_id="p1",topic="winter modular house",duration_seconds=43); assert from_dict(ContentRequest,to_dict(r))==r
def test_nested_roundtrip():
    r=ResearchResult(topic="winter",facts=("fact 1",),sources=(ResearchSource(title="Example",url="https://example.test"),)); x=from_json(ResearchResult,to_json(r)); assert x==r and isinstance(x.sources[0],ResearchSource)
def test_file_roundtrip(tmp_path:Path):
    p=tmp_path/"request.json"; r=ContentRequest(project_id="p1",topic="test"); write_json(p,r); assert read_json(p,ContentRequest)==r
