"""Used for storing results of function returns"""
from interpreter.expressions.expressions import Expression
from interpreter.parser.knit_script_context import Knit_Script_Context
from interpreter.statements.Statement import Statement


class Return_Statement(Statement):
    """
        Statement which will break out of function scope leaving behind a returned value
    """

    def __init__(self, exp: Expression):
        """
        Instantiate
        :param exp: expression to return
        """
        super().__init__()
        self._exp: Expression = exp

    def execute(self, context: Knit_Script_Context):
        """
        Collects return value and exits scope to next function level
        :param context:  The current context of the interpreter
        """
        value = self._exp.evaluate(context)
        context.variable_scope.return_value = value
        context.variable_scope.has_return = True

    def __str__(self):
        return f"return {self._exp}"

    def __repr__(self):
        return str(self)