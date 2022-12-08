"""The class structures used to maintain the machine state"""
import math
from typing import Optional, List, Tuple, Iterable, Dict

from knit_graphs.Knit_Graph import Knit_Graph, Pull_Direction
from knit_graphs.Loop import Loop
from knitting_machine.knitout_instructions import xfer
from knitting_machine.machine_components.Carrier_Grippers import Carrier_Insertion_System
from knitting_machine.machine_components.Sheet_Needle import get_sheet_needle, Sheet_Needle, Slider_Sheet_Needle
from knitting_machine.machine_components.machine_bed import Machine_Bed
from knitting_machine.machine_components.machine_pass_direction import Pass_Direction
from knitting_machine.machine_components.needles import Needle, Slider_Needle
from knitting_machine.machine_components.yarn_carrier import Yarn_Carrier


class Machine_State:
    """
    The current state of a whole V-bed knitting machine
    ...

    Attributes
    ----------
    racking: int
        The current racking of the machine: R = f-b
    front_bed: Machine_Bed
        The status of needles on the front bed
    back_bed: Machine_Bed
        The status of needles on the back bed
    last_carriage_direction: Pass_Direction
        the last direction the carriage took, used to infer the current position of the carriage (left or right)
    yarn_manager: Carrier_Insertion_System
        The system used to track the state of carriers and the yarn inserting hook
    knit_graph: Knit_Graph
        The knit graph that has been made by operations on the machine
    """
    MAX_GAUGE = 10

    def __init__(self, needle_count: int = 250, max_rack: float = 4.25, carrier_count:int = 10, hook_size:int = 5):
        """
        Maintains the state of the machine
        :param needle_count:the number of needles that are on this bed
        :param max_rack: Maximum allowed racking on machine
        :param carrier_count: Number of carriers available on the machine
        :param hook_size: the number of needles blocked by the yarn inserting hook
        """
        self._max_rack = max_rack
        self.racking: float = 0.0
        self.front_bed: Machine_Bed = Machine_Bed(is_front=True, needle_count=needle_count)
        self.back_bed: Machine_Bed = Machine_Bed(is_front=False, needle_count=needle_count)
        self.last_carriage_direction: Pass_Direction = Pass_Direction.Left_to_Right_Increasing
        # Presumes carriage is left on Right side before knitting
        self.yarn_manager: Carrier_Insertion_System = Carrier_Insertion_System(carrier_count, hook_size)
        self._loop_id_counter: int = 0
        self.knit_graph: Knit_Graph = Knit_Graph()
        self._gauge: int = 1
        self._loop_record: Dict[int, Tuple[bool, bool]] = {i: (False, False) for i in range(0, self.needle_count)}
        # needle index -> Loops on front, loops on back
        # self.sheet_records: Dict[int, Optional[Sheet_Record]] = {i: None for i in range(0, self._gauge)}
        # lower key value signals front layers, values are layer index in gauging
        self._needle_pos_to_layer_pos: Dict[int, int] = {i: 0 for i in range(0, self.needle_count)}
        self.gauge = 1  # applies property setter to fill layer records
        self._sheet: int = 0

    def _use_loop_id_counter(self) -> int:
        counter = self._loop_id_counter
        self._loop_id_counter += 1
        return counter

    @property
    def max_rack(self) -> float:
        """
        Returns
        -------
        The maximum racking value of the machine
        """
        return self._max_rack

    @property
    def gauge(self) -> int:
        """
        :return: The number of layers supported at this gauging
        """
        return self._gauge

    @gauge.setter
    def gauge(self, value: int):
        assert value > 0, "Knitout Error: Gauging must be greater than 0"
        assert value <= Machine_State.MAX_GAUGE, \
            f"KnitScript Error: Gauging cannot be greater than max_gauge=={Machine_State.MAX_GAUGE}"
        old_gauge = self.gauge
        self._gauge = value
        if self.gauge != old_gauge:  # don't reset if gauge is held constant
            self.sheet_records = {}
            self._needle_pos_to_layer_pos: Dict[int, int] = {}
            for n in range(0, self.needle_count):
                l_needle = get_sheet_needle(Needle(True, n), self.gauge)
                self._needle_pos_to_layer_pos[n] = l_needle.sheet
            for i in range(0, self.gauge):
                self.record_sheet(i)

    @property
    def sheet(self) -> int:
        """
        Setting the layer will not reset the machine to a machine state to work the given layer
        :return: the current layer being worked
        """
        return self._sheet

    @sheet.setter
    def sheet(self, value: int):
        self.record_sheet(self.sheet)  # record layer before changing layers
        assert 0 <= value < self.gauge, f"KnitScript Error: Layer must be between 0 and the gauge {self.gauge}"
        self._sheet = value

    def sliders_are_clear(self) -> bool:
        """
        :return: True if no loops are on a slider needle and knitting can be executed
        """
        return self.front_bed.sliders_are_clear() and self.back_bed.sliders_are_clear()

    def in_hook(self, yarn_carrier: Yarn_Carrier):
        """
        Declares that the in_hook for this yarn carrier is in use
        :param yarn_carrier: the yarn_carrier to bring in
        """
        self.yarn_manager.inhook(yarn_carrier)

    def release_hook(self):
        """
        Declares that the in-hook is not in use but yarn remains in use
        """
        self.yarn_manager.releasehook()

    def out_hook(self, yarn_carrier: Yarn_Carrier):
        """
        Declares that the yarn is no longer in service, will need to be in-hooked to use
        :param yarn_carrier: the yarn carrier to remove from service
        """
        self.yarn_manager.outhook(yarn_carrier)

    def bring_in(self, yarn_carrier: Yarn_Carrier):
        """
        Brings the yarn carrier into action
        :param yarn_carrier:
        """
        self.yarn_manager.bring_in(yarn_carrier)

    def out(self, yarn_carrier: Yarn_Carrier):
        """
        Moves the yarn_carrier out of action
        :param yarn_carrier:
        """
        self.yarn_manager.out(yarn_carrier)

    def switch_carriage_direction(self):
        """
        Switches the last carriage direction set
        """
        self.last_carriage_direction = self.last_carriage_direction.opposite()

    @property
    def needle_count(self) -> int:
        """
        :return: the number of needles on either bed of the machine
        """
        return self.front_bed.needle_count

    def __len__(self):
        return self.needle_count

    def record_needle_position(self, needle_position: int):
        """
        Records if there are loops on front and back of given needle position
        :param needle_position:
        """
        loops_on_front = self[Needle(is_front=True, position=needle_position)].has_loops
        loops_on_back = self[Needle(is_front=False, position=needle_position)].has_loops
        self._loop_record[needle_position] = loops_on_front, loops_on_back

    def add_loops(self, needle: Needle, carrier_set: Optional[Yarn_Carrier] = None,
                  loops: Optional[Iterable[Loop]] = None,
                  drop_prior_loops: bool = True, record_needle=True) -> List[Loop]:
        """
        Puts the loop_id on given needle, overrides existing loops as if a knit operation took place
        :param record_needle: If true, records locations of loops at this position. Used for resetting sheets
        :param loops: If none, means a new loop is created in knitgraph. Otherwise, use old loops
        :param needle: The needle to add loops to
        :param carrier_set: the set  of yarns making this loop
        :param drop_prior_loops: If true, drops prior loops on the needle
        :return set of loops added to the needle
        """
        new_loops = loops is None
        bed = self.front_bed if needle.is_front else self.back_bed
        prior_loops = [l for l in bed[needle].held_loops]
        if carrier_set is not None:
            assert self.yarn_manager.is_active(carrier_set), f"Yarn Carrier {carrier_set} not in operation"
            self.yarn_manager.make_loop(carrier_set, needle)
        loops = bed.add_loops(needle, self.knit_graph, carrier_set, loops, drop_prior_loops=drop_prior_loops)
        if new_loops:  # Manage Knit Graph construction
            for loop in loops:
                if drop_prior_loops:
                    for parent_loop in prior_loops:
                        self.knit_graph.connect_loops(parent_loop.loop_id, loop.loop_id,
                                                      Pull_Direction.BtF if bed.is_front else Pull_Direction.FtB)  # todo mange cable depth and parent offsets
        if record_needle:
            self.record_needle_position(needle.position)
        return loops

    def knit(self, needle: Needle, carrier_set: Yarn_Carrier, record_needle=True) -> List[Loop]:
        """
        Create new loop with carrier set on needle. Pull through held needles
        :param record_needle: If true, records locations of loops at this position. Used for resetting sheets
        :param needle: needle to knit with
        :param carrier_set: carrier set to use to make loop (multiple loops when plating with multiple carrier
        :return: list of loops created
        """
        assert not needle.is_slider, f"Cannot Knit on slider {needle}"
        assert self.sliders_are_clear(), "Cannot knit when sliders are in use"
        loops = self.add_loops(needle, carrier_set, drop_prior_loops=True, record_needle=record_needle)
        return loops

    def tuck(self, needle: Needle, carrier_set: Yarn_Carrier, record_needle=True) -> List[Loop]:
        """
        Create new loop with carrier set on needle. Do not pull through held loops
        :param record_needle: If true, records locations of loops at this position. Used for resetting sheets
        :param needle: needle to tuck with
        :param carrier_set: carrier set to make loops from
        :return: list of loops created
        """
        assert not needle.is_slider, f"Cannot tuck on slider {needle}"
        assert self.sliders_are_clear(), "Cannot tuck when sliders are in use"
        loops = self.add_loops(needle, carrier_set, drop_prior_loops=False, record_needle=record_needle)
        return loops

    def drop(self, needle: Needle, record_needle=True) -> List[Loop]:
        """
        Clears the loops held at this position as though a drop operation has been done.
        Also drops loop on sliders
        :param record_needle: If true, records locations of loops at this position. Used for resetting sheets
        :param needle: The needle to drop loops from
        :return list of loops that are dropped
        """
        assert not needle.is_slider, f"Cannot drop on slider needles: {needle}"
        assert self.sliders_are_clear(), f"Cannot drop when sliders are not clear"
        if needle.is_front:
            loops = self.front_bed.drop(needle)
        else:
            loops = self.back_bed.drop(needle)
        if record_needle:
            self.record_needle_position(needle.position)
        return loops

    def xfer(self, start: Needle, target: Needle, record_needle=True):
        """
        Xfer's the loop from the starting position to the ending position. Must transfer front to back or back to front
        :param record_needle: If true, records locations of loops at this position. Used for resetting sheets
        :param start: needle to start xfer from
        :param target: needle to end xfer at
        """
        start = self[start]
        target = self[target]
        assert target.is_clear(self), f"{target} is not clear for transfer"
        assert start.is_clear(self), f"{start} is not clear for transfer"
        if start.is_front and target.is_back:
            assert self.valid_rack(start.position, target.position), \
                f"racking {self.racking} does not match f{start.position} to b{target.position}"
        else:
            assert self.valid_rack(target.position, start.position), \
                f"racking {self.racking} does not match b{start.position} to f{target.position}"
        loops = start.held_loops
        if len(loops) > 0:
            self.add_loops(target, loops=loops, drop_prior_loops=False, record_needle=record_needle)
            self.drop(start, record_needle=record_needle)

    def split(self, start: Needle, target: Needle, carrier_set: Yarn_Carrier, record_needle=True) -> List[Loop]:
        """
        Xfers needle from start to target and makes new loop with carrier set on start needle
        :param record_needle: If true, records locations of loops at this position. Used for resetting sheets
        :param start:
        :param target:
        :param carrier_set:
        :return: Loops created by split
        """
        self.xfer(start, target, record_needle=record_needle)
        return self.knit(start, carrier_set, record_needle=record_needle)

    def update_rack(self, front_pos: int, back_pos: int) -> Tuple[int, bool]:
        """
        Updates the current racking to align front and back
        :param front_pos: front needle to align
        :param back_pos: back needle to align
        :return: Return the updated racking, True if the racking is the same as original
        """
        original = self.racking
        self.racking = self.get_rack(front_pos, back_pos)
        return self.racking, original == self.racking

    @staticmethod
    def get_rack(front_pos: int, back_pos: int) -> int:
        """
        Return racking between front and back position
        :param front_pos: front aligned needle
        :param back_pos: back aligned needle
        :return: Racking needed to xfer from front position to back position
        """
        return front_pos - back_pos

    def valid_rack(self, front_pos: int, back_pos: int) -> bool:
        """
        True xfer can be completed at current racking
        :param front_pos: the front needle in the racking
        :param back_pos: the back needle in the racking
        :return: True if the current racking can make this transfer
        """
        needed_rack = self.get_rack(front_pos, back_pos)
        return self.racking == needed_rack

    def xfer_needle_at_racking(self, needle: Needle, slider: bool = False) -> Needle:
        """
        Get teh needle to xfer to at current racking
        :param needle: the needle that will start a xfer or split
        :param slider: if true, returns a slider needle to return to
        :return: The needle that can be transferred to from needle at the current racking of the machine
        """
        if needle.is_front:  # F = B + R, B= F - R
            pos = needle.position - math.floor(self.racking)
        else:
            pos = needle.position + math.floor(self.racking)
        if slider:
            return self[Slider_Needle(not needle.is_front, pos)]
        else:
            return self[Needle(not needle.is_front, pos)]

    def __getitem__(self, item: Needle) -> Needle:
        """
        the needle instance in the machine state
        :param item: a needle object to index by
        :return: the needle instance that holds loops in current machine state
        """
        if item.is_front:
            return self.front_bed[item]
        else:
            return self.back_bed[item]

    def needle(self, is_front: bool, position: int, sheet: Optional[int] = None, gauge: Optional[int] = None) -> Needle:
        """
        The needle in the machine state specified
        :param is_front: True if on front
        :param position: the needle index
        :param sheet: the sheet of the needle, or None for current sheet
        :param gauge: the gauge of the sheet needle, or None for current gauge
        :return: needle on machine at given location
        """
        if sheet is None:
            sheet = self.sheet
        if gauge is None:
            gauge = self.gauge
        return self[Sheet_Needle(is_front, position, sheet, gauge)]

    def get_needle_of_loop(self, loop: Loop) -> Optional[Needle]:
        """
        :return: the needle holding the loop or None if it is not held
        :param loop: The loop to search for
        """
        front_needle = self.front_bed.get_needle_of_loop(loop)
        back_needle = self.back_bed.get_needle_of_loop(loop)
        if front_needle is None and back_needle is None:
            return None
        elif front_needle is None:
            return back_needle
        else:
            assert back_needle is None, f"Loop {loop.loop_id} cannot be on f{front_needle.position} and b{back_needle.position}"
            return front_needle

    def sheet_needle_count(self, gauge: Optional[int] = None) -> int:
        """
        :param: Gauge, set to current gauge if None
        :return: The needle count of the bed broken up by current gauge
        """
        if gauge is None:
            gauge = self.gauge
        assert gauge > 0, "Gauge must be 1 or greater"
        actual_count = self.needle_count
        return int(actual_count / gauge)

    def front_needles(self, on_sheet=True, sheet: Optional[int] = None, gauge: Optional[int] = None) -> List[Needle]:
        """
        :param gauge: defaults to current gauge
        :param sheet: defaults to current sheet
        :param on_sheet: If true, only returns needle on specified sheet and gauge
        :return: List of the needles on the front bed
        """
        if not on_sheet:
            return [f for f in self.front_bed.needles]
        if gauge is None:
            gauge = self.gauge
        assert gauge > 0, "Gauge must be 1 or greater"
        if sheet is None:
            sheet = self.sheet
        assert 0 <= sheet < gauge, f"Sheet {sheet} must be between 0 and gauge {gauge}"
        return [self[Sheet_Needle(True, n, sheet, gauge)] for n in range(0, self.sheet_needle_count(gauge))]

    def back_needles(self, on_sheet=True, sheet: Optional[int] = None, gauge: Optional[int] = None) -> List[Needle]:
        """
        :param gauge: defaults to current gauge
        :param sheet: defaults to current sheet
        :param on_sheet: If true, only returns needle on specified sheet and gauge
        :return: List of the needles on the back bed
        """
        if not on_sheet:
            return [b for b in self.back_bed.needles]
        if gauge is None:
            gauge = self.gauge
        assert gauge > 0, "Gauge must be 1 or greater"
        if sheet is None:
            sheet = self.sheet
        assert 0 <= sheet < gauge, f"Sheet {sheet} must be between 0 and gauge {gauge}"
        return [self[Sheet_Needle(False, n, sheet, gauge)] for n in range(0, self.sheet_needle_count(gauge))]

    def front_sliders(self, on_sheet: bool = True, sheet: Optional[int] = None, gauge: Optional[int] = None) -> List[Needle]:
        """
        :param gauge: defaults to current gauge
        :param sheet: defaults to current sheet
        :param on_sheet: If true, only returns needle on specified sheet and gauge
        :return: List of the sliders on the front bed
        """
        if not on_sheet:
            return [f for f in self.front_bed.sliders]
        if gauge is None:
            gauge = self.gauge
        assert gauge > 0, "Gauge must be 1 or greater"
        if sheet is None:
            sheet = self.sheet
        assert 0 <= sheet < gauge, f"Sheet {sheet} must be between 0 and gauge {gauge}"
        return [self[Slider_Sheet_Needle(True, n, sheet, gauge)] for n in range(0, self.sheet_needle_count(gauge))]

    def back_sliders(self, on_sheet: bool = True, sheet: Optional[int] = None, gauge: Optional[int] = None) -> List[Needle]:
        """
        :param gauge: defaults to current gauge
        :param sheet: defaults to current sheet
        :param on_sheet: If true, only returns needle on specified sheet and gauge
        :return: List of the sliders on the back bed
        """
        if not on_sheet:
            return [b for b in self.back_bed.sliders]
        if gauge is None:
            gauge = self.gauge
        assert gauge > 0, "Gauge must be 1 or greater"
        if sheet is None:
            sheet = self.sheet
        assert 0 <= sheet < gauge, f"Sheet {sheet} must be between 0 and gauge {gauge}"
        return [self[Slider_Sheet_Needle(False, n, sheet, gauge)] for n in range(0, self.sheet_needle_count(gauge))]

    def front_loops(self, on_sheet: bool = True, sheet: Optional[int] = None, gauge: Optional[int] = None) -> List[Needle]:
        """
        The front needles that hold loops
        :param on_sheet: If true, only returns loops on specified sheet
        :param sheet: sheet defaults to current sheet
        :param gauge: gauge defaults to current gauge
        :return: Set of front bed needles with loops on them
        """
        needles = self.front_needles(on_sheet, sheet=sheet, gauge=gauge)
        return [n for n in needles if n.has_loops]

    def back_loops(self, on_sheet: bool = True, sheet: Optional[int] = None, gauge: Optional[int] = None) -> List[Needle]:
        """
        The back needles that hold loops
        :param on_sheet: If true, only returns loops on specified sheet
        :param sheet: sheet defaults to current sheet
        :param gauge: gauge defaults to current gauge
        :return: Set of front bed needles with loops on them
        """
        needles = self.back_needles(on_sheet, sheet=sheet, gauge=gauge)
        return [n for n in needles if n.has_loops]

    def front_slider_loops(self, on_sheet: bool = True, sheet: Optional[int] = None, gauge: Optional[int] = None) -> List[Needle]:
        """
        The front sliders that hold loops
        :param on_sheet: If true, only returns loops on specified sheet
        :param sheet: sheet defaults to current sheet
        :param gauge: gauge defaults to current gauge
        :return: Set of front bed needles with loops on them
        """
        needles = self.front_sliders(on_sheet, sheet=sheet, gauge=gauge)
        return [n for n in needles if n.has_loops]

    def back_slider_loops(self, on_sheet: bool = True, sheet: Optional[int] = None, gauge: Optional[int] = None) -> List[Needle]:
        """
        The back sliders that hold loops
        :param on_sheet: If true, only returns loops on specified sheet
        :param sheet: sheet defaults to current sheet
        :param gauge: gauge defaults to current gauge
        :return: Set of front bed needles with loops on them
        """
        needles = self.back_sliders(on_sheet, sheet=sheet, gauge=gauge)
        return [n for n in needles if n.has_loops]

    def all_needles(self, on_sheet: bool = True, sheet: Optional[int] = None, gauge: Optional[int] = None) -> List[Needle]:
        """
        All needles ordered for a machine pass
        :param on_sheet: If true, only returns loops on specified sheet
        :param sheet: sheet defaults to current sheet
        :param gauge: gauge defaults to current gauge
        :return: Set of front bed needles with loops on them
        """
        needles = self.front_needles(on_sheet, sheet, gauge)
        back_needles = self.back_needles(on_sheet, sheet, gauge)
        needles.extend(back_needles)
        return needles

    def all_sliders(self, on_sheet: bool = True, sheet: Optional[int] = None, gauge: Optional[int] = None) -> List[Needle]:
        """
        All sliders ordered for a machine pass
        :param on_sheet: If true, only returns loops on specified sheet
        :param sheet: sheet defaults to current sheet
        :param gauge: gauge defaults to current gauge
        :return: Set of front bed needles with loops on them
        """
        needles = self.front_sliders(on_sheet, sheet, gauge)
        back_needles = self.back_sliders(on_sheet, sheet, gauge)
        needles.extend(back_needles)
        return needles

    def all_loops(self, on_sheet: bool = True, sheet: Optional[int] = None, gauge: Optional[int] = None) -> List[Needle]:
        """
        All needles that hold loops ordered for a machine pass
        :param on_sheet: If true, only returns loops on specified sheet
        :param sheet: sheet defaults to current sheet
        :param gauge: gauge defaults to current gauge
        :return: Set of front bed needles with loops on them
        """
        return [n for n in self.all_needles(on_sheet, sheet, gauge) if n.has_loops]

    def all_slider_loops(self, on_sheet: bool = True, sheet: Optional[int] = None, gauge: Optional[int] = None) -> List[Needle]:
        """
        All slider needles that hold loops ordered for a machine pass
        :param on_sheet: If true, only returns loops on specified sheet
        :param sheet: sheet defaults to current sheet
        :param gauge: gauge defaults to current gauge
        :return: Set of front bed needles with loops on them
        """
        return [n for n in self.all_sliders(on_sheet, sheet, gauge) if n.has_loops]

    def record_sheet(self, sheet: int):
        """
        Stores a record of the sheet's needle locations to be returned when the sheet is set back to this
        :param sheet: current sheet to record
        """
        return
        # record = Sheet_Record(self.gauge, sheet)
        # record.record_machine_state(self)
        # self.sheet_records[sheet] = record

    # def move_layer_relative_to_active_layer(self, layer_position, layer_index: int,
    #                                         active_layer_position: int,
    #                                         gauge: int, allow_layer_merge: bool = False) -> List[str]:
    #     """
    #     Move layer relative to layer that will be active. No-op if layer and active_layer are the same
    #     :param layer_index: The index of the layer (0.0, 0.1, 0.2...) in the gauging schema that needs to be peeled away
    #     :param layer_position: the position (lower -> front) of the layer to be peeled
    #     :param active_layer_position: the position of the layer to remain active
    #     :param gauge: the gauge of the current schema
    #     :param allow_layer_merge:
    #     :return: knitout instructions from xfers
    #     """
    #     if layer_position < active_layer_position:
    #         return self.bring_layer_to_front(layer_index, gauge, allow_layer_merge)
    #     elif layer_position > active_layer_position:
    #         return self.bring_layer_to_back(layer_index, gauge, allow_layer_merge)
    #     else:
    #         return []

    def peel_sheet_relative_to_active_sheet(self, active_sheet: int) -> Tuple[List[str], List[int]]:
        """
        Moves loops out of the way of the active sheet based on needle layer positions
        :param active_sheet: the sheet to activate
        :return: xfer knitout instructions
        """
        peel_order_to_needles: Dict[int, List[Needle]] = {i: [] for i in range(0, self.gauge)}
        same_layer_needles: List[int] = []

        for needle_pos, needle_layer in self._needle_pos_to_layer_pos.items():
            back = self[Needle(False, needle_pos)]
            front = self[Needle(True, needle_pos)]
            if back.has_loops or front.has_loops:
                sheet_needle = get_sheet_needle(Needle(True, needle_pos), self.gauge)
                if sheet_needle.sheet != active_sheet:
                    active_sheet_needle = Sheet_Needle(True, sheet_needle.sheet_pos, active_sheet, self.gauge)
                    active_sheet_layer = self._needle_pos_to_layer_pos[active_sheet_needle.position]
                    if active_sheet_layer == needle_layer:
                        same_layer_needles.append(needle_pos)
                    if needle_layer < active_sheet_layer and back.has_loops:  # needle is in front of sheet
                        peel_order_to_needles[sheet_needle.sheet].append(back)
                    elif needle_layer > active_sheet_layer and front.has_loops:  # needle is in back of sheet
                        peel_order_to_needles[sheet_needle.sheet].append(front)

        xfers = []
        for sheet, peel_needles in peel_order_to_needles.items():
            xfers.append(f"; Peel sheet {sheet} relative to {active_sheet}\n")
            for peel_needle in peel_needles:
                xfer_instruction = xfer(self, peel_needle, peel_needle.opposite(), record_needle=False)
                xfers.append(xfer_instruction)
        return xfers, same_layer_needles

    def peel_sheet_relative_to_active_sheets(self, active_sheets: list[int]) -> List[str]:
        """
        Moves loops out of the way of the active sheet based on needle layer positions
        :param active_sheets: the sheets to activate
        :return: xfer knitout instructions
        """
        peel_order_to_needles: Dict[int, List[Needle]] = {i: [] for i in range(0, self.gauge)}

        for needle_pos, needle_layer in self._needle_pos_to_layer_pos.items():
            back = self[Needle(False, needle_pos)]
            front = self[Needle(True, needle_pos)]
            if back.has_loops or front.has_loops:
                sheet_needle = get_sheet_needle(Needle(True, needle_pos), self.gauge)
                if sheet_needle.sheet not in active_sheets:
                    active_sheet_layer = None
                    for active_sheet in active_sheets:
                        active_sheet_needle = Sheet_Needle(True, sheet_needle.sheet_pos, active_sheet, self.gauge)
                        other_layer = self._needle_pos_to_layer_pos[active_sheet_needle.position]
                        if active_sheet is not None:
                            assert other_layer == active_sheet_layer, \
                                f"Cannot Work sheets {active_sheets} with different layers at {needle_pos}"
                        active_sheet_layer = other_layer
                    assert active_sheet_layer != needle_layer, \
                        f"Cannot separate sheets {sheet_needle.sheet_pos} and sheets {active_sheets} with same layer position at {needle_pos}"
                    if needle_layer < active_sheet_layer and back.has_loops:  # needle is in front of sheet
                        peel_order_to_needles[sheet_needle.sheet].append(back)
                    elif needle_layer > active_sheet_layer and front.has_loops:  # needle is in back of sheet
                        peel_order_to_needles[sheet_needle.sheet].append(front)

        xfers = []
        for sheet, peel_needles in peel_order_to_needles.items():
            xfers.append(f"; Peel sheet {sheet} relative to {active_sheets}\n")
            for peel_needle in peel_needles:
                xfer_instruction = xfer(self, peel_needle, peel_needle.opposite(), record_needle=False)
                xfers.append(xfer_instruction)
        return xfers

    def reset_sheet(self, sheet: int) -> List[str]:
        """
        Returns loops to a recorded location in a layer gauging schema
        :param sheet: the sheet to reset to
        :return: the knitout of the xfers
        """
        knitout, same_layer_needles = self.peel_sheet_relative_to_active_sheet(sheet)

        for f, b in zip(self.front_bed.needles, self.back_bed.needles):
            sheet_needle = get_sheet_needle(f, self.gauge)
            if sheet_needle.sheet == sheet or f.position in same_layer_needles:
                front_had_loops, back_had_loops = self._loop_record[f.position]
                if front_had_loops and back_had_loops:
                    assert f.has_loops and b.has_loops, f"Loops recorded on {f} and {b}, but cannot return to seperated state"
                elif front_had_loops:
                    if f.has_loops:
                        assert not b.has_loops, f"Cannot return loops from {b} because loops are on {f}"
                    else:
                        assert b.has_loops, f"Loops recorded on {f} have been lost"
                        knitout.append(xfer(self, b, f, f"Return loops {b.held_loops} on {b} to {f}"))
                elif back_had_loops:
                    if b.has_loops:
                        assert not f.has_loops, f"Cannot return loops from {f} because loops are on {f}"
                    else:
                        assert f.has_loops, f"Loops recorded on {b} have been lost"
                        knitout.append(xfer(self, f, b, f"return loops {f.held_loops} on {f} to {b}"))
        return knitout

    def reset_sheets(self, sheets: List[int]) -> List[str]:
        """
        Returns loops to a recorded location in a layer gauging schema
        :param sheets: the sheets to reset to
        :return: the knitout of the xfers
        """
        knitout = self.peel_sheet_relative_to_active_sheets(sheets)

        for f, b in zip(self.front_bed.needles, self.back_bed.needles):
            sheet_needle = get_sheet_needle(f, self.gauge)
            if sheet_needle.sheet in sheets:
                front_had_loops, back_had_loops = self._loop_record[f.position]
                if front_had_loops and back_had_loops:
                    assert f.has_loops and b.has_loops, f"Loops recorded on {f} and {b}, but cannot return to seperated state"
                elif front_had_loops:
                    if f.has_loops:
                        assert not b.has_loops, f"Cannot return loops from {b} because loops are on {f}"
                    else:
                        assert b.has_loops, f"Loops recorded on {f} have been lost"
                        knitout.append(xfer(self, b, f, f"Return loops {b.held_loops} on {b} to {f}"))
                elif back_had_loops:
                    if b.has_loops:
                        assert not f.has_loops, f"Cannot return loops from {f} because loops are on {f}"
                    else:
                        assert f.has_loops, f"Loops recorded on {b} have been lost"
                        knitout.append(xfer(self, f, b, f"return loops {f.held_loops} on {f} to {b}"))
        return knitout

    def set_layer_position(self, needle_pos: int, layer_value: int):
        """
        Moves the layer_index's position to new_position and pushes all subsequent layers forward, circling back
        :param needle_pos:
        :param layer_value: the position to set the layer to. Lower values are brought forward
        """
        self._needle_pos_to_layer_pos[needle_pos] = layer_value
        # if self.needle_pos_to_layer_pos[needle_pos] != layer_value:
        #     l_needle = get_sheet_needle(Needle(True, needle_pos), self.gauge)
        #     neighbor_positions = [n.position for n in l_needle.gauge_neighbors()]
        #     layer_to_positions = {self.needle_pos_to_layer_pos[pos]: pos for pos in neighbor_positions}
        #     layer_to_positions[self.needle_pos_to_layer_pos[needle_pos]] = needle_pos
        #
        #     new_layer_positions = {}
        #     layer_dif = layer_value - self.needle_pos_to_layer_pos[needle_pos]
        #     for layer, position in layer_to_positions.items():
        #         new_layer = (layer + layer_dif) % self.gauge
        #         new_layer_positions[new_layer] = position
        #
        #     for layer, n_pos in new_layer_positions.items():
        #         self.needle_pos_to_layer_pos[n_pos] = layer

    def push_layer_backward(self, needle_position: int, backward_layers: int = 1):
        """
        Moves a layer's position forward from current position
        :param needle_position:
        :param backward_layers: amount to move forward, circles around from 0 to back layer
        """
        if backward_layers == 0:
            return  # no op because no change to layer order
        layer_position = (self._needle_pos_to_layer_pos[needle_position] + backward_layers) % self.gauge
        self.set_layer_position(needle_position, layer_position)

    def push_layer_forward(self, needle_position: int, forward_layers: int = 1):
        """
        Moves a layer back in position
        :param needle_position:
        :param forward_layers:
        """
        self.push_layer_backward(needle_position, -1 * forward_layers)

    def set_layer_to_front(self, needle_position: int):
        """
        Sets the layer as the front layer
        :param needle_position:
        """
        self.set_layer_position(needle_position, 0)

    def set_layer_to_back(self, needle_position: int):
        """
        Sets the layer as the back layer
        :param needle_position:
        """
        self.set_layer_position(needle_position, self.gauge - 1)