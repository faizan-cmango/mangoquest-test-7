# ==== A. Header ===================================================================
# Testbench:     tb_counter4d (cocotb)
# Project:       counter4d
# SAD:           spec/counter4d/sad.md section 3.1
# Risk:          LOW: line, branch, toggle, FSM and functional 100 % (riskmap.yaml)
# Testplan:      verif/counter4d/testplan.yaml @v1.0
# Author:        Dayo
# PURPOSE:       One directed test per VPS scenario and one seeded random test; a monitor
#                feeds every rising edge to a scoreboard built on a model of REQ-3.1.1 to 3.1.4.
# DEBUG NOTES:   Read the first MISMATCH line. Add to the waveform, in order: rst_n, en, count.
# KNOWN GOTCHAS: Inputs are driven only after the falling edge (IDD rule R1, ADR-05); the
#                monitor reads inputs at the rising edge and count after ReadOnly().
#                count is undefined before the first reset edge (ADR-03): reset first.
"""cocotb harness for counter4d (skeleton: test bodies are filled in at verification)."""

import logging
import random
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, ReadOnly, RisingEdge
from cocotb_coverage.coverage import CoverPoint, coverage_db

# ==== B. Interface layer ==========================================================
CLK_PERIOD_NS = 10  # clocks.yaml: clk at 100 MHz
RESET_EDGES = 2  # REQ-3.1.1: rst_n held for two rising edges so every flop is reset
COUNT_BITS = 4  # REQ-3.1.6: count is 4 bits wide
COUNT_MAX = 15  # REQ-3.1.3: the value at which count wraps
WAIT_CYCLES = 4  # REQ-3.1.5: an edge is sampled every cycle; 4 without one is a hang
HOLD_EDGES = 4  # VPS-03: edges held per count value, my choice
MID_STEPS = 7  # VPS-03: steps from 0 to a mid value (7), inside 1..14
MAX_STEPS = 8  # VPS-03: steps from 7 to 15 (REQ-3.1.3's value)
RAND_EDGES = 400  # testplan constraint_model: edges of the random test
RAND_RST_P = 0.05  # testplan constraint_model: rst_n 0 about 1 edge in 20
RAND_EN_P = 0.75  # testplan constraint_model: en 1 on 3 edges in 4
LOG = logging.getLogger("tb_counter4d")


@dataclass(frozen=True)
class CntSample:
    """One rising edge: the inputs it acted on and count after it."""

    rst_n: int
    en: int
    count: int


def cnt_read(handle, name: str) -> int:
    """A port's value as an int; X or Z is a failure, never read as 0."""
    value = handle.value
    if not value.is_resolvable:
        raise AssertionError(f"UNKNOWN signal={name} observed={value}")
    return int(value)


class CntDriver:
    """Drives en after the falling edge (R1). It only drives."""

    def __init__(self, dut) -> None:
        self.clk = dut.clk
        self.en = dut.en
        self.rst_n = dut.rst_n

    def power_up(self, dut) -> None:
        self.en.value = 0
        self.rst_n.value = 0
        for name in ("test_mode", "scan_mode", "scan_en", "scan_in"):
            if hasattr(dut, name):
                getattr(dut, name).value = 0

    async def drive(self, en: int, rst_n: int = 1) -> None:
        await FallingEdge(self.clk)
        self.en.value = en
        self.rst_n.value = rst_n


class CntMonitor:
    """Observes every rising edge and hands the sample on. It only observes."""

    def __init__(self, dut, on_sample: Callable[[CntSample], None]) -> None:
        self.dut = dut
        self.on_sample = on_sample

    async def run(self) -> None:
        dut = self.dut
        while True:
            await RisingEdge(dut.clk)
            rst_n = cnt_read(dut.rst_n, "rst_n")
            en = cnt_read(dut.en, "en")
            await ReadOnly()
            self.on_sample(CntSample(rst_n, en, cnt_read(dut.count, "count")))


