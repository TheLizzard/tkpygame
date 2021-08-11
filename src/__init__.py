from widgets import Frame, Label, Button
from canvas import Canvas, CanvasObject
from widget import Widget, BaseWidget
from event import Event
from grid import Grid
import pygame_winapi
import constants

from threading import Lock
from sys import stderr
import traceback
import pygame


ROOT_HANDLED_EVENTS = ("<Configure>", "<Enter>", "<Leave>",
                       "<FocusIn>", "<FocusOut>")


class AfterHandler:
    def __init__(self, root):
        self.root = root
        self.lock = Lock()
        self.next_free = pygame.USEREVENT + 1
        self.free_list = []
        self.functions_dict = {} # {event_id: (function, args)}
        self.root.bind("<UserEvent>", self.callit)

    def get_next_free(self) -> int:
        with self.lock:
            if len(self.free_list) > 0:
                return self.free_list.pop(0)
            id = self.next_free
            self.next_free += 1
            if self.next_free == pygame.NUMEVENTS:
                raise RuntimeError("You generated too many `.after` scripts.")
            return id

    def free_id(self, id:int) -> None:
        with self.lock:
            if id + 1 == self.next_free:
                self.next_free -= 1
            else:
                self.free_list.append(id)

    def start_after_script(self, time_in_ms:int, function, args:tuple) -> int:
        id = self.get_next_free()
        with self.lock:
            pygame.time.set_timer(id, time_in_ms, True)
            self.functions_dict.update({id: (function, args)})
        return id

    def stop_after_script(self, id:int) -> None:
        if id in self.functions_dict:
            self.free_id(id)

    def callit(self, event:Event) -> str:
        id = event.type
        if id in self.functions_dict:
            self.free_id(id)
            function, args = self.functions_dict.pop(id)
            try:
                function(*args)
            except Exception as error:
                stderr.write("An exception occured in a `.after` script\n")
                traceback.print_exc()
        return "break"


