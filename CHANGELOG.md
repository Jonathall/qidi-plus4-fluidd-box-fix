# Changelog

Bundle format: QIDI's shipped Fluidd v1.30.4, firmware 2.1.1
(`index-BHXUyR-O.js`).
Reference stock bundle SHA-256:
`4770bade9c2154fc1f44b3650746bc855eb008e6376f1d24820db59eb541ed59`.

## Table correction — 2026-11-06

Filament table rebuilt to mirror the printer's own filament
database (see Correction 2 in docs/changes.md). Bundle unchanged.
Filament table (`officiall_filas_list.cfg`) SHA-256:
`b0ecc65a98a2d8366a524325f47c8a2d6b548c29568f6ae803567fa672ec3199`

- Names and vendor forms now match the printer's database
  throughout (`Generic PLA+`, `Polymaker PLA`, vendor `Bambu`,
  including `vendor_list`).
- Seven legacy entries gained their QF codes (PLA Metal, PLA
  Silk, PLA-Wood, ABS-Metal, ABS-Odorless, PETG-Though [stock
  typo], TPU-AERO); the five database filaments the first table
  skipped are appended as fila83–fila86; stock sections that are
  not in the printer's database are now unnamed placeholders.
  No existing entry renumbered.
- Bench battery re-run against the corrected table: vendor
  switches 11/11, print gate 6/6.

## 1.0.0 — 2026-11-06

Patched bundle SHA-256:
`223edbccdf2bdc79ec6deefd85f0126ae916bb75819059d0f13f81aa3a03c19b`
Filament table (`officiall_filas_list.cfg`) SHA-256:
`19008ea3484091f967235064c12593d940716ee67c8dc8b900cb645250d2137d`

- **Slot identity read from `multi_color_controller`.** Tiles and
  the edit panel now resolve name, vendor, hex color and filament
  ID from the identity the firmware publishes per slot (the same
  data the printer screen uses), with the stock numeric resolution
  kept as fallback. A slot set on the screen to a third-party
  filament now displays that filament in Fluidd.
- **Vendor-scoped material list with refresh on switch.** The
  dropdown only lists the selected vendor's entries (current
  filament always kept, full-list fallback on an empty scope).
  The vendor setter re-points the filament in the same step —
  same material name under the new vendor, else its first table
  entry — so a vendor switch always lands on a valid material
  and the list follows.
- **Write-back protection.** When a slot's current identity has
  no valid representation in the filament table, the three
  setters emit no write at all and the vendor / filament / color
  controls are disabled; the identity stays displayed. An
  unrelated edit in Fluidd can no longer silently overwrite a
  screen-set assignment.
- **Panel state from the structured objects.** The operation
  lock reads `multi_color_controller.operation.box_button_state`
  first (fallback: `box_extras`), and the button logic takes the
  loaded slot and buffer state from `multi_color_controller.box`
  first (fallback: legacy variables / `box_extras`). Button
  formulas, the `E_BOX` / `E_LOAD` / `E_UNLOAD` / `RFID_READ`
  commands, and the print-start gate are unchanged from stock.
- **Filament table built for the Plus 4.** The 50 stock entries
  keep their stock numbering, names and temperatures; 19 gain
  vendor + filament-ID data by exact catalogue match; the
  remaining screen-catalogue filaments are appended as
  `fila51`–`fila82`, and `vendor_list` gains HATCHBOX,
  Polymaker, Bambu Lab and Overture. Every vendor in the list
  owns at least one entry — the HATCHBOX / Overture entries
  (`fila78`–`fila82`, generic PLA/PETG/ABS names shared between
  vendors) were initially missed by the name-based construction
  and were added after bench testing caught a vendor switch to
  them producing a vendor-only write (see docs/testing.md).
- **Validation status:** tested on a simulated bench reproducing
  the firmware 2.1.1 data contracts (two-way Fluidd ↔ emulated
  screen synchronization, vendor-switch matrix, load/unload
  cycles, print-gate regression, patcher refusal/reproducibility)
  — see docs/testing.md. Beta: not yet smoke-tested on a real
  Plus 4.
