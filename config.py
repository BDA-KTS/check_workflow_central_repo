#config.py

from pathlib import Path
# Configuration
class Settings:
    TEST_PATH: Path = Path("testee")
    CENTRAL_PATH: Path = Path("central")
    NECESSARY_SUBTITLES: list[str] = [
        "Description", "Use Cases", "Input Data", "Output Data",
        "Hardware Requirements", "Environment Setup", "How to Use",
        "Technical Details", "Contact Details"
    ]
    BINDER_DIRS: list[str] = ["","binder", "binder/"]
    FREE_LICENSES: list[str]=["Apache-2.0","MIT","BSD-2-Clause","BSD-3-Clause","ISC","Zlib","BSL-1.0","GNU"]
    REPO_REQUIREMENTS: list[str] = {"citation", "license", "postbuild"}