# Radio and Communications

Repository for the code for the radio and communications system of the rover
for the Domer Rover team, 2024-2026.

## Maintainers

**Please add your name and email below if you help maintain this codebase.***

- Henry Jochaniewicz (hjochani@nd.edu), graduating 2027
    - Please do not hestitate to contact me even after I graduate and really
    need something from this codebase

## TODO

- Adding authors (or any modifiers) and modification dates at the top of all files.

- Adding a proper user interface and command-line handling. Use the `argparse` library

- The socket reader writer is incomplete. There can only be one
connection between the rover and base station, and if the connection
fails, the entire program must be restarted. Additionally,
the rover side must be running before the base station,
and the rover side will not continue in the program until a connection
is made.
    - This is simply because of my lack of understanding of sockets.
    I am sure that this is not too complicated to fix.
    - N.B. This is mostly fixed by changing things to UDP rather than TCP.
    This *does* mean that there must be some other check when the rover and
    base station are disconnected / cannot send packets directly to one another.

- Dynamically changing between the two connection types as needed.
    - This feels very, *very* hard. I made it simple to swap between
    them (simply change out `SocketReaderWriter` for `SerialReaderWriter`),
    but I have no idea how to actually detect when to switch them out.
    - My best guess is to have the rover find its own distance from
    the base station and change out the variable once a certain distance
    threshold is met, or if heartbeats aren't being received.
    - N.B. This is fairly straightforward. The rover should just send a heartbeat packet
    every N seconds, and if that packet is not acknowledged, a certain number 
    of times, switch communication methods.

- The data structure for already seen messages is messy. It stores everything
in a set and simply removes 

- I *believe* acknowledgments are being set up well: there is a concurrent
set in the processing functions on both sides to catch acknowledgments.
However, it is possible that there are redundant messages being sent.

- It would be good to write a simple abstraction over creating
messages and decoding messages of different types.
    - e.g. make a function like:
    ```python
    def createAcknowledgmentMessage(messageID : int) -> Message:
        pass
    ```
    for each message type. This has already been done
    for the acknowledgments (in `messageProcessor.py`), but it might
    be best to abstract this to its own module?

- Currently, driving from the UI will simple have the rover
continue driving at that speed indefinitely. There should be a time
limit on this.

- I haven't tested it in a while, but I ran into problems when I tried
to send many photos at once or send really, really large photos where
I was definitely losing data. I have several theories for why this
was happening:
    - race conditions on my data structures. If this was the reason
    why, it *should* be fixed.
    - the transceivers have a fixed-sized buffer that was being
    exceeded. If this is the case, we need to find the size
    of this buffer via testing (or estimated size), and only allow
    sending messages until we know that this buffer has been filled.
    If the buffer is filled, we *will not send messages again* until
    the receiver sends some sort of `reading-failed` message, i.e.
    that it has finished reading, so that the sender can keep sending
    more messages.

- Controller support for driving.

## Software Setup

