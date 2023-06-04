# Qsound - Real-time Audio Streaming Application

 Qsound is an alpha-stage concept for a real-time audio streaming application written in Python for Windows machines. It allows you to capture audio from the default sound device via WASAPI loopback, compress it, and transmit the audio stream over a TCP connection to a single machine.
### Features
- **Real-time Audio Capture**: Qsound \**attempts to* capture audio in real-time from the default playback device on your Windows machine.
- **Basic Compression**: The captured audio is compressed using ffmpeg and the mp3 compression algorithm to "*optimize*" data transmission.
- **TCP Streaming**: Qsound establishes a TCP connection between the client and server, enabling the "*seamless*" transfer of the compressed audio stream.

## Usage
 `python Qsound.py [-n HOST] [-p PORT] [-m MODE]`
### Arguments
 The script accepts the following arguments:

    -n HOST, --host HOST: The IP address of the host/server. As a Client you conect to host address.

    -p PORT, --port PORT: The port to run on. Client and Server must run on same port.

    -m MODE, --mode MODE: The operational mode. Choose one of the following modes:

        1 or --mode 1: Server/TX mode. This mode enables the script to act as a server and transmit audio data.

        2 or --mode 2: Client/RX mode. This mode allows the script to act as a client and receive audio data.

        3 or --mode 3: Server/RX mode. This mode allows the script to act as a server and receive audio data.

        4 or --mode 4: Client/TX mode. This mode enables the script to act as a client and transmit audio data.
###  Examples
#### Mode 1
 To run the script as a Server and transmit audio data to a client on a specific port:

    python Qsound.py -p 8000 -m 1
#### Mode 2
 To run the script as a Client and receive audio data from a specific host(in mode 1) and port:

    python Qsound.py -n 192.168.0.100 -p 8000 -m 2 

## Notes
 *Python may not be the ideal language for such an application, the program is only able to capture ~60-88 percent of the sound on my machine and I surmise it is spending the rest of the time compressing and  sending the data. I have experimented with threading and async functions, but both routes have only decreased performance so far. And as such, I continue to search for a more direct audio capture to socket-write   capable architecture 
  
 *Default port is 5000 \
 *Default host is 127.0.0.1 \
 *Default mode is 2, Client that reveives audio \
 *Client/Server modes must be matched for sucsessful connection. modes(1-2) and modes(3-4) for Server and Client respectivly
 
## Apologies
 Some sections of this code have been directly pulled from some online examples, with no credit given.  ); \
As atonement I offer up this code for anyone to use as they like, no attribution nessacery.
