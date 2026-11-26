# System Architecture Document — counter4d · SAD v0.1

> Machine index: `sad.yaml`. Requirements live in `rtm.yaml`, ports in `idd/`, scenarios in
> `vps.yaml`, risk in `riskmap.yaml`, clocks in `clocks.yaml`.

## 1 Scope and context
counter4d is a 4-bit synchronous wrapping up-counter with enable and synchronous active-low reset, on one clock. It goes on the counter4d_eval board (`brs.yaml`). Out of scope: registers, bus interfaces, interrupts, clock crossings, power management, memories, clock gating. Scan ports are added by DFT insertion and are not part of the interface.

Assumptions (simplest option, see `decisions.yaml`): one level-class IDD (ADR-01); no area budget and DFT not_applicable in this package (ADR-02); count undefined before the first reset edge (ADR-03); board currents estimated and the 1.8 V LDO is a gap in the board standard (ADR-04); harness drives inputs at falling edges only (ADR-05).

## 2 Block decomposition
One block, counter4d. No partition is needed.

## 3.1 Counter behaviour — REQ-3.1.1 … REQ-3.1.6
At each rising edge of clk: reset has priority (REQ-3.1.1), else enable increments with wrap (REQ-3.1.2, REQ-3.1.3), else the value holds (REQ-3.1.4). Outputs change only at that edge (REQ-3.1.5). Ports are fixed (REQ-3.1.6; IDD-COUNTER_IO).

Timing sketch: inputs change at a falling edge; the next rising edge samples them and count updates just after it.

Feasibility (proxy, opensta_liberty, confidence 0.5, pre-layout): fmax estimate 1257.9 MHz against the clock target, area 140.1 um2, target met. Recorded in `sad.yaml` `feasibility`.

## 7 Risk register
See `riskmap.yaml`.

## 8 Open items
No open ArchChallenges. Open questions: the Device Models of the chip and of the 1.8 V LDO, and the parts snapshot, are supplied by a person (BRS-4).
