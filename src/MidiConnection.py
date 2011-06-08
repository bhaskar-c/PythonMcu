# -*- coding: utf-8 -*-

"""
PythonMcu
=========
Mackie Host Controller written in Python

Copyright (c) 2011 Martin Zuther (http://www.mzuther.de/)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

Thank you for using free software!

"""

import pygame.midi
import time
import types

import math

class MidiConnection:
    __module__ = __name__
    __doc__ = 'MIDI connection handler'

    NOTE_OFF_EVENT = 0x80
    NOTE_ON_EVENT = 0x90
    POLYPHONIC_KEY_PRESSURE = 0xA0
    CONTROL_CHANGE = 0xB0
    PROGRAM_CHANGE = 0xC0
    CHANNEL_PRESSURE = 0xD0
    PITCH_WHEEL_CHANGE = 0xE0
    SYSTEM_MESSAGE = 0xF0


    def __init__(self, callback, midi_input=None, midi_output=None):
        pygame.midi.init()

        self._callback = callback

        self._midi_input = self._init_input(midi_input)
        self._midi_output = self._init_output(midi_output)


    def disconnect(self):
        if self._midi_input:
            self._log('Closing MIDI input...')
            self._midi_input.close()

        if self._midi_output:
            self._log('Closing MIDI output...')
            self._midi_output.close()


    def _log(self, message):
        print '[MIDI Connection      ]  ' + message


    def _init_input(self, device_name):
        if device_name == None:
            return None

        for device_id in range(pygame.midi.get_count()):
            device = pygame.midi.get_device_info(device_id)

            if device[1] == device_name and (device[2] == 1):
                self._log('Opening MIDI input "%s"...' % device_name)
                return pygame.midi.Input(device_id)

        self._log('MIDI In \'%s\' not found.\n' % device_name)
        return None


    def _init_output(self, device_name):
        if device_name == None:
            return None

        for device_id in range(pygame.midi.get_count()):
            device = pygame.midi.get_device_info(device_id)

            if device[1] == device_name and (device[3] == 1):
                self._log('Opening MIDI output "%s"...' % device_name)
                return pygame.midi.Output(device_id, latency=0)

        self._log('MIDI Out \'%s\' not found.\n' % device_name)
        return None


    def buffer_is_empty(self, use_callback=True):
        return not self._midi_input.poll()


    def process_input_buffer(self, use_callback=True):
        if not self._midi_output:
            self._log('MIDI output not connected.')
            return

        while self._midi_input.poll():
            (status, message) = self._receive_message()

            if use_callback:
                self._callback(status, message)


    def _receive_message(self):
        message = self._midi_input.read(1)[0][0]
        status_byte = message[0] & 0xF0

        if message[0] == 0xF0:
            while 0xF7 not in message:
                message.extend(self._midi_input.read(1)[0][0])
            while message[-1] != 0xF7:
                del message[-1]

        if status_byte == self.NOTE_OFF_EVENT:
            status = self.NOTE_OFF_EVENT
            del message[3]
        elif status_byte == self.NOTE_ON_EVENT:
            status = self.NOTE_ON_EVENT
            del message[3]
        elif status_byte == self.POLYPHONIC_KEY_PRESSURE:
            status = self.POLYPHONIC_KEY_PRESSURE
            del message[3]
        elif status_byte == self.CONTROL_CHANGE:
            status = self.CONTROL_CHANGE
            del message[3]
        elif status_byte == self.PROGRAM_CHANGE:
            status = self.PROGRAM_CHANGE
            del message[2:3]
        elif status_byte == self.CHANNEL_PRESSURE:
            status = self.CHANNEL_PRESSURE
            del message[2:3]
        elif status_byte == self.PITCH_WHEEL_CHANGE:
            status = self.PITCH_WHEEL_CHANGE
            del message[3]
        elif status_byte == self.SYSTEM_MESSAGE:
            status = self.SYSTEM_MESSAGE

        return (status, message)


    def send(self, status, data_1, data_2):
        if not self._midi_output:
            self._log('MIDI output not connected.')
            return

        self._midi_output.write_short(status, data_1, data_2)


    def send_cc(self, channel, cc_number, cc_value):
        if not self._midi_output:
            self._log('MIDI output not connected.')
            return

        self._midi_output.write_short(0xB0 + channel, cc_number, cc_value)


    def send_sysex(self, header, data):
        if not self._midi_output:
            self._log('MIDI output not connected.')
            return

        assert(type(header) == types.ListType)
        assert(type(data) == types.ListType)

        sysex = [0xF0]
        sysex.extend(header)
        sysex.extend(data)
        sysex.append(0xF7)

        self._midi_output.write_sys_ex(0, sysex)


if __name__ == "__main__":
    def callback_midi_in(status_byte, message):
        print 'status %02X: ' % status_byte,
        for byte in message:
            print '%02X' % byte,
        print

    midi_input = 'In From MIDI Yoke:  2'
    midi_output = 'Out To MIDI Yoke:  1'

    midi_connection = MidiConnection(callback_midi_in, midi_input, midi_output)

    midi_connection.send_cc(0, 0x07, 0x80)
    midi_connection.send_sysex([0x01, 0x02], [0x11, 0x12, 0x13])

    try:
        while True:
            midi_connection.process_input_buffer()

            time.sleep(0.1)
    except KeyboardInterrupt:
        pass

    midi_connection.disconnect()