You will need both [python](https://www.python.org/downloads/) 
and [git](https://git-scm.com/) installed to use this repository.

When installing Python (on Windows), ensure that you check the box
during installation that **adds python to your PATH variable!**

### Introductory git and making changes

To clone this repo:

```sh
git clone https://github.com/DomerRover2024-2025/PhoenixSoftware.git
```

To see the most recent radio comms code:

```sh
git checkout -b radiocomms
git pull origin radiocomms
```

You must *become a contributor* if you want to make any permanent modifications
to the repository. However, for maintainability,
please *make a branch* and make a pull request to the radio-comms branch
for changes, and someone who is a contributor ought to review
and then accept/reject the pull request as needed.

```sh
git checkout -b <new_branch>
...
git add .
git commit -m "New branch changes"
git push -u origin <new_branch>
# Then, go to github website to make pull request
```

### Python virtual environment

#### Setup

Set up a python virtual environment in the directory JUST OUTSIDE of the main repo. 
If you want to include it in the repo itself, you ***must*** add the name 
of the directory to the `.gitignore` file, i.e. this must not be added to the repository itself.

To set up a virtual environment:
- On Unix (Linux / Mac):

```sh
python3 -m venv <environment_name>
```

- On Windows:

```sh
python -m venv <environment_name>
```

To activate the virtual environment:
- On Unix (Linux / Mac):

```sh
source <environment_name>/bin/activate
```

- On Windows:

```sh
.\<environment_name>\Scripts\Activate
```

You will know this is successful if `(<environment_name>)` appears before your 
user in the command prompt.

To deactivate,

```sh
deactivate
```

To install a package, make sure your virtual environment is activated first.
- On Unix systems,

```sh
python3 -m pip install <package>
```

- On Windows:

```sh
python -m pip install <package>
```

#### Packages

These are the Python modules we are currently using. 
If you want to run the code please install these to the virtual environment.
Run

```sh
python3 -m pip install <Package Name>
```

and in the code itself,

```python
import <Import Name>
```

| Package Name      | Import Name   | Reason                        |
| ----------------- | ------------- | ----------------------------  |
| `pyzmq`           | `zmq`         | For sockets (now unused)      |
| `opencv-python`   | `cv2`         | Video feed and camera capture |
| `numpy`           | `numpy`       | Array math                    |
| `pyserial`        | `serial`      | Serial port communications    |
| `pygame`          | `pygame`      | For controller handling       | 


### IP addresses

You must ensure that the rover and user have the correct IP addresses
in order to actually run the 2.4GHz connection over the rover.
For regularly ssh-ing into the Jetson over ND-Guest, ssh into
 `jetsonson@jetsonson.dhcp.nd.edu` (you can thank Sean for the naming).

> This is now deprecated, since ND-Guest is no longer the main point
> of connection. The Jetson computer should be accessible via eduroam
> by the same DHCP address, though.

As a note, here are the addresses of relevant items:

| The thing | Address       |
| --------- | ------------- |
| Bullet-1  | 192.168.11.180|
| Bullet-2  | 192.168.11.20 |
| Jetson    | 192.168.11.17  (manual setup)|
| Gerbil    | 192.168.11.178 (manual setup)|
| User      | 192.168.11.179 (manual setup)|

The rover should automatically update its IP address to the correct one
once the communications system is properly set up.
This is done via a cronjob, which you may see and edit
via `sudo crontab -e`.

If it isn't, you may need to run the following:

```sh
sudo ifconfig enP8p1s0 192.168.11.17 netmask 255.255.255.0 up
```

This opens the ethernet IP address to the following.
You can see the status of various IP addressing with

```sh
nmcli dev wifi list
```

in a very nice looking output.

## Hardware Setup

### RFD-900x

If ever in doubt, see the [manual](https://rfdesign.com.au/wp-content/uploads/x-Series-Datasheet-V2.0.pdf).

These are two 900MHz modems. Included in the box are two FTDI to USB adapters and
a few baby antennas.

For the true connection to the rover, they should be connected via the TX and RX
pins of the rover. See the manual, but in essence, the transceiver's
TX pin ought to be connected to the Jetson's RX pin, and the Jetson's TX pin to the
transceiver's RX pin. Additionally, the Jetson's CTS pin should be connected
to the Jetson's RTS pin, and vice versa.

The coax connection of the transceiver should be connected to coaxial cable and that
to the large 900MHz antenna on the rover.

On the base station side, the transceiver can be connected via the FTDI adapter
to a computer. For the competition, the coaxial cable from the transceiver should
run all the way to the super large yagi antenna on the base station, but in practice
a baby antenna should be good enough.

#### Firmware Adjustment

**You will need to adjust the firmware of the transceivers to fit
the URC rules.** Unfortunately, as far as I can tell, the software to update the
firmware is only available on Windows, but I could be wrong.

On the Domer Rover PC (not the laptop), there is an RFDTools application on the desktop.
Plug in a transceiver via the FTDI adapter and select the relevant COM port,
and then load the current settings.

Here, you can adjust the baud, but more importantly is the minimum and maximum frequency.
Here you can adjust the channels used.

> Frankly, I am pretty sure the engineers of these transceivers have made it such that
> other communication on the same frequency won't affect it.
> The data is even encrypted.
> But, I am frankly not completely sure.

Because the URC will make you adjust the channels on the fly, you will need to
update this firmware manually. 
There may be an easier way to do this, but I do not know how.

### Bullets

These are two essentially WiFi bridges. See the [IP address](#ip-addresses) information above.

In order to use, you will need a router and two ethernet cables per bullet. Take
an ethernet cable from the bullet into the LAN of the router, and another from the PoE
to your computer. Do the same on the other side.

> It may be the other way around. My memory is rather poor on this.

The antennas should be connected to the coaxial connection of the bullets.
If you do not use antennas, the range of the bullets is very limited.

Note that, once the bullet is connected to the Jetson, *it should automatically
connect to the network* via the [cronjob](#ip-addresses) mentioned prior.
I don't think this will lock out regular WiFi ssh-ing, but it might,
so be prepared to connect to the Jetson across the addresses listed above.
Once you do, though, it acts as a regular SSH connection, so the information
and connectivity possibilities here are very malleable.

In order to connect to the Jetson here, your laptop MUST have the IP address
listed above [in the table](#ip-addresses).

#### Test Connection

If you want to ensure the connection across the bullets is working correctly,
run the following:

```sh
ping <ip-address>
```

for the given IP addresses [in the table](#ip-addresses).
Packets should be sent and received.

#### Firmware adjustment

You can also adjust the settings of the bullets.
I don't believe this is necessary anymore, but you never know when you
might need to. The instructions are listed in the
physical manuals included in the boxes (which I kept), but I've
also found it online [here](https://dl.ubnt.com/qsg/BulletM2-HP/BulletM2-HP_EN.html).

Basically, once the bullet is connected to your computer, type in
`https://192.168.1.20` into a browser (if this doesn't work,
try the IP addresses given in that table).
The manual will tell you to use username `ubnt` and password `ubnt`,
but I've adjusted both passwords to be `D0merR0ver!` for both bullets.
- For Bullet-1, its **access point** should be checked,
and its dBi should be **17**. You may need to adjust the dBi if the antenna
changes.
- For Bullet-2, its **station** should be checked, and its dBi
should be **8**. You may need to adjust this if you get different antennas.

For more information, take a look at this [Google Doc](https://docs.google.com/document/d/1zqrMQSnEG07DRZDH8TrgdfqI6baC9tWreErHnTZrSlo/edit?tab=t.0), 
which is probably somewhat wrong, but is also a good place to start troubleshooting from.

## Quick Testing

If you ever need to quickly send over specific information to the rover
over wifi or the bullets, you can find files for this in
`info_over_bullet_files`.

## Software Usage

On the client (user), run 

```sh
python3 hieroglyphics/baseStationComms.py
```

if in the radio/comms directory. 
On the server (rover), run

```sh
python3 hieroglyphics/roverComms.py
```

### Over the 900MHz transceivers

You will need to plug in the RFD-900x transceivers.
See the [relevant section](#rfd-900x) for more information.

You must ensure that the `readerWriter` variable in `main`
for both files is set to the `SerialReaderWriter()` constructor.
This variable was designed to easily be swapped out with
a `SocketReaderWriter()`, but this behavior is not yet dynamic or
automated at the code level.

You may need to change a few lines at the top of
`roverComms.py` and `baseStationComms.py` in order to
correctly interface with the transceivers.
There are several lines at the top of these files that
look like:

```python
path = 'some string'
```

If this is `roverComms.py`, and you are running this via
the pin connections on the Jetson, path must be `/dev/ttyTHS1`.

In either case, if this is a Linux system and connecting via a USB,
path must be `/dev/ttyUSB0`.

If you are unsure what the path to the port is to the transceivers
(when connecting via usb), run the following in a terminal,
given that your virtual environment is activated:
- On Unix:

```sh
python3 -m serial.tools.list_ports
```

- On Windows:

```
python -m serial.tools.list_ports
```

### Across 2.4GHz or wifi

You must ensure that the `readerWriter` variable in `main`
for both files is set to the `SocketReaderWriter()` constructor.

There are still quite a few quirks with this implementation.
You will need to run `roverComms.py` first, and then `baseStationComms.py`
second, and you must kill the latter before the former.

> This is because of some incomplete socket handling.
> See the [TODO](#TODO) section.

You must ensure that the ports of the two sides match.
For the hosts,
- For simplicity, in `roverComms.py`, leave the port as `''`,
as this will ensure that the socket is reachable via any address.
- For `baseStationComms.py`, use the relevant [IP address](#ip-addresses),
or just `localhost` if running on a single computer.

## Overall Code Structure

There are two main directories.
- `hieroglyphics`, which was called as such because of how difficult this was
initally to me, contains the real code for the communications system. It was
originally designed only for the 900MHz system, but I believe it should
be used for both now for simplicity's sake.
- `info_over_bullet_files`, which holds a bunch of disparate files
to send different information over sockets. Use these for quick testing and
scrappy work, but the final product should probably be in the other directory.

As the former holds most of the true code structure, I will only be focusing
on that one.

### Files

- `baseStationComms.py`: main driver for the client-side connection
- `baseStationMessageProcessor.py`: contains base-station-specific message processing
for received messages
- `concurrentSet.py`: a data structure to handle concurrent operations on a set.
This is used to handle holding the acknowledgments, as acknowledgments that are received
have the corresponding message IDs added to this set.
    - this is not, in the long run, the best way to handle this, as the set
    will contain lots of unused, old data.
- `imageCapturer.py`: holds image capturing logic. This should be updated, as it
is currently very bare-bones and mostly just for testing purposes.
- `message.py`: data structure of the message packets. Also holds the enumeration
of the different purposes
- `messageProcessor.py`: holds the shared processing functionality between the client
and server.
- `messageQueue.py`: a concurrent queue data structure that pops and holds message.
- `readerWriter.py`: an interface for an abstraction of reading and writing to the
other side of a connection
- `roverComms.py`: the main driver for the server-side connection
- `roverMessageProcessor.py`: contains rover-specific message processing for received
messages
- `scheduler.py`: the scheduler that sends information over the socket or serial port,
which uses underneath a weighted round robin structure
- `serialReaderWriter.py`: an implementation of the interface above that uses serial ports
- `socketReaderWriter.py`: an implementation of the interface above that uses sockets
- `userInterface.py`: code for the UI that the user interacts with

### High Level

At a high level, there is a **server**, `roverComms.py`, and
a **client**, `baseStationComms.py`. Each in essence reads for
messages from the other and performs actions based on the type,
and sends messages to the other when relevant.
- These are connected via either serial (`SerialReaderWriter`) or 
via UDP connectionless packets (`SocketReaderWriter`).
- the **server** has three concurrent threads:
    - Reading: the main thread, which reads across the port (or socket)
    for messages, and when received, adds them to a concurrent queue
    - Processing: the `process_messages` function, which pops
    messages from the queue and performs actions based on the type;
    most of these involve adding messages to the scheduler's queues
    - Sending: the scheduler, which periodically sends messages
    to the client based on what's been added to its queues
- the **server** has four concurrent threads:
    - UI: the main thread, which reads user input and adds messages
    to the scheduler's queues to go out to the server
    - Reading: exactly like the server's
    - Processing: pops messages from the queue and operates on them
    based on the type; usually involves printing to stdout or modifying
    logs / files
    - Sending: the scheduler, exactly like the server

In order to protect against dropped messages due to connection failures,
I implemented (or made an attempt to implement) **acknowledgments**.
This is the intended structure.
- When a message is sent, the sender *expects an acknowledgment*
for the sent message, and after two seconds, resends the message
if an acknowledgment is not received
- When a message is received, the receiver sends an acknowledgment for the message.
- If a message is received *which the receiver already acknowledged*, i.e.
the sender did not receive the acknowledgment and had resent the message,
the receiver *drops the message*, i.e. *does not perform the action, as it has
already been performed*, and resends another acknowledgment to let the sender know
it has been received.
- If a sender receives multiple acknowledgments for the same message, it simply
drops the new acknowledgments, and obviously stops resending the same message.

### Message Structure

Data across the serial port is encapsulated in messages that I've defined.
The structure is as follows:
- ID (2 bytes)
- purpose (1 byte)
- number (1 byte)
- size of payload (4 bytes)
- payload (variably sized)
- checksum (1 byte)

Some more information about these:
- The ID is only unique *per-side*, because there's no way to synchronize the ID
between sides without doing something like making the rover-side all even and the
client-side all odd or something like this.
    - this means the first message the ROVER sends will have ID 1, and the first
    message the client sends will have ID 1.
    - this should not screw up acknowledgments because the client cannot
    send information to itself and the server cannot do the same.
- the purpose is enumerated in a `Purpose` class at the top of `message.py`.
This should have really been called *opcode* or something similar.
- the number field is only useful for certain purpose fields, and is used
to keep an order on messages. For example, it is used in sending images
to make sure the order between payloads is maintained so the original message
can be recovered.
    - This ought to be automated.
- the payload differs per purpose. In most cases, it is obvious, but
here are a few special cases:
    - the `ACK` purpose has the ID of the message for which it is acknowledging
    in its payload.
    - the `ERROR` purpose has the error string as its payload.
    - For messages that act as *signals*, i.e. that don't have any need for the payload,
    simply ignore the payload. I believe the payload is a single byte in these cases.
- the checksum is a bytewise XOR.
- Use the `.get_as_bytes()` to serialize a message. This should really be called
`.serialize()`.

### Scheduler

The scheduler has a list of queues called **topics** each with an associated
**weight**. In essence, the scheduler will repeatedly iterate over each queue
and send `c` messages for the given queue's weight `c`.

The scheduler has a retransmission queue and a set of acknowledged message IDs.
When the scheduler sends a message, it will also add the message
to its retransmisssion queue and eventually resend it from that queue if
an acknowledgment is not received.

If an acknowledgment is received, the ID for the message being acknowledged
is added to the scheduler's concurrent set. When the scheduler goes to resend
a message from the retransmission queue, it first checks if the ID has been
acknowledged, i.e. is in the set. If it is, it drops the message from the queue.
Otherwise, it resends the message *and readds it to the retransmission queue* again.

### Message Processing

There's too much specific functionality here to list it all; read the code itself
for how each message processor handles specific message purposes. I will
detail how acknowledgments and general messaging is handled, which operates
the same on client and server side.

The message processing thread will pop a message from the queue, which is a
*blocking action* on a timeout.

If the message being processed is an acknowledgment, the thread updates the
scheduler's concurrent set and goes to pop the next message.

Otherwise, the processor will create an acknowledgment message and add it
to the scheduler.

Each processing thread holds its own concurrent set of processed messages
(this may be able to just be a regular set). If the message ID has already
been processed, it just goes to pop the next one; otherwise it adds
the ID to the set and handles it via the client/server-side specific processing
actions.

### User Interface

The user interface should be clear from the options. To be frank,
some of them are unimplemented and serve only as a reminder for future updating.
Here is what is implemented:
- `quit`: should really be "exit", but will quit the user interface and clean
up the client side. This **does not stop** the rover from running.
- `test`: send over a string as a debug message. Type `exit` to quit this mode.
- `log`: see the log.
- `dr`: type in two integers separated by spaces to be wheel speeds.
This is not a continuous mode, so you will have to type in `dr`, enter,
and then the two integers each time.
- `stop`: for panic moments, this will set both wheel speeds to 0.
- `vid`: this is supposed to turn video reception on/off, but I don't think it works.
- `ldp`: send a **l**ow **d**efinition **p**hoto. This does work and places the folder
in an `ldp/` folder in the directory.
- `hdp`: send a **h**ow **d**efinition **p**hoto. This *should* work and places the folder
in an `hdp/` folder in the directory, but takes a hot second.
- `f`: send a file. This may break with too large a file.
- `cp`: copy a file from the rover to the client.

In general, the only ones I know that really work are `test`, `quit`, `dr`, `stop`, and `ldp`.

