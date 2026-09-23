from pathlib import Path
import pytest
from core.config import AppConfig,ReliabilityConfig,load_config
from core.exceptions import ConfigurationError
def test_load_default_config(tmp_path:Path):
    p=tmp_path/"config.yaml"; p.write_text("agent_mode: mock\nlog_level: INFO\nvideo:\n  min_duration_seconds: 43\n  max_duration_seconds: 60\n",encoding="utf-8")
    c=load_config(p,env={}); assert isinstance(c,AppConfig); assert c.video.min_duration_seconds==43 and c.providers.llm=="mock"
def test_environment_overrides_yaml(tmp_path:Path):
    p=tmp_path/"config.yaml"; p.write_text("video:\n  width: 720\n",encoding="utf-8")
    c=load_config(p,env={"AI_AGENT_WIDTH":"1080"}); assert c.video.width==1080
def test_cli_override_has_highest_precedence(tmp_path:Path):
    p=tmp_path/"config.yaml"; p.write_text("video:\n  width: 720\n",encoding="utf-8")
    c=load_config(p,env={"AI_AGENT_WIDTH":"1080"},cli_overrides={"video.width":640}); assert c.video.width==640
def test_invalid_log_level_fails():
    with pytest.raises(ConfigurationError): AppConfig(log_level="NOPE").validate()
def test_retry_count_must_not_be_negative():
    with pytest.raises(ConfigurationError): AppConfig(reliability=ReliabilityConfig(retry_count=-1)).validate()
