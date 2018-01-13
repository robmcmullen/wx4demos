import wx
import wx.html

app = wx.App()
import wx.lib.wxpTag

import wx.adv

frame = wx.Frame(None, -1, "Test", size=(400,400))
html = wx.html.HtmlWindow(frame, -1)
frame.Show(True)
app.MainLoop()
