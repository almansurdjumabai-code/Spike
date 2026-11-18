# Getting started

This page takes you from nothing to a pipeline plugin SpikeClip can run, in short steps. [Your first game pipeline](first-game-pipeline.md) does the same with every command's output, for one made-up game. You need Python 3.11, the version SpikeClip's own Python is (any 3.10 or newer works for the SDK, but test on 3.11), FFmpeg, and Git. You never change SpikeClip's code.

The commands are shown for PowerShell on Windows (`py -m`) and for bash on macOS or Linux (`python -m`).

## 1. Install the SDK

PowerShell:

```powershell
py -m pip install "spikeclip-sdk[yaml,test] @ git+https://github.com/ColinGPT9/spikeclip#subdirectory=sdk/python"
```

bash:

```bash
python -m pip install "spikeclip-sdk[yaml,test] @ git+https://github.com/ColinGPT9/spikeclip#subdirectory=sdk/python"
```

SpikeClip 2.1.0 is the first release that runs plugins, and it comes with SDK 1.3.0.

To try a plugin with changes that aren't in a release yet, run SpikeClip from source: [From source](../../README.md#from-source). If you use a virtual environment, keep it next to your plugin's folder, not inside it.

## 2. Start from a template

PowerShell:

```powershell
py -m spikeclip_sdk new my-plugin --template blank --publisher your-github-name
```

bash:

```bash
python -m spikeclip_sdk new my-plugin --template blank --publisher your-github-name
```

Use your own GitHub name, in lower case. `new --list` shows the six templates: `blank`, `transcript`, `game-events`, `rater`, `understander` and `editor`. In the new folder's `spikeclip.yaml`:

- `id` is `<your GitHub name>/<plugin name>`, lower case;
- set `name`, `description` (what it detects, honestly), `license` and `repository`;
- list the `permissions` you need: `video.read` for the file, `transcript.read` for what was said, `ffmpeg` for SpikeClip's FFmpeg, `ollama` for the user's local AI model;
- declare your `settings`.

[Plugin manifest](plugin-manifest.md) has every field.

## 3. Write the detector

In `src/main.py`, read what you need from the job and add a range for each moment:

```python
from spikeclip_sdk import run


def main(job):
    for start, end, score in my_detector(job.video.path, job.settings):
        job.add_range(start, end, score=score, label="big_play", reason="5 eliminations in 6 s")


if __name__ == "__main__":
    run(main)
```

Import only the standard library and `spikeclip_sdk`, at the top of the file: SpikeClip runs plugins on its own Python, which has nothing else. The SDK's `media`, `signals` and `text` modules read frames, loudness, scene cuts and words for you ([Signals cookbook](signals-cookbook.md)). [SDK](sdk.md) lists everything on `job`; [Pipeline development](pipeline-development.md) explains the contract and what SpikeClip does with your moments.

## 4. Check it and run it

PowerShell:

```powershell
py -m spikeclip_sdk validate my-plugin
py -m spikeclip_sdk run my-plugin --sample
```

bash:

```bash
python -m spikeclip_sdk validate my-plugin
python -m spikeclip_sdk run my-plugin --sample
```

`validate` runs the checks SpikeClip and the registry run, and warns about code that would fail on SpikeClip's Python. `run --sample` builds the job folder exactly as the app does, on a 40-second test video, runs your plugin, and prints the moments the app would take. When both pass, the app would accept your plugin and its answer. Then try it on your own recordings with `--video`.

## 5. Install it in SpikeClip

In a SpikeClip that runs plugins (see step 1), with the app running:

PowerShell:

```powershell
py -m spikeclip_sdk install my-plugin --watch
```

bash:

```bash
python -m spikeclip_sdk install my-plugin --watch
```

It shows SpikeClip's own install screen as text and asks first, then reinstalls the plugin each time you save ([SDK › Installing it into SpikeClip](sdk.md#installing-it-into-spikeclip)). In the desktop app the same is **For developers: install a pipeline you're writing**, a link at the bottom of **Marketplace → Browse** ([Plugin development](plugin-development.md)). Then choose it with the **Pipeline** switch on a video in the Generate bar.

## 6. Publish it

Push the folder to a public GitHub repository and tag a release, in the plugin's folder:

```text
git tag v0.1.0
git push origin v0.1.0
```

Then make its catalog listing, from the folder that holds the plugin's folder, with `python -m spikeclip_sdk listing my-plugin --section gaming/generic` (in PowerShell, `py -m spikeclip_sdk`). How users install it, and how to get it listed in the Marketplace, is in [Marketplace publishing](marketplace-publishing.md).

## Where to go next

- [Your first game pipeline](first-game-pipeline.md): the same steps for one game, with every command's output
- [Signals cookbook](signals-cookbook.md): a recipe for each thing a game pipeline reads
- [Example pipeline](example-pipeline.md): a complete one, laid out as its own repository, and how it is tested
- [Permissions](permissions.md) and [Security](security.md): what users see before they install
- [Troubleshooting](troubleshooting.md)
