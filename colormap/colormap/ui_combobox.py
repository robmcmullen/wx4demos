import wx
import wx.adv
import numpy as np
import numpy.random as rand

from . import list_colormaps, get_rgb_colors


class ColormapComboBox(wx.adv.OwnerDrawnComboBox):
    def __init__(self, *args, **kwargs):
        self.colormap_names = list_colormaps()
        kwargs['choices'] = self.colormap_names
        wx.adv.OwnerDrawnComboBox.__init__(self, *args, **kwargs)
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
        colors = get_rgb_colors(self.colormap_names[index], self.line)
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
