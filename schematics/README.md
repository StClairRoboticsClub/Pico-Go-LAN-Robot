# Schematics & Wiring Diagrams

## 📐 Future Content

This directory will contain:

- Circuit diagrams
- Wiring schematics
- PCB layouts (if designed)
- 3D CAD models
- Assembly diagrams

## 🔌 Quick Pin Reference

For detailed pin assignments, see [../docs/HARDWARE.md](../docs/HARDWARE.md)

### Motor Driver (TB6612FNG)
```
GP0 → PWMA    GP3 → PWMB
GP1 → AIN1    GP4 → BIN1
GP2 → AIN2    GP5 → BIN2
GP6 → STBY
```

### LCD (ST7789)
```
GP18 → SCK     GP20 → RST
GP19 → MOSI    GP17 → CS
GP16 → DC      GP21 → BL
```

### Power
```
7.4V Battery → 5V Regulator → Pico VSYS
7.4V Battery → Motor Driver VM
```

## 📊 Future Additions

Contributions welcome! We're looking for:
- KiCad schematics
- Fritzing diagrams
- Custom PCB designs
- 3D printed enclosures
- Mounting brackets

## 📸 Photos

Assembly photos and build documentation will be added as the project progresses.

---

For now, refer to:
- [Waveshare Pico-Go Wiki](https://www.waveshare.com/wiki/Pico-Go)
- [Hardware Documentation](../docs/HARDWARE.md)
