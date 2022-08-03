import PCANBasic as pb
import Chroma62000H as ch
import time as tm
import threading
# import tkinter
# import psutil


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

    # Send a message to inform that the main code is running
    print("PCAN Signal Received. CAN Loop Running...")

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

    # ----------------------------- Serial Loop ----------------------------- #
    while(1):
        if (requested_voltage_local != requested_voltage):
            # send voltage request to PSU
            a = 0

        if (requested_current_local != requested_current):
            # send current request to PSU
            b = 0


def InfoThread():
    global msg_count, errors, measured_voltage, measured_current

    # Info message rate in seconds
    rate = 10

    # timing for status print
    app_start_time = tm.perf_counter()
    curr_app_time = tm.perf_counter()
    prev_app_time = tm.perf_counter()

    # ------------------------------ Info Loop ------------------------------ #
    while(1):
        if ((curr_app_time - prev_app_time) > rate):
            print("Run Time: " + f'{(curr_app_time-app_start_time)/60:.2f}'
                    + "mins \tCAN Msg Count: " + str(msg_count))
            print("\tPSU Measured Voltage: " + f'{measured_voltage:.2f}' + "V \tPSU Measured Current: " + f'{measured_current:.2f}' + "A")

            curr_app_time = tm.perf_counter()
            prev_app_time = tm.perf_counter()
        else:
            curr_app_time = tm.perf_counter()

###############################################################################
#                                  INIT                                       #
###############################################################################

# Initialize global variables
msg_count = 0
errors = 0

requested_voltage = 0.0
requested_current = 0.0

measured_voltage = 0.0
measured_current = 0.0


# Initialize pcan object
pcan = pb.PCANBasic()

pcan_handle = pb.PCAN_USBBUS1 # Get PCAN Channel
baudrate = pb.PCAN_BAUD_500K # Setup Connection's Baud Rate
result = pcan.Initialize(pcan_handle, baudrate) # initialize device

# Initialize Chroma PSU object
chroma = ch.CHROMA_62000H()

# Initialization flag - assume no errors
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

if chroma.status == "Not Connected":
    init_complete = False

    print("Chroma PSU Error!")
    print(chroma.error_reason)

if init_complete:
    x = threading.Thread(target=CANThread)
    y = threading.Thread(target=SerialThread)
    z = threading.Thread(target=InfoThread)

    print("Running Shore Charger Translation Layer...")
    x.start()
    y.start()
    z.start()


print(".\n.\n.\nProgram Exit")
exit(0)
