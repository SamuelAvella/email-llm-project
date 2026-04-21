from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.cleaning import DEFAULT_REPORT_NAME, clean_directory, clean_email_text


class CleanEmailTextTests(unittest.TestCase):
    def test_removes_noise_and_redacts_contacts(self) -> None:
        raw = """
        <div><b>URGENT:</b> Please read this immediately!</div>
        <p>I have asked for a refund three times now.</p>

        I expect a call at +1 (555) 010-9988 or email me at admin@personal.net.
        Check my order status here: https://portal.techcompany.com/orders/998822

        > On Mon, Feb 10, 2026 at 9:00 AM, Support wrote:
        > > Thank you for contacting us.

        ----------
        Sent from my iPhone
        """

        cleaned, stats = clean_email_text(raw)

        self.assertIn("URGENT:", cleaned)
        self.assertIn("<PHONE>", cleaned)
        self.assertIn("<EMAIL>", cleaned)
        self.assertIn("<URL>", cleaned)
        self.assertNotIn("Sent from my iPhone", cleaned)
        self.assertEqual(stats["quoted_blocks_removed"], 1)

    def test_preserves_bug_report_structure(self) -> None:
        raw = """
        Hi Engineering Team,

        **Steps to reproduce:**
        1. Go to Settings
        2. Click "Upload avatar"
        3. HTTP 500 Internal Server Error appears immediately

        **Expected:** Avatar saved. **Actual:** 500 error.

        Regards,
        QA External Team | qa.external@testing.com
        """

        cleaned, stats = clean_email_text(raw)

        self.assertIn("Steps to reproduce:", cleaned)
        self.assertIn("HTTP 500 Internal Server Error", cleaned)
        self.assertNotIn("Regards,", cleaned)
        self.assertNotIn("qa.external@testing.com", cleaned)
        self.assertEqual(stats["signature_blocks_removed"], 1)


class CleanDirectoryTests(unittest.TestCase):
    def test_writes_clean_files_and_report(self) -> None:
        with TemporaryDirectory() as input_dir_name, TemporaryDirectory() as output_dir_name:
            input_dir = Path(input_dir_name)
            output_dir = Path(output_dir_name)

            (input_dir / "msg_001.txt").write_text(
                "Hello.\nCall me at +34 600 123 123.\n",
                encoding="utf-8",
            )

            processed = clean_directory(input_dir=input_dir, output_dir=output_dir)

            self.assertEqual(processed, 1)
            self.assertTrue((output_dir / "msg_001.txt").exists())

            report = json.loads(
                (output_dir / DEFAULT_REPORT_NAME).read_text(encoding="utf-8")
            )
            self.assertEqual(report["processed_files"], 1)
            self.assertEqual(report["files"][0]["phone_redactions"], 1)


if __name__ == "__main__":
    unittest.main()
