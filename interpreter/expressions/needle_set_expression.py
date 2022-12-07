"""Expressions for accessing standard needle sets from the machine state"""

from enum import Enum
from typing import List

from interpreter.expressions.expressions import Expression
from interpreter.parser.knit_pass_context import Knit_Script_Context
from knitting_machine.machine_components.needles import Needle


class Needle_Sets(Enum):
    """Naming of Needles sets on Machine State"""
    Needles = "Needles"
    Front_Needles = "Front_Needles"
    Back_Needles = "Back_Needles"
    Sliders = "Sliders"
    Front_Sliders = "Front_Sliders"
    Back_Sliders = "Back_Sliders"
    Loops = "Loops"
    Front_Loops = "Front_Loops"
    Back_Loops = "Back_Loops"
    Slider_Loops = "Slider_Loops"
    Front_Slider_Loops = "Front_Slider_Loops"
    Back_Slider_Loops = "Back_Slider_Loops"

    @staticmethod
    def values() -> List[str]:
        """
        :return: value strings of KP_Type
        """
        return [*(e.value for e in Needle_Sets)]


class Needle_Set_Expression(Expression):
    """Evaluates keywords to sets of needles on the machine"""

    def __init__(self, set_str: str):
        """
        Instantiate
        :param set_str: the string to identify the set
        """
        super().__init__()
        self._set_str:str = set_str

    def evaluate(self, context: Knit_Script_Context) -> List[Needle]:
        """
        Evaluate the expression
        :param context: The current context of the interpreter
        :return: Specified set of needles
        """
        kp_set = Needle_Sets[self._set_str]
        if kp_set is Needle_Sets.Front_Needles:
            return context.machine_state.front_needles()
        elif kp_set is Needle_Sets.Back_Needles:
            return context.machine_state.back_needles()
        elif kp_set is Needle_Sets.Front_Sliders:
            return context.machine_state.front_sliders()
        elif kp_set is Needle_Sets.Back_Sliders:
            return context.machine_state.back_sliders()
        elif kp_set is Needle_Sets.Front_Loops:
            return context.machine_state.front_loops()
        elif kp_set is Needle_Sets.Back_Loops:
            return context.machine_state.back_loops()
        elif kp_set is Needle_Sets.Needles:
            return context.machine_state.all_needles()
        elif kp_set is Needle_Sets.Front_Slider_Loops:
            return context.machine_state.front_slider_loops()
        elif kp_set is Needle_Sets.Back_Slider_Loops:
            return context.machine_state.back_slider_loops()
        elif kp_set is Needle_Sets.Sliders:
            return context.machine_state.all_sliders()
        elif kp_set is Needle_Sets.Loops:
            return context.machine_state.all_loops()
        elif kp_set is Needle_Sets.Slider_Loops:
            return context.machine_state.all_slider_loops()

    def __str__(self):
        return self._set_str

    def __repr__(self):
        return str(self)
