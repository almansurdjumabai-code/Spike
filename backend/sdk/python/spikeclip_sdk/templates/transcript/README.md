# @@NAME@@

A SpikeClip pipeline that finds the moments where the commentary says your words or phrases.

It is set up for Quarkbloom Arena (a made-up game): replace it with yours. There, a caster shouts "quark burst" when a big play happens, so that is what it listens for. Put your game's own words in the `words` setting.

## What it does

1. It reads what is said in the video, which SpikeClip writes down before any pipeline runs.
2. Each time one of your words is said, it adds a moment from `lead_in_seconds` before the words to 6 seconds after. Words said close together share one moment.
3. SpikeClip then cuts, frames and captions the clips, as it does for every video.

A word matches as a whole word in any case, so `win` doesn't match `window`.

## What it can't see

It only reads what is said. It doesn't see the screen, it can't tell whether the words are about what is happening, and a moment nobody talks about is missed. A video with no commentary gets no moments.

## Settings

| Setting | Default | |
|---|---|---|
| `words` | `quark burst, triple bloom` | Words or phrases to look for, separated by commas |
| `lead_in_seconds` | 10 | Seconds to keep before the words are said |

## Try it

You need Python @@PYTHON@@, the Python SpikeClip runs plugins on. FFmpeg isn't needed: this plugin never reads the video. In the plugin's folder, in PowerShell:

```powershell
py -m pip install "spikeclip-sdk[yaml,test] @ git+https://github.com/ColinGPT9/spikeclip#subdirectory=sdk/python"
py -m spikeclip_sdk validate .
py -m spikeclip_sdk run . --sample
py -m spikeclip_sdk run . --sample --set "words=quark burst, triple bloom"
py -m pytest -q
```

Or in bash:

```bash
python -m pip install "spikeclip-sdk[yaml,test] @ git+https://github.com/ColinGPT9/spikeclip#subdirectory=sdk/python"
python -m spikeclip_sdk validate .
python -m spikeclip_sdk run . --sample
python -m spikeclip_sdk run . --sample --set "words=quark burst, triple bloom"
python -m pytest -q
```

`validate` checks `spikeclip.yaml` and the code the way SpikeClip does. `run . --sample` runs the plugin on what is said in the SDK's 40-second sample video, where "quark burst" is said from 23.5 to 26 s. `pytest` runs `tests/test_main.py`. If you use a virtual environment, make it next to this folder, not inside it: SpikeClip copies everything in the folder when it installs it.

## Use it in SpikeClip

In a SpikeClip that runs plugins ([which release does](https://github.com/ColinGPT9/spikeclip/blob/main/docs/developers/versioning.md#which-release-runs-plugins)), open **Marketplace › Browse**, choose **For developers: install a pipeline you're writing** at the bottom, and pick this folder. Then choose it as the **Pipeline** when you add a video.

## Share it

Push this folder to GitHub as its own repository. Its id, `@@ID@@`, starts with `@@PUBLISHER@@`: for a Marketplace listing, that must be the GitHub name that owns the repository. `.github/workflows/spikeclip-check.yml` then checks it on Linux and Windows with Python @@PYTHON@@ on every push. How to get it listed in the Marketplace: [Marketplace publishing](https://github.com/ColinGPT9/spikeclip/blob/main/docs/developers/marketplace-publishing.md).

## Files

```text
spikeclip.yaml        what SpikeClip reads about the plugin: its inputs, outputs, permissions and settings
src/main.py            the plugin: SpikeClip starts it with a job folder
tests/test_main.py     its tests, on the sample video's transcript
LICENSE                your licence for the plugin
TEMPLATE-LICENSE.txt   the MIT licence of the code that came from the template
```

The SDK's helpers and the job's contract: [SDK](https://github.com/ColinGPT9/spikeclip/blob/main/docs/developers/sdk.md).
