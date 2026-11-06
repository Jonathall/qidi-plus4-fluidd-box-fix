# Testing — method, results, limitations

This fix was developed and tested **without a real Plus 4**, on a
simulated bench built to reproduce the printer's data contracts.
This page describes what that bench is, what was run against it,
and — just as important — what it cannot prove.

## The bench

- **Real upstream Klipper and Moonraker** (no API mock): the
  transport behavior Fluidd relies on — object subscriptions,
  status notifications over the websocket — is the genuine one.
- **The printer MCU is emulated** (simulavr, atmega644p target);
  temperatures and motion are simulated constants. Irrelevant
  here: the panel under test only consumes published objects.
- **Simulated Box modules** publish the Klipper objects in the
  exact shapes the 2.1.1 firmware publishes:
  `box_extras` (`box_button_state`, `b_endstop_state`,
  `e_endstop_state`), `box_stepper slot0..15` (`runout_button`,
  `rfid_state`), `save_variables` seeded with the stock Plus 4
  variable set, and `multi_color_controller` resolving slot
  identities from `save_variables` plus the official filament
  catalogue, the way the firmware does. They accept the stock
  commands (`E_BOX` / `E_LOAD` / `E_UNLOAD`, `RFID_READ`) and
  perform timed state transitions (an operation holds the busy
  state ~2 s, then publishes the resulting loaded/sensor states
  and `last_load_slot`).
- **The printer screen is emulated as a second Moonraker
  client**: it subscribes to the same objects, logs every status
  delta it receives, and can perform the screen's writes
  (`SAVE_VARIABLE` on the slot variables, load/unload,
  box enable). It also resolves each slot's identity through the
  catalogue, the way the screen displays it.
- **Three Fluidd builds were served in parallel** against the
  same bench state — stock 2.1.1, ThorSc's patched bundle, and
  this fix — and driven in a real (headless) browser: the actual
  served page, its Vue component instances, and its DOM button
  states are what the tests read.

## Results

### 1. Vendor switching (the refresh fix)

From two starting filaments (QIDI PETG Basic, Generic PETG), the
panel's vendor setter was applied for every target vendor, and
the resulting `save_variables` diff was compared against an
independent model of the expected remap:

- **11 combinations** in the initial run: every switch produced a
  coherent pair of writes (vendor, then remapped filament: same
  material name when the new vendor has it, else its first
  entry), no other variable was touched, and no value was ever
  empty or invalid.
- **Initial failure, kept on record:** switches to **HATCHBOX**
  and **Overture** produced a *vendor-only* write. Root cause was
  the shipped table, not the code: `vendor_list` announced six
  vendors but no table entry carried those two. Their catalogue
  filaments are named simply `PLA` / `PETG` / `ABS` — names that
  already exist as vendor-less legacy entries and are shared by
  several vendors — so the table construction, which matched and
  appended *by name*, dropped them (unique, vendor-prefixed names
  like Polymaker's and Bambu Lab's survived). The data was never
  missing: the screen catalogue holds them (HATCHBOX
  PLA/PETG/ABS, Overture PLA/ABS).
- **Correction:** those five filaments were appended as
  `fila78`–`fila82` (values from the screen catalogue; nothing
  existing renumbered), and the four affected combinations were
  re-run: **4/4 now produce the two coherent writes**, the
  material list shows the vendor's entries (3 HATCHBOX,
  2 Overture), and the slot no longer falls into the protected
  state after such a switch. Every vendor in `vendor_list` now
  owns at least one valid entry.

### 2. Two-way synchronization Fluidd ↔ screen

- **Screen → Fluidd:** a slot assignment written by the emulated
  screen client (Polymaker / PolyLite PLA on slot 2) appeared in
  the already-loaded panel — tiles and selects updated from the
  pushed object deltas, no page reload — with the same resolved
  name, vendor and color on both sides.
- **Fluidd → screen:** a vendor change made through the panel
  was received by the screen client, which resolved the slot to
  the identical identity (Polymaker / PolyLite PLA) from both
  `save_variables` and `multi_color_controller`.

### 3. Load / unload cycles from the panel

Driven through the panel's real DOM buttons (slot 1), sampled
throughout the operation:

- during the operation the panel reports *operating* and **all
  three buttons are disabled** in the DOM (the lock reads
  `multi_color_controller.operation.box_button_state`, the field
  this fix reads first);
- after load: `loaded_slot` agrees in `box_extras`,
  `multi_color_controller` and the screen client's view; sensor
  states and button enablement match the stock formulas applied
  to the new state;
- unload mirrors this back to the unloaded state.

### 4. Print-start gate (regression only)

The gate is **not patched** — the relevant function extracted
from the stock and patched bundles is byte-identical. Its live
verdicts in the real Check-Filament dialog, on the bench:
box enabled with a mappable file → passes (with the correct
automatic slot mapping); box enabled with an incomplete mapping
→ blocked; box disabled → passes exactly when
`e_endstop_state = 1` and `b_endstop_state ≠ 0`, with the
correct message in each failing case. **6/6 scenarios** conform
to the behavior validated against the firmware.

### 5. Patcher

- input with a wrong hash (a 1.7.x-line bundle) → refused, file
  untouched;
- input already patched → refused (it no longer carries the
  stock hash, so no double application is possible);
- two clean runs from the stock bundle → identical output,
  byte for byte equal to the shipped drop-in file.

### Reference checks on the stock and community builds

For orientation, the same bench also confirmed: the stock panel
renders and resolves identities from the numeric encoding alone
(it never reads `multi_color_controller`), and ThorSc's patched
bundle boots and renders correctly when installed in the served
tree with its data needs satisfied. The firmware package's
install trap is real, though: it ships **two** Fluidd trees (only
the root `/home/mks/fluidd/` is served; the `Fluidd/` subfolder
is an older, unserved build) and multiple accumulated
`index-*.js` bundles — a correct patch copied to the wrong tree
or name changes nothing at all.

## Limitations

- **No real Plus 4 was used.** Object shapes and fields are the
  ones documented and measured for firmware 2.1.1, but the real
  Box mechanics, the real screen application (here emulated in
  its role as a state client, not its binary), the printer's
  metadata pipeline, and real timing/race behavior are **not**
  covered. The fix is **beta until a smoke test on an actual
  machine**.
- The bench's `multi_color_controller` model publishes QIDI
  filament IDs only for QIDI-vendor matches; for other vendors it
  publishes an empty ID. That is a bench-model limit, not fix
  behavior — the fix displays whatever the firmware publishes.
- Spoolman integration was not exercised.
- Bench incident, for the record: while setting up the gate
  test, a file without metadata was once sent to print through
  the direct (dialog-free) path; the ensuing homing shut down
  the emulated MCU once. No test conclusion was drawn from it,
  and the gate results above were produced afterwards through
  the normal dialog flow.
