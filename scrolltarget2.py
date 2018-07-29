import wx
import time

class HexGridWindow(wx.ScrolledWindow):
    def __init__(self, *args, **kwargs):
        wx.ScrolledWindow.__init__ (self, *args, **kwargs)
        self.SetAutoLayout(True)

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
        self.SetScrollRate(20,20)
        self.Bind(wx.EVT_SCROLLWIN, self.on_scroll_window)
        self.Bind(wx.EVT_LEFT_UP, self.on_left_up)
       
    def on_left_up(self, event):
        print()
        print("Title " + str(self))
        print("Position " + str(self.GetPosition()))
        print("Size " + str(self.GetSize()))
        print("VirtualSize " + str(self.GetVirtualSize()))
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
        print("Size " + str(self.GetSize()))
        print("VirtualSize " + str(self.GetVirtualSize()))
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
        #self.parent.PrepareDC(dc)
        size = self.GetVirtualSize()

        s = "Size: %d x %d"%(size.x, size.y)
        vbX, vbY = self.parent.GetViewStart()
        posX, posY = self.parent.CalcUnscrolledPosition (0, 0)
        vbX, vbY = vbX * self.use_x, vbY * self.use_y
        posX, posY = posX * self.use_x, posY * self.use_y
        # vbX, vbY = self.GetViewStart()
        # posX, posY = self.CalcUnscrolledPosition (0, 0)
        upd = wx.RegionIterator(self.GetUpdateRegion())  # get the update rect list
        r = []
        while upd.HaveRects():
            rect = upd.GetRect()

            # Repaint this rectangle
            #PaintRectangle(rect, dc)
            r.append("rect: %s" % str(rect))
            upd.Next()
        print(s, (posX, posY), (vbX, vbY), " ".join(r))
        dc.SetLogicalOrigin(posX, posY)

        dc.SetFont(wx.NORMAL_FONT)
        w, height = dc.GetTextExtent(s)
        height += 3
        dc.SetBrush(wx.WHITE_BRUSH)
        dc.SetPen(wx.WHITE_PEN)
        dc.DrawRectangle(0, 0, size.x, size.y)
        dc.SetPen(wx.LIGHT_GREY_PEN)
        dc.DrawLine(0, 0, size.x, size.y)
        dc.DrawLine(0, size.y, size.x, 0)
        dc.DrawText(s, (size.x-w)/2, (size.y-height*5)/2)
     
    def on_left_up(self, event):
        print()
        print("Title " + str(self))
        print("Position " + str(self.GetPosition()))
        print("ViewStart " + str(self.GetViewStart()))
        print("Size " + str(self.GetSize()))
        print("VirtualSize " + str(self.GetVirtualSize()))


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
        scroll = HexGridWindow(frame, wx.NewId())
        scroll.set_pane_sizes(3000, 1000, 80, 20)
        scroll.SetScrollRate(20,20)
        #(width, height) = dc.GetTextExtent("M")
        frame.Show()
        # self.SetTopWindow(frame)
       
        print("wx.VERSION = " + wx.VERSION_STRING)
        return True
       
#For testing
if __name__ == '__main__':
    app = MyApp(False)
    app.MainLoop()
