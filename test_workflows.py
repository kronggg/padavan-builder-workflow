#!/usr/bin/env python3
"""Тесты логики workflow-пайплайна Padavan.

Запуск: python3 -m unittest test_workflows -v
"""
import os
import subprocess
import tempfile
import unittest

import yaml

WF_FILES = ["build.yml", "build-one.yml", "watch-upstream.yml"]

AWK_PARSE = """awk '/"Firmware"/{ getline; getline; gsub(/,$/,""); print $2 }'"""

SAMPLE = '''{{
\tname:\t"Bootloader",
\toffset:\t0x0,
\tsize:\t0x30000,
}}, {{
\tname:\t"Firmware",
\toffset:\t0x600000,
\tsize:\t{s},
}}, {{
\tname:\t"Config",
\toffset:\t0x1A00000,
\tsize:\t0x10000,
}}, {{
'''


def awk_size(text):
    with tempfile.NamedTemporaryFile("w", suffix=".config", delete=False) as f:
        f.write(text)
        path = f.name
    try:
        r = subprocess.run(["bash", "-c", AWK_PARSE + " " + path],
                           capture_output=True, text=True)
        return r.stdout.strip()
    finally:
        os.unlink(path)


class TestPartitionParsing(unittest.TestCase):
    def test_mi4_20mb(self):
        hexv = awk_size(SAMPLE.format(s="0x1400000"))
        self.assertEqual(hexv, "0x1400000")
        self.assertEqual(round(int(hexv, 16) / 1048576), 20)

    def test_small_15mb(self):
        hexv = awk_size(SAMPLE.format(s="0xF70000"))
        self.assertEqual(hexv, "0xF70000")
        self.assertEqual(round(int(hexv, 16) / 1048576), 15)

    def test_no_firmware_block(self):
        self.assertEqual(awk_size('{ name: "Bootloader", size: 0x80000, },\n'), "")


class TestWorkflowFiles(unittest.TestCase):
    def test_yaml_valid(self):
        for f in WF_FILES:
            with self.subTest(f=f):
                with open(os.path.join(".github/workflows", f), encoding="utf-8") as fh:
                    doc = yaml.safe_load(fh)
                self.assertIsInstance(doc, dict)

    def test_run_blocks_bash_syntax(self):
        for f in WF_FILES:
            with open(os.path.join(".github/workflows", f), encoding="utf-8") as fh:
                doc = yaml.safe_load(fh)
            for jn, job in (doc.get("jobs") or {}).items():
                steps = job.get("steps")
                if not isinstance(steps, list):
                    continue
                for st in steps:
                    if not (isinstance(st, dict) and "run" in st):
                        continue
                    with self.subTest(file=f, step=st.get("name")):
                        with tempfile.NamedTemporaryFile("w", suffix=".sh", delete=False) as fh:
                            fh.write(st["run"])
                            p = fh.name
                        try:
                            r = subprocess.run(["bash", "-n", p], capture_output=True, text=True)
                            self.assertEqual(r.returncode, 0, r.stderr)
                        finally:
                            os.unlink(p)


class TestModelRegistration(unittest.TestCase):
    @staticmethod
    def _triggers(doc):
        # YAML 1.1 парсит ключ 'on' как True, YAML 1.2 — как 'on'.
        return doc.get("on") or doc.get(True) or {}

    def setUp(self):
        with open(".github/workflows/build.yml", encoding="utf-8") as f:
            self.build = yaml.safe_load(f)
        with open(".github/workflows/watch-upstream.yml", encoding="utf-8") as f:
            self.watch = yaml.safe_load(f)

    def _model_options(self, doc):
        trig = self._triggers(doc)
        wd = trig.get("workflow_dispatch") or trig.get(True) or {}
        return (wd.get("inputs") or {}).get("model", {}).get("options", [])

    def test_all_models_in_finalize(self):
        opts = self._model_options(self.build)
        self.assertTrue(opts, "options пусты в build.yml")
        for m in ["all", "rm-ac2100", "mi-3", "mi-r3gv2", "mi-4"]:
            self.assertIn(m, opts)

    def test_all_models_in_watch(self):
        opts = self._model_options(self.watch)
        self.assertTrue(opts, "options пусты в watch-upstream.yml")
        for m in ["all", "rm-ac2100", "mi-3", "mi-r3gv2", "mi-4"]:
            self.assertIn(m, opts)

    def test_jobs_exist(self):
        jobs = set((self.build.get("jobs") or {}).keys())
        for m in ["rm-ac2100", "mi-3", "mi-r3gv2", "mi-4"]:
            self.assertIn(m, jobs)

    def test_finalize_needs_four(self):
        needs = self.build["jobs"]["finalize"]["needs"]
        self.assertEqual(len(needs), 4, needs)
        self.assertIn("mi-4", needs)


