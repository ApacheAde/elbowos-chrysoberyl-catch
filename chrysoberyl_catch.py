#!/usr/bin/env python3
"""Chrysoberyl Catch — neon crystal catcher arcade for ElbowOS. Python 3 + pygame."""
import math
import os
import random
import subprocess
import sys

RECORD = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
PLAY = "--play" in sys.argv

if RECORD or not PLAY:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

W, H, FPS, SECS = 1080, 1920, 30, 15
OUT = os.environ.get("ELBOWOS_MP4", "/home/workdir/artifacts/CHRYSOBERYL_CATCH_ElbowOS.mp4")
TITLE, HANDLE = "CHRYSOBERYL CATCH", "x.com/ElbowOS"

BG = (6, 2, 18)
PADDLE_COL = (0, 255, 210)
GLOW = (0, 160, 255)
GEM_COLORS = [
    (255, 70, 200), (255, 200, 50), (120, 255, 80),
    (40, 230, 255), (180, 80, 255), (255, 120, 60)
]
WHITE = (245, 250, 255)
SCORE_COL = (255, 230, 80)
ACCENT = (255, 100, 180)

class Gem:
    def __init__(self):
        self.x = random.randint(100, W - 100)
        self.y = random.randint(-1200, -40)
        self.vy = random.uniform(5.5, 11)
        self.color = random.choice(GEM_COLORS)
        self.r = random.randint(32, 56)
        self.rot = random.uniform(0, math.pi * 2)
        self.spin = random.uniform(-0.12, 0.12)
        self.points = 8 + self.r // 3
        self.sway = random.uniform(0.6, 1.4)

    def update(self):
        self.y += self.vy
        self.rot += self.spin
        self.x += math.sin(self.y * 0.008) * self.sway

    def draw(self, surf):
        pts = []
        for i in range(4):
            a = self.rot + i * (math.pi / 2)
            rx = self.r * (1.1 if i % 2 == 0 else 0.75)
            pts.append((self.x + math.cos(a) * rx, self.y + math.sin(a) * self.r))
        pygame.draw.polygon(surf, self.color, pts)
        pygame.draw.polygon(surf, WHITE, pts, 4)
        pygame.draw.circle(surf, WHITE, (int(self.x), int(self.y)), 6)

