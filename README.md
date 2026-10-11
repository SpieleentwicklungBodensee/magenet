# 📶🔮 Mage.NET – Der Magier mit WLAN-Problemen

Bodensee Game Jam 2026 · Thema **Magie** · Roguelite-Dungeon-Crawler + Comedy (Top-Down 2D, pygame)

Magie wurde in die Cloud ausgelagert. Dummerweise haust der Drache **NullPointergon** tief unter der Erde – wo der Empfang miserabel ist.

## Starten

```bash
pip install -r requirements.txt
python3 mage_net.py
```

Keine Assets nötig – Grafik und Sound werden prozedural erzeugt. Fenster ist frei skalierbar.

## Steuerung

| Taste | Aktion |
|---|---|
| WASD / Pfeile | Bewegen |
| Maus | Zielen |
| Linke Maustaste (halten) | Feuerball |
| Rechte Maustaste / Leertaste | Teleport |
| Q | Heilung |
| R / F | Heruntergeladene Zauber (Kettenblitz / Meteor) |
| E (halten) | Router/Funkmast/Schüssel verbinden, Router **aus- und wieder einschalten**, Truhen öffnen |
| ESC | Pause · M Ton an/aus · N Musik an/aus · F10 Etage überspringen (Demo-Cheat) |

### Gamepad (Xbox / PlayStation / Switch Pro – Hot-Plug, Rumble)

| Taste | Aktion |
|---|---|
| Linker Stick / Steuerkreuz | Bewegen (analog) |
| Rechter Stick | Zielen (Twin-Stick, leichte Zielhilfe); ohne rechten Stick wird in Laufrichtung gezielt |
| RT / RB (halten) | Feuerball |
| LT / LB | Teleport |
| X · Y · B | Heilung · Kettenblitz · Meteor |
| A (halten) | Interagieren (Router, Truhen) · in Menüs: bestätigen |
| SELECT / View / Share | Oberstes Werbefenster schließen |
| START | Pause |

Maus bewegen schaltet automatisch zurück auf Maus-Zielen. Die Tastenhinweise im HUD passen sich dem aktiven Eingabegerät an.

## Kernmechanik: Empfang statt Mana

| Balken | Effekt |
|---|---|
| 5 | Alles funktioniert. Langweilig, aber zuverlässig. |
| 4 | Minimale Latenz |
| 3 | Zauber kommen 0,4–1,1 s später an, Projektile ruckeln, Cooldowns werden ungenau |
| 2 | Noch mehr Lag, 20 % Chaos-Chance |
| 1 | **Chaos:** Feuerball → Eisball / Huhn / Bürostuhl / Mini-Sonne / Steuerformular; Teleport → du / Gegner / Tausch / zufälliger Pilz; Heilung → heilt Gegner, Hühnersuppe, Abo-Falle … |
| 0 | `ERROR 404: FEUERBALL NICHT GEFUNDEN` – Zauber landen in der **Warteschlange** und feuern alle auf einmal, sobald das Netz zurück ist |

Der Empfang hängt vom Raum ab (Kristallraum 5 → Drachenhöhle 0, Gänge mit dicken Steinwänden 1–2), plus aktivierte Hotspots (Router +3, Funkmast +2, Satellitenschüssel +2 mit großer Reichweite), zufällige Störungen und **Funkloch-Fledermäuse** (−1 pro Fledermaus in der Nähe).

**Router neu starten** (E halten an einem aktiven Router): 2,5 s kein Signal, danach eine Neustart-Welle, die Gegnern und Bossen (durch Schilde hindurch!) heftig schadet, plus 8 s Turbo-Signal.

## Inhalte

- **3 Etagen**, prozedural generiert, jeweils mit Bossraum
- **Gegner:** Paketverlust-Schleim, Lag-Goblin (bewegt sich ruckelnd), Funkloch-Fledermaus (Störsender), Spam-Bot (Spam-Mails öffnen Werbung)
- **Bosse**
  - *Firewall-Wächter* – Schild verschluckt Pakete von vorne, sperrt Ports, drosselt auf 56k
  - *Router-Lich* – ändert WLAN-Passwörter (Router neu verbinden!), trennt dich vom Netz, VPN-Schild solange er die Router kontrolliert
  - *NullPointergon* – Cloud-Schild bis seine Server zerstört sind, „Sie sind Position 847 in der Warteschlange“, „Bitte warten…“
- **Zauber-Downloads** im Hintergrund: Kettenblitz v1.3 (250 MB), Meteor v2.0 (800 MB), Patch v1.0.1 – Geschwindigkeit hängt vom Empfang ab (bei 1 Balken: 4 KB/s, Restzeit: 17 Stunden)
- **Werbe-Popups** beim Zaubern – mit dem X schließen, nicht auf „JETZT KAUFEN“ klicken
- **Upgrades** (Truhen + nach jedem Boss): Empfangsverstärker-Hut, Vergoldeter Routerstab, Premium-Abonnement, Offline-Cache-Amulett, Adblocker-Brille, Mesh-Mantel … · Pickup *Mage.NET Premium+* = 30 s werbefrei
- **10 Achievements** (dauerhaft gespeichert in `mage_net_save.json`), u. a. „Hast du es aus- und wieder eingeschaltet?“, „Lag Wizard“, „Offline Hero“, „404 Magic Not Found“

## 🎵 Soundtrack (C64/SID-Stil)

Komponiert in `mage_music.py` und beim Start prozedural synthetisiert – drei SID-artige Stimmen (Pulse-Lead mit PWM, Vibrato und Echo · Saw/Pulse-Bass · 50-Hz-Akkord-Arpeggio wie auf dem C64) plus Rauschen-Drums.

| Track | Wann | Stil |
|---|---|---|
| Title | Titel, Intro, Achievements | a-Moll, 132 BPM, heroisch |
| Dungeon | beim Erkunden | d-Moll, 112 BPM, düsterer Half-Time-Groove |
| Boss | Bosskämpfe | e-Moll/phrygisch, 158 BPM, Four-on-the-floor |
| Victory / Game Over | Jingles | einmalig |

**Gimmick:** Die Musik ist ein *Stream* und hängt am Empfang – bei 3 Balken gelegentliche Hänger, bei 1 Balken ruckelt sie ständig, offline pausiert sie („MUSIK PUFFERT...“) und läuft nach dem Reconnect weiter.

Erster Start: Rendern dauert ~3 s im Hintergrund, Ergebnis landet in `music_cache/` (danach sofort da). Nach Änderungen an den Noten `MUSIC_VERSION` in `mage_music.py` erhöhen. `N` schaltet nur die Musik stumm, `M` alles.

Noten editieren: In `SONGS` steht pro Takt ein String wie `"A4:4 C5:2 E5:2 A5:4 G5:2 E5:2"` (Note:Länge in Sechzehnteln, `R` = Pause, Summe = 16) plus ein Akkord pro Takt und 16-stellige Patterns für Bass/Kick/Snare/Hi-Hat.

## Code-Überblick (`mage_net.py`)

Eine Datei, gegliedert in Abschnitte: Konstanten/Balancing-Tabellen oben (`THEMES`, `ENEMY_STATS`, `PROJ`, `UPGRADES`, Texte) → `SoundBank` (Synth) → `Dungeon` (Generierung + Kollision) → Entitäten → Boss-Klassen → `Game` (Signal, Zaubern, Kampf, Räume, Zeichnen, Menüs). Balancing lässt sich fast komplett über die Tabellen oben anpassen.
