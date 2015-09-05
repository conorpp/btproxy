
# BT MiTM

## Bluetooth Man in The Middle tool

### Dependencies

Need 2 Bluetooth cards (either USB or internal).

Needs Linux or OSX OS.

Need bluez tools

For a debian system, run

    - sudo apt-get install bluez bluez-utils bluez-tools libbluetooth-dev python-dev

If you don't have apt-get, then lookup how to install the bluez
suite on your system. You also need to install python development headers/libraries (python-dev)

Install pybluez with pip

    - pip install pybluez

### Installation

run these commands:

    - make

The program relies on calling replace_bluetoothd.bash and bluez_simple_agent.py
As seperate processes right now.  So btproxy.py should be run in the same
directory

If you need to use python 2 or 3 specifically,
just change the PY variable in the Makefile and run
make clean && make.  A few other things need to be updated for python 3 too.

### Running

    from the project root, run ./btproxy.py to get a list of
    command arguments.

    It needs to be in the same directory as clone.so and bluez_simple_agent.py.

    To run a simple MiTM attack on two devices, run

        ./btproxy.py <master-bt-mac-address> <slave-bt-mac-address>

    e.g.

        # This will connect to the 40:14:33:66:CC:FF device and 
        # wait for a connection from F1:64:F3:31:67:88
        ./btproxy.py F1:64:F3:31:67:88 40:14:33:66:CC:FF

        # You should be able to follow the state of the program
        # from the output.  It will scan the services of both the
        # devices.  

    Where the master mac address is typically the phone and the slave mac
    address is typically the other peripherial device (headphones, keyboard, obd2 dongle, etc).

#### How to find the BT MAC Address?  

    Well, you can look it up in the settings usually for a phone.  The most
    robost way is to put the device in advertising mode and scan for it.

    There are two ways to scan for it.

    Using hcitool scan or inquiring types of inquiries:
    
        - hcitool scan
        - hcitool inq

    # To get a list of services:
        - sdptool records <bt-address>

    The master is the device the sends the connection request and the slave is 
    the device listening for something to connect to it.

### Usage

    The program will lookup the class and address of both devices
    and set the bluetooth dongles address and class to match those 
    devices, i.e. "cloning" them.

    This will fool most simple or classical bluetooth devices.

    Then it will first try connecting to the slave device from the
    cloned master adaptor.  It will make a socket for each service
    hosted by the slave and relay traffic for each one independently.
    TODO: indicate in the output which service the output is from.

    After the slave is connected, the cloned slave adaptor will be set
    to be listening for a connection.  At this point, the real master device
    should connect to the adaptor.  The MiTM connection will be complete
    and the communication will be output to STDOUT.

### Advanced Usage

    Manipulation of the traffic can be handled via python 
    in the btproxy_replace.py file.  Just edit the master_cb and
    slave_cb callback functions.  This are called upon receiving 
    data and the returned data is sent back out to the corresponding device.

    See the example functions for manipulating Pebble watch traffic in btproxy_replace.py

    This code can be edited and reloaded during runtime by entering 'r'
    into the program console. This avoids the pains of reconnecting.  Any errors
    will be caught and regular transmission will continue.

### TODO

    This code needs some serious refactoring.  I know.  In particular, things
    should be made more object oriented and error catching should be encapsulated.
    A lot of this was rushed.

    Improve the file logging of the traffic and make it more interactive for
    replays/manipulation.

    Indicate which service is which in the output.

    Provide control for disconnecting/connecting services.

    PCAP file support

    ncurses?


### How it works

    This program starts by killing the bluetoothd process, running it again with
    a LD_PRELOAD pointed to a wrapper for the bind system call to block bluetoothd
    from binding to L2CAP port 1 (SDP).  All SDP traffic goes over L2CAP port 1 so
    this makes it easy to MiTM/forward between the two devices and we don't have to
    worry about mimicking the advertising.

    The program first scans each device for their name and device class to make
    accurate clones.  It will append the string '_EVIL' to each name to make them
    distinguishable from a user perspective.  Alternatively, you can specify the
    names to use at the command line.

    The program then scans the services of the slave device.  It makes a socket
    connection to each service and open a listening port for the master device to 
    connect to.  Once the master connects, the MiTM is complete and output will be
    output to STDOUT.

### Notes

Some bluetooth devices have different methods of pairing which
makes this process more complicated.  Right now it supports
current SPP and legacy pin pairing.

This program doesn't yet have support for Bluetooth Low Energy.
A similiar approach to BLE can be taken.

### Errors

#### error accessing bluetooth device

Make sure the bluetooth adaptors are plugged in and enabled.

Run

    # See the list of all adaptors
    
    - hciconfig -a

    # Enable

    sudo hciconfig hciX up

    if you get this message

    -   Can't init device hci0: Operation not possible due to RF-kill (132)

    Then try unblocking it with the rfkill command

    - sudo rfkill unblock all



