#!/usr/bin/env python2.5

"""
a small test of initializing a wxImage from a numpy array
"""
import random

import wx
import numpy as np
import numpy.random as rand


def displace(height_map):
    height_map[:,:] = 128
    divide(height_map, height_map.shape[0]-1)

def divide(height_map, size, roughness=.6):
    half = size // 2;
    scale = int(roughness * size);
    if (half < 1):
        return

    for y in range(half, height_map.shape[0]-1, size):
        for x in range(half, height_map.shape[1]-1, size):
            square(height_map, x, y, half, random.randint(-scale, scale))

    for y in range(0, height_map.shape[0]-1, half):
        for x in range((y + half) % size, height_map.shape[1]-1, size):
            diamond(height_map, x, y, half, random.randint(-scale, scale))

    divide(height_map, size // 2, roughness)

def square(m, x, y, size, offset):
    print(f"square: x={x} y={y}, size={size}, offset={offset}")
    avg = (m[y-size,x-size] + m[y-size,x+size] + m[y+size,x+size] + m[y+size,x-size]) // 4
    m[y, x] = avg + offset

def diamond(m, x, y, size, offset):
    print(f"diamond: x={x} y={y}, size={size}, offset={offset}")
    avg = (m[y-size,x] + m[y+size,x] + m[y,x+size] + m[y,x-size]) // 4
    m[y, x] = avg + offset


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

        btn = wx.Button(self, label = "NewImage")
        btn.Bind(wx.EVT_BUTTON, self.OnNewImage )

        self.Bind(wx.EVT_CLOSE, self.OnQuit)

        ##Create numpy array, and image from it
        self.height_map = np.zeros((256, 256), dtype=np.uint8)
        h, w = self.height_map.shape
        self.array = np.zeros((h, w, 3), dtype='uint8')

        displace(self.height_map)
        self.Panel = None
        self.set_image()
        print(self.array.shape)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(btn, 0, wx.ALIGN_CENTER|wx.ALL, 5)
        sizer.Add(self.Panel, 1, wx.GROW)
        
        self.SetSizer(sizer)

    def set_image(self):
        h, w = self.height_map.shape
        self.array = np.zeros((h, w, 3), dtype='uint8')
        self.array[:,:,0] = self.height_map
        self.array[:,:,1] = self.height_map
        self.array[:,:,2] = self.height_map
        print(self.array.shape)
        image = wx.ImageFromBuffer(w, h, self.array)
        self.Panel = ImagePanel(image, self)

    def OnNewImage(self, event=None):
        """
        create a new image by changing underlying numpy array
        """
        displace(self.height_map)
        self.array[:,:,0] = self.height_map
        self.array[:,:,1] = self.height_map
        self.array[:,:,2] = self.height_map
        self.Panel.Refresh()
        
        
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

app = wx.App(False)
frame = DemoFrame()
frame.Show()
app.MainLoop()
