#!/usr/bin/env python2.5

"""
a small test of initializing a wxImage from a numpy array
"""


import wx
import wx.adv
import numpy as np
import numpy.random as rand

import colormap
import colormap.ui_combobox

class ImagePanel(wx.Panel):
    """ 
    A very simple panel for displaying a wx.Image
    """
    def __init__(self, image, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)
        
        self.image = image
        self.Bind(wx.EVT_PAINT, self.OnPaint)
    
    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        dc.DrawBitmap(wx.BitmapFromImage(self.image), 0, 0)
        

class DemoFrame(wx.Frame):
    """ This window displays a button """
    def __init__(self, title = "Micro App"):
        wx.Frame.__init__(self, None , -1, title)

        MenuBar = wx.MenuBar()
        FileMenu = wx.Menu()

        item = FileMenu.Append(wx.ID_ANY, "&Open")
        self.Bind(wx.EVT_MENU, self.OnOpen, item)

        item = FileMenu.Append(wx.ID_PREFERENCES, "&Preferences")
        self.Bind(wx.EVT_MENU, self.OnPrefs, item)

        item = FileMenu.Append(wx.ID_EXIT, "&Exit")
        self.Bind(wx.EVT_MENU, self.OnQuit, item)

        MenuBar.Append(FileMenu, "&File")
        
        HelpMenu = wx.Menu()

        item = HelpMenu.Append(wx.ID_HELP, "Test &Help",
                                "Help for this simple test")
        self.Bind(wx.EVT_MENU, self.OnHelp, item)

        ## this gets put in the App menu on OS-X
        item = HelpMenu.Append(wx.ID_ABOUT, "&About",
                                "More information About this program")
        self.Bind(wx.EVT_MENU, self.OnAbout, item)
        MenuBar.Append(HelpMenu, "&Help")

        self.SetMenuBar(MenuBar)

        self.Bind(wx.EVT_CLOSE, self.OnQuit)

        
        c = colormap.ui_combobox.ColormapComboBox(self, -1, "", size=(300,30), style=wx.CB_READONLY)
        #c.Bind(wx.EVT_COMBOBOX, self.colormap_changed)
        c.SetSelection(10)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(c, 0, wx.ALIGN_CENTER|wx.ALL, 5)

        self.SetSizer(sizer)

    def OnQuit(self,Event):
        self.Destroy()
        
    def OnAbout(self, event):
        dlg = wx.MessageDialog(self, "This is a small program to test\n"
                                     "the use of menus on Mac, etc.\n",
                                "About Me", wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    def OnHelp(self, event):
        dlg = wx.MessageDialog(self, "This would be help\n"
                                     "If there was any\n",
                                "Test Help", wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    def OnOpen(self, event):
        dlg = wx.MessageDialog(self, "This would be an open Dialog\n"
                                     "If there was anything to open\n",
                                "Open File", wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    def OnPrefs(self, event):
        dlg = wx.MessageDialog(self, "This would be an preferences Dialog\n"
                                     "If there were any preferences to set.\n",
                                "Preferences", wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

if __name__ == "__main__":
    print "\n".join(colormap.list_colormaps())
    app = wx.App(False)
    frame = DemoFrame()
    frame.Show()
    app.MainLoop()
