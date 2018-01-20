import time

import wx
import hexview

# Check wxpython demo for Editor to see a pure-python implementation of an on-
# demand renderer for lines of text: wx.lib.editor

class DummyScroller(object):
    def SetScrollbars(self, *args, **kwargs):
        pass

class AuxWindow(wx.ScrolledWindow):
    def __init__(self, parent, scroll_source, use_x, use_y):
        wx.ScrolledWindow.__init__(self, parent, -1)
        self.scroll_source = scroll_source
        if use_x:
            self.Draw = self.DrawHorz
        else:
            self.Draw = self.DrawVert
        #             "0A 0X 0Y FF sv-bdizc  00 00 00 LDA $%04x"
        self.header = " A  X  Y SP sv-bdizc  Opcodes  Assembly"
        self.isDrawing = False
        self.EnableScrolling(False, False)
        self.ShowScrollbars(wx.SHOW_SB_NEVER, wx.SHOW_SB_NEVER)

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)

    def OnSize(self, event):
        self.AdjustScrollbars()
        self.SetFocus()

    def UpdateView(self, dc = None):
        if dc is None:
            dc = wx.ClientDC(self)
        if dc.IsOk():
            self.Draw(dc)

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        if self.isDrawing:
            return
        self.isDrawing = True
        self.UpdateView(dc)
        self.isDrawing = False

    def OnEraseBackground(self, evt):
        pass

    def DrawEditText(self, t, x, y, dc):
        s = self.scroll_source
        dc.DrawText(t, x * s.fw, y * s.fh)

    def DrawLine(self, t, line, dc):
        s = self.scroll_source
        self.DrawEditText(t, 0, line - s.sy, dc)

    def DrawVert(self, odc=None):
        if not odc:
            odc = wx.ClientDC(self)

        dc = wx.BufferedDC(odc)
        s = self.scroll_source
        if dc.IsOk():
            dc.SetFont(s.font)
            dc.SetBackgroundMode(wx.SOLID)
            dc.SetTextBackground(s.bgColor)
            dc.SetTextForeground(s.fgColor)
            dc.SetBackground(wx.Brush(s.bgColor))
            dc.Clear()
            for line in range(s.sy, s.sy + s.sh):
                if s.IsLine(line):
                    self.DrawLine("%04x" % line, line, dc)

    def DrawHorz(self, odc=None):
        if not odc:
            odc = wx.ClientDC(self)

        dc = wx.BufferedDC(odc)
        s = self.scroll_source
        if dc.IsOk():
            dc.SetFont(s.font)
            dc.SetBackgroundMode(wx.SOLID)
            dc.SetTextBackground(s.bgColor)
            dc.SetTextForeground(s.fgColor)
            dc.SetBackground(wx.Brush(s.bgColor))
            dc.Clear()
            line = self.header[s.sx:]
            self.DrawLine(line, s.sy, dc)



class HexGridWindow(wx.ScrolledWindow):
    def __init__(self, *args, **kwargs):
        wx.ScrolledWindow.__init__ (self, *args, **kwargs)
        self.SetAutoLayout(True)

        self.update_dependents = self.update_dependents_null
        self.main = hexview.FixedFontDataWindow(self, 1000)
        self.top = AuxWindow(self, self.main, True, False)
        self.left = AuxWindow(self, self.main, False, True)
        sizer = wx.FlexGridSizer(2,2,0,0)
        self.corner = sizer.Add(5, 5, 0, wx.EXPAND)
        sizer.Add(self.top, 0, wx.EXPAND)
        sizer.Add(self.left, 0, wx.EXPAND)
        sizer.Add(self.main, 0, wx.EXPAND)
        sizer.AddGrowableCol(1)
        sizer.AddGrowableRow(1)
        self.SetSizer(sizer)
        self.SetTargetWindow(self.main)
        #self.SetScrollRate(20,20)
        self.Bind(wx.EVT_SCROLLWIN, self.on_scroll_window)
        self.Bind(wx.EVT_LEFT_UP, self.on_left_up)

        self.ShowScrollbars(wx.SHOW_SB_ALWAYS, wx.SHOW_SB_ALWAYS)
        self.main.ShowScrollbars(wx.SHOW_SB_NEVER, wx.SHOW_SB_NEVER)
        self.top.ShowScrollbars(wx.SHOW_SB_NEVER, wx.SHOW_SB_NEVER)
        self.left.ShowScrollbars(wx.SHOW_SB_NEVER, wx.SHOW_SB_NEVER)
        self.update_dependents = self.update_dependents_post_init

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
        wx.CallAfter(self.main.SetScrollManager, self)

    def HorizScroll(self, event, eventType):
        maxLineLen = self.main.CalcMaxLineLen()

        if eventType == wx.wxEVT_SCROLLWIN_LINEUP:
            self.main.sx -= 1
        elif eventType == wx.wxEVT_SCROLLWIN_LINEDOWN:
            self.main.sx += 1
        elif eventType == wx.wxEVT_SCROLLWIN_PAGEUP:
            self.main.sx -= self.main.sw
        elif eventType == wx.wxEVT_SCROLLWIN_PAGEDOWN:
            self.main.sx += self.main.sw
        elif eventType == wx.wxEVT_SCROLLWIN_TOP:
            self.main.sx = self.main.cx = 0
        elif eventType == wx.wxEVT_SCROLLWIN_BOTTOM:
            self.main.sx = maxLineLen - self.main.sw
            self.main.cx = maxLineLen
        else:
            self.main.sx = event.GetPosition()

        self.main.HorizBoundaries()

    def VertScroll(self, event, eventType):
        if   eventType == wx.wxEVT_SCROLLWIN_LINEUP:
            self.main.sy -= 1
        elif eventType == wx.wxEVT_SCROLLWIN_LINEDOWN:
            self.main.sy += 1
        elif eventType == wx.wxEVT_SCROLLWIN_PAGEUP:
            self.main.sy -= self.main.sh
        elif eventType == wx.wxEVT_SCROLLWIN_PAGEDOWN:
            self.main.sy += self.main.sh
        elif eventType == wx.wxEVT_SCROLLWIN_TOP:
            self.main.sy = self.main.cy = 0
        elif eventType == wx.wxEVT_SCROLLWIN_BOTTOM:
            self.main.sy = self.main.LinesInFile() - self.main.sh
            self.main.cy = self.main.LinesInFile()
        else:
            self.main.sy = event.GetPosition()

        self.main.VertBoundaries()

    def on_scroll_window(self, event):
        dir = event.GetOrientation()
        eventType = event.GetEventType()
        if dir == wx.HORIZONTAL:
            self.HorizScroll(event, eventType)
        else:
            self.VertScroll(event, eventType)
        self.main.UpdateView()

    def update_dependents_null(self):
        pass

    def update_dependents_post_init(self):
        self.top.UpdateView()
        self.left.UpdateView()


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
        frame = wx.Frame(None, id, "Test Text Grid" )
        scroll = HexGridWindow(frame, wx.NewId())
        scroll.set_pane_sizes(3000, 1000, 80, 20)

        #(width, height) = dc.GetTextExtent("M")
        frame.Show()
        # self.SetTopWindow(frame)
       
        print "wx.VERSION = " + wx.VERSION_STRING
        return True
       
#For testing
if __name__ == '__main__':
    app = MyApp(False)
    app.MainLoop()