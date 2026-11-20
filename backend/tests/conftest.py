import os
import sys
from pathlib import Path

os.environ["SPIKECLIP_API_NO_AUTOAPP"] = "1"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