class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        flags = 0 if PLAY else pygame.HIDDEN
        try:
            self.screen = pygame.display.set_mode((W, H), flags)
        except pygame.error:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            pygame.display.init()
            self.screen = pygame.display.set_mode((W, H), pygame.HIDDEN)
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.font_lg = pygame.font.SysFont("arial", 68, bold=True)
        self.font_md = pygame.font.SysFont("arial", 52, bold=True)
        self.font_sm = pygame.font.SysFont("arial", 40)
        self.stars = [(random.randint(0, W), random.randint(0, H), random.randint(1, 3)) for _ in range(60)]
        self.reset()

    def reset(self):
        self.paddle_x = W // 2
        self.paddle_w = 240
        self.paddle_h = 32
        self.paddle_y = H - 200
        self.score = 0
        self.gems = [Gem() for _ in range(10)]
        self.time = 0
        self.lives = 5
        self.particles = []

    def spawn_gem(self):
        g = Gem()
        g.y = random.randint(-400, -20)
        self.gems.append(g)

    def update_auto(self):
        target = self.paddle_x
        best_dist = 9999
        for g in self.gems:
            if g.y > 200 and g.y < self.paddle_y + 40:
                dist = abs(g.x - self.paddle_x) + (self.paddle_y - g.y) * 0.3
                if dist < best_dist:
                    best_dist = dist
                    target = g.x
        speed = 18
        if self.paddle_x < target - 8:
            self.paddle_x += speed
        elif self.paddle_x > target + 8:
            self.paddle_x -= speed
        self.paddle_x = max(self.paddle_w // 2 + 30, min(W - self.paddle_w // 2 - 30, self.paddle_x))

    def update(self, keys=None):
        self.time += 1
        if not PLAY:
            self.update_auto()
        else:
            speed = 18
            if keys and (keys[pygame.K_LEFT] or keys[pygame.K_a]):
                self.paddle_x -= speed
            if keys and (keys[pygame.K_RIGHT] or keys[pygame.K_d]):
                self.paddle_x += speed
            self.paddle_x = max(self.paddle_w // 2 + 30, min(W - self.paddle_w // 2 - 30, self.paddle_x))

        for g in self.gems[:]:
            g.update()
            caught = (abs(g.x - self.paddle_x) < self.paddle_w // 2 + g.r * 0.6 and
                      abs(g.y - self.paddle_y) < self.paddle_h + g.r * 0.7)
            if caught:
                self.score += g.points
                self.gems.remove(g)
                self.spawn_gem()
                for _ in range(12):
                    self.particles.append([
                        g.x, g.y,
                        random.uniform(-6, 6), random.uniform(-8, -2),
                        g.color, 18
                    ])
            elif g.y > H + 80:
                self.gems.remove(g)
                self.spawn_gem()
                self.lives -= 1
                if self.lives <= 0:
                    self.score = max(0, self.score - 30)
                    self.lives = 5

        for p in self.particles[:]:
            p[0] += p[2]
            p[1] += p[3]
            p[5] -= 1
            if p[5] <= 0:
                self.particles.remove(p)

        if random.random() < 0.03 and len(self.gems) < 14:
            self.spawn_gem()

    def draw(self):
        self.screen.fill(BG)
        for sx, sy, sz in self.stars:
            y = (sy + self.time * 2) % H
            pygame.draw.circle(self.screen, (50, 40, 90), (sx, int(y)), sz)

        for p in self.particles:
            alpha_r = max(2, p[5] // 3)
            pygame.draw.circle(self.screen, p[4], (int(p[0]), int(p[1])), alpha_r)

        for g in self.gems:
            g.draw(self.screen)

        px = int(self.paddle_x - self.paddle_w // 2)
        pygame.draw.rect(self.screen, GLOW, (px - 6, self.paddle_y - 6, self.paddle_w + 12, self.paddle_h + 12), border_radius=16)
        pygame.draw.rect(self.screen, PADDLE_COL, (px, self.paddle_y, self.paddle_w, self.paddle_h), border_radius=12)
        pygame.draw.rect(self.screen, WHITE, (px + 20, self.paddle_y + 4, self.paddle_w - 40, 8), border_radius=4)

        title_surf = self.font_lg.render(TITLE, True, (255, 220, 120))
        self.screen.blit(title_surf, (W // 2 - title_surf.get_width() // 2, 70))
        score_surf = self.font_md.render(f"SCORE  {self.score}", True, SCORE_COL)
        self.screen.blit(score_surf, (W // 2 - score_surf.get_width() // 2, 170))
        lives_surf = self.font_sm.render(f"LIVES {self.lives}", True, ACCENT)
        self.screen.blit(lives_surf, (50, 180))
        handle_surf = self.font_sm.render(HANDLE, True, (160, 180, 255))
        self.screen.blit(handle_surf, (W // 2 - handle_surf.get_width() // 2, H - 90))

        if PLAY:
            pygame.display.flip()

    def record(self):
        frames = FPS * SECS
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        cmd = [
            "ffmpeg", "-y",
            "-f", "rawvideo", "-vcodec", "rawvideo",
            "-s", f"{W}x{H}", "-pix_fmt", "rgb24",
            "-r", str(FPS), "-i", "-",
            "-an",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "20", "-preset", "fast",
            "-movflags", "+faststart",
            OUT
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        for _ in range(frames):
            self.update()
            self.draw()
            raw = pygame.image.tostring(self.screen, "RGB")
            try:
                proc.stdin.write(raw)
            except BrokenPipeError:
                break
        proc.stdin.close()
        stderr = proc.stderr.read().decode()
        code = proc.wait()
        if code != 0:
            raise RuntimeError(f"ffmpeg failed (code {code}): {stderr}")
        print(f"Recorded {OUT}")

    def play_interactive(self):
        running = True
        while running:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                    running = False
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_r:
                    self.reset()
            keys = pygame.key.get_pressed()
            self.update(keys)
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()

if __name__ == "__main__":
    game = Game()
    if RECORD or not PLAY:
        game.record()
    else:
        game.play_interactive()
