import os
import unittest
from unittest.mock import patch

from backend import config


class ConfigTests(unittest.TestCase):
    def test_load_settings_uses_default_monitor_values(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            settings = config.load_settings()

        self.assertEqual(
            settings.monitor_url, "https://www.tokyodisneyresort.jp/tdr/news/update/"
        )
        self.assertEqual(settings.monitor_selector, ".linkList6.listUpdate ul")

    def test_load_settings_raises_when_check_interval_is_less_than_60(self) -> None:
        with patch.dict(os.environ, {"CHECK_INTERVAL_MINUTES": "59"}, clear=True):
            with self.assertRaisesRegex(ValueError, r"CHECK_INTERVAL_MINUTES must be >= 60\."):
                config.load_settings()


if __name__ == "__main__":
    unittest.main()
