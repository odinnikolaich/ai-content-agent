"""Configuration loader: YAML < environment < explicit overrides."""
from __future__ import annotations
import argparse, os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping
import yaml
from .exceptions import ConfigurationError
_LEVELS={"DEBUG","INFO","WARNING","ERROR","CRITICAL"}
@dataclass(frozen=True)
class VideoConfig:
    language:str="ru"; aspect_ratio:str="9:16"; width:int=1080; height:int=1920; fps:int=30; min_duration_seconds:int=43; max_duration_seconds:int=60
@dataclass(frozen=True)
class ReliabilityConfig:
    provider_timeout_seconds:int=120; retry_count:int=2
@dataclass(frozen=True)
class QualityConfig:
    min_width:int=720; min_height:int=1280; min_duration_seconds:int=43; max_duration_seconds:int=60
@dataclass(frozen=True)
class ProviderConfig:
    llm:str="mock"; image:str="mock"; video:str="mock"; voice:str="mock"; transcription:str="mock"
@dataclass(frozen=True)
class AppConfig:
    agent_mode:str="mock"; log_level:str="INFO"; workspace_dir:Path=Path("workspace"); output_dir:Path=Path("output"); temp_dir:Path=Path(".tmp")
    video:VideoConfig=field(default_factory=VideoConfig); reliability:ReliabilityConfig=field(default_factory=ReliabilityConfig); quality:QualityConfig=field(default_factory=QualityConfig); providers:ProviderConfig=field(default_factory=ProviderConfig)
    def validate(self)->None:
        if self.log_level.upper() not in _LEVELS: raise ConfigurationError(f"Unsupported log level: {self.log_level}")
        if self.reliability.provider_timeout_seconds<=0: raise ConfigurationError("provider_timeout_seconds must be positive")
        if self.reliability.retry_count<0: raise ConfigurationError("retry_count must be non-negative")
        v=self.video
        if min(v.width,v.height,v.fps,v.min_duration_seconds,v.max_duration_seconds)<=0: raise ConfigurationError("video values must be positive")
        if v.min_duration_seconds>v.max_duration_seconds: raise ConfigurationError("video minimum duration exceeds maximum duration")
        q=self.quality
        if min(q.min_width,q.min_height,q.min_duration_seconds,q.max_duration_seconds)<=0: raise ConfigurationError("QC values must be positive")
        if q.min_duration_seconds>q.max_duration_seconds: raise ConfigurationError("QC minimum duration exceeds maximum duration")
def _defaults()->dict[str,Any]:
    return {"agent_mode":"mock","log_level":"INFO","workspace_dir":"workspace","output_dir":"output","temp_dir":".tmp","video":{"language":"ru","aspect_ratio":"9:16","width":1080,"height":1920,"fps":30,"min_duration_seconds":43,"max_duration_seconds":60},"reliability":{"provider_timeout_seconds":120,"retry_count":2},"quality":{"min_width":720,"min_height":1280,"min_duration_seconds":43,"max_duration_seconds":60},"providers":{"llm":"mock","image":"mock","video":"mock","voice":"mock","transcription":"mock"}}
def _merge(a:dict[str,Any],b:Mapping[str,Any])->dict[str,Any]:
    r=dict(a)
    for k,v in b.items(): r[k]=_merge(dict(r[k]),v) if isinstance(v,Mapping) and isinstance(r.get(k),Mapping) else v
    return r
def _env(env:Mapping[str,str])->dict[str,Any]:
    m={"AI_AGENT_MODE":"agent_mode","AI_AGENT_LOG_LEVEL":"log_level","AI_AGENT_WORKSPACE_DIR":"workspace_dir","AI_AGENT_OUTPUT_DIR":"output_dir","AI_AGENT_TEMP_DIR":"temp_dir","AI_AGENT_LANGUAGE":"video.language","AI_AGENT_ASPECT_RATIO":"video.aspect_ratio","AI_AGENT_WIDTH":"video.width","AI_AGENT_HEIGHT":"video.height","AI_AGENT_FPS":"video.fps","AI_AGENT_MIN_DURATION_SECONDS":"video.min_duration_seconds","AI_AGENT_MAX_DURATION_SECONDS":"video.max_duration_seconds","AI_AGENT_PROVIDER_TIMEOUT_SECONDS":"reliability.provider_timeout_seconds","AI_AGENT_RETRY_COUNT":"reliability.retry_count","AI_AGENT_QC_MIN_WIDTH":"quality.min_width","AI_AGENT_QC_MIN_HEIGHT":"quality.min_height","AI_AGENT_QC_MIN_DURATION_SECONDS":"quality.min_duration_seconds","AI_AGENT_QC_MAX_DURATION_SECONDS":"quality.max_duration_seconds","AI_AGENT_LLM_PROVIDER":"providers.llm","AI_AGENT_IMAGE_PROVIDER":"providers.image","AI_AGENT_VIDEO_PROVIDER":"providers.video","AI_AGENT_VOICE_PROVIDER":"providers.voice","AI_AGENT_TRANSCRIPTION_PROVIDER":"providers.transcription"}
    d={}; base=_defaults()
    for ek,path in m.items():
        if ek not in env: continue
        parts=path.split("."); cur=base
        for p in parts: cur=cur[p]
        value=int(env[ek]) if isinstance(cur,int) else env[ek]
        c=d
        for p in parts[:-1]: c=c.setdefault(p,{})
        c[parts[-1]]=value
    return d
def _set(d:dict[str,Any],key:str,value:Any)->None:
    c=d; parts=key.split(".")
    for p in parts[:-1]: c=c.setdefault(p,{})
    c[parts[-1]]=value
def _build(d:Mapping[str,Any])->AppConfig:
    try: c=AppConfig(agent_mode=str(d["agent_mode"]),log_level=str(d["log_level"]).upper(),workspace_dir=Path(d["workspace_dir"]),output_dir=Path(d["output_dir"]),temp_dir=Path(d["temp_dir"]),video=VideoConfig(**d["video"]),reliability=ReliabilityConfig(**d["reliability"]),quality=QualityConfig(**d["quality"]),providers=ProviderConfig(**d["providers"]))
    except (KeyError,TypeError,ValueError) as e: raise ConfigurationError(f"Invalid configuration: {e}") from e
    c.validate(); return c
def load_config(config_path:str|Path="config/default.yaml",*,env:Mapping[str,str]|None=None,cli_overrides:Mapping[str,Any]|None=None)->AppConfig:
    p=Path(config_path); d=_defaults()
    if p.exists():
        try: raw=yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        except (OSError,yaml.YAMLError) as e: raise ConfigurationError(f"Cannot read configuration: {p}") from e
        if not isinstance(raw,Mapping): raise ConfigurationError("Top-level YAML configuration must be a mapping")
        d=_merge(d,raw)
    d=_merge(d,_env(env or os.environ))
    for k,v in (cli_overrides or {}).items(): _set(d,k,v)
    return _build(d)
def parse_cli_overrides(argv:list[str]|None=None)->dict[str,Any]:
    p=argparse.ArgumentParser(add_help=False); p.add_argument("--config",default="config/default.yaml"); p.add_argument("--agent-mode"); p.add_argument("--log-level"); p.add_argument("--workspace-dir"); p.add_argument("--output-dir"); p.add_argument("--temp-dir")
    a,_=p.parse_known_args(argv); return {"config":a.config,**{k:v for k,v in {"agent_mode":a.agent_mode,"log_level":a.log_level,"workspace_dir":a.workspace_dir,"output_dir":a.output_dir,"temp_dir":a.temp_dir}.items() if v is not None}}
