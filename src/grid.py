import pygame


DEBUG = False


# Only used when debugging:
def pretty_print_table(table:[(str, str, ...), (str, str, ...), ...]) -> str:
    column_width = -1
    for row in table:
        for item in row:
            column_width = max(column_width, len(item))
    column_width += 2
    output = ""
    for row in table:
        for item in row:
            item_width = len(item)
            output += item + " "*(column_width - item_width)
        output = output[:-2] + "\n"
    return output.rstrip("\n")


class Grid:
    """
    Functions defined:
        # Standard:
        _update_width(new_width:int) -> None
        _update_height(new_height:int) -> None
        redraw() -> None
        update() -> None
        destroy() -> None
        config(width:int=None, height:int=None) -> None
        _update_x(dx:int) -> None
        _update_y(dy:int) -> None
        _wants_self_expand() -> None


        # Use can call these:
        columnconfigure(columns:(int or tuple), weight:int) -> None
        rowconfigure(rows:(int or tuple), weight:int) -> None
        grid_propagate(value:bool) -> None


        # Helper (tested)
        _get_widget_from_xy(x:int, y:int) -> BaseWidget
        _widget_destroyed(self, widget:BaseWidget) -> None
        _add_widget(widget:BaseWidget, row:int, column:int) -> None

        _get_rows(row1:int, row2:int) # row2 can be None
        _get_columns(column1:int, column2:int) # column2 can be None

        _get_row(row:int) -> [BaseWidget, BaseWidget, ...]
        _get_column(column:int) -> [BaseWidget, BaseWidget, ...]

        _debug_table(what:str) -> str


        # Other
        _widget_changed_width(widget:BaseWidget) -> None
        _widget_changed_height(widget:BaseWidget) -> None

        _update(height:bool=True, width:bool=True) -> None

        _update_h(redraw:bool=True) -> None
        _update_v(redraw:bool=True) -> None
    """
    def __init__(self, master=None, root=None, dictate_own_size=True):
        self._dictate_own_size = dictate_own_size
        self.master = master
        self._widgets = [[]]
        self._children = []
        self._req_width = 0
        self._req_height = 0
        self._x = 0
        self._y = 0
        if master is None:
            self._width = float("inf")
            self._height = float("inf")
            if root is not None:
                self._root = root
        else:
            self._root = master._root
            self._width = 0
            self._height = 0
        self._expandable_rows = []
        self._expandable_columns = []
        self._grid_propagate = True

    # Standard:
    def _update_width(self, new_width:int) -> None:
        self._width = new_width
        self._update(height=False)
        self.redraw()

    def _update_height(self, new_height:int) -> None:
        self._height = new_height
        self._update(width=False)
        self.redraw()

    def redraw(self) -> None:
        for widget in self._children:
            widget.redraw()

    def update(self) -> None:
        for child in self._children:
            child.update()

    def destroy(self) -> None:
        for child in self._children:
            child.destroy()
        if self.master is not None:
            self.master._widget_destroyed(self)
            self.master.redraw()

    def config(self, width:int=None, height:int=None) -> None:
        if width is not None:
            self._req_width = width
            if self.master is None:
                self._wants_self_expand()
            else:
                self.master._widget_changed_width(self)
            self._update(height=False)
            self.redraw()
        if height is not None:
            self._req_height = height
            if self.master is None:
                self._wants_self_expand()
            else:
                self.master._widget_changed_height(self)
            self._update(width=False)
            self.redraw()

    def _update_x(self, dx:int) -> None:
        self._x += dx
        for widget in self._children:
            widget._update_x(dx)
        self.redraw()

    def _update_y(self, dy:int) -> None:
        self._y += dy
        for widget in self._children:
            widget._update_y(dy)
        self.redraw()

    def _wants_self_expand(self) -> None:
        if self._dictate_own_size:
            if self._req_width != self._width:
                self._update_width(self._req_width)
            if self._req_height != self._height:
                self._update_height(self._req_height)

    # Use can call these:
    def columnconfigure(self, columns:(int or tuple), weight:int) -> None:
        if isinstance(columns, int):
            columns = (columns, )
        elif not isinstance(columns, (list, tuple)):
            raise ValueError("Invalid columns parameter. " \
                             "It must a tuple/list/int.")
        if weight == 1:
            self._expandable_columns.extend(columns)
        elif weight == 0:
            for column in columns:
                if column in self._expandable_columns:
                    self._expandable_columns.remove(column)
        else:
            raise ValueError("The weight can only be 0 or 1.")
        self._update()

    def rowconfigure(self, rows:(int or tuple), weight:int) -> None:
        if isinstance(rows, int):
            rows = (rows, )
        elif not isinstance(rows, (list, tuple)):
            raise ValueError("Invalid rows parameter. " \
                             "It must a tuple/list/int.")
        if weight == 1:
            self._expandable_rows.extend(rows)
        elif weight == 0:
            for row in rows:
                if row in self._expandable_rows:
                    self._expandable_rows.remove(row)
        else:
            raise ValueError("The weight can only be 0 or 1.")
        self._update()

    def grid_propagate(self, value:bool) -> None:
        self._grid_propagate = value
        self._update()

    # Helper functions/tested
    def _get_widget_from_xy(self, x:int, y:int):
        for widget in self._children:
            if widget._x <= x <= widget._x + widget._width:
                if widget._y <= y <= widget._y + widget._height:
                    if isinstance(widget, Grid):
                        return widget._get_widget_from_xy(x, y)
                    else:
                        return widget
        return self

    def _widget_destroyed(self, widget) -> None:
        self._children.remove(widget)
        for row, row_of_widgets in enumerate(self._widgets):
            if widget in row_of_widgets:
                column = row_of_widgets.index(widget)
                row_of_widgets[column] = None
        self._update()
        self.redraw()

    def _add_widget(self, widget, row:int, column:int) -> None:
        if widget in self._children:
            raise RuntimeError("Widget \"{widget}\" already my slave.")
        self._children.append(widget)
        max_column = len(self._widgets[0])
        while row >= len(self._widgets):
            self._widgets.append([None for i in range(max_column)])
        while column >= len(self._widgets[0]):
            for row_of_widgets in self._widgets:
                row_of_widgets.append(None)
        self._widgets[row][column] = widget
        self._update()

    def _get_rows(self, row1:int, row2:int):
        if row1 is None:
            row1 = 0
        if row2 is None:
            row2 = len(self._widgets)
        for row in range(row1, row2):
            yield self._get_row(row)

    def _get_columns(self, column1:int, column2:int):
        if column1 is None:
            column1 = 0
        if column2 is None:
            column2 = len(self._widgets[0])
        for column in range(column1, column2):
            yield self._get_column(column)

    def _get_row(self, row:int):
        return tuple(self._widgets[row])

    def _get_column(self, column:int):
        return tuple(row_of_widgets[column] for row_of_widgets in self._widgets)

    def _test_table(self, what:str="widgets") -> str:
        widgets = []
        for row_of_widgets in self._widgets:
            new_row = []
            for widget in row_of_widgets:
                if what == "widgets":
                    item = str(widget)
                elif what == "sizes":
                    if widget is None:
                        item = "[0, 0]"
                    else:
                        item = str([widget._width, widget._height])
                elif what == "positions":
                    if widget is None:
                        item = "None"
                    else:
                        item = str([widget._x, widget._y])
                else:
                    raise ValueError(f"Unknown value for `what`: \"{what}\"")
                new_row.append(item)
            widgets.append(tuple(new_row))
        table = pretty_print_table(tuple(widgets))
        output = "#" * (len(table.split("\n")[0]) + 4) + "\n"
        for row in table.split("\n"):
            output += f"# {row} #\n"
        output += "#" * (len(table.split("\n")[0]) + 4)
        return output

    # Other
    def _widget_changed_width(self, widget) -> None:
        assert not isinstance(widget, int), "You should pass in the widget "\
                                            "not the new width."
        for row_of_widgets in self._widgets:
            if widget in row_of_widgets:
                column = row_of_widgets.index(widget)
                return self._update_h()

    def _widget_changed_height(self, widget) -> None:
        assert not isinstance(widget, int), "You should pass in the widget "\
                                            "not the new height."
        for row, row_of_widgets in enumerate(self._widgets):
            if widget in row_of_widgets:
                return self._update_v()

    def _update(self, height:bool=True, width:bool=True) -> None:
        if width:
            self._update_h(redraw=False)
        if height:
            self._update_v(redraw=False)
        self.redraw()

    def _update_h(self, redraw:bool=True) -> None:
        base_x = self._x
        expandable_columns = [*self._expandable_columns]
        widths = []

        columns_of_widgets = tuple(self._get_columns(0, None))

        # Get the widths of the columns of widgets:
        for column_number, column in enumerate(columns_of_widgets):
            column = tuple(filter(None, column))
            width = 0
            if len(column) == 0:
                # Remove it from the `expandable_columns` list
                if column_number in expandable_columns:
                    expandable_columns.remove(column_number)
            else:
                width = max(map(lambda widget: widget._req_width, column))
            widths.append(width)

        # Try to expand/contract the frame to fit the widgets
        if sum(widths) != self._req_width:
            if self._grid_propagate and not (len(self._children) == 0):
                self._req_width = sum(widths)
                if self.master is None:
                    self._wants_self_expand()
                else:
                    self.master._widget_changed_width(self)
        max_x = base_x + self._width

        # Calculate the spare width. Please note that the call to:
        #   `self.master._widget_changed_width(self)` can change self._width
        spare_width = max(0, self._width - sum(widths))
        if len(expandable_columns) == 0:
            spare_width_per_column = 0
        else:
            spare_width_per_column = spare_width // len(expandable_columns)

        for column_number, column in enumerate(columns_of_widgets):
            column = tuple(filter(None, column))
            if len(column) != 0:
                width = widths[column_number]
                if column_number in expandable_columns:
                    width += spare_width_per_column
                width = min(width, max_x-base_x)
                if base_x >= max_x:
                    width = 0
                for widget in column:
                    widget._update_x(base_x - widget._x)
                    if widget._width != width:
                        widget._update_width(width)
                base_x += width
        if redraw:
            self.redraw()

    def _update_v(self, redraw:bool=True) -> None:
        base_y = self._y
        expandable_rows = [*self._expandable_rows]
        heights = []

        rows_of_widgets = tuple(self._get_rows(0, None))

        # Get the heights of the rows of widgets:
        for row_number, row in enumerate(rows_of_widgets):
            row = tuple(filter(None, row))
            height = 0
            if len(row) == 0:
                # Remove it from the `expandable_rows` list
                if row_number in expandable_rows:
                    expandable_rows.remove(row_number)
            else:
                height = max(map(lambda widget: widget._req_height, row))
            heights.append(height)

        # Try to expand the frame to fit the widgets
        if sum(heights) != self._req_height:
            if self._grid_propagate and not (len(self._children) == 0):
                self._req_height = sum(heights)
                if self.master is None:
                    self._wants_self_expand()
                else:
                    self.master._widget_changed_height(self)
        max_y = base_y + self._height

        # Calculate the spare height. Please note that the call to:
        #   `self.master._widget_changed_height(self)` can change self._height
        spare_height = max(0, self._height - sum(heights))
        if len(expandable_rows) == 0:
            spare_height_per_row = 0
        else:
            spare_height_per_row = spare_height // len(expandable_rows)

        for row_number, row in enumerate(rows_of_widgets):
            row = tuple(filter(None, row))
            if len(row) != 0:
                height = heights[row_number]
                if row_number in expandable_rows:
                    height += spare_height_per_row
                height = min(height, max_y-base_y)
                if base_y >= max_y:
                    height = 0
                for widget in row:
                    widget._update_y(base_y - widget._y)
                    if widget._height != height:
                        widget._update_height(height)
                base_y += height
        if redraw:
            self.redraw()



