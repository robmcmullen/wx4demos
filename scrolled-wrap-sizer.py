import wx
import wx.lib.scrolledpanel as scrolled


class SizeReportCtrl(wx.Control):
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                size=wx.DefaultSize):
        wx.Control.__init__(self, parent, id, pos, size, style=wx.NO_BORDER)

        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.on_erase_background)
        self.Bind(wx.EVT_SIZE, self.on_size)

    def on_paint(self, event):
        dc = wx.PaintDC(self)
        size = self.GetClientSize()
        dc.SetFont(wx.NORMAL_FONT)
        dc.SetBrush(wx.WHITE_BRUSH)
        dc.SetPen(wx.WHITE_PEN)
        dc.DrawRectangle(0, 0, size.x, size.y)
        dc.SetPen(wx.LIGHT_GREY_PEN)
        dc.DrawLine(0, 0, size.x, size.y)
        dc.DrawLine(0, size.y, size.x, 0)

        print(f"on_paint: id={self.GetId()}")

        s = f"Id: {self.GetId()}"
        w, height = dc.GetTextExtent(s)
        height += 3
        dc.DrawText(s, (size.x-w)/2, (size.y//2 - height))

        s = f"Size: {size.x} x {size.y}"
        w, height = dc.GetTextExtent(s)
        height += 3
        dc.DrawText(s, (size.x-w)/2, (size.y//2 + height))

    def on_erase_background(self, event):
        pass

    def on_size(self, event):
        self.Refresh()


class ScrolledWrapPanel(scrolled.ScrolledPanel):
    def __init__(self, parent):
        scrolled.ScrolledPanel.__init__(self, parent, -1)

        wsizer = wx.WrapSizer(orient=wx.HORIZONTAL)
        for i in range(1000):
            btn = SizeReportCtrl(self, -1, size=(200,100))
            wsizer.Add(btn, 0, wx.ALL, 4)

        self.SetSizer(wsizer)
        self.SetAutoLayout(1)
        self.SetupScrolling(scroll_x=False)

        self.Bind(wx.EVT_SIZE, self.on_size)

    def on_size(self, evt):
        print("size!", evt.GetSize())
        size = self.GetSize()
        vsize = self.GetVirtualSize()
        self.SetVirtualSize((size[0], vsize[1]))
        evt.Skip()


class DemoFrame(wx.Frame):
    """ This window displays a button """
    def __init__(self, title = "Micro App"):
        wx.Frame.__init__(self, None , -1, title)

        btn = wx.Button(self, -1, "Do Stuff")
        btn.Bind(wx.EVT_BUTTON, self.on_stuff )

        panel = ScrolledWrapPanel(self)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(btn, 0, wx.ALIGN_CENTER|wx.ALL, 5)
        sizer.Add(panel, 1, wx.GROW)
        
        self.SetSizer(sizer)

    def on_stuff(self, evt):
        print("Stuff!")


if __name__ == "__main__":
    app = wx.App(False)
    frame = DemoFrame()
    frame.Show()
    app.MainLoop()
