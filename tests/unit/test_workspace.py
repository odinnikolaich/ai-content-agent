from pathlib import Path
import pytest
from core.workspace import Workspace
def test_workspace_create_is_idempotent(tmp_path:Path):
    w=Workspace.create(tmp_path/"workspace",tmp_path/"output",tmp_path/"temp"); w2=Workspace.create(tmp_path/"workspace",tmp_path/"output",tmp_path/"temp"); assert w.projects.is_dir() and w2.projects==w.projects
def test_project_and_subdirectories(tmp_path:Path):
    w=Workspace.create(tmp_path/"workspace",tmp_path/"output",tmp_path/"temp"); assert w.project_subdir("project-1","scenes")==tmp_path/"workspace"/"projects"/"project-1"/"scenes"
def test_workspace_rejects_path_traversal(tmp_path:Path):
    w=Workspace.create(tmp_path/"workspace",tmp_path/"output",tmp_path/"temp")
    with pytest.raises(ValueError): w.project_subdir("project-1","../secrets")
    with pytest.raises(ValueError): w.output_file("../video.mp4")
