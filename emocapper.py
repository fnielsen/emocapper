#!/usr/bin/env python
"""Record for Emocap system.

Usage:
  emocapper -h | --help
  emocapper --version
  emocapper record [(--verbose ...)] [--output=<output>] [--time=<seconds>]

Options:
  -h --help                    Show this screen.
  --version                    Show version.
  -v --verbose                 Show more information
  -o --output=<output>         Filename [default: recording.csv]
  --time=<seconds>             Secords to record [default: 10]

"""

from __future__ import print_function

__version__ = "0.1.0"


import platform
if platform.system() == "Windows":
    import socket
    _ = socket  # To avoid 'Unused import socket'

import time

from emokit import emotiv

import gevent


# Translation between Emotiv and Emocap electrodes
EMOTIV_TO_EMOCAP_MAP = {
    'F3': 'P4',
    'FC6': 'Fz',
    'P7': 'TP10',
    'T8': 'C3',
    'F7': 'O1',
    'F8': 'F4',
    'T7': 'P3',
    'P8': 'Cz',
    'AF4': 'Fpz',
    'F4': 'F3',
    'AF3': 'O2',
    'O2': 'C4',
    'O1': 'TP9',
    'FC5': 'Pz',
}


class EmocapWriter(object):
    """Writer for Emocap data to file."""

    def __init__(self, filename='recording.csv'):
        """Open file and write header.

        Parameters
        ----------
        filename : str
            Filename for the output file.

        """
        self.fid = open(filename, 'w')
        self.emotiv_sensor_names = [
            'F7', 'F8', 'AF3', 'AF4', 'FC5', 'FC6', 'F3', 'F4', 'O1', 'O2',
            'P7', 'P8', 'T7', 'T8']
        self.sensor_names = [
            EMOTIV_TO_EMOCAP_MAP[name] for name in self.emotiv_sensor_names]
        self.quality_names = [name + ' quality' for name in self.sensor_names]
        self.header = [
            'Time', 'Packets received', 'Queue size', 'Counter',
            'Gyro X', 'Gyro Y'] + self.sensor_names + self.quality_names
        self.write_header()

    def close(self):
        """Close file."""
        self.fid.close()

    def write_header(self):
        """Write header."""
        line = ','.join(self.header)
        self.fid.write(line + '\n')

    def write_line(self, data):
        """Write a line of data.

        Parameters
        ----------
        data : dict
            data values with keys corresponding to header.

        """
        line = ','.join([repr(data[column]) for column in self.header])
        self.fid.write(line + '\n')

    def write_packet(self, headset, packet):
        """Write Emotiv packet to line.

        Parameters
        ----------
        headset : emokit.emotiv.Emotiv
            object representing a emotiv headset
        packet : emokit.emotiv.Packet
            object with data sample from headset

        """
        data = {
            'Time': time.time(),
            'Packets received': headset.packets_received,
            'Queue size': headset.packets.qsize(),
            'Counter': packet.counter,
            'Gyro X': packet.gyro_x,
            'Gyro Y': packet.gyro_y
            }
        for sensor_name, quality_name, emotiv_name in zip(
                self.sensor_names, self.quality_names,
                self.emotiv_sensor_names):
            data[sensor_name] = packet.sensors[emotiv_name]['value']
            data[quality_name] = packet.sensors[emotiv_name]['quality']
        self.write_line(data)


def main(arguments):
    """Command-line interface.

    Parameters
    ----------
    arguments : dict
        Arguments in the docopt format

    """
    headset = emotiv.Emotiv(display_output=False)
    gevent.spawn(headset.setup)
    gevent.sleep(0)

    # Initialize file
    emocap_writer = EmocapWriter(filename=arguments['--output'])
    end_time = time.time() + float(arguments['--time'])

    try:
        while end_time > time.time():
            packet = headset.dequeue()
            emocap_writer.write_packet(headset, packet)
            gevent.sleep(0)
        emocap_writer.close()
    except KeyboardInterrupt:
        emocap_writer.close()
        headset.close()
    finally:
        headset.close()


if __name__ == '__main__':
    import docopt

    main(docopt.docopt(__doc__))
