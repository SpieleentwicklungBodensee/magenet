# -*- coding: utf-8 -*-
"""
Mage.NET – C64/SID-Soundtrack
=============================

Komplett prozedural: ein kleiner "Tracker" mit drei SID-artigen Stimmen
(Pulse-Lead mit PWM + Vibrato + Echo, Saw/Pulse-Bass, 50-Hz-Akkord-Arpeggio)
plus Rauschen-Drums. Die Songs stehen unten als Noten in `SONGS` – zum
Umkomponieren einfach dort editieren (jeder Takt = 16 Sechzehntel).

Beim ersten Start werden die Stücke im Hintergrund gerendert und als WAV in
`music_cache/` abgelegt; danach starten sie sofort.

Gimmick: Die Musik ist ein "Stream" – bei schlechtem Empfang ruckelt sie,
offline puffert sie (Pause), genau wie die Zauber.
"""
import array
import math
import os
import random
import threading
import wave

import pygame

MUSIC_VERSION = 2
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "music_cache")

# --------------------------------------------------------------------------- Kompositionen
# Notation: "Note:Länge" in Sechzehnteln, R = Pause. Akkorde: ein Akkord pro Takt.
SONGS = {
    # Titel: heroisch, a-Moll, klassischer C64-Intro-Vibe
    "title": dict(
        bpm=132, loop=True, arp_gate=2,
        chords="Am F C G Am F E E F G Em Am Dm G E E",
        lead=[
            "A4:4 C5:2 E5:2 A5:4 G5:2 E5:2",
            "F5:6 E5:2 C5:4 A4:4",
            "G4:4 C5:2 E5:2 G5:6 E5:2",
            "D5:4 B4:2 G4:2 D5:8",
            "A4:4 C5:2 E5:2 A5:4 B5:2 C6:2",
            "C6:4 A5:2 F5:2 A5:4 C6:4",
            "B5:6 G#5:2 E5:4 D5:4",
            "E5:12 R:4",
            "A5:2 C6:2 A5:2 F5:2 A5:4 C6:4",
            "B5:2 D6:2 B5:2 G5:2 B5:4 D6:4",
            "E6:6 D6:2 B5:4 G5:4",
            "A5:8 E5:4 A5:4",
            "F5:4 A5:2 D6:2 F6:4 E6:2 D6:2",
            "D6:4 B5:2 G5:2 B5:4 D6:4",
            "E6:4 D6:2 B5:2 G#5:4 B5:4",
            "E5:8 G#5:4 B5:4",
        ],
        bass="r.r.o.r.r.o.r.o.",
        kick="x.......x.x.....", snare="....x.......x...", hat="..x...x...x...x.",
    ),
    # Dungeon: düster, d-Moll, half-time Groove, viel Arpeggio
    "dungeon": dict(
        bpm=112, loop=True, arp_gate=4,
        chords="Dm Dm Bb Bb Gm Gm A A Dm C Bb A Gm Bb A A",
        lead=[
            "D5:6 F5:2 A5:4 G5:2 F5:2",
            "E5:8 D5:4 R:4",
            "D5:6 F5:2 Bb5:4 A5:2 G5:2",
            "F5:12 R:4",
            "G5:4 Bb5:4 D6:6 C6:2",
            "Bb5:4 A5:4 G5:8",
            "A5:6 G5:2 E5:4 C#5:4",
            "A4:12 R:4",
            "A5:4 F5:2 D5:2 A5:4 D6:4",
            "C6:6 Bb5:2 G5:4 E5:4",
            "F5:4 G5:2 A5:2 Bb5:4 A5:2 G5:2",
            "A5:8 E5:4 C#5:4",
            "D5:4 G5:4 Bb5:4 A5:2 G5:2",
            "F5:4 D5:4 F5:4 Bb5:4",
            "A5:4 G5:2 F5:2 E5:4 C#5:4",
            "D5:12 R:4",
        ],
        lead_vol=0.2,
        bass="r.....o.r...f.o.",
        kick="x.........x.....", snare="........x.......", hat="x...x...x...x.x.",
    ),
    # Boss: schnell, e-Moll/phrygisch, Four-on-the-floor
    "boss": dict(
        bpm=158, loop=True, arp_gate=1,
        chords="Em Em C D Em Em F B Am B C B Am C B B",
        lead=[
            "E5:2 E5:2 G5:2 E5:2 B5:4 A5:2 G5:2",
            "F#5:2 G5:2 A5:2 B5:2 E6:8",
            "E6:2 D6:2 C6:2 B5:2 C6:4 G5:4",
            "F#5:2 A5:2 D6:4 C6:2 B5:2 A5:4",
            "E5:2 G5:2 B5:2 E6:2 D6:2 B5:2 G5:2 B5:2",
            "E6:4 F#6:4 G6:8",
            "F6:4 E6:2 C6:2 A5:4 F5:4",
            "D#6:4 B5:4 F#5:4 D#5:4",
            "A5:2 C6:2 E6:2 C6:2 A5:2 C6:2 E6:4",
            "D#6:2 F#6:2 B6:2 F#6:2 D#6:4 B5:4",
            "C6:4 E6:4 G6:6 E6:2",
            "F#6:4 D#6:4 B5:8",
            "A5:2 B5:2 C6:2 D6:2 E6:4 A6:4",
            "G6:4 E6:2 C6:2 G5:4 C6:4",
            "B5:2 C6:2 B5:2 A5:2 G5:2 F#5:2 D#5:4",
            "B4:8 R:8",
        ],
        lead_vol=0.21,
        bass="rrorrrorrrorrofo",
        bass_gate=1,
        kick="x...x...x...x...", snare="....x.......x..x", hat="x.x.x.x.x.x.x.x.",
    ),
    # Jingles (laufen einmal)
    "victory": dict(
        bpm=140, loop=False, arp_gate=2,
        chords="C F G C",
        lead=[
            "C5:2 E5:2 G5:2 C6:6 B5:2 C6:2",
            "A5:4 C6:4 F6:8",
            "G5:2 B5:2 D6:2 G6:6 F6:2 D6:2",
            "E6:4 C6:12",
        ],
        bass="r...o...r...o...",
        kick="x.......x.......", snare="....x.......x...", hat="..x...x...x...x.",
        tail=1.5,
    ),
    "gameover": dict(
        bpm=84, loop=False, arp_gate=4,
        chords="Am Dm E Am",
        lead=[
            "E5:4 D5:4 C5:4 B4:4",
            "A4:4 C5:4 F5:8",
            "E5:4 G#4:4 B4:8",
            "A4:16",
        ],
        bass="r.......r.......",
        kick="................", snare="................", hat="................",
        tail=1.5,
    ),
}
RENDER_ORDER = ["title", "dungeon", "boss", "gameover", "victory"]