#################################### Tests #####################################

################################### Test 1 ####################################
def test_grid_widgets(add_breakpoint:bool=False):
    # Tests if the widgets are added in the correct row/column.

    expected_output = """
#####################################################
# None             None             Widget(widget4) #
# None             Widget(widget1)  Widget(widget2) #
# None             None             Widget(widget3) #
#####################################################
"""[1:-1]


    class Widget:
        def __init__(self, name:str):
            self.name = name
            self._req_width = self._req_height = 0
            self._width = self._height = 0
            self._x = self._y = 0

        def _update_height(self, new_height:int) -> None: ...
        def _update_width(self, new_width:int) -> None: ...
        def _update_x(self, dx:int) -> None: ...
        def _update_y(self, dy:int) -> None: ...
        def redraw(self) -> None: ...
        def update(self) -> None: ...
        def destroy(self) -> None: ...
        def grid(self) -> None: ...

        def __str__(self) -> str:
            return f"Widget({self.name})"
        __repr__ = __str__


    grid = Grid()
    widget1 = Widget(name="widget1")
    widget2 = Widget(name="widget2")
    widget3 = Widget(name="widget3")
    widget4 = Widget(name="widget4")

    grid._add_widget(widget1, row=1, column=1)
    grid._add_widget(widget2, row=1, column=2)
    grid._add_widget(widget3, row=2, column=2)
    grid._add_widget(widget4, row=0, column=2)

    if add_breakpoint:
        breakpoint()

    msg = "Failed! <Grid> doesn't add widgets in the correct row/column. " \
          "This must be fixed immediately!"
    assert grid._test_table("widgets") == expected_output, msg



