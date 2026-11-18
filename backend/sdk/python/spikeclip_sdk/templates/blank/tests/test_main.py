"""This plugin's tests. They run on your PC, never inside SpikeClip:

    python -m pytest -q

They need the SDK's test extra (pip install "spikeclip-sdk[yaml,test]").
spikeclip_sdk.testing runs the plugin the way SpikeClip would. A test that
needs the sample video is skipped when FFmpeg isn't on PATH. Change these as
you change the plugin.
"""

from pathlib import Path

from spikeclip_sdk import testing

PLUGIN = Path(__file__).resolve().parent.parent  # the folder holding spikeclip.yaml


def test_it_runs_on_the_sample_video(tmp_path):
    video = testing.sample_video(tmp_path)  # skips this test without FFmpeg
    run = testing.run_plugin(PLUGIN, video=video, tmp_path=tmp_path)
    assert run.ok, run.error
    assert run.moments == []  # the blank template finds nothing yet
    assert run.notes == "This is the blank template: add your own checks in src/main.py."
