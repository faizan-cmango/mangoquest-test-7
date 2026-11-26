# counter4d_capture.sdc -- capture view of counter4d, rendered by tola_sdc 1.0.0 (TOLA-DFT-016).
# The functional clocks for launch and capture; scan_en low and static; every capture hold atpg applied as a case analysis.
create_clock -name clk -period 10.0 [get_ports clk]
set_case_analysis 0 [get_ports scan_en]
set_false_path -from [get_ports scan_en]
set_input_delay 2.000 -clock clk [get_ports {en rst_n}]
set_output_delay 2.000 -clock clk [get_ports count[*]]
set_false_path -from [get_ports {scan_in}]
set_false_path -to [get_ports {scan_out}]