################################### Test 2 ####################################
def test_grid_sizes_and_positions(add_breakpoint:bool=False):
    # Tests if the widgets are added in the correct x/y place with the
    #   correct width/height.

    expected_output_sizes = """
################################
# [0, 0]    [0, 0]    [15, 10] #
# [0, 0]    [5, 20]   [15, 20] #
# [0, 0]    [0, 0]    [15, 10] #
################################
"""[1:-1]
    expected_output_positions = """
#############################
# None     None     [5, 0]  #
# None     [0, 10]  [5, 10] #
# None     None     [5, 30] #
#############################
"""[1:-1]


    class Widget:
        def __init__(self, name:str, width:int, height:int):
            self.name = name
            self._req_width = width
            self._req_height = height
            self._width = self._height = 0
            self._x = self._y = 0

        def _update_height(self, new_height:int) -> None:
            self._height = new_height

        def _update_width(self, new_width:int) -> None:
            self._width = new_width

        def _update_x(self, dx:int) -> None:
            self._x += dx

        def _update_y(self, dy:int) -> None:
            self._y += dy

        def __str__(self) -> str:
            return f"Widget({self.name})"
        __repr__ = __str__
        def redraw(self) -> None: ...
        def update(self) -> None: ...
        def destroy(self) -> None: ...
        def grid(self) -> None: ...


    grid = Grid()

    widget1 = Widget(name="widget1", width=5, height=10)
    widget2 = Widget(name="widget2", width=5, height=20)
    widget3 = Widget(name="widget3", width=10, height=10)
    widget4 = Widget(name="widget4", width=15, height=10)

    grid._add_widget(widget1, row=1, column=1)
    grid._add_widget(widget2, row=1, column=2)
    grid._add_widget(widget3, row=2, column=2)
    grid._add_widget(widget4, row=0, column=2)

    if add_breakpoint:
        breakpoint()

    msg = "Failed! <Grid> doesn't add widgets with the correct width/" \
          "height. This must be fixed immediately!"
    assert grid._test_table("sizes") == expected_output_sizes, msg

    msg = "Failed! <Grid> doesn't add widgets with the correct width/" \
          "height. This must be fixed immediately!"
    assert grid._test_table("positions") == expected_output_positions, msg