class CntReset:
    """Reset sequence: rst_n active low, synchronous (clocks.yaml), held RESET_EDGES edges."""

    def __init__(self, dut) -> None:
        self.clk = dut.clk
        self.rst_n = dut.rst_n

    async def release(self) -> None:
        for _ in range(RESET_EDGES):
            await RisingEdge(self.clk)
        await FallingEdge(self.clk)
        self.rst_n.value = 1


class CntWatchdog:
    """Bounds each wait (DAYO-TBS-025): a monitor that sees no edge fails as deadlock."""

    def __init__(self, dut, edges: Callable[[], int]) -> None:
        self.clk = dut.clk
        self.edges = edges

    async def wait_edges(self, target: int, vps: str) -> None:
        for _ in range(WAIT_CYCLES):
            if self.edges() >= target:
                return
            await RisingEdge(self.clk)
            await ReadOnly()
        if self.edges() < target:
            raise AssertionError(f"deadlock_detected {vps}: no edge sampled (REQ-3.1.5)")


# ==== C. Stimulus =================================================================
class CntEnv:
    """One test's harness: components, model and coverage, one seed."""

    def __init__(self, dut, test: str) -> None:
        self.seed = cocotb.RANDOM_SEED
        self.rng = random.Random(self.seed)
        LOG.info("SEED=%d test=%s harness=tb_counter4d dut=counter4d", self.seed, test)
        self.dut = dut
        self.driver = CntDriver(dut)
        self.reset = CntReset(dut)
        self.scoreboard = CntScoreboard(test, self.seed)
        self.scoreboard.listeners.append(cnt_cov_sample)
        self.monitor = CntMonitor(dut, self.scoreboard.observe)
        self.watchdog = CntWatchdog(dut, lambda: self.scoreboard.edges)

    async def start(self) -> None:
        self.driver.power_up(self.dut)
        Clock(self.dut.clk, CLK_PERIOD_NS, unit="ns").start(start_high=False)
        cocotb.start_soon(self.monitor.run())
        await self.reset.release()

    async def step(self, vps: str, en: int, rst_n: int = 1) -> None:
        target = self.scoreboard.edges + 1
        await self.driver.drive(en, rst_n)
        await self.watchdog.wait_edges(target, vps)

    def finish(self, vps: str, at_least: int) -> None:
        checked = self.scoreboard.checked[vps]
        assert checked >= at_least, f"{vps}: {checked} checks ran, {at_least} expected"
        cnt_cov_export()


@cocotb.test(timeout_time=20, timeout_unit="us")
async def test_vps_01_reset(dut) -> None:
    """VPS-01: count to a non-zero value, reset with en 0, hold, release."""
    env = CntEnv(dut, "test_vps_01_reset")
    await env.start()
    for _ in range(9):  # count 1..9 (mid)
        await env.step("VPS-01", 1)
    await env.step("VPS-01", 0, 0)  # reset at mid, en 0
    await env.step("VPS-01", 0, 0)  # held
    await env.step("VPS-01", 0, 1)  # release
    for _ in range(15):
        await env.step("VPS-01", 1)
    await env.step("VPS-01", 0, 0)  # reset at max
    await env.step("VPS-01", 0, 1)
    env.finish("VPS-01", 2)


@cocotb.test(timeout_time=20, timeout_unit="us")
async def test_vps_02_increment(dut) -> None:
    """VPS-02: en 1 for several edges."""
    env = CntEnv(dut, "test_vps_02_increment")
    await env.start()
    for _ in range(10):
        await env.step("VPS-02", 1)
    env.finish("VPS-02", 5)