class TestMi4Config(unittest.TestCase):
    def setUp(self):
        with open("configs/mi-4.config", encoding="utf-8") as f:
            self.cfg = f.read()

    def test_product_id(self):
        self.assertIn('CONFIG_FIRMWARE_PRODUCT_ID="MI-4"', self.cfg)

    def test_vendor(self):
        self.assertIn("CONFIG_VENDOR=XIAOMI", self.cfg)

    def test_platform(self):
        self.assertIn("CONFIG_PRODUCT=MT7621", self.cfg)

    def test_wifi_2ghz_mt7603e(self):
        self.assertIn("CONFIG_FIRMWARE_WIFI2_DRIVER=4.1", self.cfg)

    def test_wifi_5ghz_mt7612e(self):
        # MI-4 имеет MT7612E (3.0), НЕ MT7615E (5.1.0.0)
        self.assertIn("CONFIG_FIRMWARE_WIFI5_DRIVER=3.0", self.cfg)
        self.assertNotIn("CONFIG_FIRMWARE_WIFI_DRIVER=5.1.0.0", self.cfg)


class TestForceLogic(unittest.TestCase):
    """force=true должен запускать сборку даже при пустом pending."""

    SCRIPT = None

    @classmethod
    def setUpClass(cls):
        with open(".github/workflows/watch-upstream.yml", encoding="utf-8") as f:
            doc = yaml.safe_load(f)
        for job in (doc.get("jobs") or {}).values():
            steps = job.get("steps")
            if not isinstance(steps, list):
                continue
            for st in steps:
                if isinstance(st, dict) and "Trigger weekly or urgent build" in (st.get("name") or ""):
                    cls.SCRIPT = st["run"]
        assert cls.SCRIPT, "не найден шаг 'Trigger weekly or urgent build'"

    def _should_exit_early(self, pending, force):
        """Прогнать только проверку pending с подставленными значениями."""
        # вырезаем первый if-блок про pending и проверяем его условие
        import re
        m = re.search(r'if \[\[ "\$PENDING_COUNT" -eq 0(.*?)\]\]; then', self.SCRIPT, re.S)
        self.assertIsNotNone(m, "не найден if про PENDING_COUNT")
        extra = m.group(1)
        cond = '[[ "$PENDING_COUNT" -eq 0' + extra + ' ]]'
        r = subprocess.run(
            ["bash", "-c", f'PENDING_COUNT={pending} FORCE={force}; {cond} && echo EXIT || echo CONTINUE'],
            capture_output=True, text=True)
        return "EXIT" in r.stdout

    def test_pending_zero_force_false_exits(self):
        self.assertTrue(self._should_exit_early(0, "false"))

    def test_pending_zero_force_true_continues(self):
        self.assertFalse(self._should_exit_early(0, "true"))

    def test_pending_nonzero_force_false_continues(self):
        self.assertFalse(self._should_exit_early(3, "false"))

    def test_pending_nonzero_force_true_continues(self):
        self.assertFalse(self._should_exit_early(3, "true"))

if __name__ == "__main__":
    unittest.main(verbosity=2)