_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def note_midi(n):
    pc = _PC[n[0]]
    i = 1
    if n[i] == "#":
        pc += 1
        i += 1
    elif n[i] == "b":
        pc -= 1
        i += 1
    return 12 * (int(n[i:]) + 1) + pc


def midi_hz(m):
    return 440.0 * 2 ** ((m - 69) / 12.0)


def chord(ch):
    pc = _PC[ch[0]]
    i = 1
    if len(ch) > 1 and ch[1] == "#":
        pc += 1
        i += 1
    elif len(ch) > 1 and ch[1] == "b":
        pc -= 1
        i += 1
    minor = ch[i:] == "m"
    return pc % 12, (0, 3 if minor else 4, 7)


# --------------------------------------------------------------------------- Synthesizer
class SIDSynth:
    def __init__(self, rate):
        self.rate = rate
        rnd = random.Random(6581)  # deterministisch (SID-Chip 6581 :)
        R = rate
        # Drum-Samples vorberechnen
        n = int(0.13 * R)
        kick, ph = [], 0.0
        for i in range(n):
            t = i / n
            f = 45 + 110 * (1 - t) ** 3
            ph += f / R
            v = math.sin(2 * math.pi * ph) * (1 - t) ** 2
            if i < R * 0.003:
                v += rnd.uniform(-0.6, 0.6)
            kick.append(v)
        n = int(0.15 * R)
        snare, held = [], 0.0
        for i in range(n):
            t = i / n
            if i % 2 == 0:
                held = rnd.uniform(-1, 1)
            tri = 4 * abs((i * 190 / R) % 1.0 - 0.5) - 1
            snare.append(held * 0.8 * (1 - t) ** 3 + tri * 0.4 * (1 - t) ** 5)
        n = int(0.04 * R)
        hat, last = [], 0.0
        for i in range(n):
            t = i / n
            x = rnd.uniform(-1, 1)
            hat.append((x - last) * 0.5 * (1 - t) ** 4)
            last = x
        self.drums = {"k": kick, "s": snare, "h": hat}

    # ---- Stimmen
    def lead(self, buf, start, n, f, vol):
        R = self.rate
        att, dec, sus, rel = int(0.004 * R) + 1, int(0.12 * R) + 1, 0.65, int(0.06 * R) + 1
        end = min(len(buf), start + n + rel)
        ph, inc0 = 0.0, f / R
        inc, duty = inc0, 0.5
        vd = int(0.15 * R)
        tw = 2 * math.pi / R
        for i in range(end - start):
            if i & 63 == 0:
                duty = 0.32 + 0.16 * math.sin(i * tw * 2.7)
                inc = inc0 * (1 + 0.007 * math.sin(i * tw * 5.5)) if i > vd else inc0
            if i < att:
                e = i / att
            elif i < att + dec:
                e = 1 - (1 - sus) * (i - att) / dec
            elif i < n:
                e = sus
            else:
                e = sus * (1 - (i - n) / rel)
            ph += inc
            # mittelwertfreier Puls (kein DC -> keine Klicks)
            buf[start + i] += (vol * 2 * (1 - duty) if ph % 1.0 < duty else -vol * 2 * duty) * e

    def bass(self, buf, start, n, f, vol):
        R = self.rate
        att, dec, sus, rel = int(0.002 * R) + 1, int(0.09 * R) + 1, 0.45, int(0.03 * R) + 1
        end = min(len(buf), start + n + rel)
        ph, inc = 0.0, f / R
        for i in range(end - start):
            if i < att:
                e = i / att
            elif i < att + dec:
                e = 1 - (1 - sus) * (i - att) / dec
            elif i < n:
                e = sus
            else:
                e = sus * (1 - (i - n) / rel)
            ph += inc
            p = ph % 1.0
            v = (2 * p - 1) * 0.6 + (0.4 if p < 0.5 else -0.4)
            buf[start + i] += v * vol * e

    def arp(self, buf, start, n, freqs, vol):
        R = self.rate
        att, dec, sus, rel = int(0.001 * R) + 1, int(0.07 * R) + 1, 0.4, int(0.03 * R) + 1
        end = min(len(buf), start + n + rel)
        incs = [f / R for f in freqs]
        per = int(R / 50)  # PAL-Frame-Takt wie auf dem C64
        hi, lo = vol * 1.5, -vol * 0.5
        k = len(incs)
        ph = 0.0
        for i in range(end - start):
            if i < att:
                e = i / att
            elif i < att + dec:
                e = 1 - (1 - sus) * (i - att) / dec
            elif i < n:
                e = sus
            else:
                e = sus * (1 - (i - n) / rel)
            ph += incs[(i // per) % k]
            buf[start + i] += (hi if ph % 1.0 < 0.25 else lo) * e

    def hit(self, buf, start, kind, vol):
        smp = self.drums[kind]
        end = min(len(buf), start + len(smp))
        if end > start:
            buf[start:end] = [a + b * vol for a, b in zip(buf[start:end], smp)]

    # ---- Song rendern -> PCM-Bytes (int16, interleaved)
    def render(self, song, channels=1):
        R = self.rate
        step = 60.0 / song["bpm"] / 4 * R
        chords = song["chords"].split()
        bars = len(chords)
        tail = int(song.get("tail", 0) * R)
        N = int(bars * 16 * step) + tail
        pad = int(0.5 * R)  # Platz für Ausklingen über das Ende hinaus
        S = lambda st: int(round(st * step))
        mix = [0.0] * (N + pad)
        lead = [0.0] * (N + pad)
        lv = song.get("lead_vol", 0.24)
        for b, bar in enumerate(song["lead"]):
            pos = b * 16
            for tok in bar.split():
                nm, ln = tok.split(":")
                ln = int(ln)
                if nm != "R":
                    self.lead(lead, S(pos), S(pos + ln) - S(pos), midi_hz(note_midi(nm)), lv)
                pos += ln
        bg = song.get("bass_gate", 2)
        ag = song.get("arp_gate", 2)
        for b, chname in enumerate(chords):
            pc, iv = chord(chname)
            base = b * 16
            broot = 36 + pc
            for j, c in enumerate(song["bass"]):
                if c in "rof":
                    m = broot + {"r": 0, "o": 12, "f": 7}[c]
                    self.bass(mix, S(base + j), S(base + j + bg) - S(base + j) - int(0.01 * R), midi_hz(m), 0.26)
            aroot = 60 + pc
            if aroot > 66:
                aroot -= 12
            freqs = [midi_hz(aroot + x) for x in iv]
            for j in range(0, 16, ag):
                self.arp(mix, S(base + j), S(base + j + ag) - S(base + j), freqs, 0.085)
            fill = song.get("loop") and b % 8 == 7
            for j in range(16):
                if song["kick"][j] == "x":
                    self.hit(mix, S(base + j), "k", 0.42)
                if song["snare"][j] == "x" or (fill and j >= 12):
                    self.hit(mix, S(base + j), "s", 0.26)
                if song["hat"][j] == "x":
                    self.hit(mix, S(base + j), "h", 0.22)
        if song.get("loop"):  # Ausklingen an den Anfang wickeln -> nahtloser Loop
            for buf in (mix, lead):
                for i in range(pad):
                    buf[i] += buf[N + i]
        del mix[N:]
        del lead[N:]
        d = S(3)  # Echo (punktierte Achtel), wrappt für nahtlosen Loop
        if song.get("loop"):
            out = [m + l + 0.28 * lead[i - d] for i, (m, l) in enumerate(zip(mix, lead))]
        else:
            out = [m + l + (0.28 * lead[i - d] if i >= d else 0.0) for i, (m, l) in enumerate(zip(mix, lead))]
        mean = sum(out) / len(out)
        out = [x - mean for x in out]
        peak = max(1e-6, max(out), -min(out))
        g = 0.88 * 32767 / peak
        ints = [int(x * g) for x in out]
        if channels == 2:
            ints = [v for x in ints for v in (x, x)]
        elif channels > 2:
            ints = [v for x in ints for v in [x] * channels]
        return array.array("h", ints).tobytes()


# --------------------------------------------------------------------------- Player
class MusicPlayer:
    """Spielt die Tracks auf zwei reservierten Kanälen mit Crossfade.
    update(want, bars) koppelt die Wiedergabe an den Empfang."""

    def __init__(self, volume=0.42):
        self.ok = False
        self.sounds = {}
        self._pcm = {}
        self.track = None
        self.volume = volume
        self.muted = False
        self.paused = False
        self.hiccup_t = 3.0
        self.hiccup_dur = 0.0
        self.buffering = False
        try:
            init = pygame.mixer.get_init()
            if not init or init[1] != -16:
                return
            self.rate, _, self.channels = init
            pygame.mixer.set_reserved(2)
            self.chans = [pygame.mixer.Channel(0), pygame.mixer.Channel(1)]
            self.cur = 0
        except Exception:
            return
        self.ok = True
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    def _cache_path(self, name):
        return os.path.join(CACHE_DIR, "%s_v%d_%d_%dch.wav" % (name, MUSIC_VERSION, self.rate, self.channels))

    def _worker(self):
        synth = None
        for name in RENDER_ORDER:
            try:
                path = self._cache_path(name)
                data = None
                if os.path.exists(path):
                    try:
                        with wave.open(path, "rb") as w:
                            if w.getframerate() == self.rate and w.getnchannels() == self.channels and w.getsampwidth() == 2:
                                data = w.readframes(w.getnframes())
                    except Exception:
                        data = None
                if data is None:
                    if synth is None:
                        synth = SIDSynth(self.rate)
                    data = synth.render(SONGS[name], self.channels)
                    try:
                        os.makedirs(CACHE_DIR, exist_ok=True)
                        with wave.open(path, "wb") as w:
                            w.setnchannels(self.channels)
                            w.setsampwidth(2)
                            w.setframerate(self.rate)
                            w.writeframes(data)
                    except Exception:
                        pass
                self._pcm[name] = data
            except Exception:
                continue

    def _chan(self):
        return self.chans[self.cur]

    def update(self, dt, want, bars=5, glitch=False, duck=1.0, muted=False):
        if not self.ok:
            return
        for name in list(self._pcm):
            if name not in self.sounds:
                try:
                    self.sounds[name] = pygame.mixer.Sound(buffer=self._pcm.pop(name))
                except Exception:
                    self._pcm.pop(name, None)
        if want != self.track and want in self.sounds:
            try:
                old = self._chan()
                if self.paused:
                    old.unpause()
                old.fadeout(600)
                self.cur ^= 1
                ch = self._chan()
                ch.stop()
                ch.set_volume(0 if muted else self.volume * duck)
                ch.play(self.sounds[want], loops=-1 if SONGS[want].get("loop") else 0, fade_ms=500)
            except Exception:
                pass
            self.track = want
            self.paused = False
        ch = self._chan()
        # Streaming-Gimmick: Musik hängt am Empfang
        pause = False
        self.buffering = False
        if glitch:
            if bars <= 0:
                pause = True
                self.buffering = True
            else:
                self.hiccup_t -= dt
                if self.hiccup_dur > 0:
                    self.hiccup_dur -= dt
                    pause = True
                elif self.hiccup_t <= 0:
                    if bars <= 3:
                        lo, hi = {3: (4.0, 8.0), 2: (1.5, 3.0), 1: (0.35, 1.0)}[bars]
                        self.hiccup_t = random.uniform(lo, hi)
                        self.hiccup_dur = random.uniform(0.06, 0.14) if bars == 3 else random.uniform(0.08, 0.3)
                    else:
                        self.hiccup_t = 2.0
        try:
            if pause != self.paused:
                if pause:
                    ch.pause()
                else:
                    ch.unpause()
                self.paused = pause
            ch.set_volume(0 if muted else self.volume * duck)
        except Exception:
            pass
