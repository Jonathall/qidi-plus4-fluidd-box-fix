# What the patch changes, in detail

The patch is **10 anchored replacements** in the minified stock bundle
of firmware **2.1.1** (`assets/index-BHXUyR-O.js`, SHA-256
`4770bade…a59`), plus a version stamp
(`window.__qidiPlus4Fix = "1.0.0"`). `patcher/qidi_plus4_fluidd_fix.py`
lists the anchors verbatim and refuses any input whose SHA-256 is not
the reference stock bundle. The patched bundle's SHA-256 is
`223edbccdf2bdc79ec6deefd85f0126ae916bb75819059d0f13f81aa3a03c19b`,
reproducible byte for byte from the stock bundle.

Everything follows the same principle as the Plus 5 fix: **the
firmware is the source of truth** — Fluidd is adapted to the state
and formats the current firmware actually publishes.

## Background: on the Plus 4 the seam is read/write, not on/off

Unlike the Plus 5, the Plus 4 never lost its sensor fields:
`box_extras` on 2.1.1 still publishes `box_button_state`,
`b_endstop_state`, `e_endstop_state` (verified from the 1.7.0 source,
the 2.1.1 module strings, and live measurements) — so the print-start
gate is **correct as designed and is not touched**, and the panel
basically works. What is broken is subtler:

1. **Two identity worlds.** The printer screen (HMI) resolves slots
   from its rich catalogue (56 filaments, 6 vendors, QF IDs) and the
   firmware publishes the resolved identity per slot in
   `multi_color_controller` (`box<N>_filament_info_<M>_*`,
   `extra.filament_info`). The bundled Fluidd never reads it: it
   resolves slots from the legacy numeric trio in `save_variables`
   against the printer's poor table (50 entries, Generic + QIDI).
   Whenever the two disagree — a third-party filament set on the
   screen — Fluidd displays the numeric world, not the real one.
2. **The write-back crosses the seam destructively.** Editing a slot
   in Fluidd writes the numeric trio. A filament with no numeric
   representation (any third-party vendor on a stock machine) is
   silently replaced by whatever the numeric write resolves to —
   the screen assignment is destroyed by an unrelated edit
   (e.g. a color change). This is the hole in ThorSc's patch too:
   it reads `multi_color_controller` but writes back numerically.
3. **No vendor scoping.** The material dropdown always lists every
   filament name in the table, whatever vendor is selected, and a
   vendor switch writes only `vendor_slot<N>` — the filament stays
   the old vendor's, so the list never "follows" the vendor.
4. **Busy state read from the legacy object only.** The panel lock
   reads `box_extras.box_button_state`; the same state is published
   in structured form at
   `multi_color_controller.operation.box_button_state`, and the
   loaded-slot truth at `multi_color_controller.box.loaded_slot`.
   The patch reads the structured locations first (see §5).

## The changes

### 1. MCC identity resolution — changes 1–3

Change 1 adds two getters to the Control Box panel:

- `mccInfo`: builds, per slot (0–15 and the external slot 16), the
  identity published by the firmware —
  `{filament, vendor, color ("#RRGGBB"), filament_id}` — from
  `multi_color_controller.box.box<B>_filament_info_<K>_*` and
  `multi_color_controller.extra.filament_info`. Empty when MCC is
  absent or the slot has no resolved identity.
- `slotProtected`: see §3.

Changes 2 and 3 make the panel's `items` (the slot tiles and the
select models) prefer the MCC identity — name, vendor, hex color —
and fall back to the stock numeric resolution untouched when MCC
has nothing for the slot. The tile for a slot set on the screen to a
Bambu filament now shows that filament, in its color, instead
of whatever the stale numeric trio happens to decode to.

### 2. Vendor-scoped material list + refresh — changes 4–5

Change 4 scopes `filamentItems` to the selected slot's vendor:

- entries of the filament table that carry a `vendor` field (the
  enriched table shipped in `drop-in/`) match only that vendor;
- legacy entries without a `vendor` field belong to the stock world
  and match the Generic / QIDI selections;
- the current slot's filament is always kept in the list (so the
  select can render it, including a protected identity — §3);
- an empty scope falls back to the full list (stock behavior —
  with the stock table installed, nothing changes at all).

Change 5 fixes the refresh half of the Plus 5 "V9.2" bug class.
The stock vendor setter wrote only `vendor_slot<N>`: the slot kept
the previous vendor's filament, and since the material list keys
off the slot identity, nothing visibly followed the switch for the
combinations where no other write happened. The patched setter,
after writing the vendor, re-points the filament in the same step:
same material name under the new vendor if it exists, otherwise
the new vendor's first table entry — so **every** vendor switch
produces a valid (vendor, filament) pair and the list refreshes.
With the stock table (no vendor data), the remap finds nothing to
re-point and the setter behaves exactly like stock.

### 3. Write-back protection — changes 1, 6, 7, 10