################################### Test 3 ####################################
def test_grid_change_width_height(add_breakpoint:bool=False):
    # Tests if the widgets can request to change thier width/height

    expected_output_sizes = """
################################
# [0, 0]    [0, 0]    [15, 11] #
# [0, 0]    [6, 20]   [15, 20] #
# [0, 0]    [0, 0]    [15, 10] #
################################
"""[1:-1]
    expected_output_positions = """
#############################
# None     None     [6, 0]  #
# None     [0, 11]  [6, 11] #
# None     None     [6, 31] #
#############################
"""[1:-1]


    class Widget:
        def __init__(self, master, name:str, width:int, height:int):
            self.master = master
            self.name = name
            self._req_width = width
            self._req_height = height
            self._width = self._height = 0
            self._x = self._y = 0

        def _update_height(self, new_height:int) -> None:
            self._height = new_height

        def _update_width(self, new_width:int) -> None:
            self._width = new_width

        def _update_x(self, dx:int) -> None:
            self._x += dx

        def _update_y(self, dy:int) -> None:
            self._y += dy

        def __str__(self) -> str:
            return f"Widget({self.name})"
        __repr__ = __str__
        def redraw(self) -> None: ...
        def update(self) -> None: ...
        def destroy(self) -> None: ...
        def grid(self) -> None: ...

        def config(self, width:int=None, height:int=None) -> None:
            if width is not None:
                self._req_width = width
                self.master._widget_changed_width(self)
            if height is not None:
                self._req_height = height
                self.master._widget_changed_height(self)


    grid = Grid(dictate_own_size=False)
    widget1 = Widget(master=grid, name="widget1", width=5, height=10)
    widget2 = Widget(master=grid, name="widget2", width=5, height=20)
    widget3 = Widget(master=grid, name="widget3", width=10, height=10)
    widget4 = Widget(master=grid, name="widget4", width=15, height=10)

    grid._add_widget(widget1, row=1, column=1)
    grid._add_widget(widget2, row=1, column=2)
    grid._add_widget(widget3, row=2, column=2)
    grid._add_widget(widget4, row=0, column=2)

    widget1.config(width=6)
    widget4.config(height=11)

    if add_breakpoint:
        breakpoint()

    msg = "Failed! <Grid> doesn't add widgets with the correct width/" \
          "height when the width/height of one of the widgets is changed. " \
          "This must be fixed immediately!"
    assert grid._test_table("sizes") == expected_output_sizes, msg

    msg = "Failed! <Grid> doesn't add widgets with the correct width/" \
          "height when the width/height of one of the widgets is changed. " \
          "This must be fixed immediately!"
    assert grid._test_table("positions") == expected_output_positions, msg



