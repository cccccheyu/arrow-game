"""动画系统：缓动函数、粒子、飞出/抖动动画。

所有动画都是"数据驱动"的：每帧调用 update(dt) 推进进度，
渲染层读取当前状态进行绘制。这样便于暂停、回放与单元测试。
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import List, Tuple

import pygame

from .arrow import Arrow, ArrowState
from .constants import (
    ANIM_FLY_DURATION,
    ANIM_PARTICLE_LIFE,
    ANIM_SHAKE_DURATION,
)
from .direction import Direction


# ---------------- 缓动函数 ----------------

def ease_out_cubic(t: float) -> float:
    return 1 - (1 - t) ** 3


def ease_in_quad(t: float) -> float:
    return t * t


def ease_out_back(t: float, s: float = 1.70158) -> float:
    t -= 1
    return t * t * ((s + 1) * t + s) + 1


def ease_in_out_sine(t: float) -> float:
    return -(math.cos(math.pi * t) - 1) / 2


# ---------------- 粒子 ----------------

@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float           # 剩余寿命（秒）
    max_life: float
    color: Tuple[int, int, int]
    size: float = 3.0
    gravity: float = 0.0

    @property
    def alive(self) -> bool:
        return self.life > 0

    @property
    def alpha(self) -> int:
        return max(0, min(255, int(255 * (self.life / self.max_life))))

    def update(self, dt: float) -> None:
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.gravity * dt
        self.life -= dt


class ParticleSystem:
    """管理所有活跃粒子。"""

    def __init__(self) -> None:
        self.particles: List[Particle] = []

    def burst(
        self,
        x: float,
        y: float,
        color: Tuple[int, int, int],
        count: int = 14,
        speed: float = 180.0,
        life: float = ANIM_PARTICLE_LIFE,
        gravity: float = 0.0,
    ) -> None:
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            sp = random.uniform(speed * 0.4, speed)
            self.particles.append(
                Particle(
                    x=x, y=y,
                    vx=math.cos(angle) * sp,
                    vy=math.sin(angle) * sp,
                    life=random.uniform(life * 0.6, life),
                    max_life=life,
                    color=color,
                    size=random.uniform(2.0, 4.5),
                    gravity=gravity,
                )
            )

    def trail(
        self,
        x: float,
        y: float,
        color: Tuple[int, int, int],
        count: int = 3,
    ) -> None:
        """飞行尾迹：少量、短寿命、向后飘。"""
        for _ in range(count):
            self.particles.append(
                Particle(
                    x=x + random.uniform(-4, 4),
                    y=y + random.uniform(-4, 4),
                    vx=random.uniform(-30, 30),
                    vy=random.uniform(-30, 30),
                    life=random.uniform(0.18, 0.32),
                    max_life=0.32,
                    color=color,
                    size=random.uniform(1.5, 3.0),
                )
            )

    def update(self, dt: float) -> None:
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.alive]

    def draw(self, surface: pygame.Surface) -> None:
        for p in self.particles:
            color = (*p.color, p.alpha)
            layer = pygame.Surface((int(p.size * 2), int(p.size * 2)), pygame.SRCALPHA)
            pygame.draw.circle(layer, color, (int(p.size), int(p.size)), int(p.size))
            surface.blit(layer, (p.x - p.size, p.y - p.size))

    def clear(self) -> None:
        self.particles.clear()


# ---------------- 箭头动画控制器 ----------------

@dataclass
class FlyAnimation:
    """控制一个箭头飞出棋盘。"""
    arrow: Arrow
    cell_size: int
    board_origin: Tuple[int, int]   # 棋盘左上角像素坐标
    elapsed: float = 0.0
    duration: float = ANIM_FLY_DURATION
    finished: bool = False
    on_finish: field(default=None, repr=False) = None  # 可选回调

    def update(self, dt: float) -> None:
        self.elapsed += dt
        t = min(1.0, self.elapsed / self.duration)
        eased = ease_out_cubic(t)
        dr, dc = self.arrow.direction.delta
        # 飞出距离：至少覆盖到棋盘外 2 格
        max_distance = self.cell_size * 3
        dist = eased * max_distance
        self.arrow.pixel_offset = (dc * dist, dr * dist)
        if t >= 1.0 and not self.finished:
            self.finished = True
            self.arrow.state = ArrowState.GONE
            if self.on_finish:
                self.on_finish(self.arrow)


@dataclass
class ShakeAnimation:
    """碰撞反馈：箭头沿垂直方向来回抖动 + 变红。"""
    arrow: Arrow
    elapsed: float = 0.0
    duration: float = ANIM_SHAKE_DURATION
    amplitude: float = 8.0
    finished: bool = False

    def update(self, dt: float) -> None:
        self.elapsed += dt
        t = self.elapsed / self.duration
        if t >= 1.0:
            self.arrow.shake_offset = (0.0, 0.0)
            self.arrow.state = ArrowState.IDLE
            self.finished = True
            return
        # 衰减正弦波
        decay = 1.0 - t
        # 沿箭头方向的垂直轴抖动
        dr, dc = self.arrow.direction.delta
        # 垂直方向：(dr, dc) -> (-dc, dr)
        px, py = -dc, dr
        offset = math.sin(t * math.pi * 6) * self.amplitude * decay
        self.arrow.shake_offset = (px * offset, py * offset)


class AnimationManager:
    """统一管理所有活跃动画。"""

    def __init__(self) -> None:
        self.fly_anims: List[FlyAnimation] = []
        self.shake_anims: List[ShakeAnimation] = []
        self.particles = ParticleSystem()

    def start_fly(
        self,
        arrow: Arrow,
        cell_size: int,
        board_origin: Tuple[int, int],
        on_finish=None,
    ) -> None:
        arrow.state = ArrowState.FLYING
        arrow.anim_t = 0.0
        self.fly_anims.append(
            FlyAnimation(arrow, cell_size, board_origin, on_finish=on_finish)
        )

    def start_shake(self, arrow: Arrow) -> None:
        arrow.state = ArrowState.SHAKING
        arrow.anim_t = 0.0
        self.shake_anims.append(ShakeAnimation(arrow))

    def update(self, dt: float) -> None:
        for a in self.fly_anims:
            a.update(dt)
        self.fly_anims = [a for a in self.fly_anims if not a.finished]
        for a in self.shake_anims:
            a.update(dt)
        self.shake_anims = [a for a in self.shake_anims if not a.finished]
        self.particles.update(dt)

    def is_busy(self) -> bool:
        return bool(self.fly_anims or self.shake_anims)

    def clear(self) -> None:
        self.fly_anims.clear()
        self.shake_anims.clear()
        self.particles.clear()
