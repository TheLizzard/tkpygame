import pygame

# Win API stuff:
from ctypes import POINTER, WINFUNCTYPE, windll, byref, WinError, c_int, c_uint
from ctypes.wintypes import BOOL, HWND, RECT

def _errcheck_bool(value, func, args):
    if value == 0:
        raise WinError()
    return args

SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOZORDER = 0x0004
HWND_TOPMOST = HWND(-1)
HWND_NOTOPMOST = HWND(-2)

GetWindowRect = windll.user32.GetWindowRect
GetWindowRect.argtypes = (HWND, POINTER(RECT))
GetWindowRect.restype = BOOL
GetWindowRect.errcheck = _errcheck_bool

MoveWindow = windll.user32.MoveWindow
MoveWindow.argtypes = (HWND, c_int, c_int, c_int, c_int, BOOL)
MoveWindow.restype = BOOL
MoveWindow.errcheck = _errcheck_bool

GetSystemMetrics = windll.user32.GetSystemMetrics
GetSystemMetrics.argtypes = (c_int, )
GetSystemMetrics.restype = c_int
GetSystemMetrics.errcheck = _errcheck_bool

SetWindowPos = windll.user32.SetWindowPos
SetWindowPos.argtypes = (HWND, HWND, c_int, c_int, c_int, c_int, c_uint)
SetWindowPos.restype = BOOL
SetWindowPos.errcheck = _errcheck_bool

def get_screen_size() -> (int, int):
    return (GetSystemMetrics(0), GetSystemMetrics(1))

def get_window_position(hwnd:int) -> (int, int):
    rect = RECT()
    GetWindowRect(hwnd, byref(rect))
    return (rect.left, rect.top)

def set_window_position(hwnd:int, x:int, y:int) -> None:
    SetWindowPos(hwnd, 0, x, y, 0, 0, SWP_NOSIZE|SWP_NOZORDER)

def set_topmost(hwnd:int, value:bool=True) -> None:
    if value:
        zorder = HWND_TOPMOST
    else:
        zorder = HWND_NOTOPMOST
    SetWindowPos(hwnd, zorder, 0, 0, 0, 0, SWP_NOSIZE|SWP_NOMOVE)


def test_window_position():
    pygame.display.set_mode((100, 100), pygame.NOFRAME)
    hwnd = pygame.display.get_wm_info()["window"]
    position = (100, 0)
    set_window_position(hwnd, *position)
    assert get_window_position(hwnd) == position, "Can't get/set the " \
                                                  "window's position."

def test_get_screen_size() -> (int, int):
    stderr.write(f"Is this: {get_screen_size()} your screen's size?\ny/n > ")
    if input().lower() in ("n", "no", "nope", "0", "o"):
        raise AssertionError("Can't get the correct screen size")

def test_set_topmost() -> (int, int):
    pygame.display.set_mode((100, 100), pygame.NOFRAME)
    hwnd = pygame.display.get_wm_info()["window"]
    set_topmost(hwnd, True)
    pygame.display.update()
    stderr.write(f"Is the window topmost?\ny/n > ")
    if input().lower() in ("n", "no", "nope", "0", "o"):
        raise AssertionError("Can't get the correct screen size")
    set_topmost(hwnd, False)
    pygame.display.update()
    stderr.write(f"Is the window not topmost?\ny/n > ")
    if input().lower() in ("n", "no", "nope", "0", "o"):
        raise AssertionError("Can't get the correct screen size")

def test():
    tests = (test_window_position, test_get_screen_size, test_set_topmost)
    for _test in tests:
        pygame.init()
        _test()
        pygame.quit()


if __name__ == "__main__":
    from sys import stderr # Needed for some tests
    test()
