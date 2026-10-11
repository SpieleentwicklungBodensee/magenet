#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mage.NET – Der Magier mit WLAN-Problemen
Bodensee Game Jam 2026 · Thema: Magie

Roguelite-Dungeon-Crawler (Top-Down). Statt Mana hast du Empfang.
Alle Grafiken und Sounds werden prozedural erzeugt – keine Assets nötig.

Steuerung
  WASD / Pfeiltasten   Bewegen
  Maus                 Zielen
  Linke Maustaste      Feuerball
  Rechte Maus / Leer   Teleport
  Q                    Heilung
  R / F                Heruntergeladene Zauber (Kettenblitz / Meteor)
  E (halten)           Router aktivieren / neu starten, Truhen öffnen
  ESC                  Pause        M  Ton an/aus     N  Musik an/aus

Gamepad (Xbox/PlayStation/Switch, Hot-Plug)
  L-Stick / Steuerkreuz  Bewegen        R-Stick  Zielen (mit leichter Zielhilfe)
  RT / RB  Feuerball     LT / LB  Teleport     X  Heilung     Y  Kettenblitz
  B  Meteor     A (halten)  Interagieren     SELECT  Werbung schließen     START  Pause
"""
import array
import json
import math
import os
import random
import sys

import pygame

try:  # C64-Soundtrack (optional – Spiel läuft auch ohne)
    from mage_music import MusicPlayer
except Exception:
    MusicPlayer = None

# --------------------------------------------------------------------------- Konstanten
W, H = 1280, 720
TILE = 32
FPS = 60
CAPTION = "Mage.NET – Der Magier mit WLAN-Problemen"
SAVE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mage_net_save.json")

WHITE = (240, 240, 250)
BLACK = (0, 0, 0)
CYAN = (80, 230, 255)
MAGENTA = (255, 80, 220)
RED = (255, 70, 70)
GREEN = (90, 255, 140)
YELLOW = (255, 220, 80)
ORANGE = (255, 150, 50)
GREY = (140, 140, 160)
DARK = (14, 12, 22)
PURPLE = (150, 90, 255)

BAR_LABELS = {5: "PERFEKT", 4: "GUT", 3: "WACKELIG", 2: "MIES", 1: "KATASTROPHE", 0: "OFFLINE"}
BAR_COLORS = {5: GREEN, 4: (170, 255, 90), 3: YELLOW, 2: ORANGE, 1: RED, 0: (120, 120, 130)}
PING = {5: 12, 4: 48, 3: 260, 2: 780, 1: 2900}
LATENCY = {5: (0.0, 0.0), 4: (0.08, 0.2), 3: (0.35, 1.1), 2: (0.6, 1.8), 1: (0.3, 1.4)}
STUTTER = {5: 0.0, 4: 0.0, 3: 0.16, 2: 0.24, 1: 0.3, 0: 0.0}
DL_SPEED = {5: 16.0, 4: 6.0, 3: 1.6, 2: 0.25, 1: 0.004, 0: 0.0}  # MB/s

SPELLS = {
    "fire": dict(name="Feuerball", key="LMB", cd=0.32, color=ORANGE),
    "tp": dict(name="Teleport", key="RMB", cd=2.4, color=PURPLE),
    "heal": dict(name="Heilung", key="Q", cd=7.0, color=GREEN),
    "chain": dict(name="Kettenblitz", key="R", cd=1.5, color=YELLOW),
    "meteor": dict(name="Meteor", key="F", cd=5.0, color=(255, 100, 60)),
}
SPELL_ORDER = ["fire", "tp", "heal", "chain", "meteor"]

DOWNLOADS = {
    1: dict(name="Kettenblitz", ver="v1.3", size=250.0, unlock="chain"),
    2: dict(name="Meteor", ver="v2.0", size=800.0, unlock="meteor"),
    3: dict(name="Mage.NET Patch", ver="v1.0.1", size=1500.0, unlock="patch"),
}

PROJ = {
    "fire": dict(name="Feuerball", speed=520, dmg=20, r=7, life=1.4, color=(255, 140, 40), aoe=42),
    "ice": dict(name="Eisball", speed=480, dmg=13, r=7, life=1.4, color=(140, 210, 255)),
    "chicken": dict(name="Huhn", speed=330, dmg=6, r=9, life=1.1, color=(250, 250, 250)),
    "chair": dict(name="Bürostuhl", speed=390, dmg=34, r=12, life=3.0, color=(70, 70, 85), bounces=3, pierce=True),
    "sun": dict(name="Mini-Sonne", speed=220, dmg=10, r=14, life=1.6, color=(255, 230, 90)),
    "tax": dict(name="Steuerformular", speed=300, dmg=3, r=10, life=2.0, color=(240, 240, 225), pierce=True),
}
CHAOS_FIRE = ["fire", "ice", "chicken", "chair", "sun", "tax"]

ENEMY_STATS = {
    "slime": dict(name="Paketverlust-Schleim", hp=34, speed=72, r=13, dmg=10, color=(90, 220, 120)),
    "goblin": dict(name="Lag-Goblin", hp=24, speed=0, r=11, dmg=9, color=(150, 200, 70)),
    "bat": dict(name="Funkloch-Fledermaus", hp=16, speed=130, r=10, dmg=6, color=(120, 85, 150), jam=True),
    "spambot": dict(name="Spam-Bot", hp=28, speed=95, r=12, dmg=7, color=(200, 200, 215)),
    "server": dict(name="Cloud-Server", hp=130, speed=0, r=20, dmg=0, color=(70, 80, 100), static=True),
    "firewall": dict(name="DER FIREWALL-WÄCHTER", hp=750, speed=70, r=40, dmg=16, color=(220, 90, 40), boss=True),
    "lich": dict(name="DER ROUTER-LICH", hp=950, speed=120, r=28, dmg=14, color=(120, 255, 200), boss=True),
    "dragon": dict(name="NULLPOINTERGON", hp=1900, speed=120, r=54, dmg=20, color=(160, 40, 60), boss=True),
}

THEMES = {
    "crystal": dict(name="Kristallraum", base=5, flicker=0.0, floor=(38, 44, 80), floor2=(46, 54, 94), wall=(96, 72, 170), dark=0),
    "tower": dict(name="Antennen-Halle", base=4, flicker=0.05, floor=(42, 46, 58), floor2=(50, 54, 68), wall=(84, 94, 116), dark=20),
    "hall": dict(name="Altes Gewölbe", base=3, flicker=0.15, floor=(50, 44, 40), floor2=(58, 50, 46), wall=(104, 86, 72), dark=40),
    "cellar": dict(name="Keller", base=2, flicker=0.35, floor=(38, 36, 34), floor2=(44, 42, 38), wall=(74, 64, 56), dark=65),
    "catacomb": dict(name="Katakomben", base=1, flicker=0.45, floor=(36, 32, 40), floor2=(42, 38, 46), wall=(68, 58, 76), dark=85),
    "cave": dict(name="Drachenhöhle", base=0, flicker=0.5, floor=(48, 26, 24), floor2=(56, 30, 28), wall=(100, 46, 38), dark=95),
    "corridor": dict(name="Gang (dicke Steinwände)", base=1, flicker=0.3, floor=(34, 34, 42), floor2=(38, 38, 46), wall=(62, 62, 74), dark=70),
    "firewall": dict(name="Serverraum der Firewall", base=3, flicker=0.1, floor=(44, 30, 30), floor2=(52, 34, 34), wall=(130, 60, 40), dark=30),
    "crypt": dict(name="Gruft des Router-Lichs", base=1, flicker=0.2, floor=(28, 40, 40), floor2=(32, 46, 46), wall=(60, 110, 100), dark=70),
    "lair": dict(name="Rechenzentrum des Drachen", base=1, flicker=0.3, floor=(46, 22, 30), floor2=(54, 26, 36), wall=(120, 40, 60), dark=75),
}
FLOOR_THEMES = {
    1: ["crystal", "crystal", "tower", "tower", "hall", "hall", "hall", "cellar", "cellar"],
    2: ["crystal", "tower", "hall", "hall", "cellar", "cellar", "cellar", "catacomb", "catacomb", "catacomb"],
    3: ["crystal", "tower", "hall", "catacomb", "catacomb", "cave", "cave", "cave", "cave"],
}
FLOOR_NAMES = {1: "Die oberen Gewölbe", 2: "Die Katakomben des Funklochs", 3: "Der Drachenhort"}
BOSS_THEME = {1: "firewall", 2: "crypt", 3: "lair"}
BOSS_KIND = {1: "firewall", 2: "lich", 3: "dragon"}
ENEMY_WEIGHTS = {
    1: [("slime", 4), ("goblin", 3), ("bat", 2), ("spambot", 2)],
    2: [("slime", 2), ("goblin", 3), ("bat", 3), ("spambot", 3)],
    3: [("slime", 2), ("goblin", 3), ("bat", 3), ("spambot", 3)],
}

HOTSPOT_STATS = {
    "router": dict(bonus=3, radius=210, name="Arkaner WLAN-Router"),
    "mast": dict(bonus=2, radius=290, name="Magischer Funkmast"),
    "dish": dict(bonus=2, radius=420, name="Verzauberte Satellitenschüssel"),
}

UPGRADES = {
    "hat": ("Empfangsverstärker-Hut", "+1 Signal überall", 2),
    "staff": ("Vergoldeter Routerstab", "+40% Hotspot-Reichweite, +25% Projektiltempo", 1),
    "premium": ("Premium-Abonnement", "-50% Latenz beim Zaubern", 1),
    "robe": ("Glasfaser-Robe", "+25 max. HP und volle Heilung", 3),
    "boots": ("Powerline-Pantoffeln", "+15% Laufgeschwindigkeit", 2),
    "booster": ("Bandbreiten-Booster", "Downloads laufen 3x schneller", 1),
    "cache": ("Offline-Cache-Amulett", "Alle 6s klappt ein Zauber auch offline", 1),
    "adblock": ("Adblocker-Brille", "70% weniger Werbung", 1),
    "mesh": ("Mesh-Mantel", "Funkloch-Fledermäuse stören nicht mehr", 1),
    "coffee": ("Koffein-Trank", "-20% Abklingzeiten", 2),
    "flat": ("Feuerball-Flatrate", "+30% Zauberschaden", 3),
}

ACHIEVEMENTS = [
    ("reboot", "Hast du es aus- und wieder eingeschaltet?", "Besiege einen Boss durch Neustart des Routers."),
    ("lag", "Lag Wizard", "Töte einen Gegner mit einem Zauber, der 30 Sekunden verspätet ankommt."),
    ("offline", "Offline Hero", "Besiege einen Boss komplett ohne Verbindung."),
    ("404", "404 Magic Not Found", "Wirke 100 fehlgeschlagene Zauber."),
    ("chicken", "Hühnerflüsterer", "Beschwöre 10 Hühner (insgesamt)."),
    ("tax", "Steuerberater", "Lähme 15 Gegner mit Steuerformularen."),
    ("adblock", "Menschlicher Adblocker", "Schließe 30 Werbefenster."),
    ("queue", "Bitte haben Sie etwas Geduld", "Habe 5 Zauber gleichzeitig in der Warteschlange."),
    ("download", "Download abgeschlossen", "Lade einen Zauber vollständig herunter."),
    ("win", "NullPointergon.exe gelöscht", "Besiege den Drachen-Administrator."),
]
ACH_BY_ID = {a[0]: a for a in ACHIEVEMENTS}

OFFLINE_ERRORS = [
    "ERROR 404: {SPELL} NICHT GEFUNDEN",
    "SERVER DERZEIT NICHT ERREICHBAR",
    "VERBINDUNG ZUM DRACHEN KONNTE NICHT HERGESTELLT WERDEN",
    "IHR ZAUBER WIRD IN DIE WARTESCHLANGE EINGEREIHT",
    "ERROR 503: MAGIE ÜBERLASTET",
    "TIMEOUT: DER HIMMEL ANTWORTET NICHT",
    "BITTE PRÜFEN SIE IHR ZAUBERKABEL",
    "ERROR 418: ICH BIN EINE TEEKANNE",
]

ADS = [
    ("SONDERANGEBOT!", ["Kostenloser Drachen-Skin!", "Nur heute: 0,00 Gold*", "*zzgl. deiner Seele"], "JETZT KAUFEN"),
    ("Kontaktanzeige", ["Singles in deiner Region", "suchen Zauberer!", "3 Hexen sind gerade online"], "JETZT CHATTEN"),
    ("WARNUNG!!!", ["Ihr Zauberstab ist mit", "3 Viren infiziert!", "Sofort handeln!"], "JETZT SCANNEN"),
    ("Mage.NET Premium", ["Jetzt 0% weniger Lag!", "Nur 999 Gold / Monat", "Mindestlaufzeit 400 Jahre"], "UPGRADE"),
    ("GLÜCKWUNSCH!", ["Sie sind der 1.000.000ste", "Besucher dieses Dungeons!", "Ihr Gewinn: ein Besen"], "ABHOLEN"),
    ("Ärzte hassen ihn!", ["Dieser Magier lernte Zaubern", "mit einem einfachen Trick.", "Nummer 7 wird Sie schockieren!"], "MEHR ERFAHREN"),
    ("Tränke-Discounter", ["Heiltränke bis zu -90%!", "Solange der Vorrat reicht.", "Nebenwirkungen: Hühner"], "ZUM SHOP"),
    ("Dungeon-Versicherung", ["Schon an Ihre", "Hinterbliebenen gedacht?", "Drachenschäden inklusive*"], "ANGEBOT"),
]

DRAGON_MSGS = [
    "Verbindung wird hergestellt...",
    "Bitte warten...",
    "Sie sind Position {pos} in der Warteschlange.",
    "Ihr Anruf ist uns wichtig.",
    "Der Drache befindet sich gerade in einem Meeting.",
    "Haben Sie es schon mit Aus- und Einschalten versucht?",
    "Ihre Sitzung läuft in 30 Sekunden ab.",
    "Bitte bewerten Sie diesen Bosskampf mit 5 Sternen.",
]

PASSWORDS = ["1234", "passwort", "hunter2", "drache123", "admin", "nullptr", "mage.net", "qwertz"]


# --------------------------------------------------------------------------- Hilfsfunktionen
def clamp(v, a, b):
    return a if v < a else b if v > b else v


def dist(ax, ay, bx, by):
    return math.hypot(ax - bx, ay - by)


def angle_diff(a, b):
    return (b - a + math.pi) % (2 * math.pi) - math.pi


def mix(c1, c2, t):
    return (int(c1[0] + (c2[0] - c1[0]) * t), int(c1[1] + (c2[1] - c1[1]) * t), int(c1[2] + (c2[2] - c1[2]) * t))


def weighted(choices):
    total = sum(w for _, w in choices)
    r = random.uniform(0, total)
    for item, w in choices:
        r -= w
        if r <= 0:
            return item
    return choices[-1][0]


_font_cache = {}


def font(size, bold=False):
    key = (size, bold)
    if key not in _font_cache:
        f = None
        for name in ("dejavusansmono", "consolas", "liberationmono", "couriernew", "menlo", "monospace"):
            try:
                path = pygame.font.match_font(name, bold=bold)
            except Exception:
                path = None
            if path:
                try:
                    f = pygame.font.Font(path, size)
                    break
                except Exception:
                    f = None
        if f is None:
            f = pygame.font.Font(None, int(size * 1.35))
        _font_cache[key] = f
    return _font_cache[key]


def text(surf, s, pos, size=16, color=WHITE, anchor="topleft", shadow=True, bold=False, alpha=255):
    f = font(size, bold)
    img = f.render(s, True, color)
    rect = img.get_rect(**{anchor: (int(pos[0]), int(pos[1]))})
    if alpha < 255:
        img.set_alpha(alpha)
    if shadow:
        sh = f.render(s, True, (0, 0, 0))
        if alpha < 255:
            sh.set_alpha(alpha)
        surf.blit(sh, (rect.x + 2, rect.y + 2))
    surf.blit(img, rect)
    return rect


_glow_cache = {}


def glow_surf(color, r):
    r = max(2, int(r) // 2 * 2)
    key = (color, r)
    s = _glow_cache.get(key)
    if s is None:
        s = pygame.Surface((r * 2, r * 2))
        s.fill((0, 0, 0))
        for i in range(r, 0, -2):
            k = (1 - i / r) ** 1.8
            pygame.draw.circle(s, (int(color[0] * k * 0.7), int(color[1] * k * 0.7), int(color[2] * k * 0.7)), (r, r), i)
        _glow_cache[key] = s
    return s


def draw_glow(surf, x, y, color, r):
    g = glow_surf(color, r)
    surf.blit(g, (int(x - g.get_width() / 2), int(y - g.get_height() / 2)), special_flags=pygame.BLEND_ADD)


def draw_bars(surf, x, y, bars, h=28, w=8, gap=3, active_color=None, blink=False):
    col = active_color or BAR_COLORS[bars]
    for i in range(5):
        bh = int(h * (i + 1) / 5)
        r = pygame.Rect(x + i * (w + gap), y + h - bh, w, bh)
        if i < bars:
            pygame.draw.rect(surf, col, r)
        else:
            pygame.draw.rect(surf, (45, 45, 55), r)
            pygame.draw.rect(surf, (70, 70, 85), r, 1)
    if bars == 0 and blink:
        cx, cy = x + 5 * (w + gap) // 2, y + h // 2
        pygame.draw.line(surf, RED, (cx - 12, cy - 12), (cx + 12, cy + 12), 4)
        pygame.draw.line(surf, RED, (cx + 12, cy - 12), (cx - 12, cy + 12), 4)


def fmt_speed(mbps):
    if mbps <= 0:
        return "0 KB/s"
    if mbps >= 1:
        return "%.1f MB/s" % mbps
    return "%d KB/s" % max(1, int(mbps * 1000))


def fmt_eta(sec):
    if sec == float("inf") or sec > 10 ** 7:
        return "unendlich"
    sec = int(sec)
    if sec >= 3600:
        return "%d Std. %d Min." % (sec // 3600, (sec % 3600) // 60)
    if sec >= 60:
        return "%d Min. %d s" % (sec // 60, sec % 60)
    return "%d s" % sec


# --------------------------------------------------------------------------- Sound (synthetisch)
class SoundBank:
    def __init__(self):
        self.ok = False
        self.sounds = {}
        self.muted = False
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(22050, -16, 1, 512)
            freq, size, ch = pygame.mixer.get_init()
            if size != -16:
                return
            self.rate, self.ch = freq, ch
            pygame.mixer.set_num_channels(24)
        except Exception:
            return
        try:
            R = self.raw
            self.add("fire", R(0.16, 520, 150, "saw", 0.22, noise=0.35))
            self.add("ice", R(0.18, 1400, 700, "sine", 0.22))
            self.add("hit", R(0.08, 220, 90, "square", 0.18, noise=0.6))
            self.add("explode", R(0.45, 120, 30, "saw", 0.35, noise=0.8))
            self.add("error", R(0.13, 330, 330, "square", 0.16) + R(0.2, 220, 220, "square", 0.16))
            self.add("heal", R(0.25, 500, 1100, "sine", 0.22) + R(0.15, 1100, 1300, "tri", 0.15))
            self.add("tp", R(0.2, 300, 1800, "sine", 0.22, vib=30))
            self.add("chicken", R(0.07, 900, 1400, "square", 0.12) + R(0.1, 1300, 800, "square", 0.12))
            self.add("pickup", R(0.08, 800, 800, "tri", 0.2) + R(0.12, 1200, 1600, "tri", 0.2))
            self.add("hurt", R(0.18, 240, 80, "square", 0.25, noise=0.2))
            self.add("modem", R(0.1, 1200, 1200, "sine", 0.15) + R(0.1, 2100, 2100, "sine", 0.15)
                     + R(0.3, 900, 2300, "square", 0.08, noise=0.75) + R(0.12, 1800, 1700, "sine", 0.12))
            self.add("ad", R(0.06, 1600, 1600, "sine", 0.18) + R(0.12, 2000, 2000, "sine", 0.18))
            self.add("click", R(0.04, 900, 600, "square", 0.12))
            self.add("zap", R(0.22, 1800, 300, "saw", 0.18, noise=0.5))
            self.add("upload", R(0.05, 1500, 1900, "tri", 0.07))
            self.add("boss", R(0.6, 90, 55, "saw", 0.3, vib=6))
            self.add("lock", R(0.1, 400, 400, "square", 0.16) + R(0.15, 200, 200, "square", 0.16))
            self.add("meteor", R(0.6, 900, 120, "saw", 0.2, noise=0.4))
            self.add("door", R(0.35, 70, 50, "square", 0.25, noise=0.3))
            self.ok = True
        except Exception:
            self.ok = False

    def raw(self, dur, f0, f1=None, wave="square", vol=0.3, noise=0.0, vib=0.0):
        rate = self.rate
        n = int(rate * dur)
        f1 = f0 if f1 is None else f1
        out = []
        ph = 0.0
        att = rate * 0.004 + 1
        for i in range(n):
            t = i / n
            f = f0 + (f1 - f0) * t
            if vib:
                f *= 1 + 0.06 * math.sin(i / rate * 2 * math.pi * vib)
            ph += f / rate
            p = ph % 1.0
            if wave == "square":
                v = 1.0 if p < 0.5 else -1.0
            elif wave == "saw":
                v = 2 * p - 1
            elif wave == "tri":
                v = 4 * abs(p - 0.5) - 1
            else:
                v = math.sin(2 * math.pi * ph)
            if noise:
                v = v * (1 - noise) + random.uniform(-1, 1) * noise
            env = min(1.0, i / att) * (1 - t) ** 1.3
            out.append(v * env * vol)
        return out

    def add(self, name, samples):
        buf = array.array("h")
        for s in samples:
            v = int(clamp(s, -1, 1) * 32000)
            for _ in range(self.ch):
                buf.append(v)
        self.sounds[name] = pygame.mixer.Sound(buffer=buf.tobytes())

    def play(self, name, vol=0.6):
        if self.ok and not self.muted and name in self.sounds:
            s = self.sounds[name]
            s.set_volume(vol)
            s.play()


# --------------------------------------------------------------------------- Gamepad
try:
    from pygame._sdl2 import controller as sdl_controller
except Exception:  # ältere pygame-Versionen
    sdl_controller = None

PAD_DEAD = 0.22
PAD_KEYS = {"fire": "RT", "tp": "LT", "heal": "X", "chain": "Y", "meteor": "B"}
PAD_DEVICE_EVENTS = {getattr(pygame, n) for n in ("JOYDEVICEADDED", "JOYDEVICEREMOVED",
                                                  "CONTROLLERDEVICEADDED", "CONTROLLERDEVICEREMOVED")
                     if hasattr(pygame, n)}


def _deadzone(x, y, dead=PAD_DEAD):
    m = math.hypot(x, y)
    if m < dead:
        return 0.0, 0.0
    k = min(1.0, (m - dead) / (1 - dead)) / m
    return x * k, y * k


class Gamepads:
    """Liest alle angeschlossenen Gamepads per Polling aus (Xbox-/PlayStation-/Switch-Layout).
    Bevorzugt die SDL-GameController-API (einheitliche Belegung), sonst Joystick-Fallback."""

    def __init__(self):
        self.devs = []
        self.held = set()
        self.prev = set()
        self.move = (0.0, 0.0)
        self.aim = (0.0, 0.0)
        self.active = False  # gab es diesen Frame irgendeine Pad-Eingabe?
        self.ctrl_ok = False
        try:
            pygame.joystick.init()
        except Exception:
            pass
        if sdl_controller is not None:
            try:
                sdl_controller.init()
                self.ctrl_ok = True
            except Exception:
                self.ctrl_ok = False
        self.scan()

    def scan(self):
        self.devs = []
        try:
            n = pygame.joystick.get_count()
        except Exception:
            n = 0
        for i in range(n):
            try:
                if self.ctrl_ok and sdl_controller.is_controller(i):
                    c = sdl_controller.Controller(i)
                    name = c.name if isinstance(getattr(c, "name", None), str) else "Gamepad"
                    self.devs.append(("ctrl", c, name))
                else:
                    j = pygame.joystick.Joystick(i)
                    j.init()
                    self.devs.append(("joy", j, j.get_name()))
            except Exception:
                pass

    @property
    def connected(self):
        return bool(self.devs)

    @property
    def name(self):
        return self.devs[0][2] if self.devs else ""

    def _read_ctrl(self, c, held):
        def ax(n):
            v = c.get_axis(getattr(pygame, "CONTROLLER_AXIS_" + n))
            return clamp(v / 32767.0, -1.0, 1.0)

        def bt(n):
            return bool(c.get_button(getattr(pygame, "CONTROLLER_BUTTON_" + n)))

        for n, key in (("A", "a"), ("B", "b"), ("X", "x"), ("Y", "y"), ("BACK", "back"), ("START", "start"),
                       ("LEFTSHOULDER", "lb"), ("RIGHTSHOULDER", "rb"), ("DPAD_UP", "up"),
                       ("DPAD_DOWN", "down"), ("DPAD_LEFT", "left"), ("DPAD_RIGHT", "right")):
            if bt(n):
                held.add(key)
        if ax("TRIGGERLEFT") > 0.5:
            held.add("lt")
        if ax("TRIGGERRIGHT") > 0.5:
            held.add("rt")
        return (ax("LEFTX"), ax("LEFTY")), (ax("RIGHTX"), ax("RIGHTY"))

    def _read_joy(self, j, held):
        names = ["a", "b", "x", "y", "lb", "rb", "back", "start"]
        for i in range(min(len(names), j.get_numbuttons())):
            if j.get_button(i):
                held.add(names[i])
        if j.get_numhats() > 0:
            hx, hy = j.get_hat(0)
            if hx < 0:
                held.add("left")
            if hx > 0:
                held.add("right")
            if hy > 0:
                held.add("up")
            if hy < 0:
                held.add("down")
        na = j.get_numaxes()
        lx = j.get_axis(0) if na > 0 else 0.0
        ly = j.get_axis(1) if na > 1 else 0.0
        rx = ry = 0.0
        if na >= 6:
            if sys.platform.startswith("win"):
                rx, ry, lt, rt = j.get_axis(2), j.get_axis(3), j.get_axis(4), j.get_axis(5)
            else:
                rx, ry, lt, rt = j.get_axis(3), j.get_axis(4), j.get_axis(2), j.get_axis(5)
            if (lt + 1) / 2 > 0.6:
                held.add("lt")
            if (rt + 1) / 2 > 0.6:
                held.add("rt")
        elif na >= 4:
            rx, ry = j.get_axis(2), j.get_axis(3)
        return (lx, ly), (rx, ry)

    def poll(self):
        self.prev = self.held
        held = set()
        best_m, best_a = (0.0, 0.0), (0.0, 0.0)
        for kind, d, _ in self.devs:
            try:
                m, a = self._read_ctrl(d, held) if kind == "ctrl" else self._read_joy(d, held)
            except Exception:
                continue
            m, a = _deadzone(*m), _deadzone(*a, dead=0.3)
            if math.hypot(*m) > math.hypot(*best_m):
                best_m = m
            if math.hypot(*a) > math.hypot(*best_a):
                best_a = a
        mx, my = best_m
        # Stick auch als Richtungstasten (für Menüs)
        if mx < -0.6:
            held.add("left")
        if mx > 0.6:
            held.add("right")
        if my < -0.6:
            held.add("up")
        if my > 0.6:
            held.add("down")
        self.move, self.aim, self.held = best_m, best_a, held
        self.active = bool(held) or best_m != (0.0, 0.0) or best_a != (0.0, 0.0)

    def pressed(self, b):
        return b in self.held and b not in self.prev

    def down(self, b):
        return b in self.held

    def rumble(self, low, high, ms):
        for _, d, _ in self.devs:
            try:
                d.rumble(low, high, ms)
            except Exception:
                pass


# --------------------------------------------------------------------------- Speicherstand / Achievements
class Save:
    def __init__(self):
        self.data = {"unlocked": [], "counters": {}, "best_floor": 0, "wins": 0}
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as fh:
                d = json.load(fh)
                self.data.update(d)
        except Exception:
            pass

    def write(self):
        try:
            with open(SAVE_FILE, "w", encoding="utf-8") as fh:
                json.dump(self.data, fh, indent=2)
        except Exception:
            pass

    def has(self, aid):
        return aid in self.data["unlocked"]

    def count(self, key, n=1):
        c = self.data["counters"]
        c[key] = c.get(key, 0) + n
        return c[key]


# --------------------------------------------------------------------------- Dungeon
class Room:
    def __init__(self, rid, cell, rect, theme, kind):
        self.id = rid
        self.cell = cell
        self.rect = rect  # in Tiles
        self.theme = theme
        self.kind = kind
        self.visited = False
        self.spawned = False
        self.cleared = kind != "normal"
        self.plan = []
        self.px = pygame.Rect(rect.x * TILE, rect.y * TILE, rect.w * TILE, rect.h * TILE)

    @property
    def center(self):
        return self.px.centerx, self.px.centery


class Hotspot:
    def __init__(self, kind, x, y, active, room):
        st = HOTSPOT_STATS[kind]
        self.kind = kind
        self.name = st["name"]
        self.bonus = st["bonus"]
        self.radius = st["radius"]
        self.x, self.y = x, y
        self.active = active
        self.room = room
        self.reboot_t = 0.0
        self.boost_t = 0.0
        self.cool = 0.0
        self.locked = False
        self.t = random.random() * 10

    def power(self):
        if not self.active or self.reboot_t > 0:
            return 0
        return self.bonus + (3 if self.boost_t > 0 else 0)


class Chest:
    def __init__(self, x, y, room):
        self.x, self.y, self.room = x, y, room
        self.opened = False


class Dungeon:
    GW, GH, CW, CH = 4, 3, 28, 20

    def __init__(self, floor):
        self.floor = floor
        self.tw, self.th = self.GW * self.CW, self.GH * self.CH
        self.grid = [[0] * self.tw for _ in range(self.th)]
        self.roomat = [[-1] * self.tw for _ in range(self.th)]
        self.rooms = []
        self.hotspots = []
        self.mushrooms = []
        self.chests = []
        self.barrier = set()
        self.barrier_on = False
        self.edges = []
        self.generate()
        self.surface = None

    # ---- Generierung
    def carve(self, x0, y0, x1, y1):
        for y in range(max(1, min(y0, y1)), min(self.th - 1, max(y0, y1) + 1)):
            for x in range(max(1, min(x0, x1)), min(self.tw - 1, max(x0, x1) + 1)):
                self.grid[y][x] = 1

    def generate(self):
        GW, GH, CW, CH = self.GW, self.GH, self.CW, self.CH
        n = {1: 7, 2: 8, 3: 9}.get(self.floor, 8)
        start = (0, random.randrange(GH))
        picked = [start]
        pset = {start}
        edges = []
        while len(picked) < n:
            c = random.choice(picked)
            dx, dy = random.choice(((1, 0), (-1, 0), (0, 1), (0, -1)))
            nb = (c[0] + dx, c[1] + dy)
            if 0 <= nb[0] < GW and 0 <= nb[1] < GH and nb not in pset:
                pset.add(nb)
                picked.append(nb)
                edges.append((c, nb))
        adj = {c: [] for c in picked}
        for a, b in edges:
            adj[a].append(b)
            adj[b].append(a)
        dists = {start: 0}
        q = [start]
        while q:
            c = q.pop(0)
            for nb in adj[c]:
                if nb not in dists:
                    dists[nb] = dists[c] + 1
                    q.append(nb)
        boss = max(picked, key=lambda c: (dists[c], random.random()))
        # Zusatzverbindungen (nicht zum Bossraum)
        for c in picked:
            for d in ((1, 0), (0, 1)):
                nb = (c[0] + d[0], c[1] + d[1])
                if nb in pset and boss not in (c, nb) and (c, nb) not in edges and (nb, c) not in edges and random.random() < 0.25:
                    edges.append((c, nb))
        cell_room = {}
        for c in picked:
            kind = "start" if c == start else "boss" if c == boss else "normal"
            if kind == "boss":
                w, h = CW - 4, CH - 4
                theme = BOSS_THEME[self.floor]
            else:
                w, h = random.randint(12, CW - 6), random.randint(9, CH - 6)
                theme = "crystal" if kind == "start" else random.choice(FLOOR_THEMES[self.floor])
            x = c[0] * CW + random.randint(2, CW - w - 2)
            y = c[1] * CH + random.randint(2, CH - h - 2)
            room = Room(len(self.rooms), c, pygame.Rect(x, y, w, h), theme, kind)
            self.rooms.append(room)
            cell_room[c] = room
            for ty in range(y, y + h):
                for tx in range(x, x + w):
                    self.grid[ty][tx] = 1
                    self.roomat[ty][tx] = room.id
        self.start_room = cell_room[start]
        self.boss_room = cell_room[boss]
        for a, b in edges:
            ra, rb = cell_room[a], cell_room[b]
            self.edges.append((ra.id, rb.id))
            if a[1] == b[1]:  # horizontal
                if ra.rect.x > rb.rect.x:
                    ra, rb = rb, ra
                lo, hi = max(ra.rect.y, rb.rect.y) + 1, min(ra.rect.bottom, rb.rect.bottom) - 2
                if lo <= hi:
                    yy = random.randint(lo, hi)
                    self.carve(ra.rect.right - 1, yy - 1, rb.rect.x, yy + 1)
                else:
                    y1, x2 = ra.rect.centery, rb.rect.centerx
                    self.carve(ra.rect.right - 1, y1 - 1, x2 + 1, y1 + 1)
                    self.carve(x2 - 1, y1 - 1, x2 + 1, rb.rect.centery)
            else:
                if ra.rect.y > rb.rect.y:
                    ra, rb = rb, ra
                lo, hi = max(ra.rect.x, rb.rect.x) + 1, min(ra.rect.right, rb.rect.right) - 2
                if lo <= hi:
                    xx = random.randint(lo, hi)
                    self.carve(xx - 1, ra.rect.bottom - 1, xx + 1, rb.rect.y)
                else:
                    x1, y2 = ra.rect.centerx, rb.rect.centery
                    self.carve(x1 - 1, ra.rect.bottom - 1, x1 + 1, y2 + 1)
                    self.carve(x1 - 1, y2 - 1, rb.rect.centerx, y2 + 1)
        # Barriere um den Bossraum
        br = self.boss_room.rect
        for tx in range(br.x - 1, br.right + 1):
            for ty in (br.y - 1, br.bottom):
                if self.grid[ty][tx] == 1:
                    self.barrier.add((tx, ty))
        for ty in range(br.y - 1, br.bottom + 1):
            for tx in (br.x - 1, br.right):
                if self.grid[ty][tx] == 1:
                    self.barrier.add((tx, ty))
        self.populate()

    def rand_pos(self, room, margin=2):
        r = room.rect
        tx = random.randint(r.x + margin, r.right - 1 - margin)
        ty = random.randint(r.y + margin, r.bottom - 1 - margin)
        return tx * TILE + TILE / 2, ty * TILE + TILE / 2

    def populate(self):
        f = self.floor
        for room in self.rooms:
            th = room.theme
            if room.kind == "start":
                cx, cy = room.center
                self.hotspots.append(Hotspot("mast", cx + 90, cy - 40, True, room))
                continue
            if room.kind == "boss":
                r = room.px
                if f == 1:
                    self.hotspots.append(Hotspot("router", r.centerx, r.bottom - 3 * TILE, False, room))
                elif f == 2:
                    for (fx, fy) in ((0.12, 0.15), (0.88, 0.15), (0.12, 0.85), (0.88, 0.85)):
                        self.hotspots.append(Hotspot("router", r.x + r.w * fx, r.y + r.h * fy, True, room))
                else:
                    self.hotspots.append(Hotspot("router", r.centerx, r.bottom - 3 * TILE, True, room))
                continue
            # normale Räume
            if th == "tower":
                x, y = self.rand_pos(room, 3)
                self.hotspots.append(Hotspot("mast", x, y, True, room))
            elif th != "crystal":
                chance = {"hall": 0.5, "cellar": 0.65, "catacomb": 0.8, "cave": 0.95}.get(th, 0.5)
                if random.random() < chance:
                    x, y = self.rand_pos(room, 3)
                    self.hotspots.append(Hotspot("dish" if random.random() < 0.3 else "router", x, y, False, room))
            nm = {"cellar": (2, 4), "catacomb": (2, 4), "cave": (1, 3)}.get(th, (0, 1))
            for _ in range(random.randint(*nm)):
                self.mushrooms.append(list(self.rand_pos(room, 1)))
            if random.random() < 0.4:
                x, y = self.rand_pos(room, 2)
                self.chests.append(Chest(x, y, room))
            count = 3 + f + random.randint(0, 2) + (1 if th in ("catacomb", "cave") else 0)
            room.plan = [weighted(ENEMY_WEIGHTS[f]) for _ in range(count)]
        if not self.mushrooms:
            r = random.choice(self.rooms)
            self.mushrooms.append(list(self.rand_pos(r, 1)))

    # ---- Abfragen
    def solid(self, tx, ty):
        if tx < 0 or ty < 0 or tx >= self.tw or ty >= self.th:
            return True
        if self.grid[ty][tx] == 0:
            return True
        return self.barrier_on and (tx, ty) in self.barrier

    def solid_px(self, x, y):
        return self.solid(int(x // TILE), int(y // TILE))

    def room_at(self, x, y):
        tx, ty = int(x // TILE), int(y // TILE)
        if 0 <= tx < self.tw and 0 <= ty < self.th:
            rid = self.roomat[ty][tx]
            if rid >= 0:
                return self.rooms[rid]
        return None

    def circle_hits(self, x, y, r):
        x0, x1 = int((x - r) // TILE), int((x + r) // TILE)
        y0, y1 = int((y - r) // TILE), int((y + r) // TILE)
        for ty in range(y0, y1 + 1):
            for tx in range(x0, x1 + 1):
                if self.solid(tx, ty):
                    cx = clamp(x, tx * TILE, tx * TILE + TILE)
                    cy = clamp(y, ty * TILE, ty * TILE + TILE)
                    if (x - cx) ** 2 + (y - cy) ** 2 < r * r:
                        return True
        return False

    def move_circle(self, x, y, dx, dy, r):
        steps = int(max(abs(dx), abs(dy)) / max(2.0, r * 0.7)) + 1
        hx = hy = False
        for _ in range(steps):
            nx = x + dx / steps
            if not self.circle_hits(nx, y, r):
                x = nx
            else:
                hx = True
            ny = y + dy / steps
            if not self.circle_hits(x, ny, r):
                y = ny
            else:
                hy = True
        return x, y, hx, hy

    def theme_at_tile(self, tx, ty):
        rid = self.roomat[ty][tx]
        return self.rooms[rid].theme if rid >= 0 else "corridor"

    # ---- Grafik backen
    def bake(self):
        surf = pygame.Surface((self.tw * TILE, self.th * TILE)).convert()
        surf.fill((8, 7, 12))
        rnd = random.Random(self.floor * 1337 + len(self.rooms))
        for ty in range(self.th):
            for tx in range(self.tw):
                r = pygame.Rect(tx * TILE, ty * TILE, TILE, TILE)
                if self.grid[ty][tx] == 1:
                    th = THEMES[self.theme_at_tile(tx, ty)]
                    c = th["floor"] if (tx + ty) % 2 == 0 else th["floor2"]
                    n = rnd.randint(-4, 4)
                    c = (clamp(c[0] + n, 0, 255), clamp(c[1] + n, 0, 255), clamp(c[2] + n, 0, 255))
                    pygame.draw.rect(surf, c, r)
                    if rnd.random() < 0.12:
                        x0, y0 = r.x + rnd.randint(4, 28), r.y + rnd.randint(4, 28)
                        pygame.draw.line(surf, mix(c, (0, 0, 0), 0.35), (x0, y0), (x0 + rnd.randint(-8, 8), y0 + rnd.randint(-8, 8)), 1)
                    if rnd.random() < 0.08:
                        pygame.draw.circle(surf, mix(c, (255, 255, 255), 0.08), (r.x + rnd.randint(5, 27), r.y + rnd.randint(5, 27)), 2)
                else:
                    nbt = None
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            nx, ny = tx + dx, ty + dy
                            if 0 <= nx < self.tw and 0 <= ny < self.th and self.grid[ny][nx] == 1:
                                nbt = self.theme_at_tile(nx, ny)
                    if nbt:
                        wc = THEMES[nbt]["wall"]
                        front = ty + 1 < self.th and self.grid[ty + 1][tx] == 1
                        base = wc if front else mix(wc, (0, 0, 0), 0.45)
                        pygame.draw.rect(surf, base, r)
                        off = 0 if ty % 2 == 0 else TILE // 2
                        lc = mix(base, (0, 0, 0), 0.3)
                        pygame.draw.line(surf, lc, (r.x, r.y + TILE // 2), (r.right, r.y + TILE // 2))
                        pygame.draw.line(surf, lc, (r.x + off, r.y), (r.x + off, r.y + TILE // 2))
                        pygame.draw.line(surf, lc, (r.x + (off + TILE // 2) % TILE, r.y + TILE // 2), (r.x + (off + TILE // 2) % TILE, r.bottom))
                        if front:
                            pygame.draw.line(surf, mix(wc, (255, 255, 255), 0.25), (r.x, r.y), (r.right, r.y), 2)
                            pygame.draw.rect(surf, mix(wc, (0, 0, 0), 0.55), (r.x, r.bottom - 5, TILE, 5))
        # Deko
        for room in self.rooms:
            th = room.theme
            for _ in range(rnd.randint(4, 8)):
                x = rnd.randint(room.px.x + 10, room.px.right - 10)
                y = rnd.randint(room.px.y + 10, room.px.bottom - 10)
                if th in ("crystal",):
                    col = rnd.choice([(120, 220, 255), (190, 120, 255), (255, 140, 240)])
                    for k in range(rnd.randint(2, 4)):
                        bx = x + rnd.randint(-8, 8)
                        hh = rnd.randint(10, 22)
                        pygame.draw.polygon(surf, col, [(bx - 4, y), (bx, y - hh), (bx + 4, y)])
                        pygame.draw.polygon(surf, mix(col, (255, 255, 255), 0.5), [(bx - 1, y), (bx, y - hh + 3), (bx + 1, y)])
                elif th in ("catacomb", "crypt"):
                    pygame.draw.circle(surf, (200, 195, 180), (x, y), 5)
                    pygame.draw.rect(surf, (200, 195, 180), (x - 3, y + 3, 6, 4))
                    pygame.draw.circle(surf, (30, 30, 30), (x - 2, y - 1), 1)
                    pygame.draw.circle(surf, (30, 30, 30), (x + 2, y - 1), 1)
                    pygame.draw.line(surf, (190, 185, 170), (x + 8, y + 6), (x + 20, y + 2), 2)
                elif th in ("tower", "firewall", "lair"):
                    col = rnd.choice([(40, 120, 220), (220, 200, 40), (60, 200, 90), (220, 60, 60)])
                    pts = [(x, y)]
                    for _k in range(5):
                        pts.append((pts[-1][0] + rnd.randint(10, 30), pts[-1][1] + rnd.randint(-12, 12)))
                    pygame.draw.lines(surf, col, False, pts, 2)
                elif th in ("cave",):
                    pygame.draw.line(surf, (200, 70, 30), (x, y), (x + rnd.randint(-20, 20), y + rnd.randint(-20, 20)), 2)
                elif th == "cellar":
                    pygame.draw.ellipse(surf, (30, 40, 50), (x, y, rnd.randint(20, 40), rnd.randint(10, 18)))
                else:
                    pygame.draw.circle(surf, mix(THEMES[th]["floor"], (0, 0, 0), 0.4), (x, y), rnd.randint(2, 5))
            if th in ("firewall", "lair"):
                # Server-Racks als Wanddeko
                for k in range(room.rect.w // 3):
                    rx = room.px.x + 16 + k * 3 * TILE
                    pygame.draw.rect(surf, (30, 32, 40), (rx, room.px.y + 4, 40, 22))
                    for j in range(4):
                        pygame.draw.circle(surf, rnd.choice([GREEN, RED, CYAN]), (rx + 6 + j * 9, room.px.y + 15), 2)
        self.surface = surf


# --------------------------------------------------------------------------- Entitäten
class Player:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.r = 11
        self.maxhp = 100
        self.hp = 100
        self.speed = 205
        self.iframes = 0.0
        self.cd = {k: 0.0 for k in SPELLS}
        self.unlocked = ["fire", "tp", "heal"]
        self.up = {k: 0 for k in UPGRADES}
        self.walk = 0.0
        self.cache_cd = 0.0
        self.patch = False


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "maxlife", "color", "size", "glow", "drag")

    def __init__(self, x, y, vx, vy, life, color, size=3, glow=False, drag=0.9):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life = self.maxlife = life
        self.color, self.size, self.glow, self.drag = color, size, glow, drag


class Chicken:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.r = 8
        self.life = 8.0
        self.hp = 25.0
        self.dir = random.uniform(0, math.tau)
        self.turn = 0.0
        self.t = random.random()


class Projectile:
    def __init__(self, x, y, ang, kind, owner, speed, dmg, r, life, color, **kw):
        self.x, self.y = x, y
        self.vx, self.vy = math.cos(ang) * speed, math.sin(ang) * speed
        self.kind, self.owner = kind, owner
        self.dmg, self.r, self.life, self.color = dmg, r, life, color
        self.pierce = kw.get("pierce", False)
        self.bounces = kw.get("bounces", 0)
        self.stutter = kw.get("stutter", 0.0)
        self.src = kw.get("src", {})
        self.homing = kw.get("homing", 0.0)
        self.hit = set()
        self.acc = 0.0
        self.st_timer = 0.0
        self.age = 0.0
        self.dead = False
        self.spin = random.uniform(0, math.tau)
        self.jx = self.jy = 0.0


class Enemy:
    def __init__(self, g, kind, x, y, room=None):
        st = ENEMY_STATS[kind]
        mult = 1.0 if st.get("boss") else 1 + 0.35 * (g.floor - 1)
        self.kind = kind
        self.name = st["name"]
        self.x, self.y = x, y
        self.r = st["r"]
        self.maxhp = self.hp = st["hp"] * mult
        self.speed = st["speed"]
        self.dmg = st["dmg"] * (1 + 0.2 * (g.floor - 1))
        self.color = st["color"]
        self.room = room
        self.boss = bool(st.get("boss"))
        self.static = st.get("static", False)
        self.jam = st.get("jam", False)
        self.flash = 0.0
        self.stun = 0.0
        self.slow = 0.0
        self.t = random.random() * 10
        self.cool = random.uniform(0.8, 2.2)
        self.spawn_t = 0.6
        self.dead = False
        self.kx = self.ky = 0.0
        self.online_damage = 0.0
        self.trail = []
        self.hop = 0.0

    # gemeinsame Timer; True = diesen Frame nichts weiter tun
    def tick(self, g, dt):
        if self.spawn_t > 0:
            self.spawn_t -= dt
            return True
        self.t += dt
        self.flash = max(0.0, self.flash - dt)
        self.slow = max(0.0, self.slow - dt)
        if abs(self.kx) + abs(self.ky) > 1 and not self.static:
            self.x, self.y, _, _ = g.dungeon.move_circle(self.x, self.y, self.kx * dt, self.ky * dt, self.r)
            self.kx *= 0.85
            self.ky *= 0.85
        if self.stun > 0:
            self.stun -= dt
            return True
        return False

    def spd(self):
        return self.speed * (0.4 if self.slow > 0 else 1.0)

    def contact(self, g):
        p = g.player
        if self.dmg > 0 and dist(self.x, self.y, p.x, p.y) < self.r + p.r:
            g.hurt_player(self.dmg, self.name)
        for c in g.chickens:
            if dist(self.x, self.y, c.x, c.y) < self.r + c.r:
                c.hp -= 40 * g.dt

    def update(self, g, dt):
        if self.tick(g, dt):
            return
        tx, ty = g.enemy_target(self)
        d = dist(self.x, self.y, tx, ty)
        ang = math.atan2(ty - self.y, tx - self.x)
        k = self.kind
        if k == "slime":
            s = self.spd() * (0.7 + 0.5 * abs(math.sin(self.t * 4)))
            self.x, self.y, _, _ = g.dungeon.move_circle(self.x, self.y, math.cos(ang) * s * dt, math.sin(ang) * s * dt, self.r)
        elif k == "goblin":
            self.hop -= dt * (0.5 if self.slow > 0 else 1)
            if self.hop <= 0:
                self.hop = random.uniform(0.25, 0.5)
                self.trail.append([self.x, self.y, 0.3])
                step = min(d, random.uniform(35, 60))
                a = ang + random.uniform(-0.4, 0.4)
                self.x, self.y, _, _ = g.dungeon.move_circle(self.x, self.y, math.cos(a) * step, math.sin(a) * step, self.r)
        elif k == "bat":
            a = ang + math.sin(self.t * 3.0) * 1.1
            s = self.spd()
            self.x, self.y, hx, hy = g.dungeon.move_circle(self.x, self.y, math.cos(a) * s * dt, math.sin(a) * s * dt, self.r)
        elif k == "spambot":
            want = 220
            s = self.spd()
            if d > want + 40:
                mv = ang
            elif d < want - 40:
                mv = ang + math.pi
            else:
                mv = ang + math.pi / 2 * (1 if math.sin(self.t * 0.7) > 0 else -1)
            self.x, self.y, _, _ = g.dungeon.move_circle(self.x, self.y, math.cos(mv) * s * dt, math.sin(mv) * s * dt, self.r)
            self.cool -= dt
            if self.cool <= 0 and d < 520:
                self.cool = random.uniform(1.5, 2.3)
                g.enemy_shoot(self.x, self.y, ang, 240, "envelope", 8 * (1 + 0.2 * (g.floor - 1)))
        elif k == "server":
            self.cool -= dt
            if self.cool <= 0 and d < 600:
                self.cool = random.uniform(2.4, 3.6)
                g.enemy_shoot(self.x, self.y, ang, 170, "packet", 8)
        for tr in self.trail:
            tr[2] -= dt
        self.trail = [t for t in self.trail if t[2] > 0]
        self.contact(g)

    def draw(self, g, surf, cx, cy):
        x, y = self.x - cx, self.y - cy
        if self.spawn_t > 0:
            k = 1 - self.spawn_t / 0.6
            pygame.draw.circle(surf, MAGENTA, (int(x), int(y)), int(self.r * 2 * (1 - k)) + 2, 2)
            draw_glow(surf, x, y, MAGENTA, 30)
            return
        col = (255, 255, 255) if self.flash > 0 else self.color
        if self.slow > 0 and self.flash <= 0:
            col = mix(col, (140, 200, 255), 0.6)
        pygame.draw.ellipse(surf, (0, 0, 0), (x - self.r, y + self.r - 4, self.r * 2, 8))
        k = self.kind
        if k == "slime":
            wob = math.sin(self.t * 8) * 2
            rect = pygame.Rect(0, 0, self.r * 2 + wob, self.r * 2 - wob)
            rect.center = (x, y)
            pygame.draw.ellipse(surf, col, rect)
            pygame.draw.ellipse(surf, mix(col, (255, 255, 255), 0.4), (rect.x + 4, rect.y + 3, 8, 5))
            pygame.draw.circle(surf, BLACK, (int(x - 4), int(y - 1)), 2)
            pygame.draw.circle(surf, BLACK, (int(x + 4), int(y - 1)), 2)
            text(surf, "?", (x, y + 4), 11, (20, 60, 30), "center", shadow=False, bold=True)
        elif k == "goblin":
            for tr in self.trail:
                gs = pygame.Surface((24, 24), pygame.SRCALPHA)
                pygame.draw.circle(gs, (150, 200, 70, int(200 * tr[2])), (12, 12), 10)
                surf.blit(gs, (tr[0] - cx - 12, tr[1] - cy - 12))
            pygame.draw.polygon(surf, col, [(x - 10, y - 4), (x - 18, y - 12), (x - 6, y - 8)])
            pygame.draw.polygon(surf, col, [(x + 10, y - 4), (x + 18, y - 12), (x + 6, y - 8)])
            pygame.draw.circle(surf, col, (int(x), int(y)), self.r)
            pygame.draw.circle(surf, YELLOW, (int(x - 4), int(y - 2)), 2)
            pygame.draw.circle(surf, YELLOW, (int(x + 4), int(y - 2)), 2)
            if int(self.t * 2) % 3 == 0:
                text(surf, "LAG", (x, y - 22), 10, RED, "center", bold=True)
        elif k == "bat":
            fl = math.sin(self.t * 18) * 8
            pygame.draw.polygon(surf, col, [(x, y), (x - 20, y - 6 + fl), (x - 10, y + 4)])
            pygame.draw.polygon(surf, col, [(x, y), (x + 20, y - 6 + fl), (x + 10, y + 4)])
            pygame.draw.circle(surf, mix(col, (0, 0, 0), 0.3), (int(x), int(y)), 7)
            pygame.draw.circle(surf, RED, (int(x - 2), int(y - 1)), 1)
            pygame.draw.circle(surf, RED, (int(x + 2), int(y - 1)), 1)
            # durchgestrichenes WLAN
            for i in range(2):
                pygame.draw.arc(surf, (255, 90, 90), (x - 6 - i * 4, y - 26 - i * 4, 12 + i * 8, 12 + i * 8), 0.6, 2.5, 1)
            pygame.draw.line(surf, RED, (x - 9, y - 28), (x + 9, y - 16), 2)
        elif k == "spambot":
            body = pygame.Rect(0, 0, 22, 24)
            body.center = (x, y)
            pygame.draw.rect(surf, col, body, border_radius=4)
            env = pygame.Rect(body.x + 4, body.y + 9, 14, 9)
            pygame.draw.rect(surf, (250, 250, 250), env)
            pygame.draw.lines(surf, (120, 120, 140), False, [env.topleft, env.center, env.topright], 1)
            pygame.draw.line(surf, GREY, (x, body.y), (x, body.y - 8), 2)
            pygame.draw.circle(surf, RED if int(self.t * 4) % 2 else YELLOW, (int(x), int(body.y - 9)), 3)
            pygame.draw.rect(surf, CYAN, (body.x + 5, body.y + 3, 4, 3))
            pygame.draw.rect(surf, CYAN, (body.x + 13, body.y + 3, 4, 3))
        elif k == "server":
            body = pygame.Rect(0, 0, 34, 46)
            body.center = (x, y)
            pygame.draw.rect(surf, col, body, border_radius=3)
            pygame.draw.rect(surf, (120, 130, 160), body, 2, border_radius=3)
            for j in range(5):
                yy = body.y + 6 + j * 8
                pygame.draw.line(surf, (40, 45, 60), (body.x + 4, yy + 4), (body.right - 4, yy + 4))
                led = GREEN if (int(self.t * 6) + j) % 3 else CYAN
                pygame.draw.circle(surf, led, (body.right - 7, yy), 2)
            draw_glow(surf, x, y - 30, CYAN, 26)
            text(surf, "CLOUD", (x, body.y - 12), 10, CYAN, "center", bold=True)
        if self.stun > 0:
            text(surf, "zZz" if int(self.t * 3) % 2 else "ZzZ", (x, y - self.r - 14), 11, YELLOW, "center")
        if self.hp < self.maxhp and not self.boss:
            w = self.r * 2 + 6
            pygame.draw.rect(surf, (40, 0, 0), (x - w / 2, y - self.r - 8, w, 4))
            pygame.draw.rect(surf, RED, (x - w / 2, y - self.r - 8, w * self.hp / self.maxhp, 4))


# --------------------------------------------------------------------------- Bosse
class FirewallBoss(Enemy):
    def __init__(self, g, x, y, room):
        super().__init__(g, "firewall", x, y, room)
        self.shield = 0.0
        self.atk_t = 2.0
        self.tele_t = 0.0
        self.next = None
        self.charge_t = 0.0
        self.cvx = self.cvy = 0.0
        self.spawn_t = 1.0

    def blocks(self, g, proj):
        a = math.atan2(proj.y - self.y, proj.x - self.x)
        return abs(angle_diff(self.shield, a)) < math.radians(62)

    def update(self, g, dt):
        if self.tick(g, dt):
            return
        p = g.player
        target = math.atan2(p.y - self.y, p.x - self.x)
        phase2 = self.hp < self.maxhp * 0.5
        turn = (1.25 if not phase2 else 1.8) * dt
        self.shield += clamp(angle_diff(self.shield, target), -turn, turn)
        d = dist(self.x, self.y, p.x, p.y)
        if self.charge_t > 0:
            self.charge_t -= dt
            self.x, self.y, hx, hy = g.dungeon.move_circle(self.x, self.y, self.cvx * dt, self.cvy * dt, self.r)
            g.particle_burst(self.x, self.y, 2, ORANGE, 80, 0.4)
            if hx or hy:
                self.charge_t = 0
                g.shake = 12
                g.sfx.play("explode", 0.4)
        else:
            mv = target if d > 230 else target + math.pi if d < 150 else target + math.pi / 2
            s = self.spd() * (1.3 if phase2 else 1)
            self.x, self.y, _, _ = g.dungeon.move_circle(self.x, self.y, math.cos(mv) * s * dt, math.sin(mv) * s * dt, self.r)
        if self.tele_t > 0:
            self.tele_t -= dt
            if self.tele_t <= 0:
                self.attack(g, self.next)
        else:
            self.atk_t -= dt
            if self.atk_t <= 0:
                self.atk_t = random.uniform(1.5, 2.4) if phase2 else random.uniform(2.3, 3.2)
                opts = ["ring", "ring", "lock", "throttle", "charge"] + (["ring2", "charge"] if phase2 else [])
                self.next = random.choice(opts)
                self.tele_t = 0.8
                g.boss_say({
                    "ring": "Firewall-Regel #1: ALLES BLOCKIEREN.",
                    "ring2": "PAKETFLUT! DDoS-Schutz aktiviert.",
                    "lock": "Port wird gesperrt...",
                    "throttle": "Drossle Verbindung auf 56k...",
                    "charge": "Eindringling erkannt. Wird entfernt.",
                }[self.next])
        self.contact(g)

    def attack(self, g, what):
        p = g.player
        if what in ("ring", "ring2"):
            n = 14
            for rep in range(2 if what == "ring2" else 1):
                off = random.uniform(0, math.tau)
                for i in range(n):
                    g.enemy_shoot(self.x, self.y, off + i * math.tau / n, 190 + rep * 60, "brick", 12)
            g.sfx.play("fire", 0.5)
        elif what == "lock":
            spell = random.choice(p.unlocked)
            g.port_lock[spell] = 6.0
            g.toast("PORT %d (%s) GESPERRT!" % (random.choice([22, 80, 443, 1337, 8080]), SPELLS[spell]["name"].upper()), RED, big=True)
            g.sfx.play("lock")
        elif what == "throttle":
            g.throttle_t = 5.0
            g.toast("VERBINDUNG GEDROSSELT AUF 56 kbit/s", ORANGE, big=True)
            g.sfx.play("lock")
        elif what == "charge":
            a = math.atan2(p.y - self.y, p.x - self.x)
            self.cvx, self.cvy = math.cos(a) * 560, math.sin(a) * 560
            self.charge_t = 0.75
            self.shield = a

    def draw(self, g, surf, cx, cy):
        x, y = self.x - cx, self.y - cy
        if self.spawn_t > 0:
            draw_glow(surf, x, y, ORANGE, int(80 * (1 - self.spawn_t)) + 10)
            return
        pygame.draw.ellipse(surf, BLACK, (x - 40, y + 30, 80, 16))
        col = WHITE if self.flash > 0 else self.color
        body = pygame.Rect(0, 0, 70, 70)
        body.center = (x, y)
        pygame.draw.rect(surf, col, body, border_radius=6)
        for j in range(5):
            yy = body.y + j * 14
            pygame.draw.line(surf, (120, 40, 20), (body.x, yy), (body.right, yy), 2)
            off = 0 if j % 2 == 0 else 12
            for xx in range(body.x + off, body.right, 24):
                pygame.draw.line(surf, (120, 40, 20), (xx, yy), (xx, yy + 14), 2)
        eye = YELLOW if self.tele_t <= 0 else RED
        pygame.draw.rect(surf, eye, (x - 18, y - 12, 12, 6))
        pygame.draw.rect(surf, eye, (x + 6, y - 12, 12, 6))
        draw_glow(surf, x, y - 10, ORANGE, 50)
        # Schild-Bogen
        for i in range(9):
            a = self.shield - math.radians(60) + i * math.radians(120) / 8
            bx, by = x + math.cos(a) * 62, y + math.sin(a) * 62
            fl = 4 * math.sin(self.t * 12 + i)
            pygame.draw.circle(surf, (255, 120 + int(fl * 10), 40), (int(bx), int(by)), 9)
            draw_glow(surf, bx, by, (255, 120, 30), 26)
        text(surf, "FIREWALL", (x + math.cos(self.shield) * 84, y + math.sin(self.shield) * 84), 11, YELLOW, "center", bold=True)


class LichBoss(Enemy):
    def __init__(self, g, x, y, room):
        super().__init__(g, "lich", x, y, room)
        self.atk_t = 2.5
        self.tp_t = 8.0
        self.tele_t = 0.0
        self.next = None
        self.spawn_t = 1.0
        self.shield_msg = 0.0

    def routers(self, g):
        return [h for h in g.dungeon.hotspots if h.room is self.room and h.kind == "router"]

    def shielded(self, g):
        return sum(1 for h in self.routers(g) if not h.active) >= 2

    def update(self, g, dt):
        if self.tick(g, dt):
            return
        cx, cy = self.room.center
        tx = cx + math.cos(self.t * 0.6) * 230
        ty = cy + math.sin(self.t * 1.2) * 120
        a = math.atan2(ty - self.y, tx - self.x)
        s = self.spd()
        self.x, self.y, _, _ = g.dungeon.move_circle(self.x, self.y, math.cos(a) * s * dt, math.sin(a) * s * dt, self.r)
        self.tp_t -= dt
        if self.tp_t <= 0:
            self.tp_t = random.uniform(6, 9)
            g.particle_burst(self.x, self.y, 30, (120, 255, 200), 200, 0.6)
            for _ in range(20):
                nx, ny = g.dungeon.rand_pos(self.room, 3)
                if dist(nx, ny, g.player.x, g.player.y) > 250:
                    self.x, self.y = nx, ny
                    break
            g.sfx.play("tp", 0.4)
        phase2 = self.hp < self.maxhp * 0.5
        if self.tele_t > 0:
            self.tele_t -= dt
            if self.tele_t <= 0:
                self.attack(g, self.next)
        else:
            self.atk_t -= dt
            if self.atk_t <= 0:
                self.atk_t = random.uniform(1.6, 2.6) if phase2 else random.uniform(2.4, 3.4)
                active = sum(1 for h in self.routers(g) if h.active)
                opts = ["skulls", "skulls", "summon", "disconnect"]
                if active >= 2:
                    opts += ["password", "password"]
                self.next = random.choice(opts)
                self.tele_t = 0.8
                g.boss_say({
                    "skulls": "Sende Totenkopf-Pakete...",
                    "summon": "Neue Geräte verbinden sich mit dem Netzwerk...",
                    "disconnect": "Sie werden vom Netzwerk getrennt.",
                    "password": "Ändere WLAN-Passwort...",
                }[self.next])
        self.contact(g)

    def attack(self, g, what):
        p = g.player
        if what == "skulls":
            base = math.atan2(p.y - self.y, p.x - self.x)
            n = 7 if self.hp < self.maxhp * 0.5 else 5
            for i in range(n):
                g.enemy_shoot(self.x, self.y, base + (i - n // 2) * 0.28, 210, "skull", 11, homing=1.4)
            g.sfx.play("zap", 0.4)
        elif what == "summon":
            alive = sum(1 for e in g.enemies if not e.boss)
            for _ in range(3 if alive < 6 else 1):
                x, y = g.dungeon.rand_pos(self.room, 3)
                g.spawn_enemy(random.choice(["bat", "bat", "spambot"]), x, y, self.room)
        elif what == "disconnect":
            g.disconnect_t = 3.5
            g.toast("SIE WURDEN VOM NETZWERK GETRENNT.", RED, big=True)
            g.sfx.play("error")
        elif what == "password":
            act = [h for h in self.routers(g) if h.active]
            random.shuffle(act)
            for h in act[:2]:
                h.active = False
                h.locked = True
                g.float_text(h.x, h.y - 40, "PASSWORT GEÄNDERT!", RED)
            g.toast("WLAN-PASSWORT GEÄNDERT! Router neu verbinden [E]", ORANGE, big=True)
            g.sfx.play("lock")

    def draw(self, g, surf, cx, cy):
        x, y = self.x - cx, self.y - cy + math.sin(self.t * 3) * 5
        if self.spawn_t > 0:
            draw_glow(surf, x, y, (120, 255, 200), int(80 * (1 - self.spawn_t)) + 10)
            return
        pygame.draw.ellipse(surf, BLACK, (x - 26, y + 34, 52, 12))
        col = WHITE if self.flash > 0 else (60, 50, 90)
        pygame.draw.polygon(surf, col, [(x - 28, y + 36), (x, y - 20), (x + 28, y + 36)])
        pygame.draw.circle(surf, (230, 225, 210), (int(x), int(y - 22)), 15)
        pygame.draw.circle(surf, (120, 255, 200), (int(x - 5), int(y - 24)), 3)
        pygame.draw.circle(surf, (120, 255, 200), (int(x + 5), int(y - 24)), 3)
        pygame.draw.rect(surf, (40, 40, 40), (x - 6, y - 15, 12, 4))
        # Router-Krone
        pygame.draw.rect(surf, (30, 30, 40), (x - 16, y - 44, 32, 8), border_radius=2)
        for i in (-12, 0, 12):
            pygame.draw.line(surf, (30, 30, 40), (x + i, y - 44), (x + i * 1.4, y - 60), 2)
            pygame.draw.circle(surf, GREEN if int(self.t * 5 + i) % 2 else CYAN, (int(x + i * 1.4), int(y - 60)), 3)
        draw_glow(surf, x, y - 22, (120, 255, 200), 50)
        # Stab
        pygame.draw.line(surf, (150, 120, 80), (x + 26, y + 30), (x + 34, y - 40), 3)
        pygame.draw.circle(surf, (120, 255, 200), (int(x + 34), int(y - 42)), 6)
        if self.shielded(g):
            r = 46 + math.sin(self.t * 6) * 3
            pygame.draw.circle(surf, (120, 255, 200), (int(x), int(y)), int(r), 3)
            text(surf, "VPN-SCHILD", (x, y - 80), 11, (120, 255, 200), "center", bold=True)


class DragonBoss(Enemy):
    def __init__(self, g, x, y, room):
        super().__init__(g, "dragon", x, y, room)
        self.atk_t = 3.0
        self.tele_t = 0.0
        self.next = None
        self.breath_t = 0.0
        self.msg_t = 4.0
        self.pos = 847
        self.phase2 = False
        self.spawn_t = 1.5
        self.servers = []

    def spawn_servers(self, g, n):
        r = self.room.px
        spots = [(0.15, 0.3), (0.85, 0.3), (0.2, 0.8), (0.8, 0.8)]
        random.shuffle(spots)
        for fx, fy in spots[:n]:
            e = g.spawn_enemy("server", r.x + r.w * fx, r.y + r.h * fy, self.room)
            self.servers.append(e)

    def shielded(self):
        return any(not s.dead for s in self.servers)

    def update(self, g, dt):
        if self.tick(g, dt):
            return
        p = g.player
        r = self.room.px
        tx = clamp(p.x, r.x + 120, r.right - 120)
        ty = r.y + 130 + math.sin(self.t * 0.8) * 50
        self.x += clamp(tx - self.x, -self.spd() * dt, self.spd() * dt)
        self.y += clamp(ty - self.y, -self.spd() * dt, self.spd() * dt)
        if not self.phase2 and self.hp < self.maxhp * 0.5:
            self.phase2 = True
            self.spawn_servers(g, 2)
            g.toast("BACKUP WIEDERHERGESTELLT – 2 Server wieder online!", RED, big=True)
            g.boss_say("Wiederherstellung aus der Cloud abgeschlossen.")
        self.msg_t -= dt
        if self.msg_t <= 0:
            self.msg_t = random.uniform(5, 8)
            self.pos = max(1, self.pos + random.choice([-1, -3, -120, 356]))
            g.boss_say(random.choice(DRAGON_MSGS).format(pos=self.pos))
        if self.breath_t > 0:
            self.breath_t -= dt
            base = math.atan2(p.y - self.y, p.x - self.x)
            if random.random() < dt * 40:
                g.enemy_shoot(self.x, self.y + 20, base + random.uniform(-0.35, 0.35), random.uniform(260, 340), "breath", 7)
        elif self.tele_t > 0:
            self.tele_t -= dt
            if self.tele_t <= 0:
                self.attack(g, self.next)
        else:
            self.atk_t -= dt
            if self.atk_t <= 0:
                self.atk_t = random.uniform(1.6, 2.6) if self.phase2 else random.uniform(2.3, 3.3)
                self.next = random.choice(["breath", "breath", "barrage", "summon", "wait"])
                self.tele_t = 0.9
                g.boss_say({
                    "breath": "Starte Feueratem.exe ...",
                    "barrage": "Sende Feuer-Pakete (UDP, ohne Garantie)...",
                    "summon": "Skaliere Infrastruktur horizontal...",
                    "wait": "Bitte warten...",
                }[self.next])
        self.contact(g)

    def attack(self, g, what):
        p = g.player
        if what == "breath":
            self.breath_t = 1.4
            g.sfx.play("meteor", 0.4)
        elif what == "barrage":
            base = math.atan2(p.y - self.y, p.x - self.x)
            for i in range(-3, 4):
                g.enemy_shoot(self.x, self.y + 20, base + i * 0.18, 260, "dfire", 14)
            g.sfx.play("fire", 0.6)
        elif what == "summon":
            for _ in range(3):
                x, y = g.dungeon.rand_pos(self.room, 3)
                g.spawn_enemy("goblin", x, y, self.room)
        elif what == "wait":
            g.wait_t = 2.2
            g.toast("BITTE WARTEN... Zaubern vorübergehend nicht möglich", YELLOW, big=True)

    def draw(self, g, surf, cx, cy):
        x, y = self.x - cx, self.y - cy
        if self.spawn_t > 0:
            draw_glow(surf, x, y, RED, int(120 * (1 - self.spawn_t / 1.5)) + 10)
            return
        col = WHITE if self.flash > 0 else self.color
        dk = mix(col, (0, 0, 0), 0.4)
        wing = math.sin(self.t * 4) * 18
        pygame.draw.ellipse(surf, BLACK, (x - 60, y + 50, 120, 24))
        for sgn in (-1, 1):
            pts = [(x + sgn * 20, y - 10), (x + sgn * 120, y - 60 + wing), (x + sgn * 100, y + 10 + wing * 0.5),
                   (x + sgn * 70, y + 0), (x + sgn * 50, y + 25)]
            pygame.draw.polygon(surf, dk, pts)
            pygame.draw.lines(surf, col, False, pts[:3], 3)
        pygame.draw.ellipse(surf, col, (x - 38, y - 30, 76, 80))
        pygame.draw.ellipse(surf, mix(col, (255, 200, 120), 0.4), (x - 20, y - 6, 40, 50))
        # Kopf + Headset
        hx, hy = x, y - 44
        pygame.draw.circle(surf, col, (int(hx), int(hy)), 26)
        pygame.draw.polygon(surf, col, [(hx - 14, hy + 10), (hx, hy + 34), (hx + 14, hy + 10)])
        for sgn in (-1, 1):
            pygame.draw.polygon(surf, dk, [(hx + sgn * 12, hy - 18), (hx + sgn * 26, hy - 46), (hx + sgn * 22, hy - 14)])
        eye = YELLOW if self.tele_t <= 0 and self.breath_t <= 0 else (255, 255, 255)
        pygame.draw.circle(surf, eye, (int(hx - 10), int(hy - 4)), 5)
        pygame.draw.circle(surf, eye, (int(hx + 10), int(hy - 4)), 5)
        pygame.draw.circle(surf, BLACK, (int(hx - 10), int(hy - 4)), 2)
        pygame.draw.circle(surf, BLACK, (int(hx + 10), int(hy - 4)), 2)
        pygame.draw.arc(surf, (30, 30, 30), (hx - 30, hy - 32, 60, 50), 0.2, math.pi - 0.2, 4)
        pygame.draw.rect(surf, (30, 30, 30), (hx - 34, hy - 10, 8, 14))
        pygame.draw.line(surf, (30, 30, 30), (hx - 30, hy + 4), (hx - 12, hy + 20), 3)
        pygame.draw.circle(surf, RED, (int(hx - 12), int(hy + 20)), 3)
        draw_glow(surf, hx, hy, RED, 70)
        if self.breath_t > 0:
            draw_glow(surf, hx, hy + 30, ORANGE, 60)
        if self.shielded():
            r = 90 + math.sin(self.t * 5) * 4
            pygame.draw.circle(surf, CYAN, (int(x), int(y)), int(r), 2)
            pygame.draw.circle(surf, CYAN, (int(x), int(y)), int(r) + 6, 1)
            text(surf, "CLOUD-SCHILD", (x, y - 110), 12, CYAN, "center", bold=True)


# --------------------------------------------------------------------------- Werbung
class Ad:
    def __init__(self, g):
        self.w, self.h = 360, 200
        self.x = random.randint(60, W - self.w - 60)
        self.y = random.randint(80, H - self.h - 130)
        self.title, self.lines, self.button = random.choice(ADS)
        self.delay = random.choice([0, 0, 1.5])
        self.life = random.uniform(3.5, 5.0)  # schließt sich danach von selbst
        self.t = 0.0
        self.color = random.choice([(255, 60, 160), (60, 160, 255), (255, 170, 0), (120, 220, 60)])

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.w, self.h)

    @property
    def close_rect(self):
        return pygame.Rect(self.x + self.w - 30, self.y + 4, 24, 22)

    @property
    def buy_rect(self):
        return pygame.Rect(self.x + self.w // 2 - 95, self.y + self.h - 48, 190, 36)

    def draw(self, surf, pad_hint=False):
        sh = 0
        if self.t < 0.25:
            sh = int(math.sin(self.t * 80) * 6)
        r = self.rect.move(sh, 0)
        pygame.draw.rect(surf, (0, 0, 0), r.move(6, 6))
        pygame.draw.rect(surf, (245, 245, 250), r)
        pygame.draw.rect(surf, self.color, (r.x, r.y, r.w, 30))
        pygame.draw.rect(surf, (20, 20, 30), r, 2)
        text(surf, self.title, (r.x + 10, r.y + 6), 15, WHITE, bold=True)
        for i, ln in enumerate(self.lines):
            text(surf, ln, (r.centerx, r.y + 50 + i * 24), 16, (30, 30, 40), "midtop", shadow=False, bold=(i == 0))
        b = self.buy_rect.move(sh, 0)
        blink = int(self.t * 4) % 2
        pygame.draw.rect(surf, (255, 60, 60) if blink else (255, 120, 40), b, border_radius=6)
        text(surf, self.button, b.center, 15, WHITE, "center", bold=True)
        c = self.close_rect.move(sh, 0)
        if self.t >= self.delay:
            pygame.draw.rect(surf, (200, 40, 40), c, border_radius=3)
            pygame.draw.line(surf, WHITE, (c.x + 6, c.y + 5), (c.right - 6, c.bottom - 5), 3)
            pygame.draw.line(surf, WHITE, (c.right - 6, c.y + 5), (c.x + 6, c.bottom - 5), 3)
        else:
            text(surf, "%d" % (int(self.delay - self.t) + 1), c.center, 14, (60, 60, 60), "center", shadow=False)
            text(surf, "Werbung schließbar in...", (r.right - 36, r.y + 36), 11, (90, 90, 90), "topright", shadow=False)
        rem = clamp(1 - (self.t - self.delay) / self.life, 0, 1) if self.t >= self.delay else 1.0
        pygame.draw.rect(surf, (210, 210, 220), (r.x + 2, r.bottom - 6, r.w - 4, 4))
        pygame.draw.rect(surf, self.color, (r.x + 2, r.bottom - 6, int((r.w - 4) * rem), 4))
        if pad_hint and self.t >= self.delay:
            text(surf, "[SELECT] schließen", (r.right - 36, r.y + 7), 12, WHITE, "topright", shadow=False, bold=True)


# --------------------------------------------------------------------------- Das Spiel
class Game:
    def __init__(self):
        try:
            pygame.mixer.pre_init(22050, -16, 1, 512)
        except Exception:
            pass
        pygame.init()
        flags = pygame.SCALED | pygame.RESIZABLE
        try:
            self.screen = pygame.display.set_mode((W, H), flags)
        except Exception:
            self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption(CAPTION)
        self.clock = pygame.time.Clock()
        self.sfx = SoundBank()
        self.music = None
        self.music_off = False
        if MusicPlayer is not None:
            try:
                self.music = MusicPlayer()
            except Exception:
                self.music = None
        self.pads = Gamepads()
        self.input_mode = "mouse"
        self.aim_dir = (1.0, 0.0)
        self.card_sel = 0
        self.save = Save()
        self.state = "title"
        self.time = 0.0
        self.dt = 0.0
        self.title_t = 0.0
        self.victory_t = 0.0
        self.boss_started = False
        self.boss = None
        self.intro_t = 0.0
        self.ach_popups = []
        self.make_vignettes()
        self.rain = [[random.randint(0, W), random.randint(-H, H), random.uniform(60, 220), random.choice("01")] for _ in range(90)]
        self.dungeon = None

    # ---------------------------------------------------------------- Setup
    def make_vignettes(self):
        self.vignettes = []
        for maxa in (40, 90, 140, 185, 215):
            s = pygame.Surface((W // 2, H // 2), pygame.SRCALPHA)
            s.fill((0, 0, 0, maxa))
            R = int(math.hypot(W / 4, H / 4))
            for i in range(R, 0, -3):
                k = clamp((i / R - 0.25) / 0.75, 0, 1)
                pygame.draw.circle(s, (0, 0, 0, int(maxa * k ** 1.5)), (W // 4, H // 4), i)
            self.vignettes.append(pygame.transform.smoothscale(s, (W, H)))

    def new_run(self):
        self.floor = 1
        self.player = None
        self.stats = dict(casts=0, failed=0, chickens=0, ads=0, kills=0, chaos=0, time=0.0)
        self.dl_queue = []
        self.start_floor(1, fresh=True)
        self.state = "play"

    def start_floor(self, floor, fresh=False):
        self.floor = floor
        self.dungeon = Dungeon(floor)
        self.dungeon.bake()
        sx, sy = self.dungeon.start_room.center
        if fresh or self.player is None:
            self.player = Player(sx, sy)
        else:
            self.player.x, self.player.y = sx, sy
        self.dungeon.start_room.visited = True
        self.enemies = []
        self.projectiles = []
        self.particles = []
        self.chickens = []
        self.floats = []
        self.toasts = []
        self.ads = []
        self.pending = []
        self.meteors = []
        self.rings = []
        self.bolts = []
        self.pickups = []
        self.portal = None
        self.boss = None
        self.boss_started = False
        self.banner = (FLOOR_NAMES[floor], "ETAGE %d" % floor, 2.2)
        self.cam_x, self.cam_y = sx - W / 2, sy - H / 2
        self.signal = 5.0
        self.bars = 5
        self.prev_bars = 5
        self.flicker_t = 0.0
        self.flicker_amt = 0
        self.throttle_t = 0.0
        self.disconnect_t = 0.0
        self.wait_t = 0.0
        self.port_lock = {}
        self.premium_t = 0.0
        self.shake = 0.0
        self.cur_room = self.dungeon.start_room
        self.hold = 0.0
        self.hold_target = None
        self.hold_block = False
        self.mouse_block = False
        self.victory_t = 0.0
        self.offline_since = None
        self.dark = 0.0
        dl = DOWNLOADS.get(floor)
        if dl and dl["unlock"] not in self.player.unlocked and not any(d["unlock"] == dl["unlock"] for d in self.dl_queue):
            self.dl_queue.append(dict(dl, done=0.0))
        self.save.data["best_floor"] = max(self.save.data.get("best_floor", 0), floor)
        self.save.write()
        if floor == 1:
            self.toast("Willkommen bei Mage.NET! Hier im Kristallraum ist der Empfang noch super.", CYAN)

    # ---------------------------------------------------------------- Feedback-Helfer
    FEED_MAX = 3

    def toast(self, s, color=WHITE, big=False, life=None, kind="info"):
        """Eine HUD-Zeile oben. Max. 3 Zeilen, kurze Dauer, Duplikate werden nur aufgefrischt.
        Fehler- und Boss-Meldungen belegen jeweils höchstens eine Zeile (neue ersetzt alte)."""
        if life is None:
            life = 2.6 if big else 2.0
        if len(s) > 78:
            s = s[:76] + "…"
        for t in self.toasts:
            if t["text"] == s or (kind in ("error", "boss") and t["kind"] == kind):
                if t["text"] != s:
                    t["text"] = s
                    t["t0"] = 0.0
                t.update(color=color, big=big, life=max(life, t["life"] - t["t"]), t=min(t["t"], 0.15))
                return
        self.toasts.append(dict(text=s, color=color, big=big, t=0.0, life=life, kind=kind, t0=0.0))
        while len(self.toasts) > self.FEED_MAX:
            # zuerst unwichtige (nicht "big") Meldungen verdrängen
            idx = next((i for i, t in enumerate(self.toasts) if not t["big"]), 0)
            self.toasts.pop(idx)

    def error(self, s):
        self.toast(s, (255, 120, 120), life=1.5, kind="error")

    def boss_say(self, s):
        self.toast(s, GREEN, life=2.6, kind="boss")

    def float_text(self, x, y, s, color=WHITE, size=14):
        if len(s) > 28:  # lange Sätze gehören in den HUD-Feed, nicht ins Spielfeld
            self.toast(s, color)
            return
        if len(self.floats) > 40:
            self.floats.pop(0)
        self.floats.append([x, y, s, color, 0.9, size])

    def particle_burst(self, x, y, n, color, speed=150, life=0.5, size=3, glow=False):
        if len(self.particles) > 900:
            return
        for _ in range(n):
            a = random.uniform(0, math.tau)
            s = random.uniform(0.2, 1) * speed
            self.particles.append(Particle(x, y, math.cos(a) * s, math.sin(a) * s, random.uniform(0.5, 1) * life, color, size, glow))

    def unlock(self, aid):
        if self.save.has(aid):
            return
        self.save.data["unlocked"].append(aid)
        self.save.write()
        self.ach_popups.append(dict(aid=aid, t=0.0))
        self.sfx.play("pickup", 0.7)

    # ---------------------------------------------------------------- Signal
    def compute_signal(self):
        p = self.player
        room = self.dungeon.room_at(p.x, p.y)
        th = THEMES[room.theme] if room else THEMES["corridor"]
        base = th["base"]
        if room is None and self.floor == 1:
            base = 2
        mult = 1.4 if p.up["staff"] else 1.0
        bonus = 0
        for h in self.dungeon.hotspots:
            pw = h.power()
            if pw and dist(p.x, p.y, h.x, h.y) < h.radius * mult:
                bonus += pw
        s = base + bonus + p.up["hat"]
        if not p.up["mesh"]:
            for e in self.enemies:
                if e.jam and e.spawn_t <= 0 and dist(e.x, e.y, p.x, p.y) < 230:
                    s -= 1
        if self.flicker_t > 0:
            s -= self.flicker_amt
        s = clamp(s, 0, 5)
        if self.throttle_t > 0:
            s = min(s, 1)
        if self.disconnect_t > 0:
            s = 0
        return s, th

    def update_signal(self, dt):
        target, th = self.compute_signal()
        self.flicker_t -= dt
        if self.flicker_t <= 0 and random.random() < th["flicker"] * dt * 0.9:
            self.flicker_t = random.uniform(0.4, 1.8)
            self.flicker_amt = random.randint(1, 3)
        rate = 4.0 if target < self.signal else 2.5
        if self.disconnect_t > 0:
            rate = 30
        self.signal += clamp(target - self.signal, -rate * dt, rate * dt)
        self.bars = int(round(self.signal))
        self.dark += (th["dark"] - self.dark) * min(1.0, dt * 3)
        if self.bars == 0 and self.prev_bars > 0:
            self.toast("Verbindung zur magischen Cloud verloren", RED)
            self.sfx.play("error", 0.4)
        if self.bars > 0 and self.prev_bars == 0:
            self.sfx.play("modem", 0.45)
            waiting = [pd for pd in self.pending if pd["fire_at"] is None]
            if waiting:
                self.toast("VERBINDUNG WIEDERHERGESTELLT – Warteschlange wird abgearbeitet (%d)" % len(waiting), GREEN, big=True)
                for i, pd in enumerate(waiting):
                    pd["fire_at"] = self.time + 0.3 + i * 0.22
            else:
                self.toast("Verbindung wiederhergestellt", GREEN)
        self.prev_bars = self.bars

    # ---------------------------------------------------------------- Zaubern
    def pad_mode(self):
        return self.input_mode == "pad"

    def aim_screen(self):
        if self.pad_mode() and self.dungeon is not None and getattr(self, "player", None) is not None:
            p = self.player
            x = p.x - self.cam_x + self.aim_dir[0] * 230
            y = p.y - self.cam_y + self.aim_dir[1] * 230
            return int(clamp(x, 8, W - 8)), int(clamp(y, 8, H - 8))
        return pygame.mouse.get_pos()

    def mouse_world(self, assist=False):
        mx, my = self.aim_screen()
        wx, wy = mx + self.cam_x, my + self.cam_y
        if assist and self.pad_mode():
            # leichte Zielhilfe für Gamepad: nächster Gegner im 20°-Kegel
            p = self.player
            aim = math.atan2(self.aim_dir[1], self.aim_dir[0])
            best, bd = None, 0.35
            for e in self.enemies:
                if e.dead or e.spawn_t > 0 or dist(e.x, e.y, p.x, p.y) > 560:
                    continue
                d = abs(angle_diff(aim, math.atan2(e.y - p.y, e.x - p.x)))
                if d < bd:
                    best, bd = e, d
            if best is not None:
                return best.x, best.y
        return wx, wy

    def dmg_mult(self):
        return (1.3 ** self.player.up["flat"]) * (1.3 if self.player.patch else 1.0)

    def try_cast(self, spell):
        p = self.player
        if spell not in p.unlocked:
            if p.cd.get(spell, 0) <= 0:
                dl = next((d for d in self.dl_queue if d["unlock"] == spell), None)
                if dl:
                    self.toast("%s ist noch nicht installiert – Download: %d%%" % (SPELLS[spell]["name"], int(100 * dl["done"] / dl["size"])), GREY)
                else:
                    self.toast("%s nicht verfügbar. Bitte Mage.NET Plus buchen." % SPELLS[spell]["name"], GREY)
                p.cd[spell] = 1.0
            return
        if p.cd[spell] > 0:
            return
        if self.port_lock.get(spell, 0) > 0:
            p.cd[spell] = 0.5
            self.error("PORT GESPERRT: %s BLOCKIERT DURCH FIREWALL" % SPELLS[spell]["name"].upper())
            self.sfx.play("lock", 0.4)
            return
        if self.wait_t > 0:
            p.cd[spell] = 0.4
            self.error("BITTE WARTEN...")
            return
        mx, my = self.mouse_world(assist=spell in ("fire", "chain", "meteor"))
        cd = SPELLS[spell]["cd"] * (0.8 ** p.up["coffee"])
        bars = self.bars
        if 0 < bars <= 3:
            cd *= random.uniform(0.5, 1.7)
        self.stats["casts"] += 1
        self.maybe_ad(bars)
        if bars == 0:
            if p.up["cache"] and p.cache_cd <= 0:
                p.cache_cd = 6.0
                p.cd[spell] = cd
                self.float_text(p.x, p.y - 30, "OFFLINE-CACHE!", CYAN)
                self.execute(spell, mx, my, self.time, False, 5)
                return
            p.cd[spell] = max(0.25, cd * 0.5)
            self.fail_spell(spell)
            if len(self.pending) < 12:
                self.pending.append(dict(spell=spell, tx=mx, ty=my, cast=self.time, fire_at=None, online=False))
                if sum(1 for pd in self.pending if pd["fire_at"] is None) >= 5:
                    self.unlock("queue")
            return
        p.cd[spell] = cd
        lo, hi = LATENCY[bars]
        delay = random.uniform(lo, hi) * (0.5 if p.up["premium"] else 1.0)
        if delay < 0.04:
            self.execute(spell, mx, my, self.time, True, bars)
        else:
            self.pending.append(dict(spell=spell, tx=mx, ty=my, cast=self.time, fire_at=self.time + delay, online=True, delay=delay))
            self.sfx.play("upload", 0.3)

    def fail_spell(self, spell):
        self.stats["failed"] += 1
        msg = random.choice(OFFLINE_ERRORS).replace("{SPELL}", SPELLS[spell]["name"].upper())
        self.error(msg)
        self.sfx.play("error", 0.35)
        if self.save.count("failed") >= 100:
            self.unlock("404")

    def update_pending(self):
        for pd in list(self.pending):
            if pd["fire_at"] is None or self.time < pd["fire_at"]:
                continue
            self.pending.remove(pd)
            if self.bars == 0:
                pd["fire_at"] = None
                self.pending.append(pd)
                self.float_text(self.player.x, self.player.y - 34, "Paket verloren", RED, 12)
                continue
            tx, ty = pd["tx"], pd["ty"]
            if not pd["online"]:
                tx, ty = self.mouse_world(assist=pd["spell"] != "tp")
            self.execute(pd["spell"], tx, ty, pd["cast"], pd["online"], self.bars)

    def execute(self, spell, tx, ty, cast_time, online, bars):
        p = self.player
        lag = self.time - cast_time
        src = dict(lag=lag, online=online, spell=True)
        chaos = bars <= 1 or (bars == 2 and random.random() < 0.2)
        if chaos:
            self.stats["chaos"] += 1
        if lag > 2.5:
            self.float_text(p.x, p.y - 44, "+%.1fs Lag" % lag, YELLOW, 12)
        ang = math.atan2(ty - p.y, tx - p.x)
        if spell == "fire":
            kind = random.choice(CHAOS_FIRE) if chaos else "fire"
            if kind != "fire":
                self.float_text(p.x, p.y - 30, "Feuerball -> %s?!" % PROJ[kind]["name"], MAGENTA, 15)
            self.spawn_player_proj(kind, ang, STUTTER[bars], src)
        elif spell == "tp":
            self.do_teleport(tx, ty, chaos)
        elif spell == "heal":
            self.do_heal(chaos)
        elif spell == "chain":
            self.do_chain(tx, ty, chaos, src)
        elif spell == "meteor":
            self.do_meteor(tx, ty, chaos, src)

    def spawn_player_proj(self, kind, ang, stutter, src):
        p = self.player
        st = PROJ[kind]
        spd = st["speed"] * (1.25 if p.up["staff"] else 1.0)
        pr = Projectile(p.x + math.cos(ang) * 16, p.y + math.sin(ang) * 16, ang, kind, "player", spd,
                        st["dmg"] * self.dmg_mult(), st["r"], st["life"], st["color"],
                        pierce=st.get("pierce", False), bounces=st.get("bounces", 0), stutter=stutter, src=src)
        self.projectiles.append(pr)
        self.sfx.play({"ice": "ice", "chicken": "chicken"}.get(kind, "fire"), 0.4)
        if kind == "chicken":
            self.stats["chickens"] += 1
            if self.save.count("chickens") >= 10:
                self.unlock("chicken")

    def find_tp_dest(self, tx, ty, maxd=300):
        p = self.player
        d = dist(p.x, p.y, tx, ty)
        ang = math.atan2(ty - p.y, tx - p.x)
        d = min(d, maxd)
        while d > 0:
            x, y = p.x + math.cos(ang) * d, p.y + math.sin(ang) * d
            ok = not self.dungeon.circle_hits(x, y, p.r)
            if ok and self.boss_started and self.boss and not self.boss.dead:
                ok = self.dungeon.boss_room.px.inflate(-24, -24).collidepoint(x, y)
            if ok:
                return x, y
            d -= 8
        return p.x, p.y

    def tp_fx(self, x, y):
        self.particle_burst(x, y, 24, PURPLE, 220, 0.5, 3, True)
        self.rings.append([x, y, 0.0, 50, 0.3, PURPLE])

    def do_teleport(self, tx, ty, chaos):
        p = self.player
        self.sfx.play("tp", 0.5)
        mode = random.choice(["self", "enemy", "both", "mushroom"]) if chaos else "self"
        cands = [e for e in self.enemies if not e.boss and not e.static and e.spawn_t <= 0]
        if mode in ("enemy", "both") and not cands:
            mode = "mushroom"
        if mode == "self":
            x, y = self.find_tp_dest(tx, ty)
            self.tp_fx(p.x, p.y)
            p.x, p.y = x, y
            self.tp_fx(x, y)
        elif mode == "enemy":
            e = min(cands, key=lambda e: dist(e.x, e.y, tx, ty))
            self.tp_fx(e.x, e.y)
            room = e.room or self.dungeon.room_at(e.x, e.y) or self.cur_room or self.dungeon.start_room
            for _ in range(20):
                nx, ny = self.dungeon.rand_pos(room, 2)
                if not self.dungeon.circle_hits(nx, ny, e.r):
                    e.x, e.y = nx, ny
                    break
            self.tp_fx(e.x, e.y)
            self.float_text(p.x, p.y - 30, "Teleport: falsches Ziel. Gegner verschoben.", MAGENTA)
        elif mode == "both":
            e = min(cands, key=lambda e: dist(e.x, e.y, p.x, p.y))
            self.tp_fx(p.x, p.y)
            self.tp_fx(e.x, e.y)
            p.x, p.y, e.x, e.y = e.x, e.y, p.x, p.y
            self.float_text(p.x, p.y - 30, "Positionstausch!", MAGENTA)
        else:
            m = random.choice(self.dungeon.mushrooms)
            x, y = self.find_tp_dest(tx, ty)
            self.tp_fx(m[0], m[1])
            m[0], m[1] = x, y
            self.tp_fx(x, y)
            self.toast("Ein zufälliger Pilz wurde erfolgreich teleportiert.", MAGENTA)

    def do_heal(self, chaos):
        p = self.player
        mode = random.choice(["enemies", "tiny", "mega", "chicken", "subscribe"]) if chaos else "normal"
        self.sfx.play("heal", 0.5)
        if mode in ("normal", "subscribe"):
            self.heal_player(35)
            if mode == "subscribe":
                self.toast("Heilung abonniert! Nur 4,99 Gold/Monat.", MAGENTA)
                if len(self.ads) < 6 and self.premium_t <= 0 and random.random() < 1 / 3:
                    self.ads.append(Ad(self))
        elif mode == "tiny":
            self.heal_player(1)
            self.float_text(p.x, p.y - 40, "Patch 0.0.1 installiert: +1 HP", MAGENTA)
        elif mode == "mega":
            self.heal_player(80)
            self.float_text(p.x, p.y - 40, "PREMIUM-HEILUNG (Testversion)", GREEN)
        elif mode == "enemies":
            n = 0
            for e in self.enemies:
                if dist(e.x, e.y, p.x, p.y) < 320:
                    e.hp = min(e.maxhp, e.hp + 30)
                    self.particle_burst(e.x, e.y, 10, GREEN, 80, 0.6)
                    n += 1
            self.toast("Heilung an falsche IP gesendet! (%d Gegner geheilt)" % n, MAGENTA)
        elif mode == "chicken":
            for _ in range(3):
                self.chickens.append(Chicken(p.x + random.uniform(-30, 30), p.y + random.uniform(-30, 30)))
            self.toast("Heilung -> Hühnersuppe. Hühner geliefert.", MAGENTA)
            self.stats["chickens"] += 3
            if self.save.count("chickens", 3) >= 10:
                self.unlock("chicken")

    def heal_player(self, n):
        p = self.player
        p.hp = min(p.maxhp, p.hp + n)
        self.float_text(p.x, p.y - 26, "+%d" % n, GREEN, 16)
        self.particle_burst(p.x, p.y, 18, GREEN, 120, 0.7, 3, True)

    def do_chain(self, tx, ty, chaos, src):
        p = self.player
        self.sfx.play("zap", 0.5)
        if chaos:
            n = 0
            for e in self.enemies:
                if dist(e.x, e.y, p.x, p.y) < 320 and not e.boss:
                    e.stun = max(e.stun, 2.5)
                    n += 1
                    self.float_text(e.x, e.y - 20, "Kettenbrief!", WHITE, 11)
            self.toast("Kettenblitz -> KETTENBRIEF. %d Gegner lesen ihn." % n, MAGENTA)
            return
        cand = [e for e in self.enemies if e.spawn_t <= 0 and dist(e.x, e.y, p.x, p.y) < 360]
        if not cand:
            a = math.atan2(ty - p.y, tx - p.x)
            self.add_bolt([(p.x, p.y), (p.x + math.cos(a) * 140, p.y + math.sin(a) * 140)])
            self.float_text(p.x, p.y - 30, "Kein Ziel. Blitz ins Leere.", GREY)
            return
        first = min(cand, key=lambda e: dist(e.x, e.y, tx, ty))
        chain = [first]
        while len(chain) < 4:
            last = chain[-1]
            nxt = [e for e in self.enemies if e not in chain and e.spawn_t <= 0 and dist(e.x, e.y, last.x, last.y) < 220]
            if not nxt:
                break
            chain.append(min(nxt, key=lambda e: dist(e.x, e.y, last.x, last.y)))
        pts = [(p.x, p.y)] + [(e.x, e.y) for e in chain]
        self.add_bolt(pts)
        for e in chain:
            self.damage_enemy(e, 24 * self.dmg_mult(), src)

    def add_bolt(self, pts):
        segs = []
        for i in range(len(pts) - 1):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            n = 7
            for k in range(n + 1):
                t = k / n
                j = 0 if k in (0, n) else random.uniform(-12, 12)
                segs.append((x0 + (x1 - x0) * t + j, y0 + (y1 - y0) * t + j))
        self.bolts.append([segs, 0.25])

    def do_meteor(self, tx, ty, chaos, src):
        p = self.player
        if chaos:
            tx, ty = p.x + random.uniform(-260, 260), p.y + random.uniform(-260, 260)
            self.toast("METEOR-STANDORT: UNBEKANNT", MAGENTA)
        else:
            d = dist(p.x, p.y, tx, ty)
            if d > 420:
                a = math.atan2(ty - p.y, tx - p.x)
                tx, ty = p.x + math.cos(a) * 420, p.y + math.sin(a) * 420
        self.meteors.append(dict(x=tx, y=ty, t=0.8, src=src, chaos=chaos))
        self.sfx.play("meteor", 0.4)

    def maybe_ad(self, bars):
        if self.premium_t > 0 or len(self.ads) >= 4:
            return
        chance = 0.01 + (0.01 if bars <= 2 else 0)  # Werbe-Häufigkeit
        if self.player.up["adblock"]:
            chance *= 0.3
        if random.random() < chance:
            self.ads.append(Ad(self))
            self.sfx.play("ad", 0.5)

    # ---------------------------------------------------------------- Kampf
    def enemy_target(self, e):
        best = None
        bd = 280
        for c in self.chickens:
            d = dist(e.x, e.y, c.x, c.y)
            if d < bd:
                bd, best = d, c
        if best:
            return best.x, best.y
        return self.player.x, self.player.y

    def enemy_shoot(self, x, y, ang, speed, kind, dmg, homing=0.0):
        col = {"envelope": WHITE, "brick": ORANGE, "skull": (200, 255, 220), "dfire": (255, 90, 40),
               "breath": (255, 160, 40), "packet": CYAN}[kind]
        r = {"envelope": 7, "brick": 8, "skull": 9, "dfire": 11, "breath": 7, "packet": 7}[kind]
        life = 0.9 if kind == "breath" else 3.5
        self.projectiles.append(Projectile(x, y, ang, kind, "enemy", speed, dmg, r, life, col, homing=homing))

    def spawn_enemy(self, kind, x, y, room):
        e = Enemy(self, kind, x, y, room)
        self.enemies.append(e)
        return e

    def hurt_player(self, dmg, by):
        p = self.player
        if p.iframes > 0 or self.state != "play":
            return
        p.hp -= dmg
        p.iframes = 0.6
        self.shake = max(self.shake, 8)
        self.pads.rumble(0.5, 0.9, 160)
        self.sfx.play("hurt", 0.5)
        self.float_text(p.x, p.y - 20, "-%d" % int(dmg), RED, 16)
        self.particle_burst(p.x, p.y, 12, RED, 140, 0.4)
        if p.hp <= 0:
            p.hp = 0
            self.killed_by = by
            self.state = "gameover"
            self.sfx.play("explode", 0.6)
            self.save.write()

    def damage_enemy(self, e, dmg, src):
        if e.dead or e.spawn_t > 0:
            return
        if e.kind == "lich" and not src.get("ignore_shield") and e.shielded(self):
            dmg *= 0.15
            if e.shield_msg <= self.time:
                e.shield_msg = self.time + 1.2
                self.float_text(e.x, e.y - 50, "VPN-SCHILD: Router neu verbinden!", (120, 255, 200), 13)
        if e.kind == "dragon" and not src.get("ignore_shield") and e.shielded():
            dmg *= 0.2
            if random.random() < 0.15:
                self.float_text(e.x, e.y - 70, "Schaden wird in der Cloud verarbeitet...", CYAN, 12)
        e.hp -= dmg
        e.flash = 0.1
        if src.get("online", True):
            e.online_damage += dmg
        self.float_text(e.x + random.uniform(-8, 8), e.y - e.r - 6, str(max(1, int(dmg))), YELLOW if dmg >= 20 else WHITE, 13)
        if not e.static and not e.boss:
            a = math.atan2(e.y - self.player.y, e.x - self.player.x)
            e.kx += math.cos(a) * 160
            e.ky += math.sin(a) * 160
        if e.hp <= 0:
            self.kill_enemy(e, src)

    def kill_enemy(self, e, src):
        e.dead = True
        self.stats["kills"] += 1
        self.particle_burst(e.x, e.y, 26 if not e.boss else 120, e.color, 200 if not e.boss else 400, 0.7, 4, True)
        self.sfx.play("hit", 0.5)
        if src.get("lag", 0) >= 30:
            self.unlock("lag")
            self.toast("LAG WIZARD: Zauber kam %.0f Sekunden zu spät an!" % src["lag"], YELLOW, big=True)
        if e.kind == "server":
            self.toast("Cloud-Server offline!", CYAN)
        if e.boss:
            self.on_boss_dead(e, src)
            return
        r = random.random()
        if r < 0.12:
            self.pickups.append(dict(kind="heart", x=e.x, y=e.y, t=0.0))
        elif r < 0.15:
            self.pickups.append(dict(kind="premium", x=e.x, y=e.y, t=0.0))

    def on_boss_dead(self, e, src):
        self.shake = 25
        self.pads.rumble(1.0, 1.0, 700)
        self.sfx.play("explode", 0.9)
        self.rings.append([e.x, e.y, 0.0, 400, 0.8, e.color])
        if src.get("kind") == "reboot":
            self.unlock("reboot")
            self.toast("BOSS DURCH ROUTER-NEUSTART BESIEGT!", GREEN, big=True)
        if e.online_damage <= 0.01:
            self.unlock("offline")
        for o in self.enemies:
            if not o.dead and o is not e:
                o.dead = True
                self.particle_burst(o.x, o.y, 15, o.color, 150, 0.5)
        self.dungeon.barrier_on = False
        self.toasts = [t for t in self.toasts if t["kind"] != "boss"]
        self.throttle_t = self.disconnect_t = self.wait_t = 0
        self.port_lock = {}
        cx, cy = self.dungeon.boss_room.center
        if e.kind == "dragon":
            self.unlock("win")
            self.save.data["wins"] = self.save.data.get("wins", 0) + 1
            self.save.write()
            self.victory_t = 3.0
            self.banner = ("NullPointergon.exe wurde deinstalliert", "SIEG", 2.5)
        else:
            self.portal = [cx, cy, 0.0]
            self.banner = ("%s besiegt!" % e.name.title(), "VERBINDUNG GESICHERT", 2.2)
            self.pickups.append(dict(kind="heart", x=cx + 60, y=cy, t=0.0))

    def explode(self, x, y, radius, dmg, src, color=(255, 160, 60), self_dmg=0):
        self.particle_burst(x, y, 40, color, radius * 3, 0.6, 4, True)
        self.rings.append([x, y, 0.0, radius, 0.35, color])
        self.shake = max(self.shake, 10)
        self.sfx.play("explode", 0.5)
        self.pads.rumble(0.35, 0.2, 110)
        for e in list(self.enemies):
            if not e.dead and dist(e.x, e.y, x, y) < radius + e.r:
                self.damage_enemy(e, dmg, src)
        p = self.player
        if self_dmg and dist(p.x, p.y, x, y) < radius:
            self.hurt_player(self_dmg, "die eigene Mini-Sonne")

    def projectile_end(self, pr):
        pr.dead = True
        if pr.owner != "player":
            self.particle_burst(pr.x, pr.y, 6, pr.color, 80, 0.3)
            return
        k = pr.kind
        if k == "fire":
            self.explode(pr.x, pr.y, PROJ["fire"]["aoe"], 8 * self.dmg_mult(), pr.src, (255, 140, 40))
        elif k == "sun":
            self.explode(pr.x, pr.y, 125, 55 * self.dmg_mult(), pr.src, (255, 230, 90), self_dmg=10)
        elif k == "chicken":
            self.chickens.append(Chicken(pr.x, pr.y))
            self.sfx.play("chicken", 0.5)
            self.particle_burst(pr.x, pr.y, 14, WHITE, 120, 0.6, 3)
        elif k == "tax":
            self.particle_burst(pr.x, pr.y, 10, (240, 240, 225), 100, 0.6, 4)
        else:
            self.particle_burst(pr.x, pr.y, 10, pr.color, 120, 0.4)

    # ---------------------------------------------------------------- Interaktion
    def find_interact(self):
        p = self.player
        best, bd = None, 64
        for h in self.dungeon.hotspots:
            d = dist(p.x, p.y, h.x, h.y)
            if d < bd:
                best, bd = h, d
        for c in self.dungeon.chests:
            if not c.opened:
                d = dist(p.x, p.y, c.x, c.y)
                if d < bd:
                    best, bd = c, d
        return best

    def interact_info(self, t):
        """(Prompt-Text, benötigte Haltezeit oder None)"""
        if isinstance(t, Chest):
            if not t.room.cleared:
                return "Truhe verschlossen – erst den Raum säubern!", None
            return "[E] Truhe öffnen", 0.25
        if t.reboot_t > 0:
            return "Router startet neu... bitte nicht ausschalten", None
        if not t.active:
            if t.locked:
                return "[E halten] Neues WLAN-Passwort erraten", 1.4
            return "[E halten] %s verbinden" % t.name, 1.1
        if t.kind == "router":
            if t.cool > 0:
                return "Router neu gestartet (wieder möglich in %ds)" % (int(t.cool) + 1), None
            return "[E halten] Router aus- und wieder einschalten", 0.9
        return "%s aktiv (+%d Signal)" % (t.name, t.bonus), None

    def do_interact(self, t):
        p = self.player
        if isinstance(t, Chest):
            t.opened = True
            self.sfx.play("pickup", 0.6)
            self.particle_burst(t.x, t.y, 30, YELLOW, 160, 0.7, 3, True)
            pool = [k for k, v in UPGRADES.items() if p.up[k] < v[2]]
            if random.random() < 0.25 or not pool:
                self.premium_t = 30.0
                self.toast("Truhe: Mage.NET Premium+ Gutschein! 30s werbefrei.", YELLOW, big=True)
            else:
                k = random.choice(pool)
                self.apply_upgrade(k)
                self.toast("Truhe: %s – %s" % (UPGRADES[k][0], UPGRADES[k][1]), YELLOW, big=True)
            return
        if not t.active:
            t.active = True
            if t.locked:
                t.locked = False
                self.float_text(t.x, t.y - 40, "Passwort erraten: %s" % random.choice(PASSWORDS), GREEN)
            else:
                self.float_text(t.x, t.y - 40, "Verbunden! +%d Signal" % t.bonus, GREEN)
            self.sfx.play("modem", 0.4)
            self.rings.append([t.x, t.y, 0.0, t.radius, 0.6, CYAN])
            return
        if t.kind == "router" and t.cool <= 0:
            t.reboot_t = 2.5
            t.cool = 18.0
            self.toast("Router wird neu gestartet... Bitte nicht ausschalten.", CYAN)
            self.sfx.play("click", 0.5)

    def reboot_wave(self, h):
        self.rings.append([h.x, h.y, 0.0, 320, 0.6, CYAN])
        self.rings.append([h.x, h.y, 0.0, 260, 0.45, WHITE])
        self.particle_burst(h.x, h.y, 60, CYAN, 400, 0.8, 3, True)
        self.shake = max(self.shake, 14)
        self.sfx.play("modem", 0.6)
        self.sfx.play("explode", 0.4)
        h.boost_t = 8.0
        self.pads.rumble(0.8, 0.5, 400)
        src = dict(kind="reboot", online=True, ignore_shield=True, lag=0)
        for e in list(self.enemies):
            if not e.dead and e.spawn_t <= 0 and dist(e.x, e.y, h.x, h.y) < 320 + e.r:
                self.damage_enemy(e, 170 if e.boss else 45, src)
                e.stun = max(e.stun, 0.6 if e.boss else 1.5)
        self.toast("NEUSTART ABGESCHLOSSEN – Turbo-Signal für 8 Sekunden!", GREEN, big=True)

    def apply_upgrade(self, k):
        p = self.player
        p.up[k] += 1
        if k == "robe":
            p.maxhp += 25
            p.hp = p.maxhp

    # ---------------------------------------------------------------- Räume
    def update_rooms(self):
        p = self.player
        room = self.dungeon.room_at(p.x, p.y)
        if room is not self.cur_room:
            self.cur_room = room
            if room and not room.visited:
                room.visited = True
                th = THEMES[room.theme]
                q = {5: "exzellent", 4: "gut", 3: "mittel", 2: "schlecht", 1: "miserabel", 0: "nicht vorhanden"}[th["base"]]
                self.toast("%s – Empfang: %s" % (th["name"], q), GREY)
            if room and room.kind == "normal" and not room.spawned:
                room.spawned = True
                for kind in room.plan:
                    for _ in range(30):
                        x, y = self.dungeon.rand_pos(room, 2)
                        if dist(x, y, p.x, p.y) > 150:
                            break
                    self.spawn_enemy(kind, x, y, room)
                if not room.plan:
                    room.cleared = True
        if room and room.kind == "boss" and not self.boss_started:
            if room.rect.inflate(-4, -4).collidepoint(int(p.x // TILE), int(p.y // TILE)):
                self.start_boss(room)
        for r in self.dungeon.rooms:
            if r.kind == "normal" and r.spawned and not r.cleared:
                if not any(e.room is r and not e.dead for e in self.enemies):
                    r.cleared = True
                    self.toast("Raum gesäubert.", GREEN)
                    self.sfx.play("pickup", 0.4)

    def start_boss(self, room):
        self.boss_started = True
        self.dungeon.barrier_on = True
        self.sfx.play("door", 0.7)
        self.sfx.play("boss", 0.7)
        cx, cy = room.center
        kind = BOSS_KIND[self.floor]
        if kind == "firewall":
            self.boss = FirewallBoss(self, cx, cy - 80, room)
            sub = "Lebendiger Firewall-Dämon · Port sperren · Verbindung drosseln · Pakete verschlucken"
            self.toast("Tipp: Der Schild verschluckt Pakete von vorne. Umrunde ihn!", YELLOW, life=5)
        elif kind == "lich":
            self.boss = LichBoss(self, cx, cy - 60, room)
            sub = "Untoter Netzwerktechniker · ändert WLAN-Passwörter · trennt Verbindungen"
            self.toast("Tipp: Halte die Router online – sonst schützt ihn ein VPN-Schild.", YELLOW, life=5)
        else:
            self.boss = DragonBoss(self, cx, room.px.y + 140, room)
            self.boss.spawn_servers(self, 4)
            sub = "Uralter Drachen-Administrator · legt sein Netzwerk lahm!"
            self.toast("Tipp: Zerstöre die Cloud-Server, um sein Schild zu senken.", YELLOW, life=5)
        self.enemies.append(self.boss)
        self.banner = (self.boss.name, sub, 2.4)

    # ---------------------------------------------------------------- Update
    def pad_events(self):
        pd = self.pads
        st = self.state

        def key(k):
            self.handle_event(pygame.event.Event(pygame.KEYDOWN, key=k))

        if st == "title":
            if pd.pressed("a") or pd.pressed("start"):
                key(pygame.K_RETURN)
            elif pd.pressed("y"):
                key(pygame.K_a)
        elif st == "achievements":
            if pd.pressed("a") or pd.pressed("b") or pd.pressed("start"):
                key(pygame.K_RETURN)
        elif st == "intro":
            if pd.pressed("a") or pd.pressed("start"):
                key(pygame.K_RETURN)
        elif st == "play":
            if pd.pressed("start"):
                key(pygame.K_ESCAPE)
                return
            if pd.pressed("x"):
                key(pygame.K_q)
            if pd.pressed("y"):
                key(pygame.K_r)
            if pd.pressed("b"):
                key(pygame.K_f)
            if pd.pressed("lt") or pd.pressed("lb"):
                key(pygame.K_SPACE)
            if pd.pressed("back"):
                self.close_top_ad()
        elif st == "pause":
            if pd.pressed("start") or pd.pressed("b"):
                key(pygame.K_ESCAPE)
            elif pd.pressed("back"):
                key(pygame.K_t)
        elif st == "upgrade":
            if pd.pressed("left"):
                key(pygame.K_LEFT)
            elif pd.pressed("right"):
                key(pygame.K_RIGHT)
            elif pd.pressed("a"):
                key(pygame.K_RETURN)
        elif st in ("gameover", "victory"):
            if pd.pressed("a") or pd.pressed("start"):
                key(pygame.K_RETURN)
            elif pd.pressed("b"):
                key(pygame.K_ESCAPE)

    def close_ad(self, ad):
        self.ads.remove(ad)
        self.sfx.play("click", 0.5)
        if hasattr(self, "stats"):
            self.stats["ads"] += 1
        if self.save.count("ads") >= 30:
            self.unlock("adblock")

    def close_top_ad(self):
        for ad in reversed(self.ads):
            if ad.t >= ad.delay:
                self.close_ad(ad)
                return
        if self.ads:
            self.sfx.play("error", 0.3)

    def music_want(self):
        st = self.state
        if st in ("title", "intro", "achievements"):
            return "title"
        if st == "gameover":
            return "gameover"
        if st == "victory" or self.victory_t > 0:
            return "victory"
        if self.boss_started and self.boss is not None and not self.boss.dead:
            return "boss"
        return "dungeon"

    def update_music(self, dt):
        if self.music is None:
            return
        want = self.music_want()
        self.music.update(dt, want, bars=getattr(self, "bars", 5),
                          glitch=self.state == "play" and want in ("dungeon", "boss"),
                          duck=0.35 if self.state in ("pause", "upgrade") else 1.0,
                          muted=self.sfx.muted or self.music_off)

    def update(self, dt):
        self.dt = dt
        self.update_music(dt)
        self.pads.poll()
        if self.pads.active:
            self.input_mode = "pad"
        self.pad_events()
        for a in self.ach_popups:
            a["t"] += dt
        self.ach_popups = [a for a in self.ach_popups if a["t"] < 3.2]
        if self.state == "title":
            self.title_t += dt
            for r in self.rain:
                r[1] += r[2] * dt
                if r[1] > H:
                    r[1] = random.randint(-200, -10)
                    r[0] = random.randint(0, W)
            return
        if self.state == "intro":
            self.intro_t += dt
            return
        if self.state != "play":
            return
        self.time += dt
        self.stats["time"] += dt
        p = self.player
        # Timer
        for k in list(self.port_lock):
            self.port_lock[k] -= dt
            if self.port_lock[k] <= 0:
                del self.port_lock[k]
        self.throttle_t = max(0.0, self.throttle_t - dt)
        self.disconnect_t = max(0.0, self.disconnect_t - dt)
        self.wait_t = max(0.0, self.wait_t - dt)
        self.premium_t = max(0.0, self.premium_t - dt)
        self.shake = max(0.0, self.shake - dt * 40)
        for k in p.cd:
            p.cd[k] = max(0.0, p.cd[k] - dt)
        p.cache_cd = max(0.0, p.cache_cd - dt)
        p.iframes = max(0.0, p.iframes - dt)
        if self.banner:
            b = self.banner
            self.banner = (b[0], b[1], b[2] - dt) if b[2] - dt > 0 else None
        for t in self.toasts:
            t["t"] += dt
        self.toasts = [t for t in self.toasts if t["t"] < t["life"]]
        for t in self.toasts:
            t["t0"] += dt
        for a in self.ads:
            a.t += dt
        self.ads = [a for a in self.ads if a.t < a.delay + a.life]

        # Bewegung
        keys = pygame.key.get_pressed()
        pad = self.pads
        mx = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])
        my = (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP])
        if mx or my:
            l = math.hypot(mx, my)
            mx, my = mx / l, my / l
        else:
            mx, my = pad.move
            if not (mx or my):
                dx = pad.down("right") - pad.down("left")
                dy = pad.down("down") - pad.down("up")
                if dx or dy:
                    l = math.hypot(dx, dy)
                    mx, my = dx / l, dy / l
        if mx or my:
            spd = p.speed * (1.15 ** p.up["boots"])
            p.x, p.y, _, _ = self.dungeon.move_circle(p.x, p.y, mx * spd * dt, my * spd * dt, p.r)
            p.walk += dt * math.hypot(mx, my)
        # Zielrichtung (Twin-Stick: rechter Stick, sonst Laufrichtung)
        ax, ay = pad.aim
        if ax or ay:
            l = math.hypot(ax, ay)
            self.aim_dir = (ax / l, ay / l)
        elif (mx or my) and self.pad_mode():
            l = math.hypot(mx, my)
            self.aim_dir = (mx / l, my / l)

        self.update_signal(dt)
        if self.bars == 0:
            if self.offline_since is None:
                self.offline_since = self.time
        else:
            self.offline_since = None

        # Dauerfeuer
        mouse = pygame.mouse.get_pressed()
        mpos = pygame.mouse.get_pos()
        over_ad = any(a.rect.collidepoint(mpos) for a in self.ads)
        if not mouse[0]:
            self.mouse_block = False
        if (mouse[0] and not over_ad and not self.mouse_block) or pad.down("rt") or pad.down("rb"):
            self.try_cast("fire")
        self.update_pending()

        # Interaktion
        t = self.find_interact()
        self.interact_target = t
        e_down = keys[pygame.K_e] or pad.down("a")
        if e_down and t is not None and not self.hold_block:
            _, need = self.interact_info(t)
            if need is not None:
                if self.hold_target is not t:
                    self.hold_target, self.hold = t, 0.0
                self.hold += dt
                if self.hold >= need:
                    self.do_interact(t)
                    self.hold, self.hold_target, self.hold_block = 0.0, None, True
            else:
                self.hold, self.hold_target = 0.0, None
        else:
            self.hold, self.hold_target = 0.0, None
            if not e_down:
                self.hold_block = False

        # Hotspots
        for h in self.dungeon.hotspots:
            h.t += dt
            h.cool = max(0.0, h.cool - dt)
            h.boost_t = max(0.0, h.boost_t - dt)
            if h.reboot_t > 0:
                h.reboot_t -= dt
                if h.reboot_t <= 0:
                    self.reboot_wave(h)

        # Downloads
        if self.dl_queue:
            dl = self.dl_queue[0]
            sp = DL_SPEED[self.bars] * (3 if p.up["booster"] else 1) * random.uniform(0.8, 1.2)
            dl["speed"] = sp
            dl["done"] += sp * dt
            if dl["done"] >= dl["size"]:
                self.dl_queue.pop(0)
                if dl["unlock"] == "patch":
                    p.patch = True
                    self.toast("DOWNLOAD ABGESCHLOSSEN: %s %s – alle Zauber +30%% Schaden!" % (dl["name"], dl["ver"]), GREEN, big=True)
                else:
                    p.unlocked.append(dl["unlock"])
                    self.toast("DOWNLOAD ABGESCHLOSSEN: %s %s – Taste %s" % (dl["name"], dl["ver"], SPELLS[dl["unlock"]]["key"]), GREEN, big=True)
                self.sfx.play("pickup", 0.7)
                self.unlock("download")

        self.update_rooms()

        # Gegner
        for e in self.enemies:
            if not e.dead:
                e.update(self, dt)
        self.enemies = [e for e in self.enemies if not e.dead]

        # Hühner
        for c in self.chickens:
            c.life -= dt
            c.t += dt
            c.turn -= dt
            if c.turn <= 0:
                c.turn = random.uniform(0.3, 0.9)
                c.dir = random.uniform(0, math.tau)
                if random.random() < 0.3:
                    self.float_text(c.x, c.y - 14, random.choice(["Gack!", "Bock bock!", "GACK?!"]), WHITE, 11)
            c.x, c.y, _, _ = self.dungeon.move_circle(c.x, c.y, math.cos(c.dir) * 90 * dt, math.sin(c.dir) * 90 * dt, c.r)
        for c in self.chickens:
            if c.life <= 0 or c.hp <= 0:
                self.particle_burst(c.x, c.y, 12, WHITE, 100, 0.6, 2)
        self.chickens = [c for c in self.chickens if c.life > 0 and c.hp > 0]

        # Projektile
        self.update_projectiles(dt)

        # Meteore
        for m in self.meteors:
            m["t"] -= dt
            if m["t"] <= 0:
                self.explode(m["x"], m["y"], 115, 70 * self.dmg_mult(), m["src"], (255, 110, 50), self_dmg=15 if m["chaos"] else 0)
        self.meteors = [m for m in self.meteors if m["t"] > 0]

        # Pickups
        for pk in self.pickups:
            pk["t"] += dt
            if dist(pk["x"], pk["y"], p.x, p.y) < 24:
                pk["taken"] = True
                self.sfx.play("pickup", 0.5)
                if pk["kind"] == "heart":
                    self.heal_player(20)
                else:
                    self.premium_t = 30.0
                    self.ads.clear()
                    self.toast("Mage.NET Premium+ aktiviert: 30 Sekunden ohne Werbung!", YELLOW, big=True)
        self.pickups = [pk for pk in self.pickups if not pk.get("taken")]

        # Portal
        if self.portal:
            self.portal[2] += dt
            if dist(self.portal[0], self.portal[1], p.x, p.y) < 34 and self.portal[2] > 0.8:
                self.open_upgrade_screen()

        if self.victory_t > 0:
            self.victory_t -= dt
            if self.victory_t <= 0:
                self.state = "victory"

        # Partikel & Effekte
        for pa in self.particles:
            pa.life -= dt
            pa.x += pa.vx * dt
            pa.y += pa.vy * dt
            pa.vx *= pa.drag
            pa.vy *= pa.drag
        self.particles = [pa for pa in self.particles if pa.life > 0]
        for f in self.floats:
            f[1] -= 36 * dt
            f[4] -= dt
        self.floats = [f for f in self.floats if f[4] > 0]
        for r in self.rings:
            r[2] += dt
        self.rings = [r for r in self.rings if r[2] < r[4]]
        for b in self.bolts:
            b[1] -= dt
        self.bolts = [b for b in self.bolts if b[1] > 0]

        # Kamera
        tw, th = self.dungeon.tw * TILE, self.dungeon.th * TILE
        tx = clamp(p.x - W / 2, 0, tw - W)
        ty = clamp(p.y - H / 2, 0, th - H)
        self.cam_x += (tx - self.cam_x) * min(1.0, dt * 8)
        self.cam_y += (ty - self.cam_y) * min(1.0, dt * 8)

    def update_projectiles(self, dt):
        dg = self.dungeon
        p = self.player
        for pr in self.projectiles:
            if pr.dead:
                continue
            pr.age += dt
            pr.life -= dt
            pr.spin += dt * 10
            if pr.life <= 0:
                self.projectile_end(pr)
                continue
            mdt = dt
            if pr.stutter > 0:
                pr.acc += dt
                pr.st_timer -= dt
                if pr.st_timer > 0:
                    mdt = 0.0
                else:
                    mdt = pr.acc
                    pr.acc = 0.0
                    pr.st_timer = random.uniform(0.05, pr.stutter)
                    pr.jx, pr.jy = random.uniform(-4, 4), random.uniform(-4, 4)
            if pr.homing and pr.owner == "enemy":
                want = math.atan2(p.y - pr.y, p.x - pr.x)
                cur = math.atan2(pr.vy, pr.vx)
                sp = math.hypot(pr.vx, pr.vy)
                cur += clamp(angle_diff(cur, want), -pr.homing * dt, pr.homing * dt)
                pr.vx, pr.vy = math.cos(cur) * sp, math.sin(cur) * sp
            if mdt > 0:
                sp = math.hypot(pr.vx, pr.vy) * mdt
                steps = int(sp / 6) + 1
                for _ in range(steps):
                    nx, ny = pr.x + pr.vx * mdt / steps, pr.y + pr.vy * mdt / steps
                    if dg.solid_px(nx, ny):
                        if pr.bounces > 0:
                            if dg.solid_px(nx, pr.y):
                                pr.vx = -pr.vx
                            if dg.solid_px(pr.x, ny):
                                pr.vy = -pr.vy
                            pr.bounces -= 1
                            self.sfx.play("hit", 0.3)
                            break
                        self.projectile_end(pr)
                        break
                    pr.x, pr.y = nx, ny
                if pr.dead:
                    continue
            # Treffer
            if pr.owner == "player":
                for e in self.enemies:
                    if e.dead or e.spawn_t > 0 or e in pr.hit:
                        continue
                    if dist(e.x, e.y, pr.x, pr.y) < e.r + pr.r:
                        if isinstance(e, FirewallBoss) and e.blocks(self, pr):
                            self.float_text(pr.x, pr.y - 10, "PAKET VERSCHLUCKT", ORANGE, 12)
                            self.particle_burst(pr.x, pr.y, 8, ORANGE, 100, 0.3)
                            pr.dead = True
                            break
                        pr.hit.add(e)
                        self.sfx.play("hit", 0.3)
                        if pr.kind == "ice":
                            e.slow = 3.0
                        if pr.kind == "tax" and not e.boss:
                            e.stun = max(e.stun, 3.0)
                            self.float_text(e.x, e.y - 24, "BÜROKRATIE!", WHITE, 12)
                            if self.save.count("tax") >= 15:
                                self.unlock("tax")
                        self.damage_enemy(e, pr.dmg, pr.src)
                        if not pr.pierce:
                            self.projectile_end(pr)
                            break
            else:
                if dist(p.x, p.y, pr.x, pr.y) < p.r + pr.r:
                    self.hurt_player(pr.dmg, {"envelope": "Spam-Mail", "brick": "Firewall-Ziegel", "skull": "Totenkopf-Paket",
                                              "dfire": "Drachenfeuer", "breath": "Feueratem.exe", "packet": "ein Cloud-Paket"}[pr.kind])
                    if pr.kind == "envelope" and random.random() < 0.1 and self.premium_t <= 0 and len(self.ads) < 4:
                        self.ads.append(Ad(self))
                        self.sfx.play("ad", 0.5)
                    pr.dead = True
                    self.particle_burst(pr.x, pr.y, 8, pr.color, 100, 0.3)
                    continue
                for c in self.chickens:
                    if dist(c.x, c.y, pr.x, pr.y) < c.r + pr.r:
                        c.hp -= pr.dmg
                        pr.dead = True
                        break
        self.projectiles = [pr for pr in self.projectiles if not pr.dead]

    def open_upgrade_screen(self):
        p = self.player
        pool = [k for k, v in UPGRADES.items() if p.up[k] < v[2]]
        random.shuffle(pool)
        self.choices = pool[:3]
        self.card_sel = 0
        self.portal = None
        if not self.choices:
            self.next_floor()
            return
        self.state = "upgrade"
        self.sfx.play("pickup", 0.6)

    def next_floor(self):
        p = self.player
        p.hp = min(p.maxhp, p.hp + 30)
        self.start_floor(self.floor + 1)
        self.state = "play"
        self.mouse_block = True

    # ---------------------------------------------------------------- Events
    def handle_event(self, ev):
        if ev.type == pygame.QUIT:
            self.save.write()
            pygame.quit()
            sys.exit()
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_m:
            self.sfx.muted = not self.sfx.muted
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_n:
            self.music_off = not self.music_off
        if ev.type in PAD_DEVICE_EVENTS:
            had = self.pads.connected
            self.pads.scan()
            if self.state == "play" and had != self.pads.connected:
                self.toast("Gamepad verbunden: %s" % self.pads.name if self.pads.connected else "Gamepad getrennt", CYAN)
            return
        if ev.type == pygame.MOUSEMOTION and abs(ev.rel[0]) + abs(ev.rel[1]) > 3:
            self.input_mode = "mouse"
        if ev.type == pygame.MOUSEBUTTONDOWN:
            self.input_mode = "mouse"
        st = self.state
        if st == "title":
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.state = "intro"
                    self.intro_t = 0.0
                    self.sfx.play("modem", 0.5)
                elif ev.key == pygame.K_a:
                    self.state = "achievements"
                elif ev.key == pygame.K_ESCAPE:
                    self.handle_event(pygame.event.Event(pygame.QUIT))
        elif st == "achievements":
            if ev.type == pygame.KEYDOWN or ev.type == pygame.MOUSEBUTTONDOWN:
                self.state = "title"
        elif st == "intro":
            if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                if self.intro_t < len(INTRO) * 0.9 and ev.key != pygame.K_ESCAPE:
                    self.intro_t = len(INTRO) * 0.9 + 0.1
                else:
                    self.new_run()
        elif st == "play":
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    self.state = "pause"
                elif ev.key == pygame.K_q:
                    self.try_cast("heal")
                elif ev.key == pygame.K_r:
                    self.try_cast("chain")
                elif ev.key == pygame.K_f:
                    self.try_cast("meteor")
                elif ev.key == pygame.K_SPACE:
                    self.try_cast("tp")
                elif ev.key == pygame.K_F10:  # Jam-Demo-Cheat: Etage überspringen
                    if self.floor < 3:
                        self.next_floor()
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                for ad in reversed(self.ads):
                    if ad.rect.collidepoint(ev.pos):
                        self.mouse_block = True
                        if ad.t >= ad.delay and ad.close_rect.collidepoint(ev.pos):
                            self.close_ad(ad)
                        elif ad.buy_rect.collidepoint(ev.pos):
                            self.sfx.play("ad", 0.6)
                            self.toast("Danke für Ihren Einkauf! 0 Gold abgebucht. Hier ist mehr Werbung.", MAGENTA)
                            for _ in range(2):
                                if len(self.ads) < 6:
                                    self.ads.append(Ad(self))
                        return
                if ev.button == 3:
                    self.try_cast("tp")
        elif st == "pause":
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    self.state = "play"
                elif ev.key == pygame.K_t:
                    self.state = "title"
        elif st == "upgrade":
            pick = None
            if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                pick = ev.key - pygame.K_1
            if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_LEFT, pygame.K_a):
                self.card_sel = (self.card_sel - 1) % len(self.choices)
                self.sfx.play("click", 0.3)
            if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_RIGHT, pygame.K_d):
                self.card_sel = (self.card_sel + 1) % len(self.choices)
                self.sfx.play("click", 0.3)
            if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                pick = self.card_sel
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                for i, r in enumerate(self.card_rects()):
                    if r.collidepoint(ev.pos):
                        pick = i
            if pick is not None and pick < len(self.choices):
                self.apply_upgrade(self.choices[pick])
                self.sfx.play("pickup", 0.7)
                self.next_floor()
        elif st in ("gameover", "victory"):
            if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.new_run()
            elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                self.state = "title"

    # ---------------------------------------------------------------- Zeichnen
    def draw(self):
        s = self.screen
        st = self.state
        if st == "title":
            self.draw_title(s)
        elif st == "achievements":
            self.draw_achievements(s)
        elif st == "intro":
            self.draw_intro(s)
        else:
            self.draw_world(s)
            self.draw_hud(s)
            if st == "pause":
                self.draw_pause(s)
            elif st == "upgrade":
                self.draw_upgrade(s)
            elif st == "gameover":
                self.draw_gameover(s)
            elif st == "victory":
                self.draw_victory(s)
        self.draw_ach_popups(s)

    def draw_world(self, s):
        ox = random.uniform(-self.shake, self.shake) if self.shake > 0 else 0
        oy = random.uniform(-self.shake, self.shake) if self.shake > 0 else 0
        cx, cy = int(self.cam_x + ox), int(self.cam_y + oy)
        s.fill((8, 7, 12))
        s.blit(self.dungeon.surface, (-cx, -cy))
        dg = self.dungeon
        t = self.time
        # Barriere
        if dg.barrier_on:
            for (tx, ty) in dg.barrier:
                r = pygame.Rect(tx * TILE - cx, ty * TILE - cy, TILE, TILE)
                if -TILE < r.x < W and -TILE < r.y < H:
                    pygame.draw.rect(s, (120, 30, 30), r)
                    for k in range(4):
                        yy = r.y + (k * 8 + int(t * 30)) % TILE
                        pygame.draw.line(s, ORANGE, (r.x, yy), (r.right, yy), 2)
                    draw_glow(s, r.centerx, r.centery, (255, 80, 30), 24)
        # Hotspot-Reichweite & Hotspots
        mult = 1.4 if self.player.up["staff"] else 1.0
        for h in dg.hotspots:
            x, y = h.x - cx, h.y - cy
            if not (-500 < x < W + 500 and -500 < y < H + 500):
                continue
            if h.power():
                rr = h.radius * mult
                for k in range(3):
                    ph = ((t * 0.5 + k / 3) % 1.0)
                    col = mix((10, 10, 20), CYAN if h.boost_t <= 0 else GREEN, 0.35 * (1 - ph))
                    pygame.draw.circle(s, col, (int(x), int(y)), int(rr * ph), 1)
            self.draw_hotspot(s, h, x, y)
        # Pilze
        for m in dg.mushrooms:
            x, y = m[0] - cx, m[1] - cy
            if -20 < x < W + 20 and -20 < y < H + 20:
                pygame.draw.rect(s, (230, 220, 200), (x - 3, y - 2, 6, 9))
                pygame.draw.ellipse(s, (200, 50, 60), (x - 10, y - 10, 20, 12))
                pygame.draw.circle(s, WHITE, (int(x - 4), int(y - 6)), 2)
                pygame.draw.circle(s, WHITE, (int(x + 4), int(y - 5)), 2)
        # Truhen
        for c in dg.chests:
            x, y = c.x - cx, c.y - cy
            if -30 < x < W + 30 and -30 < y < H + 30:
                pygame.draw.rect(s, (110, 70, 30), (x - 14, y - 8, 28, 18), border_radius=3)
                if c.opened:
                    pygame.draw.rect(s, (60, 40, 20), (x - 14, y - 16, 28, 8))
                else:
                    pygame.draw.rect(s, (140, 90, 40), (x - 14, y - 12, 28, 8), border_radius=3)
                    pygame.draw.rect(s, YELLOW if c.room.cleared else GREY, (x - 3, y - 6, 6, 7))
                    if c.room.cleared:
                        draw_glow(s, x, y, YELLOW, 30 + int(math.sin(t * 4) * 6))
        # Pickups
        for pk in self.pickups:
            x, y = pk["x"] - cx, pk["y"] - cy + math.sin(pk["t"] * 5) * 3
            if pk["kind"] == "heart":
                pygame.draw.circle(s, RED, (int(x - 4), int(y - 2)), 6)
                pygame.draw.circle(s, RED, (int(x + 4), int(y - 2)), 6)
                pygame.draw.polygon(s, RED, [(x - 10, y), (x + 10, y), (x, y + 11)])
                draw_glow(s, x, y, RED, 26)
            else:
                pygame.draw.rect(s, YELLOW, (x - 12, y - 8, 24, 16), border_radius=3)
                text(s, "P+", (x, y), 11, (80, 40, 0), "center", shadow=False, bold=True)
                draw_glow(s, x, y, YELLOW, 30)
        # Portal
        if self.portal:
            x, y = self.portal[0] - cx, self.portal[1] - cy
            for k in range(6):
                rr = 14 + k * 6 + math.sin(t * 5 + k) * 3
                pygame.draw.circle(s, mix(CYAN, MAGENTA, k / 6), (int(x), int(y)), int(rr), 2)
            draw_glow(s, x, y, CYAN, 80)
            text(s, "NÄCHSTE ETAGE", (x, y - 64), 13, CYAN, "center", bold=True)
        # Meteor-Schatten
        for m in self.meteors:
            x, y = m["x"] - cx, m["y"] - cy
            k = 1 - m["t"] / 0.8
            pygame.draw.circle(s, (80, 20, 10), (int(x), int(y)), int(115 * k), 2)
            mx, my = x + 200 * (1 - k), y - 400 * (1 - k)
            pygame.draw.circle(s, (255, 120, 60), (int(mx), int(my)), 14)
            draw_glow(s, mx, my, (255, 120, 40), 60)
        # Gegner
        for e in sorted(self.enemies, key=lambda e: e.y):
            if -150 < e.x - cx < W + 150 and -150 < e.y - cy < H + 150:
                e.draw(self, s, cx, cy)
        # Hühner
        for c in self.chickens:
            x, y = c.x - cx, c.y - cy + abs(math.sin(c.t * 12)) * -3
            pygame.draw.ellipse(s, WHITE, (x - 9, y - 6, 18, 13))
            pygame.draw.circle(s, WHITE, (int(x + 7), int(y - 8)), 5)
            pygame.draw.polygon(s, ORANGE, [(x + 11, y - 9), (x + 16, y - 7), (x + 11, y - 6)])
            pygame.draw.circle(s, RED, (int(x + 7), int(y - 13)), 3)
            pygame.draw.circle(s, BLACK, (int(x + 8), int(y - 9)), 1)
        self.draw_player(s, cx, cy)
        # Projektile
        for pr in self.projectiles:
            self.draw_projectile(s, pr, pr.x - cx + pr.jx, pr.y - cy + pr.jy)
        # Blitze
        for b in self.bolts:
            pts = [(x - cx, y - cy) for x, y in b[0]]
            if len(pts) > 1:
                pygame.draw.lines(s, (255, 255, 180), False, pts, 3)
                pygame.draw.lines(s, WHITE, False, pts, 1)
                for x, y in pts[::3]:
                    draw_glow(s, x, y, YELLOW, 30)
        # Ringe
        for r in self.rings:
            k = r[2] / r[4]
            pygame.draw.circle(s, mix(r[5], (0, 0, 0), k), (int(r[0] - cx), int(r[1] - cy)), max(1, int(r[3] * k)), max(1, int(5 * (1 - k)) + 1))
        # Partikel
        for pa in self.particles:
            k = pa.life / pa.maxlife
            x, y = pa.x - cx, pa.y - cy
            if pa.glow:
                draw_glow(s, x, y, pa.color, int(pa.size * 4 * k) + 4)
            else:
                pygame.draw.circle(s, pa.color, (int(x), int(y)), max(1, int(pa.size * k)))
        # Dunkelheit
        idx = clamp(int(self.dark / 25), 0, 4)
        s.blit(self.vignettes[idx], (0, 0))
        # Floating Texte
        for f in self.floats:
            text(s, f[2], (f[0] - cx, f[1] - cy), f[5], f[3], "center", alpha=int(255 * clamp(f[4] * 2, 0, 1)))
        # Glitch bei schlechtem Empfang
        if self.bars <= 1 and self.state == "play":
            n = 2 if self.bars == 1 else 5
            if random.random() < (0.25 if self.bars == 1 else 0.6):
                for _ in range(n):
                    y = random.randint(0, H - 20)
                    hh = random.randint(2, 14)
                    strip = s.subsurface((0, y, W, hh)).copy()
                    s.blit(strip, (random.randint(-20, 20), y))
            if self.bars == 0:
                for _ in range(40):
                    x, y = random.randint(0, W), random.randint(0, H)
                    s.fill((90, 90, 100), (x, y, random.randint(2, 30), 1))

    def draw_hotspot(self, s, h, x, y):
        t = h.t
        if h.kind == "router":
            pygame.draw.ellipse(s, BLACK, (x - 18, y + 6, 36, 8))
            pygame.draw.rect(s, (40, 40, 55), (x - 16, y - 8, 32, 14), border_radius=3)
            for i in (-10, 10):
                pygame.draw.line(s, (40, 40, 55), (x + i, y - 8), (x + i * 1.3, y - 26), 3)
                pygame.draw.circle(s, PURPLE, (int(x + i * 1.3), int(y - 27)), 3)
            for i in range(4):
                if h.reboot_t > 0:
                    col = ORANGE if int(t * 8 + i) % 2 else (60, 40, 0)
                elif h.active:
                    col = GREEN if (int(t * 6) + i) % 4 else (40, 120, 60)
                else:
                    col = RED if h.locked and int(t * 3) % 2 else (90, 30, 30)
                pygame.draw.circle(s, col, (int(x - 9 + i * 6), int(y - 1)), 2)
            if h.power():
                for i in range(3):
                    pygame.draw.arc(s, CYAN, (x - 8 - i * 6, y - 46 - i * 6, 16 + i * 12, 16 + i * 12), 0.8, 2.35, 2)
                draw_glow(s, x, y - 10, CYAN, 40)
            elif h.locked:
                text(s, "PASSWORT?", (x, y - 44), 11, RED, "center", bold=True)
        elif h.kind == "mast":
            pygame.draw.line(s, (120, 120, 140), (x - 12, y + 10), (x, y - 50), 3)
            pygame.draw.line(s, (120, 120, 140), (x + 12, y + 10), (x, y - 50), 3)
            for k in range(4):
                yy = y + 10 - k * 15
                w = 12 * (1 - k / 4.4)
                pygame.draw.line(s, (100, 100, 120), (x - w, yy), (x + w, yy), 2)
            pygame.draw.circle(s, RED if int(t * 2) % 2 else (100, 20, 20), (int(x), int(y - 52)), 4)
            if h.power():
                for i in range(3):
                    pygame.draw.circle(s, mix(CYAN, (0, 0, 0), i / 3), (int(x), int(y - 52)), 10 + i * 8 + int((t * 20) % 8), 1)
                draw_glow(s, x, y - 52, CYAN, 40)
        elif h.kind == "dish":
            pygame.draw.line(s, (120, 120, 140), (x, y + 8), (x, y - 8), 4)
            pygame.draw.ellipse(s, (200, 200, 215) if h.active else (110, 110, 120), (x - 20, y - 30, 40, 26))
            pygame.draw.ellipse(s, (150, 150, 170), (x - 14, y - 26, 28, 18), 2)
            pygame.draw.line(s, (90, 90, 100), (x, y - 17), (x + 10, y - 34), 2)
            pygame.draw.circle(s, MAGENTA if h.active else (90, 40, 80), (int(x + 10), int(y - 35)), 4)
            if h.power():
                draw_glow(s, x + 10, y - 35, MAGENTA, 40)

    def draw_player(self, s, cx, cy):
        p = self.player
        x, y = p.x - cx, p.y - cy
        if p.iframes > 0 and int(p.iframes * 20) % 2:
            return
        mx, my = self.aim_screen()
        ang = math.atan2(my - y, mx - x)
        bob = math.sin(p.walk * 14) * 2
        pygame.draw.ellipse(s, BLACK, (x - 12, y + 8, 24, 8))
        robe = (90, 60, 200)
        pygame.draw.polygon(s, robe, [(x - 13, y + 10), (x, y - 12 + bob), (x + 13, y + 10)])
        pygame.draw.polygon(s, (120, 90, 230), [(x - 4, y + 10), (x, y - 6 + bob), (x + 4, y + 10)])
        pygame.draw.circle(s, (240, 210, 180), (int(x), int(y - 12 + bob)), 7)
        pygame.draw.polygon(s, (220, 220, 230), [(x - 6, y - 10 + bob), (x, y + 2 + bob), (x + 6, y - 10 + bob)])  # Bart
        hat = (70, 40, 170)
        pygame.draw.polygon(s, hat, [(x - 12, y - 16 + bob), (x + 12, y - 16 + bob), (x + 3, y - 38 + bob)])
        pygame.draw.rect(s, YELLOW, (x - 7, y - 21 + bob, 14, 3))
        # Antenne auf dem Hut
        ax, ay = x + 3, y - 38 + bob
        pygame.draw.line(s, GREY, (ax, ay), (ax + 4, ay - 10), 2)
        col = BAR_COLORS[self.bars]
        pygame.draw.circle(s, col, (int(ax + 4), int(ay - 11)), 3)
        draw_glow(s, ax + 4, ay - 11, col, 18)
        if p.up["hat"]:
            pygame.draw.circle(s, CYAN, (int(x - 6), int(y - 24 + bob)), 3)
        # Zauberstab
        wx, wy = x + math.cos(ang) * 18, y + math.sin(ang) * 18 + bob
        pygame.draw.line(s, (240, 200, 60) if p.up["staff"] else (130, 90, 50), (x, y + bob), (wx, wy), 3)
        pygame.draw.circle(s, col, (int(wx), int(wy)), 3)
        for i in range(self.bars):
            r = 6 + i * 4
            pygame.draw.arc(s, mix(col, (0, 0, 0), i * 0.12), (wx - r, wy - r, r * 2, r * 2), -ang - 0.5, -ang + 0.5, 1)
        if self.bars == 0:
            k = int(self.time * 3) % 2
            if k:
                pygame.draw.line(s, RED, (x - 7, y - 58), (x + 7, y - 44), 3)
                pygame.draw.line(s, RED, (x + 7, y - 58), (x - 7, y - 44), 3)
        # Übertragungen in der Leitung
        live = [pd for pd in self.pending if pd["fire_at"] is not None]
        for i, pd in enumerate(live):
            k = clamp(1 - (pd["fire_at"] - self.time) / max(0.01, pd.get("delay", 1)), 0, 1)
            a = self.time * 4 + i * 1.3
            px, py = x + math.cos(a) * 22, y - 6 + math.sin(a) * 22
            pygame.draw.rect(s, SPELLS[pd["spell"]]["color"], (px - 3, py - 3, 6, 6))
            pygame.draw.arc(s, WHITE, (px - 7, py - 7, 14, 14), 0, math.tau * k, 2)
        queued = sum(1 for pd in self.pending if pd["fire_at"] is None)
        if queued:
            text(s, "Warteschlange: %d" % queued, (x, y + 22), 11, ORANGE, "midtop")
        if self.wait_t > 0:
            for i in range(8):
                a = self.time * 8 + i * math.tau / 8
                c = mix(WHITE, (40, 40, 40), i / 8)
                pygame.draw.circle(s, c, (int(x + math.cos(a) * 26), int(y - 8 + math.sin(a) * 26)), 3)

    def draw_projectile(self, s, pr, x, y):
        k = pr.kind
        if k == "fire" or k == "dfire" or k == "breath":
            pygame.draw.circle(s, pr.color, (int(x), int(y)), pr.r)
            pygame.draw.circle(s, YELLOW, (int(x), int(y)), max(2, pr.r - 4))
            draw_glow(s, x, y, pr.color, pr.r * 5)
            if random.random() < 0.5:
                self.particles.append(Particle(pr.x, pr.y, random.uniform(-30, 30), random.uniform(-30, 30), 0.3, pr.color, 3))
        elif k == "ice":
            pygame.draw.polygon(s, pr.color, [(x + math.cos(pr.spin + i * math.pi / 3) * pr.r * (1.4 if i % 2 else 0.7),
                                               y + math.sin(pr.spin + i * math.pi / 3) * pr.r * (1.4 if i % 2 else 0.7)) for i in range(6)])
            draw_glow(s, x, y, pr.color, 30)
        elif k == "chicken":
            pygame.draw.ellipse(s, WHITE, (x - 9, y - 6, 18, 13))
            pygame.draw.circle(s, WHITE, (int(x + 6), int(y - 7)), 5)
            pygame.draw.circle(s, RED, (int(x + 6), int(y - 12)), 3)
            pygame.draw.polygon(s, ORANGE, [(x + 10, y - 8), (x + 15, y - 6), (x + 10, y - 5)])
            pygame.draw.line(s, WHITE, (x - 9, y), (x - 14, y - 6 + math.sin(pr.age * 40) * 4), 3)
        elif k == "chair":
            a = pr.spin
            pts = [(x + math.cos(a + i * math.tau / 5) * 13, y + math.sin(a + i * math.tau / 5) * 13) for i in range(5)]
            for px, py in pts:
                pygame.draw.line(s, (50, 50, 60), (x, y), (px, py), 3)
                pygame.draw.circle(s, BLACK, (int(px), int(py)), 3)
            pygame.draw.rect(s, (30, 30, 35), (x - 9, y - 16, 18, 14), border_radius=4)
            pygame.draw.rect(s, (60, 60, 70), (x - 8, y - 4, 16, 6), border_radius=2)
        elif k == "sun":
            draw_glow(s, x, y, (255, 200, 60), 70)
            pygame.draw.circle(s, (255, 240, 150), (int(x), int(y)), pr.r)
            for i in range(8):
                a = pr.spin * 0.3 + i * math.tau / 8
                pygame.draw.line(s, YELLOW, (x + math.cos(a) * 16, y + math.sin(a) * 16), (x + math.cos(a) * 24, y + math.sin(a) * 24), 2)
        elif k == "tax":
            r = pygame.Rect(0, 0, 18, 22)
            r.center = (x, y + math.sin(pr.spin) * 3)
            pygame.draw.rect(s, (245, 245, 235), r)
            for j in range(4):
                pygame.draw.line(s, (120, 120, 140), (r.x + 3, r.y + 5 + j * 4), (r.right - 3, r.y + 5 + j * 4), 1)
            text(s, "§", (r.right - 5, r.bottom - 7), 10, RED, "center", shadow=False, bold=True)
        elif k == "envelope":
            r = pygame.Rect(0, 0, 16, 11)
            r.center = (x, y)
            pygame.draw.rect(s, WHITE, r)
            pygame.draw.lines(s, RED, False, [r.topleft, r.center, r.topright], 1)
        elif k == "brick":
            r = pygame.Rect(0, 0, 16, 10)
            r.center = (x, y)
            pygame.draw.rect(s, (200, 70, 40), r)
            pygame.draw.rect(s, YELLOW, r, 1)
            draw_glow(s, x, y, ORANGE, 24)
        elif k == "skull":
            pygame.draw.circle(s, (230, 230, 220), (int(x), int(y)), 8)
            pygame.draw.circle(s, BLACK, (int(x - 3), int(y - 1)), 2)
            pygame.draw.circle(s, BLACK, (int(x + 3), int(y - 1)), 2)
            draw_glow(s, x, y, (120, 255, 200), 30)
        elif k == "packet":
            pygame.draw.rect(s, CYAN, (x - 6, y - 6, 12, 12), 2)
            text(s, "01", (x, y), 8, CYAN, "center", shadow=False)
            draw_glow(s, x, y, CYAN, 24)

    def draw_hud(self, s):
        p = self.player
        t = self.time
        # Panel links oben
        panel = pygame.Rect(10, 10, 330, 92)
        ps = pygame.Surface(panel.size, pygame.SRCALPHA)
        ps.fill((10, 8, 20, 190))
        s.blit(ps, panel)
        off_blink = self.bars == 0 and int(t * 3) % 2
        pygame.draw.rect(s, RED if off_blink else (80, 70, 140), panel, 2 if self.bars == 0 else 1, border_radius=4)
        hpk = p.hp / p.maxhp
        pygame.draw.rect(s, (50, 10, 20), (22, 20, 230, 16))
        pygame.draw.rect(s, mix(RED, GREEN, hpk), (22, 20, 230 * hpk, 16))
        text(s, "HP %d/%d" % (p.hp, p.maxhp), (26, 20), 13, WHITE)
        draw_bars(s, 22, 46, self.bars, blink=int(t * 3) % 2 == 0)
        text(s, "%s" % BAR_LABELS[self.bars], (85, 46), 15, BAR_COLORS[self.bars], bold=True)
        if self.bars:
            ping = int(PING[self.bars] * random.uniform(0.85, 1.25)) if int(t * 4) % 2 else PING[self.bars]
            text(s, "Ping: %d ms" % ping, (85, 66), 12, GREY)
        else:
            text(s, "Ping: ---", (85, 66), 12, GREY)
        status = []
        if self.throttle_t > 0:
            status.append(("GEDROSSELT", ORANGE))
        if self.disconnect_t > 0:
            status.append(("GETRENNT", RED))
        if self.flicker_t > 0 and self.bars < 5:
            status.append(("STÖRUNG", YELLOW))
        if self.premium_t > 0:
            status.append(("PREMIUM+ %ds" % int(self.premium_t), YELLOW))
        if self.music is not None and self.music.buffering and not self.sfx.muted:
            status.append(("MUSIK PUFFERT...", GREY))
        for i, (st, c) in enumerate(status[:2]):
            text(s, st, (330 - 8, 46 + i * 18), 11, c, "topright", bold=True)
        if p.up["cache"]:
            text(s, "Cache: %s" % ("bereit" if p.cache_cd <= 0 else "%ds" % (int(p.cache_cd) + 1)), (200, 66), 11, CYAN)
        # Raumname
        room = self.cur_room
        nm = THEMES[room.theme]["name"] if room else THEMES["corridor"]["name"]
        text(s, "ETAGE %d · %s" % (self.floor, nm), (W // 2, 14), 15, (200, 200, 230), "midtop")
        # Boss-Leiste
        if self.boss and not self.boss.dead and self.boss.spawn_t <= 0:
            b = self.boss
            bw = 560
            bx = W // 2 - bw // 2
            by = H - 140
            pygame.draw.rect(s, (20, 0, 0), (bx - 2, by - 2, bw + 4, 18))
            pygame.draw.rect(s, b.color, (bx, by, bw * b.hp / b.maxhp, 14))
            text(s, b.name, (W // 2, by - 20), 15, WHITE, "midtop", bold=True)
            sh = (b.kind == "lich" and b.shielded(self)) or (b.kind == "dragon" and b.shielded())
            if sh:
                pygame.draw.rect(s, CYAN, (bx - 2, by - 2, bw + 4, 18), 2)
        # Minimap
        self.draw_minimap(s)
        # Zauberleiste
        n = len(SPELL_ORDER)
        sw = 62
        x0 = W // 2 - (n * (sw + 8)) // 2
        y0 = H - 82
        for i, sp in enumerate(SPELL_ORDER):
            r = pygame.Rect(x0 + i * (sw + 8), y0, sw, sw)
            pygame.draw.rect(s, (16, 14, 28), r, border_radius=6)
            have = sp in p.unlocked
            col = SPELLS[sp]["color"] if have else (70, 70, 80)
            self.draw_spell_icon(s, sp, r.centerx, r.centery - 4, col)
            if have:
                cdmax = SPELLS[sp]["cd"]
                if p.cd[sp] > 0:
                    k = clamp(p.cd[sp] / max(cdmax, 0.01), 0, 1)
                    ov = pygame.Surface((sw, int(sw * k)), pygame.SRCALPHA)
                    ov.fill((0, 0, 0, 170))
                    s.blit(ov, (r.x, r.bottom - int(sw * k)))
                if self.port_lock.get(sp, 0) > 0:
                    ov = pygame.Surface((sw, sw), pygame.SRCALPHA)
                    ov.fill((150, 0, 0, 150))
                    s.blit(ov, r)
                    text(s, "PORT", (r.centerx, r.y + 14), 11, WHITE, "center", bold=True)
                    text(s, "ZU %d" % (int(self.port_lock[sp]) + 1), (r.centerx, r.y + 30), 11, WHITE, "center", bold=True)
            else:
                dl = next((d for d in self.dl_queue if d["unlock"] == sp), None)
                if dl:
                    text(s, "%d%%" % int(100 * dl["done"] / dl["size"]), (r.centerx, r.centery), 13, CYAN, "center", bold=True)
                else:
                    text(s, "---", (r.centerx, r.centery), 13, GREY, "center")
            pygame.draw.rect(s, col, r, 2, border_radius=6)
            text(s, PAD_KEYS[sp] if self.pad_mode() else SPELLS[sp]["key"], (r.centerx, r.bottom - 12), 11, WHITE, "center")
        # Download-Panel
        if self.dl_queue:
            dl = self.dl_queue[0]
            r = pygame.Rect(10, H - 104, 340, 94)
            ps = pygame.Surface(r.size, pygame.SRCALPHA)
            ps.fill((10, 8, 20, 200))
            s.blit(ps, r)
            pygame.draw.rect(s, CYAN, r, 1, border_radius=4)
            text(s, "DOWNLOAD: %s %s" % (dl["name"], dl["ver"]), (r.x + 10, r.y + 6), 13, CYAN, bold=True)
            k = dl["done"] / dl["size"]
            pygame.draw.rect(s, (20, 30, 40), (r.x + 10, r.y + 28, 320, 12))
            pygame.draw.rect(s, CYAN, (r.x + 10, r.y + 28, 320 * k, 12))
            sp = dl.get("speed", 0)
            eta = (dl["size"] - dl["done"]) / sp if sp > 0 else float("inf")
            text(s, "%.0f / %.0f MB   %s" % (dl["done"], dl["size"], fmt_speed(sp)), (r.x + 10, r.y + 46), 12, WHITE)
            text(s, "Restzeit: %s" % fmt_eta(eta) if sp > 0 else "Download pausiert – kein Empfang", (r.x + 10, r.y + 64), 12, GREY if sp > 0 else RED)
            if self.bars <= 1 and sp > 0:
                text(s, "Bitte Zauberstab nicht ausschalten.", (r.x + 10, r.y + 78), 10, (120, 120, 140))
        # Interaktion
        it = getattr(self, "interact_target", None)
        if it is not None:
            msg, need = self.interact_info(it)
            if self.pad_mode():
                msg = msg.replace("[E", "[A")
            x, y = it.x - self.cam_x, it.y - self.cam_y - 70
            text(s, msg, (x, y), 13, YELLOW if need else GREY, "center")
            if need and self.hold > 0 and self.hold_target is it:
                pygame.draw.rect(s, (40, 40, 40), (x - 50, y + 12, 100, 6))
                pygame.draw.rect(s, YELLOW, (x - 50, y + 12, 100 * clamp(self.hold / need, 0, 1), 6))
        # HUD-Feed (max. 3 Zeilen oben)
        self.draw_feed(s)
        # Banner (kurz, oberes Drittel)
        if self.banner:
            title, sub, tl = self.banner
            a = int(255 * clamp(tl * 1.5, 0, 1))
            text(s, sub, (W // 2, 168), 15, CYAN, "center", alpha=a)
            text(s, title, (W // 2, 198), 30, WHITE, "center", bold=True, alpha=a)
        # Werbung
        for ad in self.ads:
            ad.draw(s, self.pad_mode())
        # Fadenkreuz
        mx, my = self.aim_screen()
        c = BAR_COLORS[self.bars]
        pygame.draw.circle(s, c, (mx, my), 9, 1)
        pygame.draw.line(s, c, (mx - 14, my), (mx - 5, my))
        pygame.draw.line(s, c, (mx + 5, my), (mx + 14, my))
        pygame.draw.line(s, c, (mx, my - 14), (mx, my - 5))
        pygame.draw.line(s, c, (mx, my + 5), (mx, my + 14))

    def draw_feed(self, s):
        y = 36
        for tst in self.toasts:
            k_in = clamp(tst["t"] * 8, 0, 1)
            k_out = clamp((tst["life"] - tst["t"]) * 4, 0, 1)
            a = int(255 * k_in * k_out)
            kind = tst["kind"]
            msg = tst["text"]
            if kind == "boss":
                shown = msg[:int(tst["t0"] * 45) + 1]
                msg_draw = "> " + shown + ("_" if int(tst["t0"] * 4) % 2 else " ")
                fsize, bold = 15, False
                tw = font(fsize).size("> " + msg + "_")[0]
            else:
                msg_draw = msg
                fsize, bold = (16, True) if (tst["big"] or kind == "error") else (14, False)
                tw = font(fsize, bold).size(msg)[0]
            r = pygame.Rect(0, 0, tw + 28, fsize + 12)
            r.midtop = (W // 2, y - int((1 - k_in) * 8))
            bg = {"error": (70, 0, 0), "boss": (4, 22, 10)}.get(kind, (12, 10, 24))
            box = pygame.Surface(r.size, pygame.SRCALPHA)
            box.fill(bg + (int(205 * k_in * k_out),))
            s.blit(box, r)
            edge = RED if kind == "error" else GREEN if kind == "boss" else tst["color"]
            pygame.draw.rect(s, mix((0, 0, 0), edge, k_out), (r.x, r.y, 4, r.h))
            text(s, msg_draw, (r.x + 16, r.centery), fsize, tst["color"], "midleft", bold=bold, alpha=a)
            y += r.h + 4

    def draw_spell_icon(self, s, sp, x, y, col):
        if sp == "fire":
            pygame.draw.circle(s, col, (x, y + 3), 10)
            pygame.draw.polygon(s, col, [(x - 9, y), (x, y - 16), (x + 9, y)])
            pygame.draw.circle(s, YELLOW if col != (70, 70, 80) else col, (x, y + 4), 5)
        elif sp == "tp":
            for i in range(3):
                pygame.draw.circle(s, col, (x, y), 5 + i * 5, 2)
        elif sp == "heal":
            pygame.draw.rect(s, col, (x - 4, y - 13, 8, 26))
            pygame.draw.rect(s, col, (x - 13, y - 4, 26, 8))
        elif sp == "chain":
            pygame.draw.lines(s, col, False, [(x - 6, y - 14), (x + 4, y - 3), (x - 4, y + 1), (x + 6, y + 14)], 3)
        elif sp == "meteor":
            pygame.draw.circle(s, col, (x + 4, y + 4), 8)
            for i in range(3):
                pygame.draw.line(s, col, (x - 2 - i * 3, y - 2 + i * 3), (x - 14 - i * 3, y - 14 + i * 3), 2)

    def draw_minimap(self, s):
        dg = self.dungeon
        sc = 2
        mw, mh = dg.tw * sc, dg.th * sc
        r = pygame.Rect(W - mw - 14, 10, mw + 4, mh + 4)
        ps = pygame.Surface(r.size, pygame.SRCALPHA)
        ps.fill((10, 8, 20, 180))
        s.blit(ps, r)
        pygame.draw.rect(s, (80, 70, 140), r, 1)
        ox, oy = r.x + 2, r.y + 2
        visited = {rm.id for rm in dg.rooms if rm.visited}
        for a, b in dg.edges:
            if a in visited or b in visited:
                ra, rb = dg.rooms[a], dg.rooms[b]
                pygame.draw.line(s, (70, 70, 90), (ox + ra.rect.centerx * sc, oy + ra.rect.centery * sc),
                                 (ox + rb.rect.centerx * sc, oy + rb.rect.centery * sc), 1)
        for rm in dg.rooms:
            rr = pygame.Rect(ox + rm.rect.x * sc, oy + rm.rect.y * sc, rm.rect.w * sc, rm.rect.h * sc)
            known = rm.visited or any((rm.id in e and (e[0] in visited or e[1] in visited)) for e in dg.edges)
            if not known:
                continue
            base = THEMES[rm.theme]["base"]
            col = BAR_COLORS[clamp(base, 0, 5)] if rm.visited else (50, 50, 60)
            if rm.kind == "boss":
                col = RED if rm.visited else (110, 30, 30)
            pygame.draw.rect(s, mix(col, (0, 0, 0), 0.55), rr)
            pygame.draw.rect(s, col, rr, 1)
            if rm is self.cur_room:
                pygame.draw.rect(s, WHITE, rr, 1)
        for h in dg.hotspots:
            if h.room.visited:
                s.fill(CYAN if h.power() else (90, 40, 40), (ox + h.x / TILE * sc - 1, oy + h.y / TILE * sc - 1, 3, 3))
        p = self.player
        if int(self.time * 4) % 2:
            pygame.draw.circle(s, WHITE, (int(ox + p.x / TILE * sc), int(oy + p.y / TILE * sc)), 2)

    def draw_ach_popups(self, s):
        for i, a in enumerate(self.ach_popups):
            _, title, desc = ACH_BY_ID[a["aid"]]
            k = clamp(a["t"] * 4, 0, 1) * clamp((3.2 - a["t"]) * 3, 0, 1)
            w = max(380, font(14).size(desc)[0] + 90)
            r = pygame.Rect(W - int((w + 16) * k), H - 190 - i * 84, w, 72)
            pygame.draw.rect(s, (25, 20, 10), r, border_radius=6)
            pygame.draw.rect(s, YELLOW, r, 2, border_radius=6)
            self.draw_trophy(s, r.x + 34, r.centery, YELLOW)
            text(s, "ACHIEVEMENT FREIGESCHALTET", (r.x + 66, r.y + 8), 11, (200, 180, 100))
            text(s, title, (r.x + 66, r.y + 24), 16, YELLOW, bold=True)
            text(s, desc, (r.x + 66, r.y + 46), 12, WHITE)

    def draw_trophy(self, s, x, y, col):
        pygame.draw.polygon(s, col, [(x - 12, y - 16), (x + 12, y - 16), (x + 8, y + 2), (x - 8, y + 2)])
        pygame.draw.circle(s, col, (x - 13, y - 9), 6, 2)
        pygame.draw.circle(s, col, (x + 13, y - 9), 6, 2)
        pygame.draw.rect(s, col, (x - 3, y + 2, 6, 8))
        pygame.draw.rect(s, col, (x - 10, y + 10, 20, 5))

    # ---- Menüs
    def draw_logo(self, s, y):
        t = self.title_t + self.intro_t
        bars = int(t * 2) % 6
        draw_bars(s, W // 2 - 300, y - 20, bars, h=56, w=16, gap=6, blink=True)
        text(s, "Mage.NET", (W // 2 + 30, y + 8), 84, CYAN, "center", bold=True)
        text(s, "TM", (W // 2 + 258, y - 26), 14, CYAN)
        text(s, "Der Magier mit WLAN-Problemen", (W // 2, y + 72), 22, MAGENTA, "center")

    def draw_title(self, s):
        s.fill(DARK)
        for r in self.rain:
            text(s, r[3], (r[0], r[1]), 14, (30, 80, 60), shadow=False)
        self.draw_logo(s, 190)
        t = self.title_t
        lines = [
            "Magie wurde ausgelagert. Zauber werden über die Cloud gestreamt.",
            "Leider liegt der Dungeon des Drachen tief unter der Erde.",
            "Der Empfang dort ist... ausbaufähig.",
        ]
        for i, ln in enumerate(lines):
            text(s, ln, (W // 2, 330 + i * 28), 17, (190, 190, 210), "center")
        if int(t * 2) % 2:
            text(s, "[ENTER / A] Verbindung herstellen", (W // 2, 470), 24, YELLOW, "center", bold=True)
        text(s, "[A-Taste / Pad Y] Achievements     [ESC] Beenden     [M] Ton  [N] Musik", (W // 2, 520), 15, GREY, "center")
        if self.pads.connected:
            text(s, "Gamepad erkannt: %s" % self.pads.name[:40], (W // 2, 600), 14, CYAN, "center")
        else:
            text(s, "Kein Gamepad gefunden – Maus & Tastatur (Gamepad kann jederzeit eingesteckt werden)", (W // 2, 600), 13, (100, 100, 130), "center")
        n = len(self.save.data["unlocked"])
        text(s, "Achievements: %d/%d   ·   Tiefste Etage: %d   ·   Siege: %d" % (n, len(ACHIEVEMENTS), self.save.data.get("best_floor", 0), self.save.data.get("wins", 0)),
             (W // 2, 560), 14, (150, 150, 180), "center")
        text(s, "Bodensee Game Jam 2026 · Thema: Magie", (W // 2, H - 30), 12, (90, 90, 120), "center")

    def draw_achievements(self, s):
        s.fill(DARK)
        text(s, "ACHIEVEMENTS", (W // 2, 40), 34, YELLOW, "center", bold=True)
        c = self.save.data["counters"]
        for i, (aid, title, desc) in enumerate(ACHIEVEMENTS):
            y = 100 + i * 56
            have = self.save.has(aid)
            col = YELLOW if have else (90, 90, 110)
            self.draw_trophy(s, 240, y + 22, col)
            text(s, title, (280, y + 2), 18, col, bold=True)
            extra = ""
            if aid == "404":
                extra = "  (%d/100)" % min(100, c.get("failed", 0))
            elif aid == "chicken":
                extra = "  (%d/10)" % min(10, c.get("chickens", 0))
            elif aid == "tax":
                extra = "  (%d/15)" % min(15, c.get("tax", 0))
            elif aid == "adblock":
                extra = "  (%d/30)" % min(30, c.get("ads", 0))
            text(s, desc + extra, (280, y + 26), 14, WHITE if have else GREY)
        text(s, "Beliebige Taste / A: zurück", (W // 2, H - 30), 14, GREY, "center")

    def draw_intro(self, s):
        s.fill((4, 8, 6))
        t = self.intro_t
        for i, ln in enumerate(INTRO):
            k = t - i * 0.9
            if k <= 0:
                break
            shown = ln[:int(k * 60)]
            col = YELLOW if "NULLPOINTERGON" in ln else GREEN
            text(s, shown, (120, 90 + i * 34), 20, col, shadow=False)
        if t > len(INTRO) * 0.9:
            box = pygame.Rect(120, 420, W - 240, 240)
            pygame.draw.rect(s, (10, 20, 14), box)
            pygame.draw.rect(s, GREEN, box, 1)
            ctr = [
                "WASD bewegen  ·  Maus zielen  ·  LMB Feuerball  ·  RMB/Leertaste Teleport  ·  Q Heilung",
                "R / F  heruntergeladene Zauber  ·  E (halten) Router aktivieren / neu starten / Truhen",
                "Empfang ersetzt Mana: 5 Balken = zuverlässig · 3 = Latenz · 1 = CHAOS · 0 = offline",
                "Router aus- und wieder einschalten erzeugt eine Neustart-Welle, die Bossen schadet.",
                "Werbung mit dem X schließen. Nicht auf JETZT KAUFEN klicken. Wirklich nicht.",
                "GAMEPAD: L-Stick laufen · R-Stick zielen · RT Feuer · LT/LB Teleport · X Heilung",
                "         Y Kettenblitz · B Meteor · A Interagieren · SELECT Werbung zu · START Pause",
            ]
            for i, ln in enumerate(ctr):
                text(s, ln, (box.x + 18, box.y + 14 + i * 30), 15, CYAN if ln.lstrip().startswith(("GAMEPAD", "Y Kette")) else (180, 255, 200), shadow=False)
            if int(t * 2) % 2:
                text(s, "[ENTER / A] Einloggen", (W // 2, H - 30), 20, YELLOW, "center", bold=True)

    def dim(self, s, a=170):
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, a))
        s.blit(ov, (0, 0))

    def draw_pause(self, s):
        self.dim(s)
        text(s, "PAUSE", (W // 2, 200), 48, WHITE, "center", bold=True)
        text(s, "Ihre Sitzung wurde angehalten. Der Drache wartet höflich.", (W // 2, 260), 18, GREY, "center")
        text(s, "[ESC] Weiter     [T] Titel     [M] Ton     [N] Musik", (W // 2, 320), 18, YELLOW, "center")
        text(s, "Gamepad: [START/B] Weiter     [SELECT] Titelbildschirm", (W // 2, 348), 15, CYAN, "center")
        p = self.player
        y = 390
        ups = [(UPGRADES[k][0], v) for k, v in p.up.items() if v]
        text(s, "Upgrades:" if ups else "Noch keine Upgrades.", (W // 2, y), 16, CYAN, "center")
        for i, (n, v) in enumerate(ups):
            text(s, "%s%s" % (n, " x%d" % v if v > 1 else ""), (W // 2, y + 26 + i * 22), 15, WHITE, "center")

    def card_rects(self):
        n = len(self.choices)
        cw, ch = 320, 230
        x0 = W // 2 - (n * cw + (n - 1) * 30) // 2
        return [pygame.Rect(x0 + i * (cw + 30), 260, cw, ch) for i in range(n)]

    def draw_upgrade(self, s):
        self.dim(s, 200)
        text(s, "ETAGE %d ABGESCHLOSSEN" % self.floor, (W // 2, 140), 40, CYAN, "center", bold=True)
        text(s, "Mage.NET Kundenservice bietet Ihnen ein Upgrade an. Wählen Sie weise.", (W // 2, 196), 17, GREY, "center")
        text(s, "Maus / 1-3 / Pfeiltasten + ENTER / Steuerkreuz + A", (W // 2, 530), 15, GREY, "center")
        mpos = pygame.mouse.get_pos()
        for i, (k, r) in enumerate(zip(self.choices, self.card_rects())):
            if r.collidepoint(mpos) and not self.pad_mode():
                self.card_sel = i
            hov = i == self.card_sel
            pygame.draw.rect(s, (30, 26, 50) if not hov else (50, 40, 90), r, border_radius=10)
            pygame.draw.rect(s, YELLOW if hov else PURPLE, r, 2, border_radius=10)
            name, desc, mx = UPGRADES[k]
            text(s, "[%d]" % (i + 1), (r.x + 14, r.y + 12), 14, GREY)
            self.draw_upgrade_icon(s, k, r.centerx, r.y + 70)
            text(s, name, (r.centerx, r.y + 120), 17, YELLOW, "midtop", bold=True)
            words = desc.split()
            line, lines = "", []
            for w_ in words:
                if font(15).size(line + " " + w_)[0] > r.w - 30:
                    lines.append(line)
                    line = w_
                else:
                    line = (line + " " + w_).strip()
            lines.append(line)
            for j, ln in enumerate(lines):
                text(s, ln, (r.centerx, r.y + 152 + j * 22), 15, WHITE, "midtop")
            if self.player.up[k]:
                text(s, "Stufe %d/%d" % (self.player.up[k], mx), (r.centerx, r.bottom - 22), 12, GREY, "midtop")

    def draw_upgrade_icon(self, s, k, x, y):
        draw_glow(s, x, y, PURPLE, 60)
        if k == "hat":
            pygame.draw.polygon(s, (70, 40, 170), [(x - 30, y + 18), (x + 30, y + 18), (x + 6, y - 32)])
            pygame.draw.line(s, GREY, (x + 6, y - 32), (x + 12, y - 46), 2)
            draw_bars(s, x - 26, y - 4, 5, h=18, w=5, gap=2)
        elif k == "staff":
            pygame.draw.line(s, (240, 200, 60), (x - 24, y + 28), (x + 18, y - 22), 5)
            pygame.draw.circle(s, CYAN, (x + 20, y - 25), 7)
        elif k == "premium" or k == "flat":
            text(s, "PRO" if k == "premium" else "+30%", (x, y), 28, YELLOW, "center", bold=True)
        elif k == "robe":
            pygame.draw.polygon(s, (90, 60, 200), [(x - 26, y + 28), (x, y - 28), (x + 26, y + 28)])
            for i in range(4):
                pygame.draw.line(s, CYAN, (x - 16 + i * 10, y + 26), (x - 4 + i * 3, y - 10), 1)
        elif k == "boots":
            pygame.draw.ellipse(s, (200, 120, 200), (x - 28, y, 40, 22))
            pygame.draw.line(s, GREY, (x + 10, y + 10), (x + 30, y - 10), 2)
            pygame.draw.rect(s, WHITE, (x + 26, y - 18, 10, 10))
        elif k == "booster":
            pygame.draw.polygon(s, CYAN, [(x - 14, y - 26), (x + 14, y - 26), (x + 14, y), (x + 26, y), (x, y + 28), (x - 26, y), (x - 14, y)])
        elif k == "cache":
            pygame.draw.circle(s, YELLOW, (x, y), 22, 3)
            pygame.draw.circle(s, CYAN, (x, y), 12)
            pygame.draw.line(s, YELLOW, (x, y - 22), (x, y - 36), 2)
        elif k == "adblock":
            pygame.draw.circle(s, WHITE, (x - 14, y), 12, 3)
            pygame.draw.circle(s, WHITE, (x + 14, y), 12, 3)
            pygame.draw.line(s, RED, (x - 28, y - 22), (x + 28, y + 22), 4)
        elif k == "mesh":
            for i in range(5):
                for j in range(3):
                    pygame.draw.circle(s, CYAN, (x - 24 + i * 12, y - 12 + j * 12), 3)
            pygame.draw.line(s, CYAN, (x - 24, y - 12), (x + 24, y + 12), 1)
            pygame.draw.line(s, CYAN, (x - 24, y + 12), (x + 24, y - 12), 1)
        elif k == "coffee":
            pygame.draw.rect(s, (160, 100, 60), (x - 16, y - 12, 32, 34), border_radius=4)
            pygame.draw.circle(s, (160, 100, 60), (x + 20, y + 4), 8, 3)
            for i in range(3):
                pygame.draw.arc(s, WHITE, (x - 12 + i * 8, y - 34, 8, 18), 1.0, 4.0, 2)

    def draw_gameover(self, s):
        self.dim(s, 200)
        text(s, "VERBINDUNG ZUM LEBEN GETRENNT", (W // 2, 170), 42, RED, "center", bold=True)
        text(s, "Getötet von: %s" % getattr(self, "killed_by", "?"), (W // 2, 230), 20, WHITE, "center")
        self.draw_stats(s, 290)
        text(s, "[ENTER / A] Neu verbinden     [ESC / B] Titelbildschirm", (W // 2, H - 80), 20, YELLOW, "center", bold=True)

    def draw_victory(self, s):
        self.dim(s, 200)
        text(s, "NullPointergon.exe wurde erfolgreich deinstalliert.", (W // 2, 160), 32, GREEN, "center", bold=True)
        text(s, "Das Königreich hat wieder 5 Balken. Mage.NET dankt für Ihre Geduld.", (W // 2, 214), 19, WHITE, "center")
        self.draw_stats(s, 280)
        text(s, "[ENTER / A] Neues Abenteuer     [ESC / B] Titelbildschirm", (W // 2, H - 80), 20, YELLOW, "center", bold=True)

    def draw_stats(self, s, y):
        st = self.stats
        rows = [
            ("Erreichte Etage", "%d" % self.floor),
            ("Spielzeit", fmt_eta(st["time"])),
            ("Zauber gewirkt", "%d" % st["casts"]),
            ("Fehlgeschlagene Zauber", "%d" % st["failed"]),
            ("Chaos-Zauber", "%d" % st["chaos"]),
            ("Beschworene Hühner", "%d" % st["chickens"]),
            ("Werbung geschlossen", "%d" % st["ads"]),
            ("Besiegte Gegner", "%d" % st["kills"]),
        ]
        for i, (a, b) in enumerate(rows):
            text(s, a, (W // 2 - 20, y + i * 30), 18, GREY, "topright")
            text(s, b, (W // 2 + 20, y + i * 30), 18, WHITE, "topleft", bold=True)

    # ---------------------------------------------------------------- Loop
    def run(self):
        while True:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            for ev in pygame.event.get():
                self.handle_event(ev)
            self.update(dt)
            self.draw()
            pygame.display.flip()


INTRO = [
    "> In einer modernen Fantasywelt wurde Magie ausgelagert.",
    "> Niemand lernt mehr Zauber selbst. Sie werden über die",
    "  magische Cloud Mage.NET(TM) gestreamt.",
    "> Leider haust das größte Übel der Welt tief unter der Erde...",
    "  ...wo der Empfang absolut miserabel ist.",
    "> Der dunkle Drache NULLPOINTERGON bedroht das Königreich.",
    "> Alle anderen Helden scheiterten. Nicht am Drachen -",
    "  sondern an schlechter Verbindung.",
    "> Du bist der letzte verfügbare Magier. Verbindung wird hergestellt...",
]


def main():
    random.seed()
    Game().run()


if __name__ == "__main__":
    main()
