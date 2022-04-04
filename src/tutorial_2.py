# Copyright 2018-2021 Benjamin Wiegand <benjamin.wiegand@physik.hu-berlin.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program  is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with This program.  If not, see <http://www.gnu.org/licenses/>.

from migen import Signal, Module
from misoc.interconnect.csr import AutoCSR, CSRStatus, CSRStorage

from logic.pid import PID


class DemoPIDChain(Module, AutoCSR):
    """
    If `pid_enable` is set, this demo module applies a PID with variable parameters.
    If it isn't, it just outputs the input signal.
    """

    def __init__(self, width=14, signal_width=25):
        # will be connected by parent module
        self.input = Signal((width, True))
        self.output = Signal((width, True))

        # create registers the CPU may access
        self.pid_enable = CSRStorage()

        # initialize pid submodule which does the actual work
        self.submodules.pid = PID(width=signal_width)

        # it makes sense to use more bits for a signal flow in order to mitigate
        # rounding errors
        bit_shift = signal_width - width
        input_shifted = Signal((signal_width, True))
        self.comb += [input_shifted.eq(self.input << bit_shift)]

        # connect the PID
        pid_output = Signal((signal_width, True))
        self.comb += [
            # connect PID input
            self.pid.input.eq(input_shifted),
            # make sure it's running
            self.pid.running.eq(1),
            # connect output
            pid_output.eq(self.pid.pid_out),
        ]

        # depending on the value of `pid_enable`, we set the module's output
        self.comb += [
            If(self.pid_enable.storage, self.output.eq(pid_output >> bit_shift)).Else(
                self.output.eq(self.input)
            )
        ]
