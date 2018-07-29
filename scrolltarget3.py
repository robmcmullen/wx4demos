import time
import sys

import wx


def ForceBetween(min, val, max):
    if val  > max:
        return max
    if val < min:
        return min
    return val

class HexGridWindow(wx.ScrolledWindow):
    def __init__(self, parent, line_renderer, num_lines, *args, **kwargs):
        wx.ScrolledWindow.__init__ (self, parent, -1, *args, **kwargs)
        self.SetAutoLayout(True)

        self.line_renderer = line_renderer
        self.num_lines = num_lines

        self.top = HexGridColHeader(self, 40, 40)
        self.left = HexGridRowHeader(self, 40, 40)
        self.main = HexGridDataWindow(self, 40, 40)
        sizer = wx.FlexGridSizer(2,2,0,0)
        self.corner = sizer.Add(5, 5, 0, wx.EXPAND)
        sizer.Add(self.top, 0, wx.EXPAND)
        sizer.Add(self.left, 0, wx.EXPAND)
        sizer.Add(self.main, 0, wx.EXPAND)
        sizer.AddGrowableCol(1)
        sizer.AddGrowableRow(1)
        self.SetSizer(sizer)
        self.SetTargetWindow(self.main)
        self.set_pane_sizes(self.line_renderer.virtual_width, self.num_lines * self.line_renderer.h, 80, 20)
        line_renderer.set_scroll_rate(self)
        self.Bind(wx.EVT_SCROLLWIN, self.on_scroll_window)
        self.Bind(wx.EVT_SIZE, self.on_size)

    def on_size(self, event ):
        print("Size " + str(self.GetSize()))
        print("VirtualSize " + str(self.GetVirtualSize()))
        print("ClientSize " + str(self.GetClientSize()))
        event.Skip()
       
    def set_pane_sizes(self, width, height, left_width, top_height):
        """
        Set the size of the 3 panes as follow:
            - main = width, height
            - top = width, 40
            - left = 80, height
        """
        self.main.SetVirtualSize(wx.Size(width,height))
        #(wt, ht) = self.top.GetSize()
        self.top.SetVirtualSize(wx.Size(width, top_height))
        #(wl, hl) = self.left.GetSize()
        self.left.SetVirtualSize(wx.Size(left_width, height))
        self.corner.SetMinSize(left_width, top_height)
        #self.Layout()
       
    def on_scroll_window(self, event):
        """
        OnScrollWindow Event Callback. This should let the main panel scroll in
        both direction but transmit the vertical scrolling to the left panel
        and the horizontal scrolling to the top window
        """
        sx,sy = self.GetScrollPixelsPerUnit()
        if event.GetOrientation() == wx.HORIZONTAL:
            dx = event.GetPosition()
            dy = self.GetScrollPos(wx.VERTICAL)
        else:
            dx = self.GetScrollPos(wx.HORIZONTAL)
            dy = event.GetPosition()
       
        pos = (dx ,dy)
        print("scrolling..." + str(pos) + str(event.GetPosition()))
        # self.main.Scroll(dx, dy)
        # self.top.Scroll(dx, 0)
        # self.left.Scroll(0, dy)
        event.Skip()

    def move_viewport(self, row, col):
        # self.main.SetScrollPos(wx.HORIZONTAL, col)
        # self.main.SetScrollPos(wx.VERTICAL, row)
        self.Scroll(col, row)
        print(("viewport: %d,%d" % (row, col)))
        self.main.Refresh()


class Line(object):
    def __init__(self, w, h, num_cells):
        self.w = w
        self.h = h
        self.num_cells = num_cells
        self.vw = self.w * self.num_cells

    @property
    def virtual_width(self):
        return self.vw

    def cell_to_pixel(self, line_num, cell_num):
        x = cell_num * self.w
        y = line_num * self.h
        return x, y

    def set_scroll_rate(self, parent):
        parent.SetScrollRate(self.w, self.h)

    def draw(self, dc, line_num, start_cell, num_cells):
        raise NotImplementedError("implement draw() in subclass!")


class TextLine(Line):
    def __init__(self, font, num_cells):
        self.font = font
        dc = wx.MemoryDC()
        dc.SetFont(font)
        Line.__init__(self, dc.GetCharWidth(), dc.GetCharHeight(), num_cells)

    def draw(self, dc, line_num, start_cell, num_cells):
        """
        """
        dc.SetFont(self.font)
        x = start_cell * self.w
        y = line_num * self.h
        w = self.vw
        h = self.h
        dc.SetBrush(wx.WHITE_BRUSH)
        dc.SetPen(wx.WHITE_PEN)
        dc.DrawRectangle(x, y, w, h)
        text = "line #%d at %d,%d with lots of extra stuff: %s" % (line_num, x, y, ",".join([str(i) for i in range(50)])) 
        part = text[start_cell:start_cell + num_cells]
        #print("%d,%d: %s" % (x, y, part))
        dc.DrawText(part, x, y)



