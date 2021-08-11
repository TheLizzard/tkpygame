from widget import Widget, BaseWidget
from event import Event
from grid import Grid
import constants

import pygame


class Frame(Grid, BaseWidget):
    def __init__(self, master=None, root=None, bg:str="black",
                 dictate_own_size:bool=True, cursor:str=""):
        Grid.__init__(self, master=master, root=root,
                      dictate_own_size=dictate_own_size)
        BaseWidget.__init__(self, master=master, root=root, bg=bg,
                            cursor=cursor)

    def update(self) -> (int, int, int, int):
        for child in self._children:
            child.update()

    def destroy(self) -> None:
        BaseWidget.destroy(self)
        Grid.destroy(self)

    def redraw(self) -> None:
        BaseWidget.redraw(self)
        if self._bg is not None:
            # Make sure the `width` and `height` aren't `float("inf")`:
            width, height = self._root._display.get_size()
            width = min(width, self._width)
            height = min(height, self._height)
            args = (self._x, self._y, width, height)
            # The 0 is the thickness
            pygame.draw.rect(self._root._display, self._bg, args, 0)

            for child in self._children:
                child.redraw()
            return args

    def config(self, cursor:str=None, width:int=None,
               height:int=None, bg:str=None) -> None:
        Grid.config(self, width=width, height=height)
        BaseWidget.config(self, cursor=cursor, bg=bg)
        if bg is not None:
            self.redraw()


class Label(Widget):
    def __init__(self, master, text:str="", font:tuple=None,
                 padx:int=10, pady:int=10, **kwargs):
        if None in (padx, pady):
            raise ValueError("Invalid padx/pady: None")
        if font is None:
            self._font = pygame.font.SysFont("", 30)

        super().__init__(master, height=0, width=0, **kwargs)
        self.config(text=text, padx=padx, pady=pady, font=font)

    def _create_surface(self) -> (int, int):
        self._surface = self._font.render(self._text, False, self._fg)
        width, height = self._surface.get_size()
        return (width, height)

    def config(self, text:str=None, bg:str=None, fg:str=None, pady:int=None,
               font:tuple=None, cursor:str=None, padx:int=None) -> None:
        super().config(bg=bg, fg=fg, cursor=cursor)
        if text is not None:
            self._text = text
        if font is not None:
            self._font = pygame.font.SysFont(*font)
        if padx is not None:
            if isinstance(padx, int):
                self._padx = (padx, padx)
            else:
                self._padx = padx
        if pady is not None:
            if isinstance(pady, int):
                self._pady = (pady, pady)
            else:
                self._pady = pady

        if len(tuple(filter(None, (text, font, bg, fg)))) != 0:
            width, height = self._create_surface()
            width += sum(self._padx)
            height += sum(self._pady)
            super().config(width=width, height=height)

    def redraw(self) -> (int, int, int, int):
        super().redraw()

        x = self._x
        y = self._y
        width = self._width
        height = min(self._req_height, self._height)

        if "s" in self._sticky:
            if "n" in self._sticky:
                height = self._height
            else:
                y += self._height - self._req_height
        if "e" in self._sticky:
            if "w" in self._sticky:
                width = self._width
            else:
                x += self._width - self._req_width

        args = (x, y, width, height)

        if self._bg is not None:
            # Background box (same as `Frame.redraw`):
            self._coords = (args[0], args[1], args[2]+args[0], args[3]+args[1])
            pygame.draw.rect(self._root._display, self._bg, args, 0)

        if self._text != "":
            # Draw the text:
            x += self._padx[0]
            y += self._pady[0]
            width -=  self._padx[1]
            height -=  self._pady[1]
            self._root._display.blit(self._surface, (x, y), (0, 0, width,
                                                             height))

        return args


class Button(Label):
    def __init__(self, master, command=None, bd=2, bdcolour="grey", **kwargs):
        self._bd = bd
        self._command = command
        super().__init__(master, **kwargs)
        self._bdcolour = constants.parse_colour(bdcolour)

        self._pressing = False

        super()._bind("<ButtonPress-1>", self._handle_button_press)
        super()._bind("<ButtonRelease-1>", self._handle_button_release)

    def _handle_button_press(self, event) -> str:
        x1, y1, x2, y2 = self._coords
        if (x1 < event.x < x2) and (y1 < event.y < y2):
            self._pressing = True
            return "break"

    def _handle_button_release(self, event) -> str:
        x1, y1, x2, y2 = self._coords
        if (x1 < event.x < x2) and (y1 < event.y < y2) and self._pressing:
            self._pressing = False
            if self._command is not None:
                self._command()
            return "break"

    def config(self, bd:int=None, bdcolour:str=None, command=None,
               **kwargs) -> None:
        if bd is not None:
            self._bd = bd
        if bdcolour is not None:
            self._bdcolour = bdcolour
        if command is not None:
            self._command = command
        super().config(**kwargs)

    def redraw(self) -> (int, int, int, int):
        super().redraw()
        x, y, width, height = super().redraw()
        if (self._bd != 0) and (self._bdcolour != ""):
            width -= self._bd
            height -= self._bd
            args = (x, y, width, height)
            pygame.draw.rect(self._root._display, self._bdcolour,
                             (x, y, width, height), self._bd)