################################### Test 4 ####################################
def test_grid_change_grid_height_width_x_y(add_breakpoint:bool=False):
    # Tests if the grid can be limited in width/height. And if the
    # grid's `_x` and `_y` can be changed.

    expected_output_sizes = """
#############################
# [0, 0]   [0, 0]   [4, 11] #
# [0, 0]   [6, 4]   [4, 4]  #
# [0, 0]   [0, 0]   [4, 0]  #
#############################
"""[1:-1]
    expected_output_positions = """
############################################
# None          None          [1006, 3000] #
# None          [1000, 3011]  [1006, 3011] #
# None          None          [1006, 3015] #
############################################
"""[1:-1]


    class Widget:
        def __init__(self, master, name:str, width:int, height:int):
            self.master = master
            self.name = name
            self._req_width = width
            self._req_height = height
            self._width = self._height = 0
            self._x = self._y = 0

        def _update_height(self, new_height:int) -> None:
            self._height = new_height

        def _update_width(self, new_width:int) -> None:
            self._width = new_width

        def _update_x(self, dx:int) -> None:
            self._x += dx

        def _update_y(self, dy:int) -> None:
            self._y += dy

        def __str__(self) -> str:
            return f"Widget({self.name})"
        __repr__ = __str__
        def redraw(self) -> None: ...
        def update(self) -> None: ...
        def destroy(self) -> None: ...
        def grid(self) -> None: ...

        def config(self, width:int=None, height:int=None) -> None:
            if width is not None:
                self._req_width = width
                self.master._widget_changed_width(self)
            if height is not None:
                self._req_height = height
                self.master._widget_changed_height(self)


    grid = Grid(dictate_own_size=False)
    widget1 = Widget(master=grid, name="widget1", width=5, height=10)
    widget2 = Widget(master=grid, name="widget2", width=5, height=20)
    widget3 = Widget(master=grid, name="widget3", width=10, height=10)
    widget4 = Widget(master=grid, name="widget4", width=15, height=10)

    grid._add_widget(widget1, row=1, column=1)
    grid._add_widget(widget2, row=1, column=2)
    grid._add_widget(widget3, row=2, column=2)
    grid._add_widget(widget4, row=0, column=2)

    grid._width=10
    grid._height=15

    grid._update_x(1000)
    grid._update_y(3000)

    widget1.config(width=6)
    widget4.config(height=11)

    if add_breakpoint:
        breakpoint()

    msg = "Failed! <Grid> doesn't add widgets with the correct width/" \
          "height/x/y when the width/height/x/y of the <Grid> is changed. " \
          "This must be fixed immediately!"
    assert grid._test_table("sizes") == expected_output_sizes, msg

    msg = "Failed! <Grid> doesn't add widgets with the correct width/" \
          "height/x/y when the width/height/x/y of the <Grid> is changed. " \
          "This must be fixed immediately!"
    assert grid._test_table("positions") == expected_output_positions, msg