class HexGridHeader(wx.ScrolledCanvas):
    use_x = 1
    use_y = 1

    def __init__(self, parent, width, height):
        wx.ScrolledCanvas.__init__(self, parent, -1)
        self.parent = parent
        self.zoom = 1
        self.SetBackgroundColour(wx.RED)
        self.SetSize(width, height)
        self.SetVirtualSize(width, height)
        self.calc_visible()
        self.next_scroll_time = 0
        self.scroll_timer = wx.Timer(self)
        self.scroll_delay = 1000  # milliseconds
        self.carets = []
        self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        self.Bind(wx.EVT_MOTION, self.on_motion)
        self.Bind(wx.EVT_LEFT_UP, self.on_left_up)
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_TIMER, self.on_timer)
        self.Bind(wx.EVT_ERASE_BACKGROUND, lambda evt: False)

    def pixel_pos_to_row_cell(self, x, y):
        sx, sy = self.parent.GetViewStart()
        row  = sy + int(y / self.cell_pixel_height)
        cell = sx + int(x / self.cell_pixel_width)
        return row, cell

    def clamp_row_col(self, row, col):
        sx, sy = self.parent.GetViewStart()
        row2 = ForceBetween(sy, row, sy + self.fully_visible_rows - 1)
        col2 = ForceBetween(sx, col, sx + self.fully_visible_cells - 1)
        print(("clamp: before=%d,%d after=%d,%d" % (row, col, row2, col2)))
        return row2, col2

    def ensure_visible(self, row, col):
        sx, sy = self.parent.GetViewStart()
        sy2 = ForceBetween(max(0, row - self.visible_rows), sy, row)
        sx2 = ForceBetween(max(0, col - self.visible_cells), sx, col)
        print(("ensure_visible: before=%d,%d after=%d,%d" % (sy, sx, sy2, sx2)))
        self.parent.move_viewport(sy2, sx2)

    def on_size(self, event ):
        print("Size " + str(self.GetSize()))
        print("VirtualSize " + str(self.GetVirtualSize()))
        print("ClientSize " + str(self.GetClientSize()))
        size = self.GetSize()
        vsize = self.GetVirtualSize()
        if self.use_x and self.use_y:
            # main window, no adjustment
            pass
        elif self.use_x:
            # scrolls in X dir
            self.SetVirtualSize(vsize.x, size.y)
        else:
            self.SetVirtualSize(size.x, vsize.y)

        self.calc_visible()

    def calc_visible(self):
        # For proper buffered painting, the visible_rows must include the
        # (possibly) partially obscured last row.  fully_visible_rows
        # indicates the number of rows without that last partially obscured
        # row (if it exists).
        w, h = self.GetClientSize().Get()
        self.cell_pixel_height = self.parent.line_renderer.h * self.zoom
        self.cell_pixel_width = self.parent.line_renderer.w * self.zoom
        self.fully_visible_rows = int(h / self.cell_pixel_height)
        self.fully_visible_cells = int(w / self.cell_pixel_width)
        self.visible_rows = ((h + self.cell_pixel_height - 1) / self.cell_pixel_height)
        self.visible_cells = ((w + self.cell_pixel_width - 1) / self.cell_pixel_width)

    def on_paint(self, event):
        dc = wx.PaintDC(self)
        self.first_visible_cell, self.first_visible_row = self.parent.GetViewStart()
        self.first_visible_cell *= self.use_x
        self.first_visible_row *= self.use_y

        px, py = self.parent.CalcUnscrolledPosition(0, 0)
        px *= self.use_x
        py *= self.use_y
        dc.SetLogicalOrigin(px, py)

        #print("on_paint: %dx%d at %d,%d. origin=%d,%d" % (self.visible_cells, self.visible_rows, self.first_visible_cell, self.first_visible_row, px, py))

        line_num = self.first_visible_row
        for line in range(line_num, min(line_num + self.visible_rows, self.parent.num_lines)):
            self.parent.line_renderer.draw(dc, line, self.first_visible_cell, self.visible_cells)

        for caret in self.carets:
            r, c = caret
            self.DrawSimpleCaret(c, r, dc)
     
    def can_scroll(self):
        self.set_scroll_timer()
        if time.time() >  self.next_scroll_time:
            self.next_scroll_time = time.time() + (self.scroll_delay / 1000.0)
            return True
        else:
            return False

    def set_scroll_timer(self):
        if self.scroll_timer is None:
            self.scroll_timer = wx.Timer(self)
        print("starting timer")
        self.scroll_timer.Start(self.scroll_delay/10, True)

    def on_timer(self, event):
        screenX, screenY = wx.GetMousePosition()
        x, y = self.ScreenToClient((screenX, screenY))
        row, cell = self.pixel_pos_to_row_cell(x, y)
        print(("on_timer: time=%f pos=%d,%d" % (time.time(), row, cell)))
        self.handle_on_motion(event, row, cell)

    def is_left_of_screen(self, sx, col):
        return col < sx

    def handle_left_of_screen(self, col):
        scroll_col = -1
        if col + scroll_col < 0:
            scroll_col = 0
        return scroll_col

    def is_right_of_screen(self, sx, col):
        return col >= sx + self.visible_cells

    def handle_right_of_screen(self, col):
        scroll_col = 1
        if col + scroll_col >= self.visible_cells:
            scroll_col = 0
        return scroll_col

    def is_above_screen(self, sy, row):
        return row < sy

    def handle_above_screen(self, row):
        scroll_row = -1
        if row + scroll_row < 0:
            scroll_row = 0
        return scroll_row

    def is_below_screen(self, sy, row):
        return row >= sy + self.visible_rows

    def handle_below_screen(self, row):
        scroll_row = 1
        if row + scroll_row >= self.visible_rows:
            scroll_row = 0
        return scroll_row

    def get_row_col_from_event(self, evt):
        row, cell = self.pixel_pos_to_row_cell(evt.GetX(), evt.GetY())
        return row, cell

    def on_left_down(self, evt):
        print("left down")
        self.CaptureMouse()

    def on_motion(self, evt, x=None, y=None):
        row, col = self.get_row_col_from_event(evt)
        if evt.LeftIsDown() and self.HasCapture() and not self.scroll_timer.IsRunning():
            self.handle_on_motion(evt, row, col)

    def on_left_up(self, event):
        self.scroll_timer.Stop()
        if not self.HasCapture():
            return
        self.ReleaseMouse()
        print()
        print("Title " + str(self))
        print("Position " + str(self.GetPosition()))
        print("Size " + str(self.GetSize()))
        print("VirtualSize " + str(self.GetVirtualSize()))

    def handle_on_motion(self, evt, row, col):
        scroll_row = 0
        scroll_col = 0
        sx, sy = self.GetViewStart()
        if self.is_left_of_screen(sx, col):
            if self.can_scroll():
                scroll_col = self.handle_left_of_screen(col)
        elif self.is_right_of_screen(sx, col):
            if self.can_scroll():
                scroll_col = self.handle_right_of_screen(col)
        if self.is_above_screen(sy, row):
            if self.can_scroll():
                scroll_row = self.handle_above_screen(row)
        elif self.is_below_screen(sy, row):
            if self.can_scroll():
                scroll_row = self.handle_below_screen(row)
        print(("scroll delta: %d, %d" % (scroll_row, scroll_col)))
        #row, col = self.main.clamp_row_col(row, col)
        row += scroll_row
        col += scroll_col
        self.ensure_visible(row, col)
        self.carets = [self.clamp_row_col(row, col)]
        self.parent.Refresh()

    def DrawSimpleCaret(self, cell_x, cell_y, dc = None, old=False):
        if not dc:
            dc = wx.ClientDC(self)

        lr = self.parent.line_renderer
        x, y = lr.cell_to_pixel(cell_y, cell_x)
        w = lr.w
        h = lr.h
        self.draw_caret(dc, x, y, w, h)

    def draw_caret(self, dc, x, y, w, h):
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        dc.SetPen(wx.Pen(wx.BLACK))
        dc.DrawRectangle(x, y, w, h)
        x -= 1
        y -= 1
        w += 2
        h += 2
        dc.DrawRectangle(x, y, w, h)
        x -= 1
        y -= 1
        w += 2
        h += 2
        dc.DrawRectangle(x, y, w, h)


