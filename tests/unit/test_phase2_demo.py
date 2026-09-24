from pathlib import Path
from pipeline.mock_vertical import run_demo

def test_demo_pipeline_creates_mp4(tmp_path:Path)->None:
    result=run_demo("тест модульного дома",43,str(tmp_path/"output"))
    assert result.exists(); assert result.suffix==".mp4"; assert result.stat().st_size>10_000
