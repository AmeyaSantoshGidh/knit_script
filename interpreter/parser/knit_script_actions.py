"""Actions for converting parglare elements into useful code"""
from typing import List, Tuple, Union, Optional

from parglare import get_collector

from interpreter.expressions.Gauge_Expression import Gauge_Expression
from interpreter.expressions.accessors import Attribute_Accessor_Expression, Method_Call, Indexing_Expression
from interpreter.expressions.expressions import Expression
from interpreter.expressions.variables import Variable_Expression
from interpreter.expressions.function_expressions import Function_Call
from interpreter.expressions.instruction_expression import Needle_Instruction_Exp, Needle_Instruction
from interpreter.expressions.list_expression import Knit_Script_List, Knit_Script_Dictionary, List_Comp, Dictionary_Comprehension, Unpack, Sliced_List
from interpreter.expressions.machine_accessor import Machine_Accessor, Sheet_Expression
from interpreter.expressions.needle_expression import Needle_Expression
from interpreter.expressions.carrier import Carrier_Expression
from interpreter.expressions.needle_set_expression import Needle_Sets, Needle_Set_Expression
from interpreter.expressions.not_expression import Not_Expression
from interpreter.expressions.operator_expressions import Operator_Expression
from interpreter.expressions.values import Boolean_Value, Bed_Side_Value, Bed_Value, Float_Value, Int_Value, String_Value, None_Value, Bed_Side, Machine_Position_Value, \
    Machine_Type_Value, Header_ID_Value
from interpreter.expressions.formatted_string import Formatted_String_Value
from interpreter.expressions.direction import Pass_Direction_Expression
from interpreter.expressions.xfer_pass_racking import Xfer_Pass_Racking
from interpreter.statements.Drop_Pass import Drop_Pass
from interpreter.statements.Push_Statement import Push_Statement
from interpreter.statements.Statement import Statement, Expression_Statement
from interpreter.statements.Variable_Declaration import Variable_Declaration
from interpreter.statements.Assertion import Assertion
from interpreter.statements.Print import Print
from interpreter.statements.With_Statement import With_Statement
from interpreter.statements.assignment import Assignment
from interpreter.statements.branch_statements import If_Statement
from interpreter.statements.carrier_statements import Cut_Statement, Remove_Statement
from interpreter.statements.code_block_statements import Code_Block
from interpreter.statements.control_loop_statements import While_Statement, For_Each_Statement
from interpreter.statements.function_dec_statement import Function_Declaration
from interpreter.statements.header_statement import Machine_Type, Header_ID, Header_Statement
from interpreter.statements.return_statement import Return_Statement
from interpreter.statements.in_direction_statement import In_Direction_Statement
from interpreter.statements.instruction_statements import Pause_Statement
from interpreter.statements.try_catch_statements import Try_Catch_Statement
# some boiler plate parglare code
from interpreter.statements.xfer_pass_statement import Xfer_Pass_Statement
from knitting_machine.machine_components.machine_position import Machine_Bed_Position, Machine_Position

action = get_collector()

@action
def program(_, __, head: List[Header_Statement], statements: List[Statement]):
    """
    :param _:
    :param __:
    :param head: list of header values to set the machine state
    :param statements: the list of statements to execute
    :return: header, statements
    """
    return head, statements
@action
def header(_, __, type_id:Header_ID_Value, value: Expression):
    """
    :param _:
    :param __:
    :param type_id: Value of header to update
    :param value: the value to update to
    :return: Statement for updating header
    """
    return Header_Statement(type_id, value)
# basic expressions and statements
@action
def identifier(_, node: str) -> Expression:
    """
    :param _: ignored parglare context
    :param node: the string recognized as an identifier
    :return: variable expression or withheld keyword
    """
    if node == "None":
        return None_Value()
    elif node == "True" or node == "False":
        return Boolean_Value(node)
    elif node in Bed_Side:
        return Bed_Side_Value(node)
    elif node in Machine_Bed_Position:
        return Bed_Value(node)
    elif node in Machine_Position:
        return Machine_Position_Value(node)
    elif node in Machine_Type:
        return Machine_Type_Value(node)
    elif node in Header_ID:
        return Header_ID_Value(node)
    elif node == "machine":
        return Machine_Accessor()
    elif node in Needle_Sets:
        return Needle_Set_Expression(node)
    else:
        return Variable_Expression(node)


