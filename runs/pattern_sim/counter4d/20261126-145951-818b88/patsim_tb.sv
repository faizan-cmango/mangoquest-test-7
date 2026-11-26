`timescale 1ns/1ps
module quest_patsim;
  reg [0:0] clk;
  reg [0:0] rst_n;
  reg [0:0] en;
  wire [3:0] count;
  reg [0:0] scan_en;
  reg [0:0] scan_in;
  wire [0:0] scan_out;
  counter4d dut (.clk(clk), .rst_n(rst_n), .en(en), .count(count), .scan_en(scan_en), .scan_in(scan_in), .scan_out(scan_out));
  integer errors, checks, cycle, pat, t, failed_at, shown;
  reg [3:0] load_mem [0:17];
  reg [3:0] unload_mem [0:17];
  reg [1:0] pi_mem [0:17];
  reg [3:0] po_mem [0:17];
  reg [1:0] captures_mem [0:17];
  task pulse; begin #10; clk = 1; #20; clk = 0; #10; end endtask
  initial begin
    clk = 0;
    rst_n = 0;
    en = 0;
    scan_en = 0;
    scan_in = 0;
    load_mem[0] = 4'b0010;
    unload_mem[0] = 4'b0010;
    pi_mem[0] = 2'b01;
    po_mem[0] = 4'b0010;
    captures_mem[0] = 1;
    load_mem[1] = 4'b1100;
    unload_mem[1] = 4'b0000;
    pi_mem[1] = 2'b00;
    po_mem[1] = 4'b1100;
    captures_mem[1] = 1;
    load_mem[2] = 4'b0111;
    unload_mem[2] = 4'b0000;
    pi_mem[2] = 2'b00;
    po_mem[2] = 4'b0111;
    captures_mem[2] = 1;
    load_mem[3] = 4'b1100;
    unload_mem[3] = 4'b1101;
    pi_mem[3] = 2'b11;
    po_mem[3] = 4'b1100;
    captures_mem[3] = 1;
    load_mem[4] = 4'b0101;
    unload_mem[4] = 4'b0101;
    pi_mem[4] = 2'b01;
    po_mem[4] = 4'b0101;
    captures_mem[4] = 1;
    load_mem[5] = 4'b0011;
    unload_mem[5] = 4'b0100;
    pi_mem[5] = 2'b11;
    po_mem[5] = 4'b0011;
    captures_mem[5] = 1;
    load_mem[6] = 4'b1001;
    unload_mem[6] = 4'b1010;
    pi_mem[6] = 2'b11;
    po_mem[6] = 4'b1001;
    captures_mem[6] = 1;
    load_mem[7] = 4'b1111;
    unload_mem[7] = 4'b1111;
    pi_mem[7] = 2'b01;
    po_mem[7] = 4'b1111;
    captures_mem[7] = 1;
    load_mem[8] = 4'b0010;
    unload_mem[8] = 4'b0011;
    pi_mem[8] = 2'b11;
    po_mem[8] = 4'b0010;
    captures_mem[8] = 1;
    load_mem[9] = 4'b0111;
    unload_mem[9] = 4'b1000;
    pi_mem[9] = 2'b11;
    po_mem[9] = 4'b0111;
    captures_mem[9] = 1;
    load_mem[10] = 4'b0111;
    unload_mem[10] = 4'b1001;
    pi_mem[10] = 2'b11;
    po_mem[10] = 4'b0111;
    captures_mem[10] = 2;
    load_mem[11] = 4'b0001;
    unload_mem[11] = 4'b0011;
    pi_mem[11] = 2'b11;
    po_mem[11] = 4'b0001;
    captures_mem[11] = 2;
    load_mem[12] = 4'b0100;
    unload_mem[12] = 4'b0110;
    pi_mem[12] = 2'b11;
    po_mem[12] = 4'b0100;
    captures_mem[12] = 2;
    load_mem[13] = 4'b0110;
    unload_mem[13] = 4'b1000;
    pi_mem[13] = 2'b11;
    po_mem[13] = 4'b0110;
    captures_mem[13] = 2;
    load_mem[14] = 4'b0010;
    unload_mem[14] = 4'b0100;
    pi_mem[14] = 2'b11;
    po_mem[14] = 4'b0010;
    captures_mem[14] = 2;
    load_mem[15] = 4'b1011;
    unload_mem[15] = 4'b1101;
    pi_mem[15] = 2'b11;
    po_mem[15] = 4'b1011;
    captures_mem[15] = 2;
    load_mem[16] = 4'b1110;
    unload_mem[16] = 4'b0000;
    pi_mem[16] = 2'b11;
    po_mem[16] = 4'b1110;
    captures_mem[16] = 2;
    load_mem[17] = 4'b1111;
    unload_mem[17] = 4'b0001;
    pi_mem[17] = 2'b11;
    po_mem[17] = 4'b1111;
    captures_mem[17] = 2;
    errors = 0; checks = 0; shown = 0;
    scan_en = 1;
    failed_at = -1;  // chain 0
    for (cycle = 0; cycle < 12; cycle = cycle + 1) begin
      scan_in[0] = (cycle % 4) >= 2;
      #5;
      if (cycle >= 4 && scan_out[0] !== (((cycle - 4) % 4) >= 2) && failed_at < 0) failed_at = cycle;
      #5; clk = 1; #20; clk = 0; #10;
    end
    if (failed_at < 0) $display("CHAIN TEST chain 0 length 4: sequence 0011 PASS");
    else $display("CHAIN TEST chain 0 length 4: sequence 0011 FAIL at cycle %0d", failed_at);
    for (pat = 0; pat < 18; pat = pat + 1) begin
      scan_en = 1;
      for (t = 0; t < 4; t = t + 1) begin
        scan_in[0] = load_mem[pat * 1 + 0][3 - t];
        pulse;
      end
      scan_en = 0;
      scan_in = 0;
      rst_n = pi_mem[pat][0];
      en = pi_mem[pat][1];
      scan_en = 0;
      #5;
      checks = checks + 1;
      if (count[0] !== po_mem[pat][0]) begin errors = errors + 1;
        if (shown < 50) begin shown = shown + 1; $display("MISMATCH pattern=%0d kind=po signal=count[0] expected=%b actual=%b", pat, po_mem[pat][0], count[0]); end end
      checks = checks + 1;
      if (count[1] !== po_mem[pat][1]) begin errors = errors + 1;
        if (shown < 50) begin shown = shown + 1; $display("MISMATCH pattern=%0d kind=po signal=count[1] expected=%b actual=%b", pat, po_mem[pat][1], count[1]); end end
      checks = checks + 1;
      if (count[2] !== po_mem[pat][2]) begin errors = errors + 1;
        if (shown < 50) begin shown = shown + 1; $display("MISMATCH pattern=%0d kind=po signal=count[2] expected=%b actual=%b", pat, po_mem[pat][2], count[2]); end end
      checks = checks + 1;
      if (count[3] !== po_mem[pat][3]) begin errors = errors + 1;
        if (shown < 50) begin shown = shown + 1; $display("MISMATCH pattern=%0d kind=po signal=count[3] expected=%b actual=%b", pat, po_mem[pat][3], count[3]); end end
      #5; clk = 1; #20; clk = 0; #10;
      if (captures_mem[pat] == 2) pulse;
      scan_en = 1;
      for (t = 0; t < 4; t = t + 1) begin
        #5;
        if (t < 4) begin checks = checks + 1;
          if (scan_out[0] !== unload_mem[pat * 1 + 0][3 - t]) begin errors = errors + 1;
            if (shown < 50) begin shown = shown + 1; $display("MISMATCH pattern=%0d kind=unload chain=0 position=%0d expected=%b actual=%b", pat, 3 - t, unload_mem[pat * 1 + 0][3 - t], scan_out[0]); end end end
        #5; clk = 1; #20; clk = 0; #10;
      end
    end
    $display("PATSIM: 10 stuck-at + 8 transition patterns, 18 patterns, %0d checks, %0d errors", checks, errors);
    if (errors == 0) $display("PATSIM PASS"); else $display("PATSIM FAIL");
    $finish;
  end
endmodule
