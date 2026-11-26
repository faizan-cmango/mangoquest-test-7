# DFT plan: counter4d

Package: spec/counter4d (v0.1), accepted RTL: rtl/counter4d.sv v4, risk: LOW (riskmap.yaml). Trial runs: runs/scan_insert/counter4d/20261126-145836-e2513b, runs/atpg/counter4d/20261126-145840-620215, runs/sta/counter4d/20261126-145836-b0a10b. Source: runs/yosys_synth/counter4d/20261126-144251-225198/netlist.v.

## Scan

| Item | Plan | Measured by the trial |
|---|---|---|
| Style | mux-D full scan | scan_insert ok |
| Clock domains and chains | core (clk): 1 chain (brief: one chain) | 1 chain, length 4 |
| Longest chain | <= 256 | 4 |
| Scan-in pins per domain | 2 max (T-4); 1 used | 1 |
| Flops scanned | all | 4 of 4 |
| Exceptions | none | none |
| Test mode | no async set/reset, no clock gating: scan_insert adds no test_mode | chains_intact true |
| Test clocks | shift 25 MHz from the tester (default); capture clk at 100 MHz | ATE 114 cycles, 4.56 us |

Source findings for the RTL designer: none (no dft_constraint challenges). Regions inferred from the flop prefix (cnt); no hotspots.

## ATPG

| Fault model | Required | Target | Measured test coverage | Measured constrained coverage | Patterns |
|---|---|---|---|---|---|
| stuck-at | yes | 99 % | 100.0 % | 100.0 % | 10 |
| transition (LOC) | optional (LOW); the brief asks for it | 95 % | 80.31 % | 100.0 % | 8 |

Stuck-at: 166 faults, 162 detected, 4 untestable_proven, 0 uncovered or aborted. Transition: 142 faults, 102 detected, 15 untestable_proven, 25 constrained (au_pi_held), none aborted or not run. Capture holds: none declared, none undeclared.

The transition test coverage (80.31 %) is under 95 %. Only the constrained figure (100 %) meets the target, and only while the 25 au_pi_held faults have a recovery owner. Owner: the wrapper cells or upstream flops at chip level (T-6). They sit on the primary inputs en and rst_n, which the block cannot launch a transition on. This is open; I did not lower the target.

## Equivalence
Functional-mode view (scan_en = 0, scan_in = 0) against the netlist before scan, by lec_post_scan at sign-off. Not run in this plan.

## Gate-level regression
gate_sim runs Dayo's harness unchanged at sign-off. It needs his ready sheet. Not run in this plan.

## Timing
Pre-check (ltp_proxy, tt): slack before 7584.3 ps, one mux delay 200 ps, slack after 7384.3 ps, budget 300 ps, no breach. Paths at risk: none (worst start en, end flop D). Owner if one appears: Kemi.

## Density flags for Seun

None: no region is at or over 0.30.

## Open items

- Default applied (fault_models, test clock, scan budget): confirm one chain, 25 MHz shift, no region map, stuck-at plus transition.
- Transition test coverage 80.31 % against 95 %: the constrained figure is the gate's metric. Person to confirm the au_pi_held owner (T-6).
- The chip-level test architecture (T-3) is not settled by the block.
- pattern_sim, lec_post_scan, gate_sim and dft_lint are left to sign_off_dft.