@action
def declare_variable(_, __, assign: Assignment) -> Variable_Declaration:
    """
    :param assign: assignment before eol punctuation
    :param _: ignored parglare context
    :param __: ignored nodes
    :return: Variable Declaration Statement that assigns the variable on execution
    """
    return Variable_Declaration(assign)


@action
def assertion(_, __, exp: Expression, error: Optional[Expression] = None) -> Assertion:
    """
    :param __: ignored nodes
    :param error: error to report
    :param _: ignored parglare context
    :param exp: expression to evaluate assertion by
    :return: Assertion Statement
    """
    return Assertion(exp, error)


@action
def print_statement(_, __, exp: Expression) -> Print:
    """
    :param _: ignored parglare context
    :param __: ignored nodes
    :param exp: expression to print
    :return: Print Statement
    """
    return Print(exp)


@action
def try_catch(_, __, try_block: Statement, catch_block: Statement) -> Try_Catch_Statement:
    """
    :param _: ignored parglare context
    :param __: ignored nodes
    :param try_block: statements to execute in try branch
    :param catch_block: statements to execute in catch branch
    :return: Try Catch
    """
    # todo: better exception management
    return Try_Catch_Statement(try_block, catch_block)


@action
def pause_statement(_, __) -> Pause_Statement:
    """
    :param _: ignored parglare context
    :param __: ignored nodes
    :return: Pause statement
    """
    return Pause_Statement()


@action
def assignment(_, __, var_name: Variable_Expression, exp: Expression):
    """
    :param _: ignored parglare context
    :param __: ignored nodes
    :param var_name: processed identifier to variable name
    :param exp: expression to assign variable value
    :return: assignment expression which evaluates to expression value
    """
    # todo: ensure that typing is checking identifier not over shadowing keywords
    return Assignment(var_name.variable_name, exp)


# NUMBERS #

@action
def float_exp(_, node: str) -> Float_Value:
    """
    :param _: ignored parglare context
    :param node: the number string
    :return: the positive number specified
    """
    return Float_Value(node)


@action
def int_exp(_, node: str) -> Int_Value:
    """
    :param _: ignored parglare context
    :param node: the number string
    :return: the positive number specified
    """
    return Int_Value(node)


@action
def direction_exp(_, nodes: list) -> Pass_Direction_Expression:
    """
    
    :param _: 
    :param nodes: single node list with direction keyword
    :return: pass direction
    """
    return Pass_Direction_Expression(nodes[0])


@action
def string(_, node: str) -> String_Value:
    """
    :param _: ignored parglare context
    :param node: string value
    :return: Expression storing quote
    """
    no_quotes = node.strip("\"")
    return String_Value(no_quotes)


@action
def f_string_section(_, __, exp: Optional[Expression] = None, string_value: Optional[str] = None) -> Expression:
    """
    :param __:
    :param exp: expression in formatting
    :param string_value: string in formatting
    :param _: ignored parglare context
    :return: Expression of string value of section of a formatted string
    """
    if exp is not None:
        return exp
    else:
        return String_Value(string_value)

@action
def formatted_string(_, __, sections: List[Expression]) -> Formatted_String_Value:
    """
    :param __:
    :param sections: f string sections parsed as expressions
    :param _: ignored parglare context
    :return: Formatted string expression
    """
    return Formatted_String_Value(sections)

# @action
# def param_kwargs_list(_, __,
#                       args: Optional[List[Expression]],
#                       kwargs: Optional[Tuple[str, List[Assignment]]]) -> Tuple[List[Expression], List[Assignment]]:
#     if args is None:
#         args = []
#     if kwargs is None:
#         kwargs = []
#     else:
#         kwargs = kwargs[1]
#     return args, kwargs


@action
def call_list(_, __, params: Optional[List[Expression]] = None,
              kwargs: Optional[List[Assignment]] = None) -> Tuple[List[Expression], List[Assignment]]:
    """
    :param _:
    :param __:
    :param params: the parameters in the call list
    :param kwargs: the keyword set parameters in the call list
    :return: parameters and kwargs
    """
    if params is None:
        params = []
    if kwargs is None:
        kwargs = []
    return params, kwargs


@action
def function_call(_, __, func_name: Variable_Expression,
                  args: Tuple[List[Expression], List[Assignment]]) -> Function_Call:
    """
    :param _:
    :param __:
    :param func_name: name of the function being called
    :param args: the arguments passed to the function
    :return: the function call
    """
    if args is None:
        params = []
        kwargs = []
    else:
        params = args[0]
        kwargs = args[1]
    return Function_Call(func_name, params, kwargs)


