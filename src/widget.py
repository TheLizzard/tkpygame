from __future__ import annotations
from event import Event
from grid import Grid
import constants

import pygame


class BaseWidget:
    def __init__(self, master=None, root=None, bg:str="", fg:str="",
                 cursor:str=""):
        self.master = master
        if root is None:
            root = master._root
        self._root = root

        if cursor is None:
            self._cursor = constants.parse_cursor("")
        elif cursor == "none":
            self._cursor = "none"
        else:
            self._cursor = constants.parse_cursor(cursor)

        self._default_cursor = constants.parse_cursor("")
        self._bg = constants.parse_colour(bg)
        self._fg = constants.parse_colour(fg)

        self._sticky = ""
        self._destroyed = False
        self._pointer_inside = False

############################### Event handling ################################
        self._event_bindings = {}
        self._my_event_bindings = {}
        self._bind("<Enter>", self._enter_cursor)
        self._bind("<Leave>", self._leave_cursor)

    def event_generate(self, event_name:str, when="tail", **kwargs) -> str:
        """
        Creates and forces handling of an event with `even_name`. It also
        passes in the args given
        """
        event = Event.from_name(event_name, widget=self, **kwargs)
        if when == "tail":
            self._root.event_queue.append(event)
            return None
        if when == "now":
            return self._handle_event(event)
        raise ValueError(f"Unknown value for `when`: \"{when}\"")

    def _enter_cursor(self, event:Event=None) -> str:
        self._pointer_inside = True
        if self._cursor == "none":
            pygame.mouse.set_visible(False)
        else:
            pygame.mouse.set_visible(True)
            pygame.mouse.set_system_cursor(self._cursor)
        return "break"

    def _leave_cursor(self, event:Event=None) -> str:
        self._pointer_inside = False
        pygame.mouse.set_visible(True)
        pygame.mouse.set_system_cursor(self._default_cursor)
        return "break"

    def _handle_event(self, event:Event) -> str:
        for name in event.names:
            if name in self._event_bindings:
                for function in self._event_bindings[name]:
                    if function(event) == "break":
                        return "break"
        for name in event.names:
            if name in self._my_event_bindings:
                for function in self._my_event_bindings[name]:
                    if function(event) == "break":
                        return "break"
        if self.master is not None:
            self.master._handle_event(event)

    def bind(self, sequence:str, function) -> None:
        if sequence in self._event_bindings:
            self._event_bindings[sequence].append(function)
        else:
            self._event_bindings.update({sequence: [function]})

    # Only for internal bindings please
    def _bind(self, sequence:str, function) -> None:
        if sequence in self._my_event_bindings:
            self._my_event_bindings[sequence].append(function)
        else:
            self._my_event_bindings.update({sequence: [function]})

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({str(id(self))[-4:]})"

########################### Usuall tkinter methods ############################
    def grid(self, row:int, column:int, sticky:str="") -> None:
        self._sticky = sticky
        self.master._add_widget(self, row=row, column=column)
        self.redraw()

    def after(self, time_in_ms:int, function, *args) -> int:
        self._root._after_handler.start_after_script(time_in_ms, function, args)

    def after_cancel(self, id:int) -> None:
        self._root._after_handler.stop_after_script(id)

    def update(self) -> None:
        return None

    def redraw(self) -> None:
        return None

    def destroy(self) -> None:
        if self._destroyed:
            raise RuntimeError("Widget already destroyed")
        self._destroyed = True

    def config(self, cursor:str=None, bg:str=None, fg:str=None) -> None:
        if cursor is not None:
            # Only pass in a set if you already called
            # `constants.parse_cursor(cursor)` on the cursor
            if isinstance(cursor, set):
                if len(cursor) == 1:
                    self._cursor = tuple(cursor)[0]
                else:
                    raise ValueError("If cursor is a set, it must have " \
                                     "a length of 1.")
            elif cursor == "none":
                self._cursor = cursor
            else:
                self._cursor = constants.parse_cursor(cursor)
            if self.winfo_pointer_inside():
                self._enter_cursor()
        if bg is not None:
            self._bg = constants.parse_colour(bg)
        if fg is not None:
            self._fg = constants.parse_colour(fg)

    def focus(self) -> None:
        self.root._get_widget_from_xy = self

    def winfo_pointer_inside(self) -> bool:
        return self._pointer_inside

    def winfo_screen_width(self) -> int:
        return self._root._screen_size[0]

    def winfo_screen_height(self) -> int:
        return self._root._screen_size[1]

    def winfo_width(self) -> int:
        return self._width

    def winfo_height(self) -> int:
        return self._height

    def winfo_req_width(self) -> int:
        return self._req_width

    def winfo_req_height(self) -> int:
        return self._req_height

    def winfo_x(self) -> int:
        return self._x

    def winfo_y(self) -> int:
        return self._y

    def winfo_is_child(self, widget) -> bool:
        """
        Returns if the widget given is a child of self.
        """
        return widget in self.winfo_all_parents()

    def winfo_all_parents(self) -> [BaseWidget, BaseWidget, ...]:
        parents = []
        master = self.master
        while master is not None:
            parents.append(master)
            master = master.master
        return parents
    winfo_parents = winfo_all_parents

    def find_common_ancestor(self, other:BaseWidget) -> BaseWidget:
        self_parents = self.winfo_all_parents()
        other_parents = other.winfo_all_parents()
        self_parents.insert(0, self)
        other_parents.insert(0, other)

        for widget in self_parents:
            if widget in other_parents:
                return widget


class Widget(BaseWidget):
    def __init__(self, master, width:int, height:int, **kwargs):
        super().__init__(master, **kwargs)
        self._req_width = width
        self._req_height = height
        self._width = 0
        self._height = 0
        self._x = 0
        self._y = 0

    def _update_height(self, new_height:int) -> None:
        self._height = new_height

    def _update_width(self, new_width:int) -> None:
        self._width = new_width

    def _update_x(self, dx:int) -> None:
        self._x += dx

    def _update_y(self, dy:int) -> None:
        self._y += dy

    def destroy(self) -> None:
        super().destroy()
        self.master._widget_destroyed(self)
        self.master.redraw()

    def config(self, width:int=None, height:int=None, **kwargs) -> None:
        super().config(**kwargs)
        if width is not None:
            self._req_width = width
            self.master._widget_changed_width(self)
        if height is not None:
            self._req_height = height
            self.master._widget_changed_height(self)
