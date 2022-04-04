# Copyright 2021 Benjamin Wiegand <benjamin.wiegand@physik.hu-berlin.de>
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

from migen import Module, Signal, bits_for, run_simulation
from misoc.interconnect.csr import AutoCSR, CSRStatus, CSRStorage


class BlinkerModule(Module):
    """A demo module that is capable of very sophisticated blinking \o/
    Mode of operation is simple: with each FPGA cycle, we increment a counter by
    one. As the counter has a finite width, it will overflow after some time.
    We compare the counter to half its maximum value: if it is less, output
    will be 1; otherwise 0.
    In this demo module, we want the blinker to blink once every 8 FPGA cycles.
    """

    def __init__(self):
        """The `__init__`` method of this module is called whenever this module
        is instanciated. For us this means: this is the point where we can set
        things up.
        The first important thing to understand is: an FPGA does not work
        sequentially (like a CPU core) but in parallel. When we write "normal"
        python code, it is executed statement by statement; a new command is not
        executed unless the previous command finished.
        This is not what happens in an FPGA, though: in an FPGA many things
        may happen at the very same moment.
        Therefore, the python code that you see below shouldn't be understood
        as "the FPGA does this, then it does that". Instead, it should be seen
        like a description of an electric circuit: First, we describe a battery.
        Then we describe a engine. Then we describe two wires, closing the circuit.
        In the end, this electric circuit doesn't run in a sequential way but many
        things happen in parallel: electrons leave the battery through the first
        wire AND do something in the engine AND pass through the second wire
        at the same time.
        """

        # Now we are ready to initialize signals that are required for this module.
        # Signals are like "FPGA variables" that can be used to store things.

        # our blinker will have two states: off or on.
        # It is described by a single bit, i.e. a signal of width 1.
        # Signals are created using `Signal(width: int)`. Omitting the argument
        # implicitly defines a 1-bit integer.
        self.blinker = Signal()
        # this is another blinker signal that we'll use later
        self.blinker_sync = Signal()

        # now we define our counter. For that we have to know what `bits_for`
        # does: it tells us how many bits we need to store a specific integer:
        #
        # >>> bits_for(1)
        # 1
        # >>> bin(1) # check whether `bits_for` does what we want
        # '0b1' # <-- `bits_for` was right: 1 bit was used for representing the number 1
        # >>> bits_for(7)
        # 3
        # >>> bin(7)
        # '0b111' <-- 3 bits are used for storing a 7
        #
        # We want our counter to overflow to overflow every 8 FPGA cycles.
        # Therefore we create a signal that is suited for storing the integer
        # `7` (7 is the eighth number when counting from 0).
        # Increasing `7` by `1` then causes an overflow (--> `0`).
        self.counter = Signal(bits_for(7))

        # `self.sync` means that we are now programming something that runs once
        # per FPGA cycle.
        # We want to increase our counter by 1 with every FPGA cycle.
        # NB: If the counter overflows it starts with 0 again.
        self.sync += [
            # We are inside a `sync` block which means that everything here
            # happens once per FPGA cycle.
            #
            # `self.counter.eq(...)` is an assignment: whatever is within the
            # parantheses is assigned to `self.counter`.
            self.counter.eq(
                # this expression within the parantheses is evaluated once per
                # FPGA cycle. In our case: the value of the previous FPGA cycle
                # is incremented by 1 and used as the value for the new cycle.
                self.counter
                + 1
            )
        ]

        # this is a combinatorial statement: it is executed whenever an input
        # signal changes.
        # In this case: whenever `counter` changes, we check its value and
        # and compare it to a number. If the `>=` condition is fulfilled,
        # it returns a `1`, otherwise a `0`. This result is assigned to
        # `blinker`.
        # Note that combinatorial statements (unlike synchronous
        # statements) happen within the same FPGA cycle: at the exact FPGA
        # cycle that `counter` reaches `4`, `blinker` will go high.
        self.comb += [self.blinker.eq(self.counter >= 4)]

        # to illustrate the difference between sync and comb statements, we do
        # the same thing but with a sync statement (this time writing
        # `blinker_sync` instead of `blinker`)
        # Once we run a simulation of our module (see below), we will see what
        # difference this causes.
        self.sync += [self.blinker_sync.eq(self.counter >= 4)]


def simulate_blinker():
    """Now we simulate the behavior of `BlinkerModule`. Run this python
    file and look at its output.
    You will see that
    - counter runs from 0 to 7 and then overflows.
    - blinker is 0 for 4 FPGA cycles, then 1. After the overflow, it starts again
    - blinker_sync behaves similar to blinker but is delayed by one FPGA cycle.
      The reason is that it was assigned using a synchronous statement which
      doesn't happen instantaneously. Instead, at the next FPGA cycle, the
      expression is evaluated.
    """

    def testbench(dut):
        # simulation happens FPGA cycle by FPGA cycle. Its description comes
        # with new weird syntax elements \o/
        N_cycles_to_simulate = 16

        for i in range(N_cycles_to_simulate):
            # yield followed by a variable means: get the value of this FPGA
            # signal has at the current FPGA cycle in the simulation and write
            # it to a python variable:
            # - `dut.counter` is an instance of `Signal()` class.
            # - `yield dut.counter` will give us its value (an integer)
            counter = yield dut.counter
            b = yield dut.blinker
            b_sync = yield dut.blinker_sync

            print(
                "Counter=",
                counter,
                "Blinker=",
                b,
                "Blinker_sync=",
                b_sync,
            )

            # yield without anything means: advance one FPGA cycle
            yield

    # dut = device under test
    dut = BlinkerModule()
    # this call starts the simulation
    run_simulation(
        # what module should be tested?
        dut,
        # what simulation function should run?
        testbench(dut),
        # super helpful for debugging: this will write a file that contains the
        # state of the module at each FPGA cycle (including the state of all
        # signals). Install gtkwave, open it after the simulation has run!
        vcd_name="blinker.vcd",
    )


# run this python file to see the simulation of `BlinkerModule`!
if __name__ == "__main__":
    simulate_blinker()()

# TODO: BlinkerModuleCSR
# XXX: reset_counter_every=16 konfigurierbar machen
# bitshifts
# modules and submodules
# positive negative signals
