import wx
import wx.lib.scrolledpanel as scrolled


text = "one two buckle my shoe three four shut the door five six pick up sticks seven eight lay them straight nine ten big fat hen"

class ScrolledWrapPanel(scrolled.ScrolledPanel):
    def __init__(self, parent):
        scrolled.ScrolledPanel.__init__(self, parent, -1)

        wsizer = wx.WrapSizer(orient=wx.HORIZONTAL)
        for word in text.split():
            btn = wx.Button(self, -1, word, size=(200,100))
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
