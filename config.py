#config.py

from pathlib import Path
# Configuration
class Settings:
    TEST_PATH: Path = Path("testee")
    CENTRAL_PATH: Path = Path("central")
    NECESSARY_SUBTITLES: dict = {
        "Description":"https://github.com/GESIS-Methods-Hub/guidelines/blob/v0/method/template.md#description",
        "Use Cases":"https://github.com/GESIS-Methods-Hub/guidelines/blob/v0/method/template.md#use-cases",
        "Input Data":"https://github.com/GESIS-Methods-Hub/guidelines/blob/v0/method/template.md#input-data",
        "Output Data":"https://github.com/GESIS-Methods-Hub/guidelines/blob/v0/method/template.md#output-data",
        "Hardware Requirements":"https://github.com/GESIS-Methods-Hub/guidelines/blob/v0/method/template.md#hardware-requirements",
        "Environment Setup":"https://github.com/GESIS-Methods-Hub/guidelines/blob/v0/method/template.md#environment-setup",
        "How to Use":"https://github.com/GESIS-Methods-Hub/guidelines/blob/v0/method/template.md#how-to-use",
        "Technical Details":"https://github.com/GESIS-Methods-Hub/guidelines/blob/v0/method/template.md#how-to-use",
        "Contact Details":"https://github.com/GESIS-Methods-Hub/guidelines/blob/v0/method/template.md#contact-detailsn "}
    BINDER_DIRS: list[str] = ["",".binder", "binder"]
    FREE_LICENSES: list[str]=["Apache-2.0","MIT","BSD-2-Clause","BSD-3-Clause","ISC","Zlib","BSL-1.0","GNU","GPL-3.0"]
    REPO_REQUIREMENTS:dict = {"citation":"citation missing: https://github.com/GESIS-Methods-Hub/guidelines?tab=readme-ov-file#quality-criteria",
                         "license":"license missing: https://github.com/GESIS-Methods-Hub/guidelines?tab=readme-ov-file#quality-criteria",
                                   "postbuild":"postbuild missing: https://github.com/GESIS-Methods-Hub/guidelines?tab=readme-ov-file#binder-environment"}