@action
def list_expression(_, __, exps: List[Expression]):
    """
    :param _:
    :param __:
    :param exps: expressions in the list
    :return: the list expression
    """
    return Knit_Script_List(exps)


@action
def list_comp(_, __, fill_exp: Expression, spacer: Optional[Union[str, Expression]],
              variables: List[Variable_Expression], iter_exp: Expression,
              comp_cond: Expression) -> List_Comp:
    """
    :param _:
    :param __:
    :param fill_exp: Expression that fills the list
    :param spacer: the spacer value across the variables
    :param variables: variables to fill from iterable
    :param iter_exp: the iterable to pass over
    :param comp_cond: condition to evaluate for adding a value
    :return: List comprehension
    """
    return List_Comp(fill_exp, spacer, variables, iter_exp, comp_cond)


@action
def sliced_list(_, __, iter_exp: Expression, start: Optional[Expression],
                end: Optional[Expression], spacer: Optional[Expression]) -> Sliced_List:
    """
    :param _:
    :param __:
    :param iter_exp: iterable to slice
    :param start: start of slice, inclusive, defaults to 0
    :param end: end of slice, exclusive, defaults to last element
    :param spacer: spacer of slice, defaults to 1
    :return: The sliced list
    """
    return Sliced_List(iter_exp, start, end, spacer)


# @action
# def spacer_splice(_, __, spacer: Expression) -> Expression:
#     """
#     component of sliced list
#     :param _:
#     :param __:
#     :param spacer: expression to space by
#     :return: the spacer
#     """
#     return spacer


# @action
# def comp_condition(_, __, condition: Expression) -> Expression:
#     return condition


@action
def dict_assign(_, __, key: Expression, exp: Expression) -> Tuple[Expression, Expression]:
    """
    collect key value pair
    :param _:
    :param __:
    :param key: key expression
    :param exp: value expression
    :return: key, value
    """
    return key, exp


@action
def dict_expression(_, __, kwargs: List[Tuple[Expression, Expression]]):
    """
    :param _:
    :param __:
    :param kwargs: key value pairs
    :return: The dictionary
    """
    return Knit_Script_Dictionary(kwargs)


@action
def dict_comp(_, __, key:Expression, value:Expression,
              variables: List[Variable_Expression], iter_exp: Expression) -> Dictionary_Comprehension:
    """
    :param _:
    :param __:
    :param key: key expression
    :param value: value expression
    :param variables: variables to parse from iterable
    :param iter_exp: the iterable to parse over
    :return: Dictionary comprehension
    """
    return Dictionary_Comprehension(key, value, variables, iter_exp)  # todo add conditionals


@action
def unpack(_, __, exp: Expression) -> Unpack:
    """
    :param _:
    :param __:
    :param exp: expression to unpack
    :return: Unpacking expression
    """
    return Unpack(exp)


@action
def code_block(_, __, statements: List[Statement]) -> Code_Block:
    """
    :param _: ignored parglare context
    :param __: ignored nodes
    :param statements: statements to execute in sub scope
    :return: scoping block
    """
    return Code_Block(statements)


# @action
# def else_statement(_, __, stmnt: Statement) -> Statement:
#     """
#     :param _: ignored parglare context
#     :param __: ignored nodes
#     :param stmnt: statement to execute on else
#     :return: statement to execute
#     """
#     return stmnt


@action
def elif_statement(_, __, exp: Expression, stmnt: Statement) -> Tuple[Expression, Statement]:
    """
    components of an elif statement
    :param _: ignored parglare context
    :param __: ignored nodes
    :param exp: expression to test on elif
    :param stmnt: statement to execute on true result
    :return: expression and statement to execute when true
    """
    return exp, stmnt


@action
def if_statement(_, __,
                 condition: Expression, true_statement: Code_Block,
                 elifs: List[Tuple[Expression, Statement]],
                 false_statement: Optional[Code_Block] = None) -> If_Statement:
    """

    :param elifs: list of else-if conditions and statements
    :param _:
    :param __:
    :param condition: branching condition
    :param true_statement: statement to execute on true
    :param false_statement: statement to execute on false
    :return: if statement
    """
    while len(elifs) > 0:
        elif_tuple = elifs.pop()
        false_statement = If_Statement(elif_tuple[0], elif_tuple[1], false_statement)
    return If_Statement(condition, true_statement, false_statement)


