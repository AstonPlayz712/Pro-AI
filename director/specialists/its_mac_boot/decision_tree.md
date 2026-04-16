# ITS.mac_boot — Diagnostic Decision Tree
## MacBook Pro 2010 (A1278 13-inch / A1286 15-inch)

This document describes the human-readable diagnostic flow implemented
in `agent.py`. Follow the branches in order; the first matching terminal
node is the recommended action.

---

```
START: MacBook Pro 2010 won't boot
│
├─► Q1: What do you see on screen at power-on?
│   │
│   ├─► [A] Flashing folder with question mark  ──────────────────► P001 (SATA Cable — Classic)
│   │                                                                 → Boot to external USB
│   │                                                                 → If boots: replace SATA cable
│   │                                                                 → Part: 821-0814-A (13") / 821-1226-A (15")
│   │
│   ├─► [B] Circle with a slash (Prohibitory symbol) ────────────► P003 (OS Corruption)
│   │                                                                 → Boot Recovery (Cmd+R)
│   │                                                                 → Run Disk Utility → First Aid
│   │                                                                 → Reinstall macOS if disk is OK
│   │                                                                 → If disk errors persist → replace cable
│   │
│   ├─► [C] Spinning globe / Apple logo then hang ───────────────► P004 (EFI Fallback)
│   │                                                                 → Allow Internet Recovery to load
│   │                                                                 → Check Disk Utility for drive
│   │                                                                 → Drive missing → replace SATA cable
│   │                                                                 → Drive present but blank → reinstall macOS
│   │
│   ├─► [D] "You need to restart" / grey panic screen ───────────► P002 (Kernel Panic / AHCI)
│   │         │
│   │         └─► Q2: Are panics reproducible? (under load / heat?)
│   │             │
│   │             ├─► YES → Likely SATA cable intermittent failure
│   │             │         → Check /var/log/system.log for AppleAHCIPort
│   │             │         → Replace SATA cable
│   │             │
│   │             └─► NO  → Run Apple Diagnostics (D at boot)
│   │                       → Hardware error → see Q3
│   │                       → No error → may be software; reinstall macOS
│   │
│   └─► [E] Black screen, powers on (fan spins, no display) ─────► Not SATA cable
│                                                                     → Check RAM seating
│                                                                     → Test with one RAM stick
│                                                                     → GPU failure (15" dGPU)
│
├─► Q3: Do you hear clicking or grinding during boot?
│   │
│   ├─► YES ──────────────────────────────────────────────────────► P005 (HDD Mechanical Failure — CRITICAL)
│   │         STOP: do not power cycle further
│   │         → Seek professional data recovery IMMEDIATELY
│   │         → Replace HDD with SSD + replace SATA cable
│   │
│   └─► NO  → Continue to Q4
│
├─► Q4: Does an external USB macOS drive boot successfully?
│   │
│   ├─► YES → Internal SATA cable or HDD is the problem
│   │         → Replace SATA cable first (cheaper)
│   │         → If still fails after cable replacement → replace HDD/SSD
│   │
│   └─► NO  → Problem is not storage-related
│             → Check RAM, logic board, SMC/NVRAM
│             → Reset SMC: Shift+Ctrl+Opt+Power (10 seconds)
│             → Reset NVRAM: Cmd+Opt+P+R at boot
│
└─► Q5: Did the issue start after physical impact or opening the lid sharply?
    │
    ├─► YES → SATA cable flex damage (most common)
    │         → Replace SATA cable immediately
    │
    └─► NO  → SATA cable thermal degradation (near GPU exhaust vent)
              → Replace SATA cable + consider adding thermal pad/shield
```

---

## Pattern Reference

| ID   | Name                          | Severity | Primary Symptom                     |
|------|-------------------------------|----------|-------------------------------------|
| P001 | SATA Cable Failure — Classic  | HIGH     | Flashing question mark folder       |
| P002 | Kernel Panic — Drive I/O      | HIGH     | Repeated kernel panics              |
| P003 | Prohibitory Symbol            | MEDIUM   | Circle-slash at boot                |
| P004 | Spinning Globe / EFI Fallback | LOW      | Boots to Internet Recovery          |
| P005 | Clicking / Grinding HDD       | CRITICAL | Audible mechanical drive noise      |

---

## Known-Good Parts (2010 MacBook Pro)

| Model    | SATA Cable Part Number | iFixit Guide                                      |
|----------|------------------------|---------------------------------------------------|
| 13-inch  | 821-0814-A             | https://www.ifixit.com/Guide/.../4305             |
| 15-inch  | 821-1226-A             | https://www.ifixit.com/Guide/.../1350             |

---

## Notes for Technicians

- The SATA cable on the 2010 MBP runs underneath the battery and bends
  sharply near the rear vent. This bend point fatigues over 3–5 years.
- Heat from the GPU exhaust accelerates insulation breakdown.
- Always replace the cable AND test the drive independently (via USB enclosure)
  before concluding the drive itself has failed.
- Replacing the HDD with an SSD is strongly recommended:
  it eliminates mechanical failure risk and bypasses the cable stress point
  caused by drive vibration.
