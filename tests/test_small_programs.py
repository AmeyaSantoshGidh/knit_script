from unittest import TestCase

from knit_script.knit_script_interpreter.Knit_Script_Interpreter import Knit_Script_Interpreter


class Test_Small_Code(TestCase):
    parser = Knit_Script_Interpreter(debug_grammar=False, debug_parser=False, debug_parser_layout=False)

    def test_global_in_sub_Scope(self):
        program = r"""
                    def set_c():{
                        global c = 1;
                    }
                    try: {print c;}
                    catch KeyError as e:{
                        print e;
                    }
                    set_c();
                    print f"c={c}";
                """
        knitout, knit_graph = self.parser.write_knitout(program, f"global_test.k", pattern_is_file=False)

    def test_sheet_accessor(self):
        program = """
        with Gauge as 4:{
            for s in range(0, Gauge):{
                with Sheet as s:{
                    print Sheet.f0;
                }
            }
        }
        """
        knitout, knit_graph = self.parser.write_knitout(program, f"global_test.k", pattern_is_file=False)

    def test_machine_needle(self):
        program = """
        with Gauge as 2, Sheet as 0:{
            print machine.f1;
            print machine.sheet_of(machine.f1);
            print machine.layer_of(machine.f1);
            print Sheet.f1;
            print machine.sheet_of(Sheet.f1);
            print machine.layer_of(Sheet.f1);
        }"""

        knitout, knit_graph = self.parser.write_knitout(program, f"global_test.k", pattern_is_file=False)