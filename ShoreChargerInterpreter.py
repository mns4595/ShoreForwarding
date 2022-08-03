import PCANBasic as pb
import time as tm
import threading
import tkinter
# import psutil


def CANThread():
    global pcan, pcan_handle, RequestedVoltage, RequestedCurrent

    start_time = 0

    # Message counter
    msg_count = 0
    # Start the error counter
    errors = 0

    wait_counter = 0
    # Wait for the module to start (i.e.: The clock is running)
    while start_time == 0:
        if (wait_counter % 300000 == 0):
            wait_counter = 0
            print("Waiting for PCAN Signal...")

        dumdum = pcan.Read(pcan_handle)
        start_time = dumdum[2].micros + 1000 * dumdum[2].millis + \
            int('0x100000000', 16) * 1000 * dumdum[2].millis_overflow

        wait_counter = wait_counter + 1

    # timing for status print
    app_start_time = tm.perf_counter()
    curr_app_time = tm.perf_counter()
    prev_app_time = tm.perf_counter()

    # Send a message to inform that the main code is running
    print("PCAN Signal Received. Main Loop Running...")

    # ------------------------------ CAN Loop ------------------------------ #
    while(1):
        if ((curr_app_time - prev_app_time) > 30):
            print("Run Time: " + f'{(curr_app_time-app_start_time)/60:.2f}'
                  + "mins \tMessage Count: " + str(msg_count))

            curr_app_time = tm.perf_counter()
            prev_app_time = tm.perf_counter()
        else:
            curr_app_time = tm.perf_counter()

        # We create a TPCANMsg message structure
        # this is always read in order to clear the buffer
        CANMsg = pcan.Read(pcan_handle)

        # Parse the message elements
        errors = errors + CANMsg[0]
        msg = CANMsg[1]
        time = CANMsg[2]

        current_time = time.micros + 1000 * time.millis + \
            int('0x100000000', 16) * 1000 * time.millis_overflow

        # Use this for file printing
        if ((msg.ID != 0)):
            msg_count = msg_count + 1

            # TODO - placeholder
            if (msg.ID == 0x7FF):
                RequestedVoltage = ((msg.DATA[7] << 24) | (msg.DATA[6] << 16) | (
                    msg.DATA[5] << 8) | (msg.DATA[4]))/1000.0

                RequestedCurrent = ((msg.DATA[3] << 24) | (msg.DATA[2] << 16) | (
                    msg.DATA[1] << 8) | (msg.DATA[0]))/1000.0


def SerialThread():
    global RequestedVoltage, RequestedCurrent

    # local vars
    requested_voltage = 0.0
    requested_current = 0.0

    if (requested_voltage != RequestedVoltage):
        # send voltage request to PSU
        a = 0

    if (requested_current != RequestedCurrent):
        # send current request to PSU
        b = 0

###############################################################################
#                                  INIT                                       #
###############################################################################

# ------------------------------ PCAN Objects ------------------------------ #


# Initialize common variables
# Requested pack voltage
RequestedVoltage = 0.0
# Requested current
RequestedCurrent = 0.0


# Initialize pcan object
pcan = pb.PCANBasic()
# Get PCAN Channel
pcan_handle = pb.PCAN_USBBUS1

# Setup Connection's Baud Rate
baudrate = pb.PCAN_BAUD_500K

result = pcan.Initialize(pcan_handle, baudrate)

# Initialization flag
init_complete = True

if result != pb.PCAN_ERROR_OK:
    init_complete = False

    if result != pb.PCAN_ERROR_CAUTION:
        print("PCAN Error!")
    else:
        print('******************************************************')
        print('The bitrate being used is different than the given one')
        print('******************************************************')
        result = pb.PCAN_ERROR_OK

chroma = True  # TODO - remove
if ~chroma:
    init_complete = False

if init_complete:
    x = threading.Thread(target=CANThread)
    y = threading.Thread(target=SerialThread)

    print("Running Shore Charger Translation Layer...")
    x.start()
    y.start()


print(".\n.\n.\nProgram Exit")
exit(0)
