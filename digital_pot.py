from machine import Pin
import main
import math

# ***********************Notice********************************
#   1.Resistor terminals A, B and W have no restrictions on
#     polarity with respect to each other.
#   2.Current through terminals A, B and W should not exceed ±1mA.
#   3.Voltages on terminals A, B and W should be within 0 - VCC.
# *************************************************************

# NTC resistances vs Dn vs RWB(Dn) resistance vs NTC curve temperatures at RWB res vs boiler flow temp
# (T_max CH = 70°C, T_min CH = 35°C, T_min out = -10°C, T_max out = 25°C)

# -10°C = 58880Ω    151		59109Ω	   -10.08°C		70°C
#  -5°C = 45950Ω    118		46219Ω		-5.12°C		65°C
#   0°C = 36130Ω    92		36063Ω		 0.03°C		60°C
#   5°C = 28600Ω    73		28640Ω		 4.97°C		55°C
#  10°C = 22800Ω    58		22781Ω		10.02°C		50°C
#  15°C = 18300Ω    47		18484Ω		14.76°C		45°C
#  20°C = 14770Ω    38		14969Ω		19.69°C		40°C
#  25°C = 12000Ω    31		12234Ω		24.53°C		35°C


csC = Pin(21, mode=Pin.OUT, value=1)

# ***********************MCP42XXX Commands************************
# potentiometer select byte
POT0_SEL = 0x11
POT1_SEL = 0x12
BOTH_POT_SEL = 0x13

# shutdown the device to put it into power-saving mode.
# In this mode, terminal A is open-circuited and the B and W terminals are shorted together.
# send new command and value to exit shutdown mode.
POT0_SHUTDOWN = 0x21
POT1_SHUTDOWN = 0x22
BOTH_POT_SHUTDOWN = 0x23

# ***********************Customized Variables**********************
# resistance value byte (0 - 255)
# The wiper is reset to the mid-scale position upon power-up, i.e. POT0_Dn = POT1_Dn = 128
POT0_Dn = 31  # boiler thinks it's 25°C outside so lowers the flow temp to 35°C
POT1_Dn = 128
BOTH_POT_Dn = 128


def set_dn(temp):
	match temp:
		case 35:
			dn = 31
		case 40:
			dn = 38
		case 45:
			dn = 47
		case 50:
			dn = 58
		case 55:
			dn = 73
		case 60:
			dn = 92
		case 65:
			dn = 118
		case 70:
			dn = 151
		case _:
			dn = 92  # 60°C
	return dn


def digital_pot_write(cmd, val):
	# val = constrain(val, 0, 255)  # constrain input value within 0 - 255
	csC(0)  # set the CS pin to low to select the chip
	main.spi.write(cmd)  # send the command and value via SPI:
	main.spi.write(val)
	csC(1)  # set the CS pin high to execute the command