`slotProtected` (change 1) is true when the slot's current MCC
identity has **no valid numeric representation**: its vendor is not
in the table's `vendor_list`, or no table entry carries its
filament name under that vendor. In that state:

- the vendor / filament / color setters return immediately —
  no `SAVE_VARIABLE` is emitted (changes 5, 6, 7);
- the three selects are disabled in the panel (change 10 — the
  shared `disabled` expression of the three controls, 3 anchor
  occurrences), while the tile and the selects keep **displaying**
  the real identity read from MCC.

So a third-party filament set on the printer screen can be looked
at in Fluidd, but an edit there can no longer silently overwrite
it with a numeric fallback. Setting the slot back to a
representable filament is done on the screen, or by picking a
representable assignment after clearing it there — the panel never
invents a substitute on its own. (On the stock table this already
triggers for any non-Generic/QIDI vendor; the enriched table makes
the 56 catalogue filaments representable, so protection then only
covers identities outside the catalogue.)

### 4. Operation lock and button state — changes 8–9

Change 8 (`isOperating`): the lock now reads
`multi_color_controller.operation.box_button_state` first — the
structured busy state 2.1.1 publishes — and falls back to
`box_extras.box_button_state` when MCC is absent. Same value, read
where the firmware's own components publish it; the panel locks
during load/unload/RFID operations either way.

Change 9 (`buttonStatus`): the loaded-slot comparison now uses
`multi_color_controller.box.loaded_slot` (parsed from `"slot<N>"`)
and `multi_color_controller.box.b_endstop_state` when present,
falling back to `variables.lastLoadSlot` / `box_extras` otherwise.
The formulas themselves (which button is enabled for which
inserted/loaded combination) are **unchanged** from stock — on the
test bench, where both objects publish the same state, the patched
panel produces the same button outcomes as stock on every state
exercised; what changes is that the inputs come from the object
that cannot disappear, not the legacy mirror.

The button commands are the stock ones — `E_BOX` / `E_LOAD` /
`E_UNLOAD slot=<N>`, `RFID_READ SLOT=slot<N>` — and so is the
print-start gate: both were validated correct on the Plus 4
firmware and are deliberately **not** patched.

## The filament table

`drop-in/officiall_filas_list.cfg` is required with the bundle (same
arrangement as the Plus 5 fix). It is built **for the Plus 4's
numeric world**:

- all 50 stock entries keep their stock numbering, names and
  temperatures — existing `filament_slot<N>` values keep their
  meaning (the Plus 5 table enumerates the same catalogue
  differently and must **not** be used on a Plus 4);
- 19 stock entries whose name matches exactly one catalogue entry
  gain that entry's `vendor` and QF `filament_id`;
- the 27 catalogue filaments missing from the stock table (the
  third-party vendors and the newer QIDI entries, transcribed from
  the QIDI Studio catalogue — the same source as the Plus 5 table)
  are appended as `fila51`–`fila77` with vendor, QF ID, type and
  temperatures;
- `vendor_list` keeps `0 = Generic`, `1 = QIDI` and appends
  `2 = HATCHBOX`, `3 = Polymaker`, `4 = Bambu Lab`, `5 = Overture`
  (the `Bambu Lab` form is corrected to the printer's `Bambu` in
  Correction 2 below);
- `colordict` is the stock one, untouched (color indexes are
  referenced by `color_slot<N>` values).

