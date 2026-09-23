"""Cross-platform workspace management."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
@dataclass(frozen=True)
class Workspace:
    root:Path; output:Path; temp:Path; projects:Path
    @classmethod
    def create(cls,root:str|Path="workspace",output:str|Path="output",temp:str|Path=".tmp")->"Workspace":
        r,o,t=Path(root),Path(output),Path(temp); p=r/"projects"
        for x in (r,o,t,p): x.mkdir(parents=True,exist_ok=True)
        return cls(r,o,t,p)
    def project_dir(self,project_id:str,*,create:bool=True)->Path:
        if not project_id.strip(): raise ValueError("project_id must not be empty")
        p=self.projects/project_id
        if create: p.mkdir(parents=True,exist_ok=True)
        return p
    def project_subdir(self,project_id:str,name:str,*,create:bool=True)->Path:
        if not name.strip() or Path(name).name!=name or name in {".",".."}: raise ValueError("name must be a single safe directory name")
        p=self.project_dir(project_id)/name
        if create: p.mkdir(parents=True,exist_ok=True)
        return p
    def output_file(self,filename:str)->Path:
        if not filename or Path(filename).name!=filename: raise ValueError("filename must not contain directory components")
        return self.output/filename
