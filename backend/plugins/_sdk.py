"""The plugin SDK (sdk/python/spikeclip_sdk), importable by the engine.

The engine uses the SDK's own checks and runner so that what passes under
`python -m spikeclip_sdk run` passes in the app: one copy of the contract,
never two. The SDK is a plain folder of Python files rather than an installed
package, because plugin processes are pointed at the same folder through
PYTHONPATH. In a source checkout it is next to this package; in the frozen
build it ships as data (spikeclip.spec) under the bundle's sdk/python.
"""

import importlib
import sys
from pathlib import Path


def sdk_dir() -> Path:
    bundle = getattr(sys, "_MEIPASS", None)
    if bundle:
        return Path(bundle) / "sdk" / "python"
    return Path(__file__).resolve().parent.parent / "sdk" / "python"


if str(sdk_dir()) not in sys.path:
    sys.path.insert(0, str(sdk_dir()))

import spikeclip_sdk  # noqa: E402

contract = importlib.import_module("spikeclip_sdk.contract")
host = importlib.import_module("spikeclip_sdk.host")
manifest = importlib.import_module("spikeclip_sdk.manifest")

__all__ = ["spikeclip_sdk", "contract", "host", "manifest", "sdk_dir"]
