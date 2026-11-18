# @@NAME@@

A SpikeClip pipeline that will find the moments worth a clip in a video. It finds none yet: it is the blank template of the SpikeClip SDK, the start for your own checks.

The examples here use Quarkbloom Arena (a made-up game): replace it with yours.

## What it does

It reads the video's size and frame rate, writes them to the log, and finds no moments. Add your checks to the marked block in `src/main.py`: for each thing worth a clip, add a moment with `job.add_range(start, end, label=..., reason=...)`. SpikeClip then cuts, frames and captions the clips, as it does for every video.

## What it can't see

Nothing yet. When you add checks, say here what they can't see: a check that looks at one part of the screen misses what happens elsewhere, and a check that listens for loud moments misses quiet ones.

## Try it

You need Python @@PYTHON@@ (the Python SpikeClip runs plugins on) and FFmpeg, for the sample video. In the plugin's folder, in PowerShell:

```powershell
py -m pip install "spikeclip-sdk[yaml,test] @ git+https://github.com/ColinGPT9/spikeclip#subdirectory=sdk/python"
py -m spikeclip_sdk validate .
py -m spikeclip_sdk run . --sample
py -m spikeclip_sdk run . --video "$env:USERPROFILE\Videos\match.mp4"
py -m pytest -q
```

Or in bash:

```bash
python -m pip install "spikeclip-sdk[yaml,test] @ git+https://github.com/ColinGPT9/spikeclip#subdirectory=sdk/python"
python -m spikeclip_sdk validate .
python -m spikeclip_sdk run . --sample
python -m spikeclip_sdk run . --video ~/Videos/match.mp4
python -m pytest -q
```

`validate` checks `spikeclip.yaml` and the code the way SpikeClip does. `run . --sample` runs the plugin on the SDK's 40-second sample video, and `--video` on a recording of yours. `pytest` runs `tests/test_main.py`. If you use a virtual environment, make it next to this folder, not inside it: SpikeClip copies everything in the folder when it installs it.

## Use it in SpikeClip

In a SpikeClip that runs plugins ([which release does](https://github.com/ColinGPT9/spikeclip/blob/main/docs/developers/versioning.md#which-release-runs-plugins)), open **Marketplace › Browse**, choose **For developers: install a pipeline you're writing** at the bottom, and pick this folder. Then choose it as the **Pipeline** when you add a video.

## Share it

Push this folder to GitHub as its own repository. Its id, `@@ID@@`, starts with `@@PUBLISHER@@`: for a Marketplace listing, that must be the GitHub name that owns the repository. `.github/workflows/spikeclip-check.yml` then checks it on Linux and Windows with Python @@PYTHON@@ on every push. How to get it listed in the Marketplace: [Marketplace publishing](https://github.com/ColinGPT9/spikeclip/blob/main/docs/developers/marketplace-publishing.md).

## Files

```text
spikeclip.yaml        what SpikeClip reads about the plugin: its inputs, outputs, permissions and settings
src/main.py            the plugin: SpikeClip starts it with a job folder
tests/test_main.py     its tests, on the SDK's sample video
LICENSE                your licence for the plugin
TEMPLATE-LICENSE.txt   the MIT licence of the code that came from the template
```

The SDK's helpers and the job's contract: [SDK](https://github.com/ColinGPT9/spikeclip/blob/main/docs/developers/sdk.md).
