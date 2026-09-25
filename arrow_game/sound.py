"""程序化音效生成。

不依赖外部音频文件，使用 pygame.sndarray + 简单波形合成，
避免版权与资源管理问题。所有音效都是短促的合成音。

如果 numpy 不可用，会静默降级为无声模式。
"""
from __future__ import annotations

import math
from typing import Optional

import pygame

try:
    import numpy as np
    _HAS_NUMPY = True
except ImportError:  # pragma: no cover
    _HAS_NUMPY = False


SAMPLE_RATE = 22050


class SoundBank:
    """管理所有合成音效。"""

    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled and _HAS_NUMPY
        self._cache: dict[str, Optional[pygame.mixer.Sound]] = {}
        if self.enabled:
            try:
                pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1)
            except pygame.error:
                self.enabled = False

    # ---------------- 基础波形合成 ----------------

    def _make_sound(self, samples: "np.ndarray") -> Optional[pygame.mixer.Sound]:
        if not self.enabled:
            return None
        try:
            # 归一化到 int16
            peak = float(np.max(np.abs(samples))) or 1.0
            data = (samples / peak * 32767 * 0.6).astype(np.int16)
            return pygame.sndarray.make_sound(data)
        except Exception:
            return None

    def _tone(
        self,
        freq: float,
        duration: float,
        volume: float = 1.0,
        attack: float = 0.01,
        decay: float = 0.1,
        wave: str = "sine",
    ) -> "np.ndarray":
        n = int(SAMPLE_RATE * duration)
        t = np.linspace(0, duration, n, endpoint=False)
        if wave == "sine":
            samples = np.sin(2 * np.pi * freq * t)
        elif wave == "square":
            samples = np.sign(np.sin(2 * np.pi * freq * t))
        elif wave == "triangle":
            samples = 2 * np.abs(2 * (t * freq - np.floor(t * freq + 0.5))) - 1
        elif wave == "saw":
            samples = 2 * (t * freq - np.floor(t * freq + 0.5))
        else:
            samples = np.sin(2 * np.pi * freq * t)
        # 包络
        env = np.ones(n)
        a = int(attack * SAMPLE_RATE)
        d = int(decay * SAMPLE_RATE)
        if a > 0:
            env[:a] = np.linspace(0, 1, a)
        if d > 0 and d < n:
            env[-d:] = np.linspace(1, 0, d)
        return samples * env * volume

    def _sweep(
        self,
        f_start: float,
        f_end: float,
        duration: float,
        volume: float = 1.0,
    ) -> "np.ndarray":
        n = int(SAMPLE_RATE * duration)
        t = np.linspace(0, duration, n, endpoint=False)
        freq = np.linspace(f_start, f_end, n)
        phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
        samples = np.sin(phase)
        env = np.linspace(1, 0, n) ** 1.5
        return samples * env * volume

    def _noise(self, duration: float, volume: float = 0.5) -> "np.ndarray":
        n = int(SAMPLE_RATE * duration)
        samples = np.random.uniform(-1, 1, n)
        env = np.linspace(1, 0, n) ** 2
        return samples * env * volume

    # ---------------- 具体音效 ----------------

    def _get(self, key: str, builder) -> Optional[pygame.mixer.Sound]:
        if not self.enabled:
            return None
        if key not in self._cache:
            self._cache[key] = self._make_sound(builder())
        return self._cache[key]

    def play_shoot(self) -> None:
        """箭头飞出：短促上扬音。"""
        snd = self._get("shoot", lambda: self._sweep(400, 900, 0.18, 0.7))
        if snd: snd.play()

    def play_collide(self) -> None:
        """碰撞：低沉短音 + 噪声。"""
        def build():
            a = self._tone(120, 0.15, 0.8, wave="square")
            b = self._noise(0.12, 0.4)
            n = min(len(a), len(b))
            return a[:n] + b[:n]
        snd = self._get("collide", build)
        if snd: snd.play()

    def play_click(self) -> None:
        """UI 点击：清脆短音。"""
        snd = self._get("click", lambda: self._tone(800, 0.06, 0.4, wave="triangle"))
        if snd: snd.play()

    def play_win(self) -> None:
        """通关：上行三音。"""
        def build():
            a = self._tone(523, 0.15, 0.6)  # C5
            b = self._tone(659, 0.15, 0.6)  # E5
            c = self._tone(784, 0.30, 0.7)  # G5
            return np.concatenate([a, b, c])
        snd = self._get("win", build)
        if snd: snd.play()

    def play_lose(self) -> None:
        """失败：下行二音。"""
        def build():
            a = self._tone(330, 0.20, 0.6, wave="triangle")
            b = self._tone(220, 0.35, 0.6, wave="triangle")
            return np.concatenate([a, b])
        snd = self._get("lose", build)
        if snd: snd.play()

    def play_hint(self) -> None:
        """提示：轻柔双音。"""
        def build():
            a = self._tone(880, 0.10, 0.4)
            b = self._tone(1108, 0.15, 0.4)
            return np.concatenate([a, b])
        snd = self._get("hint", build)
        if snd: snd.play()

    def play_undo(self) -> None:
        """撤销：短促下行。"""
        snd = self._get("undo", lambda: self._sweep(700, 350, 0.15, 0.5))
        if snd: snd.play()

    def play_star(self) -> None:
        """星级点亮：叮。"""
        snd = self._get("star", lambda: self._tone(1318, 0.20, 0.5))
        if snd: snd.play()


# 全局单例（懒初始化）
_bank: Optional[SoundBank] = None


def get_sound_bank() -> SoundBank:
    global _bank
    if _bank is None:
        _bank = SoundBank(enabled=True)
    return _bank


def disable_sound() -> None:
    global _bank
    _bank = SoundBank(enabled=False)
