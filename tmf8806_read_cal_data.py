"""
 *****************************************************************************
 * Copyright by ams OSRAM AG                                                 *
 * All rights are reserved.                                                  *
 *                                                                           *
 * IMPORTANT - PLEASE READ CAREFULLY BEFORE COPYING, INSTALLING OR USING     *
 * THE SOFTWARE.                                                             *
 *                                                                           *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS       *
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT         *
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS         *
 * FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT  *
 * OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,     *
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT          *
 * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,     *
 * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY     *
 * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT       *
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE     *
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.      *
 *****************************************************************************

TMF8806 CircuitPython v8.0.5 implementation specific to the RP2040 (Pin layout)

Device calibration and print calibration data example

"""

import time
import board
import busio
import digitalio

"""
Constants
"""
SLAVE_ADDR = 0x41
BSL_SLEEP = 0x00
BSL_READY = 0x41
PON = 0x01
APP0 = 0xC0
I2C_FREQUENCY_1MHz = 1000000

"""
TMF8806 register addresses
"""
app_req_id_reg = 0x02
cmd_reg = 0x10
stat_reg = 0x1D
reg_contents_reg = 0x1E
factory_cal_reg = 0x20
enable_reg = 0xE0

"""
Data array
"""
result = bytearray(14)

"""
Command string to begin factory calibration routine
"""
start_cal = [ 0x06, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x64, 0x00, 0xA0, 0x0A]             

"""
Configure TMF8806 Enable pin
"""
tmf8806_enablepin = digitalio.DigitalInOut(board.GP16) 
tmf8806_enablepin.direction = digitalio.Direction.OUTPUT

"""
I2C setup
"""
tmf8806 = busio.I2C(scl=board.GP7, sda=board.GP6, frequency = I2C_FREQUENCY_1MHz)

"""
Function definitions
"""

def enable_tmf8806():
    """
    Function to enable TMF8806 device
    """
    result = bytearray(1)
    tmf8806_enablepin.value = False
    tmf8806_enablepin.value = True
    time.sleep(0.1)

    tmf8806.writeto_then_readfrom(SLAVE_ADDR, bytes([enable_reg]), result)
    while (result[0] != BSL_SLEEP):
        tmf8806.writeto_then_readfrom(SLAVE_ADDR, bytes([enable_reg]), result)

    tmf8806.writeto_then_readfrom(SLAVE_ADDR, bytes([enable_reg, PON]), result)
    while (result[0] != BSL_READY):
        tmf8806.writeto_then_readfrom(SLAVE_ADDR, bytes([enable_reg]), result)
    
    tmf8806.writeto_then_readfrom(SLAVE_ADDR, bytes([app_req_id_reg, APP0]), result)
    tmf8806.writeto_then_readfrom(SLAVE_ADDR, bytes([app_req_id_reg]), result)
    while (result[0] != APP0):
        tmf8806.writeto_then_readfrom(SLAVE_ADDR, bytes([app_req_id_reg]), result)

def start_calibration():
    """
    Write command data string to TMF8806 device
    """
    
    tmf8806.writeto(SLAVE_ADDR, bytes(start_cal))    
    tmf8806.writeto_then_readfrom(SLAVE_ADDR, bytes([reg_contents_reg]), result)

    while (result[0] != 0x0A):
        tmf8806.writeto_then_readfrom(SLAVE_ADDR, bytes([reg_contents_reg]), result)

"""
 Main code - enable device, start calibration and print calibration data
"""

while not tmf8806.try_lock():
    pass

try:
    enable_tmf8806()                      # pull enable pin high and wait for CPU ready
    print("Gathering calibration data\n")
    start_calibration()                   # start factory calibration routine
    
    tmf8806.writeto_then_readfrom(SLAVE_ADDR, bytes([factory_cal_reg]), result)

    print (','.join(f'{byte:02X}' for byte in result))

    print("\nCopy data to cal_data in tmf8806_basic_example.py\n")

finally:
    tmf8806.unlock()