class Tk(Frame):
    def __init__(self, fps=50):
        self.mode = 0
        self._overrideredirect = False
        self._fullscreen = False
        self.event_queue = []

        numpass, numfail = pygame.init()
        if numfail != 0:
            stderr.write("Warning `pygame.init()` returned errors but we are " \
                         "ignoring them.\n")

        self.clock = pygame.time.Clock()
        super().__init__(root=self, dictate_own_size=False)
        self._mouse_over_widget = []
        self._widget_sent_pressed = None
        self._focused_widget = None
        self._running = True
        self.fps = fps
        super()._bind("<WM_DELETE_WINDOW>", lambda event: self.destroy())
        self._width = 400
        self._height = 400
        self._create_new_display()
        self._screen_size = pygame_winapi.get_screen_size()

        self._after_handler = AfterHandler(self)

    def overrideredirect(self, value:bool) -> None:
        if not value:
            raise NotImplementedError("Only .overrideredirect(True) allowed.")
        self.mode ^= pygame.NOFRAME
        self._create_new_display()
        self._root_x, self._root_y = self._get_window_position()
        self._overrideredirect = value
        self.redraw()

    def _get_window_position(self) -> (int, int):
        if self._overrideredirect:
            return self._root_x, self._root_y
        return pygame_winapi.get_window_position(self._hwnd)

    def _create_new_display(self) -> None:
        self._display = pygame.display.set_mode((self._width, self._height),
                                                self.mode)
        self._hwnd = pygame.display.get_wm_info()["window"]
        self._update()

    def fullscreen_toggle(self) -> None:
        if self._fullscreen:
            self.not_fullscreen()
        else:
            self.fullscreen()

    def fullscreen(self) -> None:
        if self._fullscreen:
            return None
        self._fullscreen = True

        self._root_x_fullscreen_backup, self._root_y_fullscreen_backup = \
                                        self._get_window_position()
        self._width_fullscreen_backup = self._width
        self._height_fullscreen_backup = self._height

        width, height = self._screen_size
        self.geometry(f"{width}x{height}+0+0")

    def not_fullscreen(self) -> None:
        if not self._fullscreen:
            return None
        self._fullscreen = False

        x = self._root_x_fullscreen_backup
        y = self._root_y_fullscreen_backup
        width = self._width_fullscreen_backup
        height = self._height_fullscreen_backup

        self.geometry(f"{width}x{height}+{x}+{y}")

    def winfo_rootx(self) -> int:
        return self._get_window_position()[0]

    def winfo_rooty(self) -> int:
        return self._get_window_position()[1]

    def destroy(self) -> None:
        super().destroy()
        pygame.display.quit()
        self._running = False

    def geometry(self, geometry:str="", send_events:bool=True) -> None:
        if geometry == "":
            w, h = self._width, self._height
            x, y = self._get_window_position()
            return f"{w}x{h}+{x}+{y}"

        x = y = None
        width = height = None
        if "+" in geometry:
            geometry, x, y = geometry.split("+")
            x, y = int(x), int(y)
        if "x" in geometry:
            width, height = geometry.split("x")
            width, height = int(width), int(height)

        if width is not None:
            self._width = width
            self._height = height
            self._create_new_display()
            self._update()
            if self._overrideredirect and send_events:
                super().event_generate("<GeometryResize>", width=width,
                                       height=height)
        if x is not None:
            pygame_winapi.set_window_position(self._hwnd, x, y)
            self._root_x, self._root_y = x, y
            if self._overrideredirect and send_events:
                super().event_generate("<GeometryMove>", new_x=x, new_y=y)

    def mainloop(self) -> None:
        if not self._running:
            raise RuntimeError("Window already closed.")
        while self._running:
            if self.fps != 0:
                self.clock.tick(self.fps)
            other_events = tuple(self.event_queue)
            self.event_queue.clear()
            for event in tuple(pygame.event.get()) + other_events:
                if not self._running:
                    break
                if isinstance(event, Event):
                    event.widget._handle_event(event)
                    continue
                if event.type == pygame.QUIT:
                    super().event_generate("<WM_DELETE_WINDOW>")
                else:
                    tk_event = Event(event, widget=self._focused_widget)
                    try:
                        self._master_event_handler(tk_event)
                    except Exception as error:
                        pygame.quit()
                        raise error
            if not self._running:
                break
            super().update()
            pygame.display.update()
        if not self._destroyed:
            self.destroy()
        pygame.quit()

    def _master_event_handler(self, event:Event) -> None:
        for name in event.names:
            if ("Button" in name) or (name == "<Motion>"):
                event.widget = self._get_widget_from_xy(event.x, event.y)
                self._handle_mouse_enter_leave_widget(event)
                break
            if name in ROOT_HANDLED_EVENTS:
                if name == "<Leave>":
                    for widget in self._mouse_over_widget:
                        widget.event_generate("<Leave>")
                    self._mouse_over_widget = []
                    return None
                if name == "<Enter>":
                    return None
                event.widget = self
        else:
            if self._focused_widget is None:
                event.widget = self
            else:
                event.widget = self._focused_widget
        event.widget._handle_event(event)

    def _handle_mouse_enter_leave_widget(self, event:Event) -> None:
        """
        Mouse moved over new widget. (last => new). This method
        handles the generation of 
        """
        new = event.widget
        news_parents = new.winfo_parents()
        news_parents.insert(0, new)
        old = self._mouse_over_widget

        idx = 0
        for widget in old:
            if widget in news_parents:
                idx = tuple(reversed(news_parents)).index(widget)+1
                break
            else:
                widget.event_generate("<Leave>")

        # Sames as:   reversed(news_parents))[idx:]):
        for widget in reversed(news_parents[:len(news_parents)-idx]):
            widget.event_generate("<Enter>")

        self._mouse_over_widget = news_parents