@cocotb.test(timeout_time=20, timeout_unit="us")
async def test_vps_03_hold(dut) -> None:
    """VPS-03: en 0 at count 0, mid and 15, with en toggled between edges."""
    env = CntEnv(dut, "test_vps_03_hold")
    await env.start()
    async def hold(n: int) -> None:
        for _ in range(n):
            target = env.scoreboard.edges + 1
            await FallingEdge(env.dut.clk)
            env.dut.en.value = 0  # en moves only at falling edges (R1)
            await env.watchdog.wait_edges(target, "VPS-03")

    await hold(HOLD_EDGES)  # at zero
    for _ in range(MID_STEPS):
        await env.step("VPS-03", 1)
    await hold(HOLD_EDGES)  # mid
    for _ in range(MAX_STEPS):
        await env.step("VPS-03", 1)
    await hold(HOLD_EDGES)  # max
    env.finish("VPS-03", 12)


@cocotb.test(timeout_time=20, timeout_unit="us")
async def test_vps_04_wrap(dut) -> None:
    """VPS-04: count up to 15 and one more enabled edge."""
    env = CntEnv(dut, "test_vps_04_wrap")
    await env.start()
    for _ in range(17):  # 0 -> 15 -> wrap -> 1
        await env.step("VPS-04", 1)
    env.finish("VPS-04", 1)


@cocotb.test(timeout_time=20, timeout_unit="us")
async def test_vps_05_reset_priority(dut) -> None:
    """VPS-05: rst_n 0 and en 1 together at a non-zero count."""
    env = CntEnv(dut, "test_vps_05_reset_priority")
    await env.start()
    for _ in range(5):
        await env.step("VPS-05", 1)
    await env.step("VPS-05", 1, 0)  # reset and en together
    await env.step("VPS-05", 1, 0)
    await env.step("VPS-05", 1, 1)
    env.finish("VPS-05", 2)


@cocotb.test(timeout_time=20, timeout_unit="us")
async def test_vps_06_port_list(dut) -> None:
    """VPS-06: ports are clk, rst_n, en, count[3:0]; count is 4 bits wide."""
    env = CntEnv(dut, "test_vps_06_port_list")
    await env.start()
    for name in ("clk", "rst_n", "en", "count"):
        if not hasattr(dut, name):
            raise AssertionError(f"MISMATCH VPS-06 REQ-3.1.6 signal={name} expected=port observed=absent")
    if len(dut.count) != COUNT_BITS:
        raise AssertionError(
            f"MISMATCH VPS-06 REQ-3.1.6 signal=count expected={COUNT_BITS} observed={len(dut.count)}"
        )
    await env.step("VPS-06", 0)
    got = cnt_read(dut.count, "count")
    if got != 0:
        raise AssertionError(f"MISMATCH VPS-06 REQ-3.1.6 signal=count expected=0 observed={got}")
    cg_vps_06(CntMatch("VPS-06", 0, CntSample(1, 0, 0)))
    env.scoreboard.checked["VPS-06"] += 1
    env.finish("VPS-06", 1)


@cocotb.test(timeout_time=100, timeout_unit="us")
async def test_random_seeded(dut) -> None:
    """Constrained-random en and rst_n from the testplan's constraint model, one seed."""
    env = CntEnv(dut, "test_random_seeded")
    await env.start()
    for _ in range(RAND_EDGES):
        rst_n = 0 if env.rng.random() < RAND_RST_P else 1
        en = 1 if env.rng.random() < RAND_EN_P else 0
        await env.step("VPS-02", en, rst_n)
    env.finish("VPS-02", 0)


# ==== D. Reference model and scoreboard ===========================================
class CntModel:
    """REQ-3.1.1 to REQ-3.1.4 at the ports, from the specification alone."""

    def __init__(self) -> None:
        self.count_exp = 0

    def apply(self, rst_n: int, en: int) -> int:
        if not rst_n:
            self.count_exp = 0  # REQ-3.1.1
        elif en:
            self.count_exp = (self.count_exp + 1) % (COUNT_MAX + 1)  # REQ-3.1.2, REQ-3.1.3
        return self.count_exp  # REQ-3.1.4 when en is 0


@dataclass(frozen=True)
class CntMatch:
    """One checked edge for the coverage model."""

    vps: str
    count_before: int
    sample: CntSample


