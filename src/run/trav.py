from char import IChar
from config import Config
from logger import Logger
from pather import Location, Pather
from item.pickit import PickIt
import template_finder
from town.town_manager import TownManager
from utils.misc import wait
from screen import convert_screen_to_abs
import keyboard

from ui import waypoint

class Trav:

    name = "run_trav"

    def __init__(
        self,
        pather: Pather,
        town_manager: TownManager,
        char: IChar,
        pickit: PickIt,
        runs: list[str]
    ):
        self._pather = pather
        self._town_manager = town_manager
        self._char = char
        self._pickit = pickit
        self._runs = runs

    def approach(self, start_loc: Location) -> bool | Location:
        # Go to Travincal via waypoint
        Logger.info("Run Trav")
        if not self._town_manager.open_wp(start_loc):
            return False
        if waypoint.use_wp("Travincal", curr_active_act = self._town_manager.get_act_idx_from_location(start_loc)):
            return Location.A3_TRAV_START
        return False

    def battle(self, do_pre_buff: bool) -> bool | tuple[Location, bool]:
        # Kill Council
        if not template_finder.search_and_wait(["TRAV_0", "TRAV_1", "TRAV_20"], threshold=0.65, timeout=20).valid:
            return False
        if do_pre_buff:
            self._char.pre_buff()
        if self._char.capabilities.can_teleport_natively:
            self._pather.traverse_nodes_fixed("trav_safe_dist", self._char)
        elif self._char.capabilities.can_teleport_with_charges:
            self._pather.traverse_nodes([220], self._char, force_move=True)
            if not self._pather.traverse_nodes_automap([1221, 1222, 1223, 1224], self._char, force_move=True):
                return False
            self._pather.traverse_nodes_automap([1226], self._char, timeout=2.5, force_tp=True)
        else:
            self._pather.traverse_nodes([220], self._char, force_move=True)
            if not self._pather.traverse_nodes_automap([1221, 1222, 1223, 1224, 1225, 1226], self._char, force_move=True):
                return False
        self._char.kill_council()
        picked_up_items = self._pickit.pick_up_items(self._char, order = 'bottom-to-top')
        # If we can teleport we want to move back inside and also check loot there
        keyboard.send("tab")
        wait(0.2, 0.3)
        match = template_finder.search_and_wait(["TRAV_AUTOMAP"], threshold=0.75, timeout=1)
        if match.valid:
            ref_pos_abs = convert_screen_to_abs(match.center)
            # Check if we are inside the temple
            if ref_pos_abs[1] * 2 - ref_pos_abs[0] < 370:
                if self._char.capabilities.can_teleport_with_charges:
                    if not self._pather.traverse_nodes_automap([1228], self._char, timeout=2, toggle_map=False):
                        self._pather.traverse_nodes([1229], self._char, timeout=2.5, use_tp_charge=True)
                elif not self._char.capabilities.can_teleport_natively:
                    self._pather.traverse_nodes_automap([1226, 1228], self._char, timeout=2.5, toggle_map=False)
                else:
                    self._pather.traverse_nodes([1229], self._char, timeout=2.5, use_tp_charge=True)
                picked_up_items |= self._pickit.pick_up_items(self._char)
        # If travincal run is not the last run
        if self.name != self._runs[-1]:
            # Make sure we go back to the center to not hide the tp
            self._pather.traverse_nodes_automap([1230], self._char, timeout=2.5, toggle_map=False)
        keyboard.send(Config().char["clear_screen"])
        return (Location.A3_TRAV_CENTER_STAIRS, picked_up_items)
