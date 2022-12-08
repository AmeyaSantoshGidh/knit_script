"""Components for managing headers"""
from enum import Enum

from interpreter.expressions.expressions import Expression
from interpreter.expressions.values import Header_ID_Value
from interpreter.parser.knit_script_context import Knit_Script_Context
from interpreter.statements.Statement import Statement
from knitting_machine.Machine_State import Machine_State
from knitting_machine.machine_components.machine_position import Machine_Position

class Header_ID(Enum):
    """
        Values that can be updated in header
    """
    Machine = "Machine"
    Width = "Width"
    Carrier_Count = "Carriers"
    Position = "Position"
    Rack = "Rack"
    Hook = "Hook"

class Machine_Type(Enum):
    """
        Accepted Machine specifications
    """
    SWG091N2 = 'SWG091N2'
class Header:
    """A class structure for generating knitout header files"""
    def __init__(self, width: int = 250,
                 position: Machine_Position = Machine_Position.Center,
                 carrier_count: int = 10, machine_type: Machine_Type = Machine_Type.SWG091N2,
                 max_rack: float =4.25, hook_size:int = 5):
        self._max_rack = max_rack
        self._hook_size = hook_size
        self._machine_type = machine_type
        self._width = width
        self._carrier_count = carrier_count
        self._position = position

    def set_value(self, header_id: Header_ID, value):
        """
        Set the header value by id
        :param header_id: Value to set in the header
        :param value: value to set it to
        """
        if header_id is Header_ID.Machine:
            assert isinstance(value, Machine_Type), f"Expected String for Machine Type but got {value}"
            self._machine_type = value
        elif header_id is Header_ID.Carrier_Count:
            assert isinstance(value, int), f"Expected carrier count but got {value}"
            self._carrier_count = value
        elif header_id is Header_ID.Width:
            assert  isinstance(value, int), f"Expected width but got {value}"
            self._width = value
        elif header_id is Header_ID.Position:
            assert isinstance(value, Machine_Position),\
                f"Expected machine position [left, right, center, keep] but got {value}"
            self._position = value
        elif header_id is Header_ID.Rack:
            assert isinstance(value, float) or isinstance(value, int), f"Expected racking value but got {value}"
            self._max_rack = float(value)
        elif header_id is Header_ID.Hook:
            assert  isinstance(value, int), f"Expected hook size but got {value}"
            self._hook_size = value
    def machine_state(self) -> Machine_State:
        """
        :return: A reset machine state with given specifications
        """
        return Machine_State(self._width, self._max_rack, self._carrier_count, self._hook_size)
    def header_lines(self):
        """
        :return: Lines of the knitout header
        """
        carriers = [i for i in range(1, self._carrier_count + 1)]
        carrier_str = str(carriers).replace(",", "")
        return [
            ";!knitout-2\n",
            f";;Machine: {self._machine_type}\n",
            f";;Width: {self._width}\n",
            f";;Carriers: {carrier_str}\n",
            f";;Position: {self._position}\n"
        ]

    @staticmethod
    def MIT(position: Machine_Position):
        """
        :param position: Position of program on bed
        :return: A header for the MIT machine in Wojciech's lab
        """
        return Header(540, position)

    @staticmethod
    def UW(position:Machine_Position):
        """
        :param position: Position of program on bed
        :return: A header for the UW CSE machine
        """
        return Header(250, position)



class Header_Statement(Statement):
    """
        Header statements update variables of the machine state and knitout
    """
    def __init__(self, type_id: Header_ID_Value, value: Expression ):
        super().__init__()
        self._value:Expression = value
        self._type_id: Header_ID_Value = type_id

    def execute(self, context: Knit_Script_Context):
        """
        Set the header value and update machine state
        :param context: context to get header and machine state from
        """
        value = self._value.evaluate(context)
        type_id = self._type_id.evaluate(context)
        context.header.set_value(type_id, value)
        context.machine_state = context.header.machine_state()