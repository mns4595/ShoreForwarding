import PCANBasic as pb
import Chroma62000H as ch
import time as tm
import threading
import sys

###############################################################################
#                                 THREADS                                     #
###############################################################################


def CANThread():
    global pcan, pcan_handle, msg_count, errors, requested_voltage, requested_current, \
        max_ac_current, enable_output, measured_output_enable, measured_voltage, \
        measured_current, measured_status

    # Wait for the module to start (i.e.: The clock is running)
    #start_time = 0
    #wait_counter = 0
    # while start_time == 0:
    #    if (wait_counter % 300000 == 0):
    #        wait_counter = 0
    #        print("Waiting for PCAN Signal...")

    #    dumdum = pcan.Read(pcan_handle)
    #    start_time = dumdum[2].micros + 1000 * dumdum[2].millis + \
    #        int('0x100000000', 16) * 1000 * dumdum[2].millis_overflow

    #    wait_counter = wait_counter + 1

    # Send a message to inform that the CAN code is running
    print("PCAN Signal Received. CAN Loop Running...")
    tm.sleep(0.5)

    curr_time = tm.perf_counter()
    prev_time = tm.perf_counter()

    # ------------------------------- CAN Loop ------------------------------ #
    while(1):
        # We create a TPCANMsg message structure
        # this is always read in order to clear the buffer
        CANMsg = pcan.Read(pcan_handle)

        # Parse the message elements
        errors = errors + CANMsg[0]
        rx_msg = CANMsg[1]

        # Message Receiver
        if ((rx_msg.ID != 0)):
            msg_count = msg_count + 1

            if (rx_msg.ID == 0x618):
                enable_output = (rx_msg.DATA[0] >> 7) & 0b1
                max_ac_current = (
                    (rx_msg.DATA[1] << 8) | (rx_msg.DATA[2]))/10.0
                requested_voltage = (
                    (rx_msg.DATA[3] << 8) | (rx_msg.DATA[4]))/10.0
                requested_current = (
                    (rx_msg.DATA[5] << 8) | (rx_msg.DATA[6]))/10.0

        # Messages to Send
        if((curr_time - prev_time) > 0.1):
            tx_msg = pb.TPCANMsg()
            tx_msg.ID = 0x611
            tx_msg.MSGTYPE = pb.PCAN_MESSAGE_STANDARD
            tx_msg.LEN = 8

            tx_msg.DATA[7] = (int(measured_current * 10.0) & 0x00FF)
            tx_msg.DATA[6] = ((int(measured_current * 10.0) >> 8) & 0x00FF)
            tx_msg.DATA[5] = (int(measured_voltage * 10.0) & 0x00FF)
            tx_msg.DATA[4] = ((int(measured_voltage * 10.0) >> 8) & 0x00FF)
            tx_msg.DATA[3] = 0xFF   # Not reported by Chroma PSU
            tx_msg.DATA[2] = 0xFF   # Not reported by Chroma PSU
            tx_msg.DATA[1] = 0xFF   # Not reported by Chroma PSU
            tx_msg.DATA[0] = 0xFF   # Not reported by Chroma PSU

            pcan.Write(pcan_handle, tx_msg)

            tx_msg.ID = 0x615
            tx_msg.DATA[7] = 0xFF   # Not reported by Chroma PSU
            tx_msg.DATA[6] = 0xFF   # Not reported by Chroma PSU
            tx_msg.DATA[5] = 0xFF   # Not reported by Chroma PSU
            tx_msg.DATA[4] = \
                ((True & 0b1) << 7) | \
                ((True & 0b1) << 5) | \
                ((True & 0b1) << 3)
            tx_msg.DATA[3] = 0xFF   # Not reported by Chroma PSU
            tx_msg.DATA[2] = 0xFF   # Not reported by Chroma PSU
            tx_msg.DATA[1] = 0xFF   # Not reported by Chroma PSU
            tx_msg.DATA[0] = \
                ((measured_status.ac_fault & 0b1) << 7) | \
                ((True & 0b1) << 6) | \
                ((measured_status.opp & 0b1) << 5) | \
                ((measured_status.ovp & 0b1) << 4)

            pcan.Write(pcan_handle, tx_msg)

            curr_time = tm.perf_counter()
            prev_time = tm.perf_counter()
        else:
            curr_time = tm.perf_counter()


def SerialThread():
    global requested_voltage, requested_current, measured_voltage, measured_current, \
        enable_output, measured_output_enable, measured_status

    # local vars
    requested_voltage_local = 0.0
    requested_current_local = 0.0
    enable_output_local = False

    curr_time = tm.perf_counter()
    prev_time = tm.perf_counter()

    # Send a message to inform that the PSU code is running
    print("Chroma Signal Received. Serial Loop Running...")
    tm.sleep(0.5)

    # ----------------------------- Serial Loop ----------------------------- #
    while(1):
        if (requested_voltage_local != requested_voltage):
            # send voltage request to PSU
            requested_voltage_local = requested_voltage
            chroma.SetVoltage(requested_voltage)

        if (requested_current_local != requested_current):
            # send current request to PSU
            requested_current_local = requested_current
            chroma.SetCurrent(requested_current)

        if (enable_output_local != enable_output):
            enable_output_local = enable_output
            if (enable_output):
                chroma.EnableOutput()
            else:
                chroma.DisableOutput()

        if((curr_time - prev_time) > 0.5):
            measured_voltage = chroma.MeasureVoltage()
            measured_current = chroma.MeasureCurrent()
            measured_output_enable = chroma.GetOutputState()
            measured_status = chroma.FetchStatus()

            curr_time = tm.perf_counter()
            prev_time = tm.perf_counter()
        else:
            curr_time = tm.perf_counter()


def InfoThread():
    global msg_count, errors, measured_voltage, measured_current, info_rate, measured_output_enable

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
        if (measured_output_enable == True):
            output_enable_string = "ON"
        else:
            output_enable_string = "OFF"

        if ((curr_app_time - prev_app_time) > info_rate):
            print("Run Time: " + f'{(curr_app_time-app_start_time)/60:.2f}'
                  + "mins    CAN Msg Count: " + str(msg_count) + "    "
                    + "PSU Measured Voltage: " + f'{measured_voltage:.2f}'
                    + " V    "
                    + "PSU Measured Current: " + f'{measured_current:.2f}'
                    + " A" + "    Output is " + output_enable_string)

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
measured_output_enable = False

max_ac_current = 0.0
enable_output = False

info_rate = 10  # Info message rate in seconds

measured_status = ch.ChromaStatus()


# Initialize pcan object
print("Initializing PCAN")
pcan = pb.PCANBasic()

pcan_handle = pb.PCAN_USBBUS1  # Get PCAN Channel
baudrate = pb.PCAN_BAUD_500K  # Setup Connection's Baud Rate
result = pcan.Initialize(pcan_handle, baudrate)  # initialize device

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

chroma.ConfigureDefaultProtections()

x = threading.Thread(target=CANThread, daemon=True)
y = threading.Thread(target=SerialThread, daemon=True)
z = threading.Thread(target=InfoThread, daemon=True)

print("\nShore Charger Translation Layer Running!")
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
        print("'x' - Terminate program\n" +
              "'r' - Change info print rate")
    else:
        print("Invalid command! Enter '?' for command list\n")
