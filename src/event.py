from __future__ import annotations
import constants

import pygame


class PyGameEventSubstitute:
    def __init__(self):
        # Dummy event type
        self.type = pygame.MOUSEMOTION


class Event:
    def __init__(self, event, widget):
        self.num = 0
        self.x, self.y = pygame.mouse.get_pos()
        self.char = None
        self.widget = widget

        if event.type == pygame.MOUSEMOTION:
            self.names = ("<Motion>", )
        elif event.type == pygame.KEYDOWN:
            self.key_pressed(event)
        elif event.type == pygame.KEYUP:
            self.key_released(event)
        elif event.type == pygame.MOUSEBUTTONUP:
            self.num = event.button
            self.names = (f"<ButtonRelease-{self.num}>", )
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.num = event.button
            self.names = (f"<Button-{self.num}>",
                                f"<ButtonPress-{self.num}>")
        # These events are usually widget specific but we can't know which
        # widget caused them:
        elif event.type in (pygame.VIDEORESIZE, pygame.WINDOWMOVED):
            self.names = ("<Configure>", )
        elif event.type == pygame.WINDOWLEAVE:
            self.names = ("<Leave>", )
        elif event.type == pygame.WINDOWENTER:
            self.names = ("<Enter>", )
        elif event.type == pygame.WINDOWFOCUSGAINED:
            self.names = ("<FocusIn>", )
        elif event.type == pygame.WINDOWFOCUSLOST:
            self.names = ("<FocusOut>", )

        else:
            event_name = pygame.event.event_name(event.type)
            if event_name == "UserEvent":
                self.type = event.type
                # For .after scripts:
                self.names = ("<UserEvent>", )
            else:
                # Unknown event
                self.names = (f"<Unknown-{event_name}>", )

    def get_char_from_event(self, event:pygame.event.Event) -> (str, str):
        self.mods = event.mod
        if event.key == pygame.K_DELETE:
            return "Delete", "<Delete>"
        if event.key == pygame.K_KP0:
            return "0", None
        if event.key == pygame.K_KP1:
            return "1", None
        if event.key == pygame.K_KP2:
            return "2", None
        if event.key == pygame.K_KP3:
            return "3", None
        if event.key == pygame.K_KP4:
            return "4", None
        if event.key == pygame.K_KP5:
            return "5", None
        if event.key == pygame.K_KP6:
            return "6", None
        if event.key == pygame.K_KP7:
            return "7", None
        if event.key == pygame.K_KP8:
            return "8", None
        if event.key == pygame.K_KP9:
            return "9", None
        if event.key == pygame.K_UP:
            return "Up", ("<Up>", )
        if event.key == pygame.K_DOWN:
            return "Down", ("<Down>", )
        if event.key == pygame.K_LEFT:
            return "Left", ("<Left>", )
        if event.key == pygame.K_RIGHT:
            return "Right", ("<Right>", )

        char = event.unicode
        if char == "\x1b":
            return char, ("<Escape>", )
        if char == "\b":
            return char, ("<Backspace>", )
        if char == "\t":
            return char, ("<Tab>", )
        if char == "\r":
            return char, ("<Enter>", )
        if char == " ":
            return char, ("<space>", )
        if (len(char) > 0) and (1 <= ord(char) <= 26):
            return chr(ord(char) + 96), None
        return char, None

    @property
    def state(self) -> (str, str, ...):
        state = set()
        for mod, value in constants.EVENT_MODS.items():
            if (self.mods & mod) != 0:
                state.update(value)
        return tuple(state)

    def key_pressed(self, event:pygame.event.Event) -> None:
        self.char, type = self.get_char_from_event(event)
        if type is not None:
            self.names = type + ("<KeyPress>", )
        elif len(self.char) == 0:
            self.names = ("<KeyPress>", )
        else:
            self.names = (f"<KeyPress-{self.char.lower()}>", "<KeyPress>")

    def key_released(self, event:pygame.event.Event) -> None:
        self.char, type = self.get_char_from_event(event)
        if type is not None:
            self.names = type + ("<KeyRelease>", )
        elif len(self.char) == 0:
            self.names = ("<KeyRelease>", )
        else:
            self.names = (f"<KeyRelease-{self.char}>", "<KeyRelease>")

    @classmethod
    def from_name(cls, names:(str or tuple), widget, **kwargs) -> Event:
        if isinstance(names, str):
            names = (names, )
        event = Event(PyGameEventSubstitute(), widget)
        event.names = names
        if len(kwargs) != 0:
            event.__dict__.update(kwargs)
        return event

    def __str__(self) -> str:
        output = ""
        for key, value in self.__dict__.items():
            if key == "names":
                if len(value) == 1:
                    output += f"name={value[0]}, "
                    continue
            if value is not None:
                output += f"{key}={value}, "
        return f"Event({output.rstrip()[:-1]})"
    __repr__ = __str__