**Correction (2026-11-06).** The first shipped table had a hole the
bench battery caught: `vendor_list` announced HATCHBOX and Overture
but no `fila` entry carried either vendor, so a vendor switch to
them wrote the vendor alone and left the filament pointing at the
previous vendor's entry. Cause: the table was built **by name** —
a stock entry was stamped only when its name matched exactly one
catalogue filament, and a catalogue filament was appended only when
its name was absent from the stock table. The five HATCHBOX/Overture
filaments carry the generic names `PLA` / `PETG` / `ABS`, which are
both already present as legacy entries (fila1/41/11) and shared by
several catalogue vendors, so they failed both tests and were
dropped; Polymaker and Bambu Lab survived because their catalogue
names are unique and vendor-prefixed. The data itself was never
missing — the HMI catalogue (the dataset embedded in ThorSc's
patched bundle, from a real Plus 4's `filament-<nozzle>.json`) holds
QFL10/QFL11/QFL12 (HATCHBOX PLA/PETG/ABS) and QFL60/QFL62 (Overture
PLA/ABS), and the Plus 5 table, transcribed from the same QIDI
Studio catalogue, carries them with temperatures. They are now
appended as `fila78`–`fila82` (values verbatim from the Plus 5
table; nothing existing renumbered), so every vendor in
`vendor_list` owns at least one valid entry — verified by re-running
the affected vendor-switch combinations on the bench
(see [testing.md](testing.md)). The same name mechanism also skipped five
Generic/QIDI catalogue filaments (QFA90, QFG90, QFB91, QFA92,
QFA05); those were deliberately **not** appended: their names are
already representable for Generic/QIDI through the vendor-less
legacy entries (which scope to Generic/QIDI under change 4), so
their absence breaks nothing **[superseded by Correction 2
  below: those filaments are part of the printer's database and
  are now in the table]**, and QFL61 does not exist in the
catalogue (a gap in QIDI's own numbering, not an omission here).

**Correction 2 (2026-11-06) — the table is rebuilt from the
printer's database.** The design rule, stated plainly: what the
HMI offers and reports is the truth, and Fluidd's lists must
reproduce it — same names, same vendor forms, same QF codes,
nothing invented on the Fluidd side. The first shipped table had
been built the other way around (the legacy stock file enriched
from the QIDI Studio catalogue), and it diverged from the
printer's own filament database (the `filament-<nozzle>.json`
dataset transcribed in ThorSc's bundle: 56 filaments, 6 vendors):
Studio name forms instead of the printer's (`PLA+` instead of
`Generic PLA+`, `PolyLite PLA` instead of `Polymaker PLA`, vendor
`Bambu Lab` instead of `Bambu`, including in `vendor_list`),
legacy filaments left without their QF codes, five database
filaments missing entirely, legacy names the printer does not
know, and — once the codes were added in place — six QF codes
present twice with conflicting temperatures.

The table shipped now is a clean rebuild from the database, the
way it should have been built the first time:

- content = the printer's 56 database filaments, each exactly
  once, under the printer's current names, vendor forms and QF
  codes;
- numbering: a database filament that has a stock entry keeps
  its stock number and its stock temperatures (26 filaments —
  including the documented legacy renames PLA Metal → PLA
  Rapido Metal QFA04, PLA Silk → QFA05, PLA-Wood → WOOD Rapido
  QFA16, ABS-Metal → QFB55, ABS-Odorless → QFB53, the stock
  typo PETG-Though → PETG Tough QFG03, TPU-AERO → QFU00); the
  30 database filaments the stock table lacks are appended as
  fila51–fila80 with catalogue temperatures;
- stock sections that are not in the printer's database (QIDI's
  own blank placeholders, plus `PLA`, `PLA Matte`, `ABS`, `PETG`,
  `PVA`, `TPU`) are unnamed placeholder sections carrying only
  their stock temperatures and type, so legacy numeric references
  cannot dangle — they claim no identity;
- one source of values per identity, by construction: a
  uniqueness check against the printer's database (56 named
  entries, 56 unique QF codes, exact 1:1 on names and vendors)
  is now part of the validation, alongside the bench battery
  (vendor switch + remap 11/11, HMI→Fluidd live identity
  display, print gate 6/6 — re-run against the rebuilt table).

The bundle is unchanged (it reads the table at runtime). Table
SHA-256:
`bbf21c8af8f71f3126a1c7c9f6feb9140dc6ce90fe8065fc74f500ab20af073e`.

Addendum (2026-11-10): five `[colordict]` entries in this table
were then corrected to the hex codes the firmware itself writes
(#4 `#5CF30F` → `#5CF30E`, #7 `#FE98FE` → `#FF98FE`,
#13 `#CADE4B` → `#CADF4B`, #17 `#FE717A` → `#FF7174`,
#20 `#898F9B` → `#898F8B`) — the panel resolves a screen-set
color by exact hex match, and the stock values never matched.
Current table SHA-256:
`9e73b75d5f2f5f483095eb5cb942f2429fb99741d8aed63697985e8197e11576`.

## Differences from ThorSc's patch (same target, different seams)

ThorSc's `qidi-max4-plus4-fluidd-box-patch` (v0.9.3, GPL-3.0) fixes
the display by reading `multi_color_controller` — confirmed working
on the test bench when installed in the served tree. This fix
differs where his README documents his own limits: the material
list is vendor-scoped with a switch refresh (§2, his dropdown
stays limited to vendor indexes 0/1), and an unrepresentable slot
is protected instead of written back numerically (§3). His patch
also renames the box commands to the `*_CONTROL` forms; this one
keeps the firmware's stock `E_*` commands, which the bench shows
the 2.1.1 panel and firmware already agree on.

## Validation (bench, no real Plus 4)

Developed and exercised on a simulated bench (real Klipper +
Moonraker, simulated Box modules publishing the 2.1.1 object
shapes, an emulated printer screen as a second Moonraker client —
full method and results in [testing.md](testing.md)):

- base state renders identically to stock, identities resolved
  from MCC;
- an unrepresentable identity posed on a slot through a bench
  scenario command (Bambu Lab "PLA Wood", a name/vendor pair the
  table cannot encode) displays rich — name, vendor, hex color —
  with all three selects disabled and no write emitted;
- a vendor change written by the emulated screen (`vendor_slot=4`,
  `filament_slot=69`) is followed live by the panel: tile and
  selects show Bambu PETG, and the material menu contains exactly
  the three Bambu entries;
- the patcher is reproducible: stock SHA-256 in, identical
  patched SHA-256 out, and it refuses the already-patched bundle.

Not validated: a real Plus 4 (none available) — treat as beta
until a machine smoke test.
