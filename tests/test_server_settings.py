import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend import server


class SettingsTests(unittest.TestCase):
    def test_settings_are_clamped_and_profiles_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'settings.json'
            with patch.object(server, 'SETTINGS_FILE', str(path)):
                result = server.save_settings({
                    'protect_limit': 'invalid',
                    'low_alert': 99,
                    'refresh_sec': 1,
                    'fan_profile': 'not-a-profile'
                })
            self.assertEqual(result['protect_limit'], 80)
            self.assertEqual(result['low_alert'], 50)
            self.assertEqual(result['refresh_sec'], 5)
            self.assertEqual(result['fan_profile'], 'Balanced')
            self.assertEqual(json.loads(path.read_text())['refresh_sec'], 5)


if __name__ == '__main__':
    unittest.main()
