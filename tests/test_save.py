"""存档系统与游戏机制测试。"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from arrow_game.save import LevelRecord, SaveData, SaveManager


class TestSaveSystem(unittest.TestCase):
    """存档读写。"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.path = Path(self.tmpdir) / "test_save.json"

    def tearDown(self):
        if self.path.exists():
            self.path.unlink()
        os.rmdir(self.tmpdir)

    def test_default_save(self):
        sm = SaveManager(self.path)
        sm.load()
        self.assertEqual(sm.data.unlocked_levels, 1)
        self.assertTrue(sm.data.sound_enabled)
        self.assertEqual(sm.data.records, {})

    def test_save_and_load(self):
        sm = SaveManager(self.path)
        sm.data.unlocked_levels = 3
        sm.data.records[1] = LevelRecord(best_score=500, stars=3, best_time=25.0, cleared=True)
        sm.data.records[2] = LevelRecord(best_score=300, stars=2, best_time=40.0, cleared=True)
        sm.save()

        sm2 = SaveManager(self.path)
        sm2.load()
        self.assertEqual(sm2.data.unlocked_levels, 3)
        self.assertEqual(sm2.data.records[1].stars, 3)
        self.assertEqual(sm2.data.records[2].best_score, 300)

    def test_update_level_result_keeps_best(self):
        sm = SaveManager(self.path)
        sm.update_level_result(1, score=500, stars=2, time_used=30.0)
        sm.update_level_result(1, score=700, stars=3, time_used=25.0)
        sm.update_level_result(1, score=400, stars=1, time_used=40.0)  # 更差，不应覆盖
        rec = sm.data.records[1]
        self.assertEqual(rec.best_score, 700)
        self.assertEqual(rec.stars, 3)
        self.assertAlmostEqual(rec.best_time, 25.0)

    def test_unlock_progression(self):
        sm = SaveManager(self.path)
        sm.update_level_result(1, 100, 1, 10.0)
        self.assertEqual(sm.data.unlocked_levels, 2)
        sm.update_level_result(2, 100, 1, 10.0)
        self.assertEqual(sm.data.unlocked_levels, 3)

    def test_corrupt_save_resets(self):
        with open(self.path, "w", encoding="utf-8") as f:
            f.write("{ not valid json")
        sm = SaveManager(self.path)
        sm.load()
        self.assertEqual(sm.data.unlocked_levels, 1)

    def test_reset(self):
        sm = SaveManager(self.path)
        sm.update_level_result(1, 100, 3, 10.0)
        sm.reset()
        self.assertFalse(self.path.exists())
        self.assertEqual(sm.data.unlocked_levels, 1)

    def test_serialization_roundtrip(self):
        data = SaveData(
            unlocked_levels=5,
            records={1: LevelRecord(500, 3, 20.0, True)},
            sound_enabled=False,
            endless_best=7,
            total_play_time=123.4,
        )
        d = data.to_dict()
        # JSON 可序列化
        s = json.dumps(d, ensure_ascii=False)
        self.assertIsInstance(s, str)
        restored = SaveData.from_dict(json.loads(s))
        self.assertEqual(restored.unlocked_levels, 5)
        self.assertFalse(restored.sound_enabled)
        self.assertEqual(restored.endless_best, 7)
        self.assertEqual(restored.records[1].stars, 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
