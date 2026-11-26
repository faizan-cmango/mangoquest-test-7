// Module: counter4d
// Project: counter4d
// SAD: 3.1
// Risk: LOW
// REQ-IDs: REQ-3.1.1, REQ-3.1.2, REQ-3.1.3, REQ-3.1.4, REQ-3.1.5, REQ-3.1.6
// Author: Kemi
// PURPOSE: 4-bit wrapping up-counter, enable, synchronous active-low reset.
// DEBUG NOTES: probe cnt_value_ff first, then en and rst_n; add wave cnt_*
// KNOWN GOTCHAS: count is undefined until the first rising edge with rst_n 0 (ADR-03).
// PREFIXES: cnt
`default_nettype none
`timescale 1ns/1ps

module counter4d (
    input  wire logic       clk,    // REQ-3.1.5
    input  wire logic       rst_n,  // REQ-3.1.1
    input  wire logic       en,     // REQ-3.1.2
    output      logic [3:0] count   // REQ-3.1.2, REQ-3.1.6
);

  // -- A · SIGNALS — SAD 3.1 ---
  logic [3:0] cnt_value_ff;  // REQ-3.1.1, REQ-3.1.2, REQ-3.1.3, REQ-3.1.4
  logic [3:0] cnt_value_next;  // REQ-3.1.2, REQ-3.1.3, REQ-3.1.4

  // -- B · UNUSED — SAD 3.1 ---

  // -- C · NEXT STATE — SAD 3.1 ---
  // .. cnt : increment with wrap, else hold — REQ-3.1.2, REQ-3.1.3, REQ-3.1.4
  assign cnt_value_next = en ? (cnt_value_ff + 4'd1) : cnt_value_ff;

  // -- D · REGISTER — SAD 3.1 ---
  // .. cnt : counter register — REQ-3.1.1, REQ-3.1.5
  always_ff @(posedge clk) begin
    if (!rst_n) begin
      cnt_value_ff <= '0;
    end else begin
      cnt_value_ff <= cnt_value_next;
    end
  end

  // -- E · GLUE — SAD 3.1 ---

  // -- F · ASSERTIONS — SAD 3.1 ---

  // -- G · OUTPUTS — SAD 3.1 ---
  assign count = cnt_value_ff;  // REQ-3.1.6

endmodule

`default_nettype wire
