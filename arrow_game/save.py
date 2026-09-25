"""存档系统：保存/读取游戏进度。

存档内容：
    - 已解锁关卡 ID
    - 每关最佳得分与星级
    - 音效开关
    - 无尽模式最高记录

存档位置：与可执行文件同目录（或用户主目录，视平台而定）。
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, Optional

from .constants import SAVE_FILE_NAME


def _save_dir() -> Path:
    """返回存档目录。

    - 开发环境：项目根目录
    - 打包后（PyInstaller）：可执行文件所在目录
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


@dataclass
class LevelRecord:
    """单关最佳记录。"""
    best_score: int = 0
    stars: int = 0
    best_time: float = 0.0
    cleared: bool = False


@dataclass
class SaveData:
    """完整存档数据。"""
    unlocked_levels: int = 1                  # 已解锁到第几关（>=1）
    records: Dict[int, LevelRecord] = field(default_factory=dict)
    sound_enabled: bool = True
    endless_best: int = 0                     # 无尽模式最高连过关卡数
    total_play_time: float = 0.0              # 累计游玩秒数
    version: int = 1

    def to_dict(self) -> dict:
        return {
            "unlocked_levels": self.unlocked_levels,
            "records": {str(k): asdict(v) for k, v in self.records.items()},
            "sound_enabled": self.sound_enabled,
            "endless_best": self.endless_best,
            "total_play_time": self.total_play_time,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SaveData":
        records = {}
        for k, v in data.get("records", {}).items():
            try:
                records[int(k)] = LevelRecord(**v)
            except (TypeError, ValueError):
                continue
        return cls(
            unlocked_levels=max(1, int(data.get("unlocked_levels", 1))),
            records=records,
            sound_enabled=bool(data.get("sound_enabled", True)),
            endless_best=int(data.get("endless_best", 0)),
            total_play_time=float(data.get("total_play_time", 0.0)),
            version=int(data.get("version", 1)),
        )


class SaveManager:
    """存档读写。"""

    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = path or (_save_dir() / SAVE_FILE_NAME)
        self.data = SaveData()

    def load(self) -> SaveData:
        if not self.path.exists():
            return self.data
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            self.data = SaveData.from_dict(raw)
        except (json.JSONDecodeError, OSError, ValueError):
            # 存档损坏时静默重置
            self.data = SaveData()
        return self.data

    def save(self) -> bool:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data.to_dict(), f, ensure_ascii=False, indent=2)
            return True
        except OSError:
            return False

    def update_level_result(
        self, level_id: int, score: int, stars: int, time_used: float
    ) -> None:
        """通关后更新记录（只保留最佳）。"""
        rec = self.data.records.get(level_id) or LevelRecord()
        rec.cleared = True
        rec.best_score = max(rec.best_score, score)
        rec.stars = max(rec.stars, stars)
        if rec.best_time <= 0 or time_used < rec.best_time:
            rec.best_time = time_used
        self.data.records[level_id] = rec
        # 解锁下一关
        if level_id + 1 > self.data.unlocked_levels:
            self.data.unlocked_levels = level_id + 1
        self.save()

    def reset(self) -> None:
        """清空存档。"""
        self.data = SaveData()
        if self.path.exists():
            try:
                self.path.unlink()
            except OSError:
                pass
