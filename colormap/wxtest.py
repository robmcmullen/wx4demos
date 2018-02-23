#!/usr/bin/env python2.5

"""
a small test of initializing a wxImage from a numpy array
"""


import wx
import wx.adv
import numpy as np
import numpy.random as rand

import colormap


class ColormapComboBox(wx.adv.OwnerDrawnComboBox):
    def __init__(self, *args, **kwargs):
        wx.adv.OwnerDrawnComboBox.__init__(self, *args, **kwargs)
        self.colormap_names = colormap.list_colormaps()
        self.line = np.arange(256, dtype=np.float32) / 255.0
        self.height = 20
        self.width = 256
        self.array = np.empty((self.height, self.width, 3), dtype='uint8')
        self.image = wx.ImageFromBuffer(self.width, self.height, self.array)
        dc = wx.MemoryDC()
        self.char_height = dc.GetCharHeight()
        self.internal_spacing = 2
        self.item_height = self.height + self.char_height + 2 * self.internal_spacing
        self.item_width = self.width + 2 * self.internal_spacing
        self.bitmap_x = self.internal_spacing
        self.bitmap_y = self.char_height + self.internal_spacing

    # Overridden from OwnerDrawnComboBox, called to draw each
    # item in the list
    def OnDrawItem(self, dc, rect, item, flags):
        if item == wx.NOT_FOUND:
            # painting the control, but there is no valid item selected yet
            return

        r = wx.Rect(*rect)  # make a copy

        b = self.get_colormap_bitmap(item)
        if flags & wx.adv.ODCB_PAINTING_CONTROL:
            x = (r.width - self.item_width) // 2
            y = (r.height - self.height) // 2
            dc.DrawBitmap(b, r.x + x, r.y + y)
        else:
            dc.DrawText(self.colormap_names[item], r.x + self.bitmap_x, r.y)
            dc.DrawBitmap(b, r.x + self.bitmap_x, r.y + self.bitmap_y)

    def get_colormap_bitmap(self, index):
        self.line = np.arange(256, dtype=np.float32)/ 255.0
        colors = colormap.get_rgb_colors(self.colormap_names[index], self.line)
        self.array[:,:,:] = colors
        return wx.BitmapFromImage(self.image)

    # Overridden from OwnerDrawnComboBox, called for drawing the
    # background area of each item.
    def OnDrawBackground(self, dc, rect, item, flags):
        # If the item is selected, or its item # iseven, or we are painting the
        # combo control itself, then use the default rendering.
        if (flags & wx.adv.ODCB_PAINTING_CONTROL):
            flags = flags & ~(wx.adv.ODCB_PAINTING_CONTROL | wx.adv.ODCB_PAINTING_SELECTED)
        wx.adv.OwnerDrawnComboBox.OnDrawBackground(self, dc, rect, item, flags)

    # Overridden from OwnerDrawnComboBox, should return the height
    # needed to display an item in the popup, or -1 for default
    def OnMeasureItem(self, item):
        return self.item_height

    # Overridden from OwnerDrawnComboBox.  Callback for item width, or
    # -1 for default/undetermined
    def OnMeasureItemWidth(self, item):
        return self.item_width


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

        self.colormap_names = colormap.list_colormaps()
        self.colormap_index = 0

        ##Create numpy array, and image from it
        w = 256
        h = 32
        self.line = np.arange(256, dtype=np.float32)/ 255.0
        colors = colormap.get_rgb_colors(self.colormap_names[self.colormap_index], self.line)
        self.array = np.empty((h, w, 3), dtype='uint8')
        self.array[:,:,:] = colors
        print self.array.shape
        image = wx.ImageFromBuffer(w, h, self.array)
        #image = wx.Image("Images/cute_close_up.jpg")
        self.Panel = ImagePanel(image, self)
        
        c = ColormapComboBox(self, -1, "", choices=self.colormap_names, size=(300,30), style=wx.CB_READONLY)
        #c.Bind(wx.EVT_COMBOBOX, self.colormap_changed)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(btn, 0, wx.ALIGN_CENTER|wx.ALL, 5)
        sizer.Add(self.Panel, 1, wx.GROW)
        sizer.Add(c, 0, wx.ALIGN_CENTER|wx.ALL, 5)

        self.SetSizer(sizer)

    def OnNewImage(self, event=None):
        """
        create a new image by changing underlying numpy array
        """
        self.colormap_index += 1
        colors = colormap.get_rgb_colors(self.colormap_names[self.colormap_index], self.line)
        self.array[:,:,:] = colors
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

if __name__ == "__main__":
    print "\n".join(colormap.list_colormaps())
    app = wx.App(False)
    frame = DemoFrame()
    frame.Show()
    app.MainLoop()
