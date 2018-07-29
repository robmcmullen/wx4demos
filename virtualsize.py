import wx

app = wx.App()

frame = wx.Frame(None, -1, "Test", size=(400,400))
s = wx.ScrolledWindow(frame, -1)
w = wx.Window(frame, -1)
frame.Show(True)
print(("scrolled GetVirtualSize: %s" % type(s.GetVirtualSize())))
print(("window GetVirtualSize: %s" % type(w.GetVirtualSize())))
app.MainLoop()