@action
def while_statement(_, __, condition: Expression, while_block: Code_Block) -> While_Statement:
    """

    :param _:
    :param __:
    :param condition: condition to evaluate on while
    :param while_block: the statement to execute with each iteration
    :return:
    """
    return While_Statement(condition, while_block)


# @action
# def on_bed(_, __, bed: Union[str, Expression], s: Optional[str]) -> Tuple[Union[str, Expression], bool]:
#     return bed, s is not None


# @action
# def every_n(_, __, n: Union[str, Expression]) -> Union[str, Expression]:
#     return n


@action
def for_each_statement(_, __, variables: List[Variable_Expression], iters: List[Expression], block: Code_Block) -> For_Each_Statement:
    """
    :param _:
    :param __:
    :param variables: to assign on each iteration of iterable
    :param iters: iterable to iterate over
    :param block: statement to execute with each iteration
    :return: For each statement
    """
    if len(iters) == 1:
        return For_Each_Statement(variables, iters[0], block)
    else:
        return For_Each_Statement(variables, iters, block)


@action
def as_assignment(_, __, variable: Variable_Expression, exp: Expression) -> Assignment:
    """
    :param _:
    :param __:
    :param variable: variable to assign to
    :param exp: expression to assign
    :return: Assignment value
    """
    return Assignment(var_name=variable.variable_name, var_expression=exp)


@action
def with_statement(_, __, assigns: List[Assignment], block: Code_Block) -> With_Statement:
    """
    :param _:
    :param __:
    :param assigns: assignments for block
    :param block: block to execute
    :return: with statement
    """
    return With_Statement(block, assigns)


@action
def needle_instruction(_, __, inst: str) -> Needle_Instruction:
    """
    :param _:
    :param __:
    :param inst: instruction keyword
    :return: needle instruction
    """
    return Needle_Instruction.get_instruction(inst)


@action
def instruction_assignment(_, __, inst: Expression, needles: List[Expression]) -> Needle_Instruction_Exp:
    """
    :param _:
    :param __:
    :param inst: instruction to apply to needles
    :param needles: needles to apply instruction to
    :return: Needle instruction expression
    """
    return Needle_Instruction_Exp(inst, needles)


@action
def carriage_pass(_, __, pass_dir: Expression, instructions: List[Needle_Instruction_Exp]) -> In_Direction_Statement:
    """
    :param _:
    :param __:
    :param pass_dir: direction to apply instructions in
    :param instructions: instructions to apply
    :return: in direction statement
    """
    return In_Direction_Statement(pass_dir, instructions)


@action
def needle(_, needle_node: str) -> Needle_Expression:
    """
    :param _:
    :param needle_node: node representing needle
    :return: Needle expression
    """
    return Needle_Expression(needle_node)


@action
def sheet(_, sheet_node: str) -> Sheet_Expression:
    """
    :param _:
    :param sheet_node: string representing sheet
    :return: sheet expression
    """
    return Sheet_Expression(sheet_node)


@action
def carrier(_, carrier_node: str) -> Carrier_Expression:
    """
    :param _:
    :param carrier_node: string describing carrier
    :return: carrier expression
    """
    return Carrier_Expression(carrier_node)


@action
def return_statement(_, __, exp: Expression) -> Return_Statement:
    """
    :param _:
    :param __:
    :param exp: expression to return
    :return: return statement
    """
    return Return_Statement(exp)

@action
def param_list(_, __, args: Optional[List[Variable_Expression]] = None,
               kwargs:Optional[List[Assignment]] = None) -> Tuple[List[Variable_Expression], List[Assignment]]:
    """
    :param _:
    :param __:
    :param args: list of argument identifiers
    :param kwargs: list of keyword assignments
    :return: arguments and keyword assignments
    """
    if args is None:
        args = []
    if kwargs is None:
        kwargs = []
    return args, kwargs


@action
def function_declaration(_, __, func_name: Variable_Expression,
                         params: Optional[Tuple[List[Variable_Expression], List[Assignment]]],
                         block: Statement) -> Function_Declaration:
    """
    :param _:
    :param __:
    :param func_name: name of function
    :param params: list of variables for arguments, list of key word assignments
    :param block: body to execute
    :return: the function declaration
    """
    if params is None:
        params = [], []
    args = params[0]
    kwargs = params[1]
    return Function_Declaration(func_name.variable_name, args, kwargs, block)


