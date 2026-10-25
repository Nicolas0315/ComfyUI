from unittest.mock import MagicMock, patch

import pytest
import torch

import folder_paths

# Match the other comfy_extras unit tests: loading the main nodes module would
# initialize accelerator/model dependencies unrelated to file-backed 3D loading.
mock_nodes = MagicMock()
mock_nodes.LoadImage.return_value.load_image.return_value = (torch.zeros(1, 8, 8, 3), torch.zeros(1, 8, 8))
with patch.dict("sys.modules", {"nodes": mock_nodes}):
    from comfy_extras import nodes_load_3d


@pytest.fixture
def directories(tmp_path, monkeypatch):
    roots = {}
    for kind in ("input", "output", "temp"):
        roots[kind] = tmp_path / kind
        roots[kind].mkdir()
        monkeypatch.setattr(folder_paths, f"{kind}_directory", str(roots[kind]))
    return roots


@pytest.fixture(params=[nodes_load_3d.Load3D, nodes_load_3d.Load3DAdvanced])
def loader(request, monkeypatch):
    monkeypatch.setattr(nodes_load_3d, "nodes", mock_nodes)
    return request.param


def load_model(loader, filename):
    viewport = {"camera_info": {}, "model_3d_info": []}
    if loader is nodes_load_3d.Load3DAdvanced:
        return loader.execute(filename, viewport, 64, 64)[0]
    image = dict(viewport, image="render.png", mask="mask.png", normal="normal.png", recording="")
    return loader.execute(filename, image)[6]


@pytest.mark.parametrize("escape", ["parent", "absolute", "symlink", "annotated"])
def test_3d_loaders_reject_outside_files(directories, tmp_path, loader, escape):
    source = tmp_path / "synthetic-source.txt"
    source.write_bytes(b"synthetic file bytes, not a 3D model")
    if escape == "parent":
        filename = "../synthetic-source.txt"
    elif escape == "absolute":
        filename = str(source)
    elif escape == "annotated":
        filename = "../synthetic-source.txt [output]"
    else:
        (directories["input"] / "linked.glb").symlink_to(source)
        filename = "linked.glb"

    assert loader.validate_inputs(filename) is not True
    with pytest.raises(ValueError):
        load_model(loader, filename)
    assert list(directories["output"].iterdir()) == []


@pytest.mark.parametrize("root, annotation", [
    ("input", ""), ("input", " [input]"), ("output", " [output]"), ("temp", " [temp]"),
])
def test_3d_loaders_preserve_nested_annotated_files(directories, loader, root, annotation):
    model = directories[root] / "3d" / "nested" / "model.glb"
    model.parent.mkdir(parents=True)
    model.write_bytes(b"synthetic model fixture")
    filename = "3d/nested/model.glb" + annotation

    assert loader.validate_inputs(filename) is True
    file_3d = load_model(loader, filename)
    destination = directories["output"] / "copied.glb"
    file_3d.save_to(str(destination))
    assert destination.read_bytes() == b"synthetic model fixture"


def test_3d_loader_rechecks_source_after_validation(directories, tmp_path, loader):
    model = directories["input"] / "model.glb"
    model.write_bytes(b"synthetic model fixture")
    assert loader.validate_inputs("model.glb") is True
    model.unlink()
    outside = tmp_path / "outside-file"
    outside.write_bytes(b"synthetic private sentinel")
    model.symlink_to(outside)
    with pytest.raises(ValueError):
        load_model(loader, "model.glb")


def test_3d_loader_rejects_directory(directories, loader):
    (directories["input"] / "directory.glb").mkdir()
    assert loader.validate_inputs("directory.glb") is not True
    with pytest.raises(ValueError):
        load_model(loader, "directory.glb")


@pytest.mark.parametrize("filename", ["", "none"])
def test_3d_loader_preserves_empty_selection(directories, loader, filename):
    assert loader.validate_inputs(filename) is True
    assert load_model(loader, filename) is None


def test_3d_loader_allows_symlinked_root(directories, tmp_path, monkeypatch, loader):
    model = directories["input"] / "model.glb"
    model.write_bytes(b"synthetic model fixture")
    alias = tmp_path / "input-alias"
    alias.symlink_to(directories["input"], target_is_directory=True)
    monkeypatch.setattr(folder_paths, "input_directory", str(alias))
    assert loader.validate_inputs("model.glb") is True
    assert load_model(loader, "model.glb").get_bytes() == b"synthetic model fixture"


@pytest.mark.parametrize("filename", ["missing.glb", "invalid\x00.glb"])
def test_3d_loader_rejects_missing_or_invalid_paths(directories, loader, filename):
    assert loader.validate_inputs(filename) is not True
    with pytest.raises(ValueError):
        load_model(loader, filename)


@pytest.mark.parametrize("target_name", ["asset.blob", "asset"])
@pytest.mark.parametrize("annotation", ["", " [input]", " [output]", " [temp]"])
def test_3d_loader_preserves_symlink_filename_format(directories, loader, target_name, annotation):
    root = annotation.strip(" []") if annotation else "input"
    target = directories[root] / target_name
    target.write_bytes(b"synthetic model fixture")
    (directories[root] / "model.GLB").symlink_to(target)
    filename = "model.GLB" + annotation

    assert loader.validate_inputs(filename) is True
    file_3d = load_model(loader, filename)
    assert file_3d.get_source() == str(target.resolve())
    assert file_3d.format == "glb"
    nodes_load_3d.Preview3D.execute(file_3d)
    previews = list(directories["output"].glob("preview3d_*.glb"))
    assert len(previews) == 1
    assert previews[0].read_bytes() == b"synthetic model fixture"