################################### Test 5 ####################################
def test_grid_destroy(add_breakpoint:bool=False):
    # Tests if we can call `<Grid>._widget_destroyed`

    expected_output_sizes = """
################################
# [0, 0]    [0, 0]    [10, 11] #
# [0, 0]    [0, 0]    [10, 4]  #
# [0, 0]    [0, 0]    [10, 0]  #
################################
"""[1:-1]
    expected_output_positions = """
############################################
# None          None          [1000, 3000] #
# None          None          [1000, 3011] #
# None          None          [1000, 3015] #
############################################
"""[1:-1]


    class Widget:
        def __init__(self, master, name:str, width:int, height:int):
            self.master = master
            self.name = name
            self._req_width = width
            self._req_height = height
            self._width = self._height = 0
            self._x = self._y = 0

        def _update_height(self, new_height:int) -> None:
            self._height = new_height

        def _update_width(self, new_width:int) -> None:
            self._width = new_width

        def _update_x(self, dx:int) -> None:
            self._x += dx

        def _update_y(self, dy:int) -> None:
            self._y += dy

        def __str__(self) -> str:
            return f"Widget({self.name})"
        __repr__ = __str__
        def redraw(self) -> None: ...
        def update(self) -> None: ...
        def destroy(self) -> None: ...
        def grid(self) -> None: ...

        def config(self, width:int=None, height:int=None) -> None:
            if width is not None:
                self._req_width = width
                self.master._widget_changed_width(self)
            if height is not None:
                self._req_height = height
                self.master._widget_changed_height(self)


    grid = Grid(dictate_own_size=False)
    widget1 = Widget(master=grid, name="widget1", width=5, height=10)
    widget2 = Widget(master=grid, name="widget2", width=5, height=20)
    widget3 = Widget(master=grid, name="widget3", width=10, height=10)
    widget4 = Widget(master=grid, name="widget4", width=15, height=10)

    grid._add_widget(widget1, row=1, column=1)
    grid._add_widget(widget2, row=1, column=2)
    grid._add_widget(widget3, row=2, column=2)
    grid._add_widget(widget4, row=0, column=2)

    grid._width=10
    grid._height=15

    grid._update_x(1000)
    grid._update_y(3000)

    grid._widget_destroyed(widget1)

    widget1.config(width=6)
    widget4.config(height=11)

    if add_breakpoint:
        breakpoint()

    msg = "Failed! <Grid> doesn't add widgets with the correct width/" \
          "height/x/y when the width/height/x/y of the <Grid> is changed. " \
          "This must be fixed immediately!"
    assert grid._test_table("sizes") == expected_output_sizes, msg

    msg = "Failed! <Grid> doesn't add widgets with the correct width/" \
          "height/x/y when the width/height/x/y of the <Grid> is changed. " \
          "This must be fixed immediately!"
    assert grid._test_table("positions") == expected_output_positions, msg



