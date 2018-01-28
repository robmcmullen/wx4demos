import wx
import time

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
        self.Bind(wx.EVT_LEFT_UP, self.on_left_up)
       
    def on_left_up(self, event):
        print
        print "Title " + str(self)
        print "Position " + str(self.GetPosition())
        print "Size " + str(self.GetSize())
        print "VirtualSize " + str(self.GetVirtualSize())
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
        print "scrolling..." + str(pos) + str(event.GetPosition())
        # self.main.Scroll(dx, dy)
        # self.top.Scroll(dx, 0)
        # self.left.Scroll(0, dy)
        event.Skip()


class Line(object):
    def __init__(self, w, h, num_cells):
        self.w = w
        self.h = h
        self.num_cells = num_cells
        self.vw = self.w * self.num_cells

    @property
    def virtual_width(self):
        return self.vw

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
        print("%d,%d: %s" % (x, y, part))
        dc.DrawText(part, x, y)



class HexGridHeader(wx.ScrolledCanvas):
    use_x = 1
    use_y = 1

    def __init__(self, parent, width, height):
        wx.ScrolledCanvas.__init__(self, parent, -1)
        self.parent = parent
        self.SetBackgroundColour(wx.RED)
        self.SetSize(width, height)
        self.SetVirtualSize(width, height)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_left_up)
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_size)

    def on_size(self, event ):
        print "Size " + str(self.GetSize())
        print "VirtualSize " + str(self.GetVirtualSize())
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

        #self.Layout()


    def on_paint(self, event):
        dc = wx.PaintDC(self)
        cell_num, line_num = self.parent.GetViewStart()
        cell_num *= self.use_x
        line_num *= self.use_y

        px, py = self.parent.CalcUnscrolledPosition(0, 0)
        px *= self.use_x
        py *= self.use_y
        dc.SetLogicalOrigin(px, py)

        w, h = self.GetClientSize()
        num_cells_wide = (w / self.parent.line_renderer.w) + 1
        if self.use_y:
            num_lines_tall = (h / self.parent.line_renderer.h) + 1
        else:
            num_lines_tall = 1

        print("on_paint: %dx%d at %d,%d. origin=%d,%d" % (num_cells_wide, num_lines_tall, cell_num, line_num, px, py))

        for line in range(line_num, min(line_num + num_lines_tall, self.parent.num_lines)):
            self.parent.line_renderer.draw(dc, line, cell_num, num_cells_wide)
     
    def on_left_up(self, event):
        print
        print "Title " + str(self)
        print "Position " + str(self.GetPosition())
        print "ViewStart " + str(self.GetViewStart())
        print "Size " + str(self.GetSize())
        print "VirtualSize " + str(self.GetVirtualSize())


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

        self.scroll = HexGridWindow(frame, TextLine(font, 100), 50)

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
       
        print "wx.VERSION = " + wx.VERSION_STRING
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
