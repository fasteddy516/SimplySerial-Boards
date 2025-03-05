# SimplySerial-Boards

###### USB Device recognition for SimplySerial
  
# Description

SimplySerial-Boards provides the `boards.json` data file used by [SimplySerial](https://github.com/fasteddy516/SimplySerial) to identify connected USB devices and serial ports.  This file is updated automatically on a weekly basis (only if devices have been added/removed/modified), and can be incorporated into SimplySerial by running the command `ss.exe -updateboards`.

Currently, the list of boards is generated almost entirely by examining the `main` branch of the [CircuitPython](https://github.com/adafruit/circuitpython) repository, along with a few manually added entries.  If there are additional devices that you would like to have added to the file, please raise an issue in this repository and be sure to include the USB Vendor ID (VID), Product ID (PID), manufacturer and model of the device(s) you would like to see included.  New entries are not guaranteed, but will most likely be added if they are appropriate and do not conflict with existing entries.
