import PCANBasic as pb
import Chroma62000H as ch
import time as tm
import threading
import sys

###############################################################################
#                                 THREADS                                     #
###############################################################################

def CANThread():
    global pcan, pcan_handle, msg_count, errors, requested_voltage, requested_current

    # Wait for the module to start (i.e.: The clock is running)
    start_time = 0
    wait_counter = 0
    while start_time == 0:
        if (wait_counter % 300000 == 0):
            wait_counter = 0
            print("Waiting for PCAN Signal...")

        dumdum = pcan.Read(pcan_handle)
        start_time = dumdum[2].micros + 1000 * dumdum[2].millis + \
            int('0x100000000', 16) * 1000 * dumdum[2].millis_overflow

        wait_counter = wait_counter + 1

    # Send a message to inform that the CAN code is running
    print("PCAN Signal Received. CAN Loop Running...")
    tm.sleep(0.5)

    # ------------------------------- CAN Loop ------------------------------ #
    while(1):
        # We create a TPCANMsg message structure
        # this is always read in order to clear the buffer
        CANMsg = pcan.Read(pcan_handle)

        # Parse the message elements
        errors = errors + CANMsg[0]
        msg = CANMsg[1]

        # Use this for file printing
        if ((msg.ID != 0)):
            msg_count = msg_count + 1

            # TODO - placeholder
            if (msg.ID == 0x7FF):
                requested_voltage = ((msg.DATA[7] << 24) | (msg.DATA[6] << 16) | (
                    msg.DATA[5] << 8) | (msg.DATA[4]))/1000.0

                requested_current = ((msg.DATA[3] << 24) | (msg.DATA[2] << 16) | (
                    msg.DATA[1] << 8) | (msg.DATA[0]))/1000.0


def SerialThread():
    global requested_voltage, requested_current

    # local vars
    requested_voltage_local = 0.0
    requested_current_local = 0.0

    # Send a message to inform that the PSU code is running
    print("Chroma Signal Received. Serial Loop Running...")
    tm.sleep(0.5)

    # ----------------------------- Serial Loop ----------------------------- #
    while(1):
        if (requested_voltage_local != requested_voltage):
            # send voltage request to PSU
            a = 0

        if (requested_current_local != requested_current):
            # send current request to PSU
            b = 0


def InfoThread():
    global msg_count, errors, measured_voltage, measured_current, info_rate

    # timing for status print
    app_start_time = tm.perf_counter()
    curr_app_time = tm.perf_counter()
    prev_app_time = tm.perf_counter()

    # Send a message to inform that the main code is running
    print("Info Loop Running...")
    tm.sleep(0.5)

    print("")
    # ------------------------------ Info Loop ------------------------------ #
    while(1):
        if ((curr_app_time - prev_app_time) > info_rate):
            print("Run Time: " + f'{(curr_app_time-app_start_time)/60:.2f}'
                    + "mins    CAN Msg Count: " + str(msg_count) + "    " \
                    + "PSU Measured Voltage: " + f'{measured_voltage:.2f}' \
                    + " V    " \
                    + "PSU Measured Current: " + f'{measured_current:.2f}' \
                    + " A")

            curr_app_time = tm.perf_counter()
            prev_app_time = tm.perf_counter()
        else:
            curr_app_time = tm.perf_counter()

###############################################################################
#                                  MAIN                                       #
###############################################################################
def ExitProgram():
    print(".\n.\n.\nProgram Exit")
    sys.exit()


print("Program Start...\n")

# Initialize global variables
msg_count = 0
errors = 0

requested_voltage = 0.0
requested_current = 0.0

measured_voltage = 0.0
measured_current = 0.0

info_rate = 10 # Info message rate in seconds


# Initialize pcan object
print("Initializing PCAN")
pcan = pb.PCANBasic()

pcan_handle = pb.PCAN_USBBUS1 # Get PCAN Channel
baudrate = pb.PCAN_BAUD_500K # Setup Connection's Baud Rate
result = pcan.Initialize(pcan_handle, baudrate) # initialize device

if result != pb.PCAN_ERROR_OK:
    if result != pb.PCAN_ERROR_CAUTION:
        print("PCAN Error!")
    else:
        print('******************************************************')
        print('The bitrate being used is different than the given one')
        print('******************************************************')
        result = pb.PCAN_ERROR_OK

    ExitProgram()

# Initialize Chroma PSU object
print("Initializing Chroma")
chroma = ch.CHROMA_62000H()

if chroma.status == "Not Connected":
    print("Chroma PSU Error! " + chroma.error_reason)

    ExitProgram()


x = threading.Thread(target=CANThread, daemon=True)
y = threading.Thread(target=SerialThread, daemon=True)
z = threading.Thread(target=InfoThread, daemon=True)

print("\nShore Charger Translation Layer Running...")
x.start()
y.start()
z.start()

while(True):
    user_input = str(input())

    if user_input == "x":
        ExitProgram()
    elif user_input == "r":
        print("Enter new info rate in seconds:")
        new_rate = float(input())
        info_rate = new_rate
    elif user_input == "?":
        print("'x' - Terminate program\n" + \
              "'r' - Change info print rate")
    else:
        print("Invalid command! Enter '?' for command list\n")