class MovableTk(Tk):
    def __init__(self, fps=50):
        super().__init__(fps)
        super().overrideredirect(True)

        # Moving the window
        super().bind("<ButtonPress-1>", self.start_move)
        super().bind("<ButtonRelease-1>", self.stop_move)
        super().bind("<Motion>", self.do_move)
        self.last_x = self.last_y = None

        # Resizing the window
        super()._bind("<Button-4>", self.resize_plus)
        super()._bind("<Button-5>", self.resize_minus)

        # Exit the window
        super()._bind("<KeyPress-w>", self.check_exit)
        # Toggle fullscreen
        super()._bind("<KeyPress-f>", self.fullscreen_toggle)

        self.moved = False

    def check_exit(self, event:Event) -> None:
        state = event.state
        if ("Control" in state) and ("Shift" not in state):
            self.destroy()

    def fullscreen_toggle(self, event:Event=None) -> None:
        if event is None:
            return super().fullscreen_toggle()
        state = event.state
        if ("Control" not in state) and ("Shift" not in state):
            return super().fullscreen_toggle()

    def resize_plus(self, event:Event) -> str:
        if self._fullscreen:
            return None
        width, height = super().winfo_width(), super().winfo_height()
        new_width = width + 10
        if new_width >= super().winfo_screen_width():
            new_width = super().winfo_screen_width()
            new_height = super().winfo_screen_height()
        else:
            new_height = int(height/width*new_width + 0.5)
        super().geometry(f"{new_width}x{new_height}")
        super().event_generate("<Configure>")

    def resize_minus(self, event:Event) -> str:
        if self._fullscreen:
            return None
        width, height = super().winfo_width(), super().winfo_height()
        new_width = width - 10
        if new_width < 300:
            new_width = 300
        new_height = int(height/width*new_width + 0.5)
        super().geometry(f"{new_width}x{new_height}")
        super().event_generate("<Configure>")

    def start_move(self, event:Event) -> str:
        if self._fullscreen:
            return None
        self.moved = False
        self.last_x = event.x
        self.last_y = event.y
        return "break"

    def stop_move(self, event) -> str:
        self.last_x = self.last_y = None
        if self.moved:
            return "break"

    def do_move(self, event:Event) -> str:
        if self.last_x is not None:
            self.moved = True
            x = super().winfo_rootx() + event.x - self.last_x
            y = super().winfo_rooty() + event.y - self.last_y
            super().geometry(f"+{x}+{y}")
            return "break"


def test_creating_update_destroy() -> None:
    root = Tk()
    root.update()
    root.destroy()

def test_creating_widget_events() -> None:
    root = Tk()
    root.config(bg="black")
    root.geometry("500x400+100+100")

    frame1 = Frame(root, bg="red")
    frame2 = Frame(root, bg="blue")

    frame1.grid_propagate(False)
    # frame2.grid_propagate(False)

    frame1.grid(row=1, column=1)
    frame2.grid(row=2, column=1)

    frame1.config(height=100, width=150)
    frame2.config(height=100, width=100)

    frame1.config(cursor="none")

    button1 = Button(root, text="Close", fg="white", bg="green",
                     command=frame1.destroy)
    button1.grid(row=1, column=2, sticky="s")

    label1 = Label(frame1, text="Hello world", fg="white", bg="")
    label1.grid(row=1, column=2, sticky="news")

    # root.overrideredirect()

    canvas = Canvas(root, bg="yellow", width=200, height=200)
    canvas.grid(row=2, column=3)

    obj = canvas.create_rectangle(50, 50, 100, 100, fill="black")

    pygame.display.update()
    root.event_generate("<WM_DELETE_WINDOW>")
    # root.mainloop()

def test() -> None:
    tests = (test_creating_update_destroy, test_creating_widget_events)
    for _test in tests:
        _test()


if __name__ == "__main__":
    # test()

    def _resized(event:Event) -> None:
        canvas.itemconfig(rectangle, 4, 4, canvas.winfo_width()-4,
                          canvas.winfo_height()-4,
                          redraw=False)
        canvas.config(cursor="hand")

    root = MovableTk()
    root.config(bg="black")
    root.geometry("600x400")
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    label = Label(root, bg="red", fg="blue")
    label.grid(row=1, column=1)
    label.config(text="Hello world")

    root.after(2000, root.after, 2000, print, "hi")

    canvas = Canvas(root, bg="grey", height=100, width=100, cursor="none")
    canvas.grid(row=0, column=0)

    rectangle = canvas.create_rectangle(4, 4, 465, 356, fill="green")

    root.bind("<GeometryResize>", _resized)

    root.mainloop()