def cnt_scenario(sample: CntSample, count_before: int) -> tuple[str, str]:
    """The VPS scenario and requirement an edge exercises, from observed values."""
    if not sample.rst_n:
        return ("VPS-05", "REQ-3.1.1") if sample.en else ("VPS-01", "REQ-3.1.1")
    if not sample.en:
        return "VPS-03", "REQ-3.1.4"
    if count_before == COUNT_MAX:
        return "VPS-04", "REQ-3.1.3"
    return "VPS-02", "REQ-3.1.2"


class CntScoreboard:
    """Compares every edge with the model: one MISMATCH line per difference."""

    def __init__(self, test: str, seed: int) -> None:
        self.test = test
        self.seed = seed
        self.model = CntModel()
        self.count_before = 0
        self.edges = 0
        self.checked: Counter[str] = Counter()
        self.listeners: list[Callable[[CntMatch], None]] = []

    def observe(self, sample: CntSample) -> None:
        vps, req = cnt_scenario(sample, self.count_before)
        expected = self.model.apply(sample.rst_n, sample.en)
        if sample.count != expected:
            raise AssertionError(
                f"MISMATCH {vps} {req} signal=count expected={expected} "
                f"observed={sample.count} test={self.test} seed={self.seed}"
            )
        self.edges += 1
        self.checked[vps] += 1
        for listener in self.listeners:
            listener(CntMatch(vps, self.count_before, sample))
        self.count_before = sample.count


# ==== E. Coverage model ===========================================================
def cnt_class(value: int) -> str:
    """The count classes the VPS distinguishes: 0, 1 to 14, 15."""
    return "zero" if value == 0 else "max" if value == COUNT_MAX else "mid"


def cnt_xf(m: CntMatch) -> str:
    return cnt_class(m.count_before)


@CoverPoint("cg_vps_01.count_at", xf=cnt_xf, bins=["mid", "max"])
def cg_vps_01(m: CntMatch) -> None:
    """VPS-01: the count held when the reset came."""


@CoverPoint("cg_vps_02.count_at", xf=cnt_xf, bins=["zero", "mid"])
def cg_vps_02(m: CntMatch) -> None:
    """VPS-02: the count an increment started from."""


@CoverPoint("cg_vps_03.count_at", xf=cnt_xf, bins=["zero", "mid", "max"])
def cg_vps_03(m: CntMatch) -> None:
    """VPS-03: the count held with en 0."""


@CoverPoint("cg_vps_04.count_at", xf=cnt_xf, bins=["max"])
def cg_vps_04(m: CntMatch) -> None:
    """VPS-04: the wrap from 15."""


@CoverPoint("cg_vps_05.count_at", xf=cnt_xf, bins=["mid"])
def cg_vps_05(m: CntMatch) -> None:
    """VPS-05: reset with en 1 at a non-zero count."""


@CoverPoint("cg_vps_06.count_at", xf=cnt_xf, bins=["zero"])
def cg_vps_06(m: CntMatch) -> None:
    """VPS-06: count at zero, 4 bits wide."""


CNT_COVERGROUPS: dict[str, Callable[[CntMatch], None]] = {
    "VPS-01": cg_vps_01,
    "VPS-02": cg_vps_02,
    "VPS-03": cg_vps_03,
    "VPS-04": cg_vps_04,
    "VPS-05": cg_vps_05,
    "VPS-06": cg_vps_06,
}


def cnt_cov_sample(match: CntMatch) -> None:
    CNT_COVERGROUPS[match.vps](match)


def cnt_cov_export() -> None:
    """This process's coverage, for cocotb_sim to collect."""
    coverage_db.export_to_xml(filename="coverage.xml")


# ==== F. Properties ===============================================================
# None: the risk map requires no formal property for counter4d.

# ==== G. Regression manifest ======================================================
# verif/seeds.yaml: locked seeds written by cocotb_sim.
