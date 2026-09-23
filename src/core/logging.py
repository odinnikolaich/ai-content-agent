"""Structured JSON logging."""
from __future__ import annotations
import json,logging,sys
from datetime import datetime,timezone
from typing import Any,Mapping
class JsonFormatter(logging.Formatter):
    def format(self,r:logging.LogRecord)->str:
        p={"timestamp":datetime.fromtimestamp(r.created,tz=timezone.utc).isoformat(),"level":r.levelname,"logger":r.name,"message":r.getMessage()}
        for k in ("stage","project_id","job_id","event"):
            if hasattr(r,k): p[k]=getattr(r,k)
        if r.exc_info: p["exception"]=self.formatException(r.exc_info)
        return json.dumps(p,ensure_ascii=False,default=str)
def configure_logging(level:str="INFO",stream:Any=None)->logging.Logger:
    n=getattr(logging,level.upper(),None)
    if not isinstance(n,int): raise ValueError(f"Unsupported log level: {level}")
    logger=logging.getLogger("ai_content_agent"); logger.setLevel(n); logger.handlers.clear()
    h=logging.StreamHandler(stream or sys.stdout); h.setLevel(n); h.setFormatter(JsonFormatter()); logger.addHandler(h); logger.propagate=False
    return logger
def get_logger(name:str="ai_content_agent")->logging.Logger: return logging.getLogger(name)
def log_event(logger:logging.Logger,event:str,message:str,*,extra:Mapping[str,Any]|None=None,level:int=logging.INFO)->None:
    values=dict(extra or {}); values["event"]=event; logger.log(level,message,extra=values)
