# counter4d_shift.sdc -- shift view of counter4d, rendered by tola_sdc 1.0.0 (TOLA-DFT-016).
# The ATE shift clock at 25 MHz, test mode and scan_en on, the chain timed: no false path on it.
create_clock -name shift_clk -period 40.000 [get_ports clk]
set_case_analysis 1 [get_ports scan_en]
set_input_delay 5.000 -clock shift_clk [get_ports scan_in]
set_output_delay 5.000 -clock shift_clk [get_ports scan_out]
set_false_path -to [get_ports count[*]]
