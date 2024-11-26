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

TMF8806 Circuitpython v8.0.5 implementation specific to the RP2040 (Pin layout)

Configure device, read xtalk

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
CLR_INT = 0x01
EN_INT = 0x01
RES_INT = 0x01
I2C_FREQUENCY_1MHz = 1000000
NUMBER_OF_MEASUREMENTS = 100

"""
TMF8806 register addresses
"""
app_req_id_reg = 0x02
cmd_reg = 0x10
stat_reg = 0x1D
factory_cal_reg = 0x20
enable_reg = 0xE0
int_stat_reg = 0xE1
int_en_reg = 0xE2

"""
Variables
"""
result = bytearray(7)
int_stat_result = bytearray(1)
number_of_measurements = 100
xtalk_min = 1000000
xtalk_max = 0
xtalk_avg = 0

"""
Alternate command data strings, changes period & # of iterations

Command =       [addr, cd9,  cd8,  cd7,  cd6,  cd5,  cd4,  cd3,  cd2,   cd1,  cd0,  cmd]
Command =       [addr, emc,  ss, cal/st, alg,  gpio,gpiot,thres,rep_ms,it_lsb,it_msb,start]
start_measure = [0x06, 0x00, 0x00, 0x11, 0x02, 0x00, 0x00, 0x06, 0xFE, 0x0A, 0x00, 0x02]            # 1Hz continuous sample rate, 10k iterations
start_measure = [0x06, 0x00, 0x00, 0x11, 0x02, 0x00, 0x00, 0x06, 0xFE, 0xFF, 0x01, 0x02]            # 1Hz continuous sample rate, 511k iterations
start_measure = [0x06, 0x00, 0x00, 0x11, 0x02, 0x03, 0x01, 0x00, 0xC8, 0x01, 0x00, 0x02]            # 10Hz continuous sample rate, 900k iterations
start_measure = [0x06, 0x00, 0x00, 0x11, 0x02, 0x00, 0x00, 0x06, 0x1E, 0xA0, 0x0F, 0x02]            # 10Hz continuous sample rate, 4000k iterations 
start_measure = [0x06, 0x00, 0x00, 0x11, 0x02, 0x00, 0x00, 0x06, 0x1E, 0x84, 0x03, 0x02]            # 30Hz continuous sample rate, 900k iterations
"""

start_measure =  [0x06, 0x00, 0x00, 0x11, 0x02, 0x00, 0x00, 0x06, 0x1E, 0x84, 0x03, 0x02]             # 30Hz continuous sample rate, 900k iterations

"""
Calibration data - individual to each device
"""
cal_data = [factory_cal_reg, 0x02,0x00,0x00,0xF9,0xCF,0xE0,0x3F,0x7F,0x03,0x00,0x40,0x20,0x00,0x04]

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
    res = bytearray(1)
    tmf8806_enablepin.value = False                 # pull enable pin low for 3 milliseconds to allow cap to discharge
    time.sleep(0.003)
    tmf8806_enablepin.value = True
    time.sleep(0.002)                               # 2ms boot time

    tmf8806.writeto_then_readfrom(SLAVE_ADDR, bytes([enable_reg]), res)  # read state of device
    while (res[0] != BSL_SLEEP):
        tmf8806.writeto_then_readfrom(SLAVE_ADDR, bytes([enable_reg]), res)  

    tmf8806.writeto_then_readfrom(SLAVE_ADDR, bytes([enable_reg, PON]), res)     # wake-up device
    while (res[0] != BSL_READY):
        tmf8806.writeto_then_readfrom(SLAVE_ADDR, bytes([enable_reg]), res)      
    
    tmf8806.writeto_then_readfrom(SLAVE_ADDR, bytes([app_req_id_reg, APP0]), res)    
    tmf8806.writeto_then_readfrom(SLAVE_ADDR, bytes([app_req_id_reg]), res)          # check the App Id here to make sure app is running
    while (res[0] != APP0):
        tmf8806.writeto_then_readfrom(SLAVE_ADDR, bytes([app_req_id_reg]), res)          

def load_cal():
    """
    Load calibration data to device
    """
    tmf8806.writeto(SLAVE_ADDR, bytes(cal_data))

def start_measurements():
    """
    Write command data string to TMF8806 device
    """
    tmf8806.writeto(SLAVE_ADDR, bytes([int_stat_reg, CLR_INT])) # clear any outdated (but still pending) interrupt (e.g. from previous run)
    tmf8806.writeto(SLAVE_ADDR, bytes([int_en_reg, EN_INT]))    # enable interrupts before starting to measure, so to not miss the first one
    tmf8806.writeto(SLAVE_ADDR, bytes(start_measure))           # send command string

"""
 Main code - Wait for result ready flag and measure crosstalk levels, print min, max and average value for 100 measurements
"""

while not tmf8806.try_lock():
    pass

try:
    enable_tmf8806()         # pull enable pin high and wait for CPU ready
    load_cal()               # load factory calibration information
    start_measurements()     # start continuous measurements as per start_measurement configuration
    
    tmf8806.writeto_then_readfrom(SLAVE_ADDR, bytes([int_stat_reg]), int_stat_result)   # just read 1 byte
    
    print("Measuring crosstalk, please wait...\n")
    
    for loop in range(NUMBER_OF_MEASUREMENTS):                       # loop for "number_of_measurements" measurements
        while (int_stat_result[0] != RES_INT):                             # poll interrupt flag for result ready indication
            tmf8806.writeto_then_readfrom(SLAVE_ADDR, bytes([int_stat_reg]), int_stat_result)

        tmf8806.writeto(SLAVE_ADDR, bytes([int_stat_reg, CLR_INT]))  
        tmf8806.writeto_then_readfrom(SLAVE_ADDR, bytes([0x3C]), result)   # read result block
        
        if (result[0] + 0xFF * result[1]) < xtalk_min:                     # is this the lowest crosstalk measurement?
            xtalk_min = (result[0] + 0xFF * result[1])
        
        if (result[0] + 0xFF * result[1]) > xtalk_max:                     # is this the highest crosstalk measurement?
            xtalk_max = (result[0] + 0xFF * result[1])
                
        xtalk_avg = xtalk_avg + (result[0] + 0xFF * result[1])             # sum xtalk for average calculation
        
        tmf8806.writeto_then_readfrom(SLAVE_ADDR, bytes([int_stat_reg]), int_stat_result) # reset interrupt for next measurement result

    print("Crosstalk minimum value:", xtalk_min)                           # print min, max and average results
    print("Crosstalk maximum value:", xtalk_max)
    print("Average of 100 measurements:",round(xtalk_avg/NUMBER_OF_MEASUREMENTS))


finally:
    tmf8806.unlock()
    