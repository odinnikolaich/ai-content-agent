"""JSON serialization helpers."""
from __future__ import annotations
import json
from dataclasses import fields,is_dataclass
from pathlib import Path
from typing import Any,Mapping,TypeVar,Union,get_args,get_origin,get_type_hints
T=TypeVar("T")
def to_dict(value:Any)->Any:
    if is_dataclass(value): return {f.name:to_dict(getattr(value,f.name)) for f in fields(value)}
    if isinstance(value,Mapping): return {str(k):to_dict(v) for k,v in value.items()}
    if isinstance(value,(tuple,list)): return [to_dict(v) for v in value]
    if isinstance(value,Path): return str(value)
    return value
def to_json(value:Any,*,indent:int|None=2)->str: return json.dumps(to_dict(value),ensure_ascii=False,indent=indent,sort_keys=True)
def from_dict(cls:type[T],data:Mapping[str,Any])->T:
    if not is_dataclass(cls): raise TypeError("cls must be a dataclass")
    hints=get_type_hints(cls)
    def conv(v:Any,t:Any)->Any:
        o=get_origin(t); a=get_args(t)
        if v is None: return None
        if o is Union:
            for c in [x for x in a if x is not type(None)]:
                try: return conv(v,c)
                except (TypeError,ValueError,KeyError): pass
            return v
        if o is tuple:
            return tuple(conv(x,a[0] if a else Any) for x in v)
        if o in (list,):
            return [conv(x,a[0] if a else Any) for x in v]
        if o in (dict,Mapping):
            kt,vt=a if len(a)==2 else (str,Any); return {conv(k,kt):conv(x,vt) for k,x in v.items()}
        if isinstance(t,type) and is_dataclass(t): return from_dict(t,v)
        if t is Path: return Path(v)
        return v
    return cls(**{n:conv(data[n],hints[n]) for n in hints if n in data})
def from_json(cls:type[T],payload:str)->T:
    d=json.loads(payload)
    if not isinstance(d,Mapping): raise TypeError("JSON payload must contain an object")
    return from_dict(cls,d)
def write_json(path:str|Path,value:Any,*,indent:int|None=2)->None:
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(to_json(value,indent=indent),encoding="utf-8")
def read_json(path:str|Path,cls:type[T])->T:
    return from_dict(cls,json.loads(Path(path).read_text(encoding="utf-8")))
