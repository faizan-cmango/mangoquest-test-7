create_clock -name clk -period 10.0000 [get_ports clk]
set_input_delay 3.0000 -clock clk [all_inputs -no_clocks]
set_output_delay 3.0000 -clock clk [all_outputs]
group_path -name reg2reg -from [all_registers] -to [all_registers]
