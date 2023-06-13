from typing import Optional

from knit_script.knit_graphs.Yarn import Yarn
from knit_script.knitout_optimization.knitout_errors.carrier_operation_errors import In_Active_Carrier_Error, Releasehook_Unhooked_Carrier, Out_Inactive_Carrier_Error


class Carrier:
    """
        Carrier on a knitting machine
    """

    def __init__(self, carrier_id: int, yarn: Optional[Yarn]):
        self._carrier_id: int = carrier_id
        if yarn is None:
            self.yarn: Yarn = Yarn(str(self._carrier_id))
        else:
            self.yarn: Yarn = yarn
        self._is_active: bool = False
        self._is_hooked: bool = False
        self._loops_since_release: int = 0

    @property
    def loops_since_release(self) -> int:
        """
        :return: Loops made since release from yarn inserting hook
        """
        return self._loops_since_release

    def count_loop(self):
        self._loops_since_release += 1

    @property
    def is_active(self) -> bool:
        """
        :return: True if active
        """
        return self._is_active

    @property
    def on_gripper(self) -> bool:
        """
        :return: True if carrier is held on grippers
        """
        return not self.is_active

    @property
    def is_hooked(self) -> bool:
        """
        :return: True if connected to inserting hook
        """
        return self._is_hooked

    def bring_in(self):
        """
            Record in operation
        """
        if self.is_active:
            raise In_Active_Carrier_Error(self.carrier_id)
        self._is_active = True

    def inhook(self):
        """
            Record inhook operation
        """
        if self.is_active:
            raise In_Active_Carrier_Error(self.carrier_id)
        self._is_active = True
        assert not self.is_hooked, f"Cannot hooked {self} because it is already on the yarn inserting hook"
        self._is_hooked = True
        self._loops_since_release = 0

    def releasehook(self):
        """
            Record release hook operation
        """
        if not self.is_hooked:
            raise Releasehook_Unhooked_Carrier(self.carrier_id)
        self._is_hooked = False
        self._loops_since_release = 0

    def out(self):
        """
            Record out operation
        """
        if not self.is_active:
            raise Out_Inactive_Carrier_Error(self.carrier_id)
        assert not self.is_hooked, f"Cannot take {self} out because it is on the yarn inserting hook"
        self._is_active = False

    def outhook(self):
        """
            Record outhook operation
        """
        if not self.is_active:
            raise Out_Inactive_Carrier_Error(self.carrier_id)
        assert not self.is_hooked, f"Cannot cut {self} because it is on the yarn inserting hook"
        self._is_active = False
        self.yarn = self.yarn.cut_yarn()
        self._loops_since_release = 0

    @property
    def carrier_id(self) -> int:
        """
        :return: id of carrier, corresponds to order in machine
        """
        return self._carrier_id

    def __lt__(self, other):
        return hash(self) < hash(other)

    def __hash__(self):
        return self.carrier_id

    def __str__(self):
        return f"{self.carrier_id}:{self.yarn}"

    def __repr__(self):
        return str(self)
