import shutil
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))


@pytest.fixture
def site(tmp_path: Path):
    """Throwaway landing (content/reports + types.json) and app-demo folders the scripts write into."""
    landing, appdemo = tmp_path / "landing", tmp_path / "app-demo"
    (landing / "content" / "reports").mkdir(parents=True)
    shutil.copy(REPO / "scripts" / "types.json", landing / "content" / "reports" / "types.json")
    appdemo.mkdir()
    return landing, appdemo


def make_png(path: Path, size=(1200, 800), color=(255, 255, 255)) -> Path:
    from PIL import Image
    Image.new("RGB", size, color).save(path)
    return path
