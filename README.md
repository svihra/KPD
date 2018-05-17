# KPD
The code works with PIN diode detector setup made at class KPD at FNSPE CTU in Prague

Arduino part makes sure the data are sent in both filtered and raw form, followed by the empty line.

Python part creates interactive plotter with, receiving data from serial port (defined at the beginning), first looking for empty line and only afterwards receiving filtered and raw data.
Data are real-time plotted, with options to change x-axis range, y-axis scale and possibly saving or loading file in two column format.
