'''
Copyright (c) 2018 Modul 9/HiFiBerry

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

# A simple fork of the HiFiBerry SPI tool, without the need for the dsptoolkit dependency.
# This means it can be installed independently from the dsptoolkit.
# This is the same SPI tool the sigmatcpserver uses, so any address found in SigmaStudio
# should work here aswell.
# The sigmatcpserver uses SPI to interface with the DSP, so if you have the correct addresses you
# shouldn't be able to break anything.
# HiFiBerry claims this is a very difficult thing to do, so I decided to take their implementation
# and modify it to make it less difficult.
# I have also ditched logging in favour of printing it.

# Sample usage: First declare a variable with the content spilib.spi_handler
# like such: spi = spilib.spi_handler
# Then you can call methods like spi.read(address, length, debug)
# Or spi.write(address, data, debug)
# address is the memory address in hex (e.g. 0x001B)
# Length is the amount of bytes you want to read (e.g. 4)
# Data is the data you want to write (e.g. [0x00, 0x00, 0x20, 0x8A])
# Debug is the debug flag, either True or False. (e.g. true)

def init_spi():
    import spidev
    spi = spidev.SpiDev()
    spi.open(0, 0)
    spi.bits_per_word = 8
    spi.max_speed_hz = 1000000
    spi.mode = 0
    print("spi initialized " + str(spi))
    return spi


class spi_handler():
    '''
    Implements access to the SPI bus. Can be used by multiple threads.

    We assume that the SPI library is thread-safe and do not use
    additional locking here.

    Data is passed in bytearrays, not string or lists
    '''

    spi = init_spi()

    @staticmethod
    def read(addr, length, debug=False):
        spi_request = []
        a0 = addr & 0xff
        a1 = (addr >> 8) & 0xff

        spi_request.append(1)
        spi_request.append(a1)
        spi_request.append(a0)

        for _i in range(0, length):
            spi_request.append(0)

        spi_response = spi_handler.spi.xfer(spi_request)  # SPI read
        if debug:
            print("spi read " + str(len(spi_request)) + " bytes from " + str(addr))
        return bytearray(spi_response[3:])

    @staticmethod
    def write(addr, data, debug=False):
        a0 = addr & 0xff
        a1 = (addr >> 8) & 0xff

        spi_request = []
        spi_request.append(0)
        spi_request.append(a1)
        spi_request.append(a0)
        for d in data:
            spi_request.append(d)

        if len(spi_request) < 4096:
            spi_handler.spi.xfer(spi_request)
            if debug:
                print("spi write " +  str(len(spi_request) - 3) + " bytes")
        else:
            finished = False
            while not finished:
                if len(spi_request) < 4096:
                    spi_handler.spi.xfer(spi_request)
                    if debug:
                        print("spi write " +  str(len(spi_request) - 3) + " bytes")
                    finished = True
                else:
                    short_request = spi_request[:4003]
                    spi_handler.spi.xfer(short_request)
                    if debug:
                        print("spi write " +  str(len(short_request)) - 3 + " bytes")

                    # skip forward 1000 cells
                    addr = addr + 1000  # each memory cell is 4 bytes long
                    a0 = addr & 0xff
                    a1 = (addr >> 8) & 0xff
                    new_request = []
                    new_request.append(0)
                    new_request.append(a1)
                    new_request.append(a0)
                    new_request.extend(spi_request[4003:])

                    spi_request = new_request

        return data
