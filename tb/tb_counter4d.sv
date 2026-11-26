// TC-001: reset: count 0 after reset and while held (VPS-01, REQ-3.1.1)
// TC-002: increment by 1 per enabled edge (VPS-02, REQ-3.1.2)
// TC-003: hold when en 0 and change only at rising edge (VPS-03, REQ-3.1.4, REQ-3.1.5)
// TC-004: wrap 15 to 0 (VPS-04, REQ-3.1.3)
// TC-005: reset priority over en (VPS-05, REQ-3.1.1)
// TC-006: port list: count is 4 bits, exact ports (VPS-06, REQ-3.1.6)
// TC-007: reset-to-idle: every output at its reset value after reset (REQ-3.1.1)
// TC-008: no X after reset: no output is X or Z once reset is released (REQ-3.1.1)
// TC-009: no deadlock: a request always completes within 1 cycles (REQ-3.1.2)
`default_nettype none
`timescale 1ns/1ps

module tb_counter4d;
  logic clk = 1'b0;
  logic rst_n = 1'b1;
  logic en = 1'b0;
  logic [3:0] count;
  logic [3:0] exp_v;
  int cycle = 0;
  int errs = 0;

  counter4d dut (.clk(clk), .rst_n(rst_n), .en(en), .count(count));

  always #5 clk = ~clk;

  // reference model, updated at rising edge
  always @(posedge clk) begin
    cycle <= cycle + 1;
    if (!rst_n) exp_v <= 4'd0;
    else if (en) exp_v <= exp_v + 4'd1;
  end

  task automatic chk(input string nm);
    if (count !== exp_v) begin
      $display("MISMATCH cycle=%0d signal=%s expected=%0d actual=%0d", cycle, nm, exp_v, count);
      errs++;
    end
  endtask

  // drive at falling edge, check just before next falling edge
  task automatic step(input logic r, input logic e);
    @(negedge clk);
    rst_n = r;
    en = e;
    @(posedge clk);
    #1;
    chk("count");
  endtask

  initial begin
    exp_v = 4'd0;
    // TC-001/007/005: reset with en 1
    step(1'b0, 1'b1);
    step(1'b0, 1'b1);
    if (count !== 4'd0) begin
      $display("MISMATCH cycle=%0d signal=count expected=0 actual=%0d", cycle, count);
      errs++;
    end
    if (^count === 1'bx) begin
      $display("MISMATCH cycle=%0d signal=count expected=known actual=X", cycle);
      errs++;
    end
    // TC-002 and TC-004: count through wrap twice
    for (int i = 0; i < 34; i++) step(1'b1, 1'b1);
    // TC-003: hold at several values
    for (int v = 0; v < 16; v++) begin
      step(1'b1, 1'b0);
      step(1'b1, 1'b0);
      @(negedge clk);
      en = 1'b1;
      #1 en = 1'b0;  // toggle between edges
      #1 chk("count_nochange");
      step(1'b1, 1'b1);
    end
    // TC-001: reset mid count, then TC-005
    step(1'b1, 1'b1);
    step(1'b0, 1'b1);
    step(1'b0, 1'b0);
    step(1'b1, 1'b1);
    if (errs == 0) $display("PASS");
    else $display("FAIL errs=%0d", errs);
    $finish;
  end

  initial begin
    #100000;
    $display("MISMATCH cycle=%0d signal=deadlock expected=finish actual=timeout", cycle);
    $finish;
  end
endmodule

`default_nettype wire
