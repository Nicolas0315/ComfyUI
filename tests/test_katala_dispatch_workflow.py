from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "dispatch_workflow.py"
SPEC = importlib.util.spec_from_file_location("dispatch_workflow", SCRIPT_PATH)
dispatch_workflow = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules["dispatch_workflow"] = dispatch_workflow
SPEC.loader.exec_module(dispatch_workflow)


def test_video_workflow_routes_to_4090_only(tmp_path: Path) -> None:
    workflow = {
        "1": {
            "class_type": "UNETLoader",
            "inputs": {"unet_name": "wan2.2_t2v_high_noise_14B_fp8_scaled.safetensors"},
        },
        "2": {"class_type": "VHS_VideoCombine", "inputs": {"filename_prefix": "wan22"}},
    }
    workflow_path = tmp_path / "wan.json"
    workflow_path.write_text(json.dumps(workflow), encoding="utf-8")

    plan = dispatch_workflow.build_dispatch_plan(
        workflow_path=workflow_path,
        kind="auto",
        workers=list(dispatch_workflow.DEFAULT_WORKERS),
    )

    assert plan["requested_kind"] == "video"
    assert plan["selected_worker"]["name"] == "rtx4090"
    assert "wan2" in plan["classification"]["video_markers"]
    assert plan["policy"]["low_tier_default"] == "excluded"


def test_image_workflow_excludes_3070_by_default(tmp_path: Path) -> None:
    workflow = {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "novaAnimeXL_ilV190.safetensors"}},
        "2": {"class_type": "SaveImage", "inputs": {"filename_prefix": "image"}},
    }
    workflow_path = tmp_path / "image.json"
    workflow_path.write_text(json.dumps(workflow), encoding="utf-8")

    plan = dispatch_workflow.build_dispatch_plan(
        workflow_path=workflow_path,
        kind="auto",
        workers=list(dispatch_workflow.DEFAULT_WORKERS),
        prefer="nicolas2025",
    )

    assert plan["requested_kind"] == "image"
    assert plan["selected_worker"]["name"] == "nicolas2025"
    assert plan["selected_worker"]["enabled_by_default"] is False


def test_preferred_medium_worker_rejects_video(tmp_path: Path) -> None:
    workflow_path = tmp_path / "ltxv.json"
    workflow_path.write_text(
        json.dumps({"1": {"class_type": "EmptyLTXVLatentVideo", "inputs": {}}}),
        encoding="utf-8",
    )

    with pytest.raises(SystemExit, match="does not support video"):
        dispatch_workflow.build_dispatch_plan(
            workflow_path=workflow_path,
            kind="auto",
            workers=list(dispatch_workflow.DEFAULT_WORKERS),
            prefer="rtx5060ti",
        )
