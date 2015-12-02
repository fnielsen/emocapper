#!/usr/bin/env python
"""Record for Emocap system.

Usage:
  emocapper -h | --help
  emocapper --version
  emocapper record [(--verbose ...)] [--output=<output>] [--duration=<seconds>]
  emocapper showmaxelectrode
  emocapper showqualities
  emocapper showvalues

Options:
  -h --help                    Show this screen.
  --version                    Show version.
  -v --verbose                 Show more information
  -o --output=<output>         Filename [default: recording.csv]
  --duration=<seconds>             Secords to record [default: 10]

"""

from __future__ import print_function

__version__ = "0.1.0"


import platform
if platform.system() == "Windows":
    import socket
    _ = socket  # To avoid 'Unused import socket'

from time import time

from emokit import emotiv

import gevent


EMOTIV_SENSOR_NAMES = [
    'F7', 'F8', 'AF3', 'AF4', 'FC5', 'FC6', 'F3', 'F4', 'O1', 'O2',
    'P7', 'P8', 'T7', 'T8']

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


FILENAME = 'recording.csv'


class EmocapWriter(object):
    """Writer for Emocap data to file."""

    def __init__(self, filename=FILENAME):
        """Open file and write header.

        Parameters
        ----------
        filename : str
            Filename for the output file.

        """
        self.fid = open(filename, 'w')
        self.emotiv_sensor_names = EMOTIV_SENSOR_NAMES
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
            'Time': time(),
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


def record(filename=FILENAME, duration=10):
    """Read EEG data from device and write to file.

    Parameters
    ----------
    filename : str
        Filename for output
    duration : float, int
        Time in seconds for the recording

    """
    # Initialize file
    emocap_writer = EmocapWriter(filename=filename)

    headset = emotiv.Emotiv(display_output=False)
    gevent.spawn(headset.setup)
    gevent.sleep(0)

    end_time = time() + float(duration)
    try:
        while end_time > time():
            packet = headset.dequeue()
            emocap_writer.write_packet(headset, packet)
            gevent.sleep(0)
        emocap_writer.close()
    except KeyboardInterrupt:
        emocap_writer.close()
        headset.close()
    finally:
        headset.close()


def sorted_names():
    """Return Emocap and Emotiv electrode names sorted.

    Returns
    -------
    names : list of 2-tuple with str
        List of pairs with electrode names

    """
    sensor_names = [EMOTIV_TO_EMOCAP_MAP[name] for name in EMOTIV_SENSOR_NAMES]
    emotiv_sensor_names = EMOTIV_SENSOR_NAMES[:]
    names = sorted(zip(sensor_names, emotiv_sensor_names))
    return names


def show_max_electrode():
    """Show name of max electrode of electrode signal."""
    names = sorted_names()
    headset = emotiv.Emotiv(display_output=False)
    gevent.spawn(headset.setup)
    gevent.sleep(0)

    # Compute an offset for each electrode
    for _ in range(10):
        packet = headset.dequeue()
        gevent.sleep(0)
    offsets = [packet.sensors[emotiv_name]['value']
               for name, emotiv_name in names]

    try:
        while True:
            packet = headset.dequeue()
            values_and_names = [
                (packet.sensors[emotiv_name]['value'] - offset, name)
                for (name, emotiv_name), offset in zip(names, offsets)]
            name_of_max = max(values_and_names)[1]
            print(name_of_max)
            gevent.sleep(0)
    except KeyboardInterrupt:
        headset.close()
    finally:
        headset.close()


def show_qualities():
    """Show quality of electrode signal."""
    names = sorted_names()
    headset = emotiv.Emotiv(display_output=False)
    gevent.spawn(headset.setup)
    gevent.sleep(0)

    try:
        while True:
            packet = headset.dequeue()
            line = " - ".join([
                "%s = %1d" % (name, packet.sensors[emotiv_name]['quality'])
                for name, emotiv_name in names])
            print(line)
            gevent.sleep(0)
    except KeyboardInterrupt:
        headset.close()
    finally:
        headset.close()


def show_values():
    """Show values of electrode signal."""
    names = sorted_names()
    headset = emotiv.Emotiv(display_output=False)
    gevent.spawn(headset.setup)
    gevent.sleep(0)

    try:
        while True:
            packet = headset.dequeue()
            line = " - ".join([
                "%s = %5d" % (name, packet.sensors[emotiv_name]['value'])
                for name, emotiv_name in names])
            print(line)
            gevent.sleep(0)
    except KeyboardInterrupt:
        headset.close()
    finally:
        headset.close()


def main(arguments):
    """Command-line interface.

    Parameters
    ----------
    arguments : dict
        Arguments in the docopt format

    """
    if arguments['record']:
        record(filename=arguments['--output'],
               duration=arguments['--duration'])
    elif arguments['showmaxelectrode']:
        show_max_electrode()
    elif arguments['showqualities']:
        show_qualities()
    elif arguments['showvalues']:
        show_values()
    else:
        raise Exception


if __name__ == '__main__':
    import docopt

    main(docopt.docopt(__doc__))
