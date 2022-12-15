"""Assignment structure"""
from typing import Any

from knit_script.knit_script_interpreter.expressions.expressions import Expression
from knit_script.knit_script_interpreter.knit_script_context import Knit_Script_Context
from knit_script.knit_script_interpreter.scope.global_scope import Machine_Variables
from knit_script.knitting_machine.machine_components.Sheet_Needle import Sheet_Identifier


class Assignment:
    """
        Class for managing assignment expressions
    """

    def __init__(self, var_name: str, var_expression: Expression):
        """
        Instantiate
        :param var_name: name of variable
        :param var_expression: value to assign
        """
        super().__init__()
        self._var_expression: Expression = var_expression
        self._variable_name: str = var_name

    @property
    def variable_name(self) -> str:
        """
        :return: Name of variable being assigned
        """
        return self._variable_name
    def assign_value(self, context: Knit_Script_Context) -> Any:
        """
        Assign the value to the variable
        :param context:  The current context of the knit_script_interpreter
        :return: result of assignment expression
        """
        value = self.value(context)
        if Machine_Variables.in_machine_variables(self.variable_name):  # short cut for always global variables
            Machine_Variables[self.variable_name].set_value(context, value)
        else:
            context.variable_scope[self.variable_name] = value
        return value

    def value(self, context) -> Any:
        """
        Get the value to be assigned
        :param context: the current context to evaluate value at
        :return: Value that is being assigned to variable
        """
        expression_result = self._var_expression.evaluate(context)
        return expression_result

    def __str__(self):
        return f"Assign({self.variable_name} <- {self._var_expression})"

    def __repr__(self):
        return str(self)