################################### Test 6 ####################################
def test_grid_columnconfigure_rowconfigure(add_breakpoint:bool=False):
    # Tests if we can call `<Grid>.columnconfigure` and `<Grid>.rowconfigure`

    expected_output_sizes = """
################################
# [0, 0]    [0, 0]    [17, 13] #
# [0, 0]    [7, 23]   [17, 23] #
# [0, 0]    [0, 0]    [17, 13] #
################################
"""[1:-1]
    expected_output_positions = """
############################################
# None          None          [1007, 3000] #
# None          [1000, 3013]  [1007, 3013] #
# None          None          [1007, 3036] #
############################################
"""[1:-1]


    class Widget:
        def __init__(self, master, name:str, width:int, height:int):
            self.master = master
            self.name = name
            self._req_width = width
            self._req_height = height
            self._width = self._height = 0
            self._x = self._y = 0

        def _update_height(self, new_height:int) -> None:
            self._height = new_height

        def _update_width(self, new_width:int) -> None:
            self._width = new_width

        def _update_x(self, dx:int) -> None:
            self._x += dx

        def _update_y(self, dy:int) -> None:
            self._y += dy

        def __str__(self) -> str:
            return f"Widget({self.name})"
        __repr__ = __str__
        def redraw(self) -> None: ...
        def update(self) -> None: ...
        def destroy(self) -> None: ...
        def grid(self) -> None: ...

        def config(self, width:int=None, height:int=None) -> None:
            if width is not None:
                self._req_width = width
                self.master._widget_changed_width(self)
            if height is not None:
                self._req_height = height
                self.master._widget_changed_height(self)


    grid = Grid(dictate_own_size=False)
    widget1 = Widget(master=grid, name="widget1", width=5, height=10)
    widget2 = Widget(master=grid, name="widget2", width=5, height=20)
    widget3 = Widget(master=grid, name="widget3", width=10, height=10)
    widget4 = Widget(master=grid, name="widget4", width=15, height=10)

    grid._add_widget(widget1, row=1, column=1)
    grid._add_widget(widget2, row=1, column=2)
    grid._add_widget(widget3, row=2, column=2)
    grid._add_widget(widget4, row=0, column=2)

    grid._width=25
    grid._height=49

    grid._update_x(1000)
    grid._update_y(3000)

    grid.columnconfigure((0, 1, 2), weight=1)
    grid.rowconfigure((0, 1, 2), weight=1)

    if add_breakpoint:
        breakpoint()

    msg = "Failed! <Grid> doesn't add widgets with the correct width/" \
          "height/x/y when the width/height/x/y of the <Grid> is changed. " \
          "This must be fixed immediately!"
    assert grid._test_table("sizes") == expected_output_sizes, msg

    msg = "Failed! <Grid> doesn't add widgets with the correct width/" \
          "height/x/y when the width/height/x/y of the <Grid> is changed. " \
          "This must be fixed immediately!"
    assert grid._test_table("positions") == expected_output_positions, msg



############################## Combine all tests ##############################
def test():
    from sys import stderr
    tests = (test_grid_widgets, test_grid_sizes_and_positions,
             test_grid_change_width_height,
             test_grid_change_grid_height_width_x_y, test_grid_destroy,
             test_grid_columnconfigure_rowconfigure)
    for _test in tests:
        stderr.write(f"[Debug]: Testing {_test.__name__}:\n")
        _test()
        stderr.write(f"[Debug]: Test passed.\n")
    stderr.write(f"[Debug]: All tests passed.\n")


if __name__ == "__main__":
    test()
