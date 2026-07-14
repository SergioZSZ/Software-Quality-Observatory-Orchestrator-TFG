import json
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


SOCA_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SOCA_ROOT / "src"))

from linkeddata_portal.builder import build  # noqa: E402
from linkeddata_portal.builder import DEFAULT_ASSETS_DIR, DEFAULT_TEMPLATES_DIR  # noqa: E402


class TestLinkedDataPortalBuilder(unittest.TestCase):
    def test_build_writes_resolved_yaml_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "linkeddata.base.yml"
            templates_dir = root / "templates"
            assets_dir = root / "assets"
            output_dir = root / "generates"
            project_metadata_dir = root / "project_metadata"
            linkeddata_metadata_dir = root / "linkeddata_metadata"
            generated_config_path = root / "linkeddata.generated.yml"

            templates_dir.mkdir()
            assets_dir.mkdir()
            project_metadata_dir.mkdir()
            (assets_dir / "starter-template.css").write_text("", encoding="utf-8")
            (templates_dir / "cards_page.html").write_text(
                "{{ page.title }}{% for item in items %}{{ item.name }}{% endfor %}",
                encoding="utf-8",
            )

            config_path.write_text(
                yaml.safe_dump(
                    {
                        "site": {"title": "LinkedData"},
                        "navigation": [],
                        "pages": {
                            "tools": {
                                "title": "Tools",
                                "output": "tools.html",
                                "collection": "tools",
                            }
                        },
                        "tools": [],
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            (project_metadata_dir / "SergioZSZ_soca_2026-07-14.json").write_text(
                json.dumps(
                    {
                        "name": [
                            {
                                "technique": "GitHub_API",
                                "result": {"value": "SOCA"},
                            }
                        ],
                        "description": [
                            {
                                "technique": "code_parser",
                                "result": {"value": "Software catalog creator."},
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            build(
                output_dir=output_dir,
                config_path=config_path,
                templates_dir=templates_dir,
                assets_dir=assets_dir,
                metadata_dir=project_metadata_dir,
                linkeddata_metadata_dir=linkeddata_metadata_dir,
                linkeddata_extra_repos=["https://github.com/SergioZSZ/soca"],
                generated_config_path=generated_config_path,
            )

            generated_config = yaml.safe_load(
                generated_config_path.read_text(encoding="utf-8")
            )

            self.assertEqual(generated_config["tools"][0]["name"], "SOCA")
            self.assertEqual(
                generated_config["tools"][0]["homepage"],
                "https://github.com/SergioZSZ/soca",
            )

    def test_card_titles_can_wrap_long_repository_names(self):
        cards_template = (DEFAULT_TEMPLATES_DIR / "cards_page.html").read_text(
            encoding="utf-8"
        )
        stylesheet = (DEFAULT_ASSETS_DIR / "starter-template.css").read_text(
            encoding="utf-8"
        )

        self.assertIn("linkeddata-card-title", cards_template)
        self.assertIn(".linkeddata-card-title", stylesheet)
        self.assertIn("overflow-wrap: anywhere", stylesheet)


if __name__ == "__main__":
    unittest.main()
