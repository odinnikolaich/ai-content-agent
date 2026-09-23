from dataclasses import FrozenInstanceError
import pytest
from core.models import CacheKey,ContentRequest,ResearchResult
def test_content_request_accepts_project_duration():
    r=ContentRequest(project_id="test",topic="winter house",duration_seconds=43); assert r.duration_seconds==43
def test_content_request_rejects_duration_outside_contract():
    with pytest.raises(ValueError): ContentRequest(project_id="test",topic="x",duration_seconds=42)
    with pytest.raises(ValueError): ContentRequest(project_id="test",topic="x",duration_seconds=61)
def test_domain_models_are_frozen():
    r=ContentRequest(project_id="test",topic="x")
    with pytest.raises(FrozenInstanceError): r.topic="changed"
def test_cache_key_contains_versions():
    k=CacheKey(stage="script",input_hash="abc",prompt_version="7"); assert "7" in k.value and k.schema_version
def test_research_result_uses_typed_collections():
    r=ResearchResult(topic="topic",facts=("a",),trends=("b",)); assert r.facts==("a",)