@action
def expression(_, nodes: list) -> Expression:
    """
    :param _: ignored parglare context
    :param nodes: nodes to parse into expression
    :return: expression
    """
    if len(nodes) == 1:
        return nodes[0]
    if nodes[0] == "(":
        return nodes[1]
    else:
        return Operator_Expression(nodes[0], nodes[1], nodes[2])


@action
def negation(_, __, exp: Expression) -> Not_Expression:
    """
    :param _:
    :param __:
    :param exp: expression to negate
    :return: not expression
    """
    return Not_Expression(exp)


@action
def xfer_rack(_, __, is_across: Optional[str], dist_exp: Optional[Expression], side_id: Optional[Expression]) -> Xfer_Pass_Racking:
    """
    :param _:
    :param __:
    :param is_across: true if xfer is directly across beds
    :param dist_exp: the needle offset for xfer
    :param side_id: offset direction
    :return: xfer pass racking
    """
    return Xfer_Pass_Racking(is_across is not None, dist_exp, side_id)


@action
def xfer_pass(_, __, needles: List[Expression],
              rack_val: Xfer_Pass_Racking,
              bed: Optional[Expression] = None,
              slider: Optional[str] =None) -> Xfer_Pass_Statement:
    """

    :param _:
    :param __:
    :param rack_val: racking for xfers
    :param needles: needles to start xfer from
    :param bed: beds to land on. Exclude needles already on bed
    :param slider: True if transferring to sliders
    :return: xfer pass statement
    """
    return Xfer_Pass_Statement(rack_val, needles, bed, slider is not None)


@action
def accessor(_, __, exp: Expression, attribute: Expression) -> Attribute_Accessor_Expression:
    """
    :param _:
    :param __:
    :param exp: expression to get from
    :param attribute: attribute to collect
    :return: accessor
    """
    return Attribute_Accessor_Expression(exp, attribute)


@action
def method_call(_, __, exp: Expression, method: Function_Call) -> Method_Call:
    """
    :param _:
    :param __:
    :param exp: expression to call from
    :param method: method to call
    :return: method call
    """
    return Method_Call(exp, method)


@action
def exp_statement(_, __, exp: Expression) -> Expression_Statement:
    """
    :param _:
    :param __:
    :param exp: expression to execute
    :return: execution of expression
    """
    return Expression_Statement(exp)


@action
def cut_statement(_, __, exps: List[Expression]) -> Cut_Statement:
    """
    :param _:
    :param __:
    :param exps: carriers to cut
    :return: cut statement
    """
    return Cut_Statement(exps)


@action
def remove_statement(_, __, exps: List[Expression]) -> Remove_Statement:
    """
    :param _:
    :param __:
    :param exps: carriers to out
    :return: remove statement
    """
    return Remove_Statement(exps)


@action
def indexing(_, __, exp: Expression, index: Expression) -> Indexing_Expression:
    """
    :param _:
    :param __:
    :param exp: expression to index
    :param index: index value
    :return: indexing expression
    """
    return Indexing_Expression(exp, index)


@action
def gauge_exp(_, __, sheet_exp: Expression, gauge: Expression) -> Gauge_Expression:
    """

    :param _:
    :param __:
    :param sheet_exp: sheet value
    :param gauge: gauge value
    :return: Gauge expression
    """
    return Gauge_Expression(sheet_exp, gauge)


@action
def drop_pass(_, __, needles: List[Expression]) -> Drop_Pass:
    """
    :param _:
    :param __:
    :param needles: needles to drop from
    :return: drop pass
    """
    return Drop_Pass(needles)


@action
def push_to(_, __, push_val: Union[str, list]) -> Union[str, Expression]:
    """
    :param _:
    :param __:
    :param push_val: front, back, or a specific layer value
    :return: identifying string or expression layer value
    """
    if isinstance(push_val, list):
        return push_val[1]
    return push_val[0]


@action
def push_dir(_, __, amount: Expression, direction: str) -> Tuple[Expression, str]:
    """
    :param _:
    :param __:
    :param amount: value to push
    :param direction: direction to push
    :return: amount, direction
    """
    return amount, direction


@action
def push_statement(_, __, needles: List[Expression], push_val: Union[str, Expression, Tuple[Expression, str]]):
    """

    :param _:
    :param __:
    :param needles: needles to push layer value
    :param push_val: specification of push value
    :return: Push statement
    """
    return Push_Statement(needles, push_val)