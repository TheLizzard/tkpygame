from __future__ import annotations
from widget import Widget
import constants

import pygame


class CanvasObject:
    def __init__(self, canvas:Canvas, type:str, *args, **kwargs):
        self.last_kwargs = kwargs
        self.last_args = args
        self.canvas = canvas
        self.deleted = False
        self.type = type
        self.config(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({str(id(self))[-4:]})"

    def parse_args_rectangle(self, *args:tuple, **kwargs:dict) -> None:
        if len(args) != 4:
            raise ValueError(f"Invalid coords: {repr(args)}")

        # Get rid of all of the negatives:
        args = (max(0, args[0]), max(0, args[1]), args[2], args[3])
        # Check if `x2` and `y2` are > than `x1` and `y1`:
        if args[2] < args[0]:
            raise ValueError("The `x2` provided is smaller than `x1`")
        if args[3] < args[1]:
            raise ValueError("The `y2` provided is smaller than `y1`")

        self.position = args
        self.fill = constants.parse_colour(kwargs.pop("fill", ""))
        self.outline = constants.parse_colour(kwargs.pop("outline", ""))
        self.border = kwargs.pop("border", 0)
        if not isinstance(self.border, int):
            raise ValueError(f"Invalid border width: {repr(self.border)}")
        self.border = min(0, self.border)
        if self.border > 0:
            if self.outline is None:
                raise ValueError("Invalid colour: None")
        if len(kwargs) != 0:
            raise ValueError(f"Unhandled kwargs: {kwargs}")

    def parse_args_image(self, *args:tuple, **kwargs:dict) -> None:
        self.image = kwargs.pop("image", None)
        if self.image is not None:
            if not isinstance(self.image, pygame.Surface):
                self.image = pygame.surfarray.make_surface(self.image)

        if len(args) == 0:
            self.position = (0, 0)
        elif len(args) == 2:
            self.position = args
        else:
            raise ValueError(f"Invalid position {repr(args)}")
        if self.position[0] < 0:
            raise ValueError("The `x` position is < 0. That isn't allowed.")
        if self.position[1] < 0:
            raise ValueError("The `y` position is < 0. That isn't allowed.")
        if len(kwargs) != 0:
            raise ValueError(f"Unhandled kwargs: {kwargs}")

    def redraw(self) -> (int, int, int, int):
        if self.deleted:
            return (0, 0, 0, 0)
        if self.type == "image":
            return self.redraw_image()
        elif self.type == "rectangle":
            return self.redraw_rectangle()

    def redraw_rectangle(self) -> (int, int, int, int):
        x1, y1, x2, y2 = self.position
        max_width = self.canvas.winfo_width() - x1
        max_height = self.canvas.winfo_height() - y1
        positions = (x1 + self.canvas.winfo_x(),
                     y1 + self.canvas.winfo_y(),
                     min(max_width, x2 - x1),
                     min(max_height, y2 - y1))
        if self.fill is not None:
            pygame.draw.rect(self.canvas._root._display, self.fill, positions,
                             0)
        if self.border != 0:
            pygame.draw.rect(self.canvas._root._display, self.outline,
                             positions, self.border)
        return positions

    def redraw_image(self) -> (int, int, int, int):
        if self.image is None:
            return (0, 0, 0, 0)

        x, y = self.position
        width, height = self.image.get_size()
        width = min(width, self.canvas.winfo_width() - x)
        height = min(height, self.canvas.winfo_height() - y)

        positions = (x + self.canvas.winfo_x(),
                     y + self.canvas.winfo_y(),
                     width, height)
        if self.image is not None:
            self.canvas._root._display.blit(self.image, positions)
        return self.position

    def config(self, *args, redraw_canvas:bool=True, **kwargs) -> None:
        if self.deleted:
            raise RuntimeError("Can't `.config` dead objects.")
        if len(args) == 0:
            args = self.last_args
        self.last_kwargs.update(kwargs)
        if self.type == "image":
            self.parse_args_image(*args, **self.last_kwargs)
        elif self.type == "rectangle":
            self.parse_args_rectangle(*args, **self.last_kwargs)
        else:
            raise ValueError(f"Invalid shape: {repr(type)}")
        if redraw_canvas:
            self.canvas.redraw()
        else:
            self.redraw()


class Canvas(Widget):
    def __init__(self, master, width:int=400, height:int=400, **kwargs):
        super().__init__(master, width=width, height=height, **kwargs)
        self.objects = []

    def redraw(self) -> (int, int, int, int):
        last_changed = None

        if self._bg is not None:
            args = (self._x, self._y, self._width, self._height)
            pygame.draw.rect(self._root._display, self._bg, args, 0)
            last_changed = args

        for object in self.objects:
            last_changed = object.redraw()
        return last_changed

    def create_image(self, *args, custom:bool=False, **kwargs) -> CanvasObject:
        object = CanvasObject(self, "image", *args, **kwargs)
        if not custom:
            self.objects.append(object)
        object.redraw()
        return object

    def create_rectangle(self, *args, custom:bool=False, **kwargs) -> CanvasObject:
        object = CanvasObject(self, "rectangle", *args, **kwargs)
        if not custom:
            self.objects.append(object)
        object.redraw()
        return object

    def add_custom(self, object:CanvasObject) -> None:
        self.objects.append(object)
        object.redraw()

    def delete(self, object:CanvasObject, redraw:bool=True) -> None:
        if object == "all":
            for object in self.objects:
                object.deleted = True
            self.objects.clear()
        else:
            self.objects.remove(object)
            object.deleted = True
        if redraw:
            self.redraw()

    def itemconfig(self, object, *args, redraw:bool=True, **kwargs) -> None:
        object.config(*args, **kwargs)
        if redraw:
            self.redraw()
        else:
            object.redraw()
