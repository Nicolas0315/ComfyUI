import json
import time

import pytest
import torch
from PIL import Image

import folder_paths
from comfy_extras import nodes_dataset


@pytest.fixture
def output_dir(tmp_path, monkeypatch):
    output = tmp_path / "output"
    output.mkdir()
    monkeypatch.setattr(folder_paths, "output_directory", str(output))
    return output


def save_dataset(kind, folder_name, prefix="image"):
    if kind == "training":
        nodes_dataset.SaveTrainingDataset.execute(
            [{"samples": torch.zeros(1, 4, 2, 2)}], [[]], [folder_name], [1]
        )
        return
    images = [torch.zeros(1, 8, 8, 3)]
    mode = "increment" if kind.endswith("increment") else "overwrite"
    if kind.startswith("captions"):
        nodes_dataset.SaveImageTextDataSetToFolderNode.execute(
            images, [folder_name], [prefix], [mode], texts=["synthetic caption"]
        )
    else:
        nodes_dataset.SaveImageDataSetToFolderNode.execute(
            images, [folder_name], [prefix], [mode]
        )


SAVERS = ["images_overwrite", "images_increment", "captions_overwrite", "captions_increment", "training"]


@pytest.mark.parametrize("kind", SAVERS)
@pytest.mark.parametrize("escape", ["parent", "absolute", "symlink"])
def test_dataset_rejects_folder_outside_output(output_dir, tmp_path, kind, escape):
    outside = tmp_path / "outside"
    if escape == "parent":
        folder = "../outside"
    elif escape == "absolute":
        folder = str(outside)
    else:
        outside.mkdir()
        (output_dir / "linked").symlink_to(outside, target_is_directory=True)
        folder = "linked/new"

    with pytest.raises(ValueError):
        save_dataset(kind, folder)

    assert not outside.exists() or not list(outside.rglob("*"))


@pytest.mark.parametrize("kind", SAVERS[:-1])
@pytest.mark.parametrize("escape", ["parent", "absolute", "symlink"])
def test_dataset_rejects_prefix_outside_dataset(output_dir, tmp_path, kind, escape):
    dataset = output_dir / "dataset"
    dataset.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    if escape == "parent":
        prefix = "../../outside/image"
    elif escape == "absolute":
        prefix = str(outside / "image")
    else:
        (dataset / "linked").symlink_to(outside, target_is_directory=True)
        prefix = "linked/image"

    with pytest.raises(ValueError):
        save_dataset(kind, "dataset", prefix)

    assert list(outside.iterdir()) == []


@pytest.mark.parametrize("kind, filename", [
    ("images_overwrite", "image_00000.png"),
    ("captions_overwrite", "image_00000.txt"),
    ("training", "shard_0000.pkl"),
    ("training", "metadata.json"),
])
def test_dataset_does_not_follow_existing_file_symlink(output_dir, tmp_path, kind, filename):
    dataset = output_dir / "dataset"
    dataset.mkdir()
    outside_file = tmp_path / "outside-file"
    outside_file.write_bytes(b"synthetic sentinel")
    (dataset / filename).symlink_to(outside_file)

    with pytest.raises(ValueError):
        save_dataset(kind, "dataset")

    assert outside_file.read_bytes() == b"synthetic sentinel"


@pytest.mark.parametrize("kind", SAVERS)
def test_dataset_keeps_nested_output_and_filenames(output_dir, kind):
    nested = output_dir / "datasets" / "nested" / "images"
    nested.mkdir(parents=True)
    save_dataset(kind, "datasets/nested", "images/example")
    if kind == "training":
        dataset = output_dir / "datasets" / "nested"
        assert json.loads((dataset / "metadata.json").read_text())["num_samples"] == 1
        data = torch.load(dataset / "shard_0000.pkl", weights_only=True)
        assert torch.equal(data["latents"][0]["samples"], torch.zeros(1, 4, 2, 2))
    else:
        filename = "example_00001_00000" if kind.endswith("increment") else "example_00000"
        with Image.open(nested / f"{filename}.png") as image:
            assert image.size == (8, 8)
        if kind.startswith("captions"):
            assert (nested / f"{filename}.txt").read_text() == "synthetic caption"


def test_dataset_allows_symlinked_output_root(output_dir, tmp_path, monkeypatch):
    alias = tmp_path / "output-alias"
    alias.symlink_to(output_dir, target_is_directory=True)
    monkeypatch.setattr(folder_paths, "output_directory", str(alias))
    save_dataset("captions_overwrite", "nested")
    assert (output_dir / "nested" / "image_00000.txt").read_text() == "synthetic caption"


def test_dataset_prefix_is_not_the_final_filename(output_dir, tmp_path):
    dataset = output_dir / "dataset"
    dataset.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (dataset / "image").symlink_to(outside, target_is_directory=True)
    save_dataset("captions_overwrite", "dataset")
    assert (dataset / "image_00000.txt").read_text() == "synthetic caption"
    assert list(outside.iterdir()) == []


def test_increment_checks_expanded_prefix_before_creating_directories(output_dir, tmp_path):
    dataset = output_dir / "dataset"
    dataset.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (dataset / str(time.localtime().tm_year)).symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError):
        save_dataset("captions_increment", "dataset", "%year%/new/image")

    assert list(outside.iterdir()) == []
