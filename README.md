# TMF8806 (Time-of-flight) CircuitPython v8.0.5 calibration and measurement example   

This folder provides simple examples to demonstrate factory calibration and basic device startup with calibration and continuous measurements

## Requirements  

- An MCU device running Circuitpython v8.0.5, this code was developed using a TMF8806 connected to an RP2040 I2C interface
- Code was developed using Thonny v4.1.6
- CircuitPython Homepage : https://circuitpython.org/

## Files  

The project consists of 2 files:
- **tmf8806_read_cal_data.py** - CircuitPython script to configure TMF8806, start factory calibration and print out calibration data
- **tmf8806_basic_example.py** - CurcuitPython script to configure TMF8806, load factory calibration, start measurements and print out TID, Distance and confidence

## Factory calibration

Please refer to the TMF8806 datasheet(DS001097) section 6.9.1 and TMF8806 Host Driver Communication Application Note (AN001069) for full details

To achieve the performance described in the next sections, a calibration of the algorithm needs to be performed (command = 0x0A). The TMF8806 shall be embedded in the final application and the cover glass including the IR ink needs to be assembled. The calibration test shall be done in a housing with minimal ambient light and no target within 40 cm in field of view of the TMF8806.

The tmf8806_read_cal_data.py script outputs a string of 14 bytes that should be copied to the tmf8806_basic_example.py script cal_data variable.

## Basic device configuration and continuous measurement example

The tmf8806_basic_example.py will configure the sensor with the defualt settings as described in the TMF8806 datasheet(DS001097) and TMF8806 Host Driver Communication Application Note (AN001069) section 8.8.  The script includes several other configuration examples which can be used to change the basic device configuration.

The script output consists of the Transaction ID (TID), a distance (mm) and a confidence (0-63).