class HexGridColHeader(HexGridHeader):
    use_x = 1
    use_y = 0


class HexGridRowHeader(HexGridHeader):
    use_x = 0
    use_y = 1


class HexGridDataWindow(HexGridHeader):
    pass


class MyApp(wx.App):
    """
    Simple Application class for testing
    """
    def OnInit(self):
        """
        Initialize the Application
        """
        #This is the frame as I want to use it, with a tri-pane scroll window
        #However, the information sent to the sub-window is incorrect, so the
        #on_paint callback draws the wrong area on screen...
        id = wx.NewId()
        frame = wx.Frame(None, id, "Test Tri-pane frame" )
        font = self.NiceFontForPlatform()

        self.scroll = HexGridWindow(frame, TextLine(font, 100), 500)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.scroll, 1, wx.EXPAND)

        btn = wx.Button(frame, -1, "Press to redraw")
        sizer.Add(btn, 0, wx.EXPAND)
        btn.Bind(wx.EVT_BUTTON, self.do_redraw)

        frame.SetSizer(sizer)
        frame.Layout()

        #(width, height) = dc.GetTextExtent("M")
        frame.Show()
        # self.SetTopWindow(frame)
       
        print("wx.VERSION = " + wx.VERSION_STRING)
        return True

    def do_redraw(self, evt):
        self.scroll.paint_all()

    def NiceFontForPlatform(self):
        point_size = 10
        family = wx.DEFAULT
        style = wx.NORMAL
        weight = wx.NORMAL
        underline = False
        if wx.Platform == "__WXMAC__":
            face_name = "Monaco"
        elif wx.Platform == "__WXMSW__":
            face_name = "Lucida Console"
        else:
            face_name = "monospace"
        font = wx.Font(point_size, family, style, weight, underline, face_name)
        return font

#For testing
if __name__ == '__main__':
    app = MyApp(False)
    app.MainLoop()
