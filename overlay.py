#!/usr/bin/env python

from collections import OrderedDict

import wx

#---------------------------------------------------------------------------

def calc_bitmap_of_window(win):
    """ Takes a screenshot of the screen at give pos & size (rect). """
    rect = win.GetRect()
    print 'Taking screenshot... of %s' % str(rect)
    # see http://aspn.activestate.com/ASPN/Mail/Message/wxpython-users/3575899
    # created by Andrea Gavana

    sx, sy = win.ClientToScreen((0, 0))
    rect.x = sx
    rect.y = sy

    #Create a DC for the whole screen area
    dcScreen = wx.ScreenDC()

    try:
        print("trying screenDC subbitmap: %s" % str(rect))
        drag_bitmap = dcScreen.GetAsBitmap().GetSubBitmap(rect)
    except wx.wxAssertionError:
        print("creating bitmap manually")
        #Create a Bitmap that will hold the screenshot image later on
        #Note that the Bitmap must have a size big enough to hold the screenshot
        #-1 means using the current default colour depth
        drag_bitmap = wx.Bitmap(rect.width, rect.height)
 
        #Create a memory DC that will be used for actually taking the screenshot
        memDC = wx.MemoryDC()
 
        #Tell the memory DC to use our Bitmap
        #all drawing action on the memory DC will go to the Bitmap now
        memDC.SelectObject(drag_bitmap)
 
        #Blit (in this case copy) the actual screen on the memory DC
        #and thus the Bitmap
        memDC.Blit( 0, #Copy to this X coordinate
                    0, #Copy to this Y coordinate
                    rect.width, #Copy this width
                    rect.height, #Copy this height
                    dcScreen, #From where do we copy?
                    sx, #What's the X offset in the original DC?
                    sy  #What's the Y offset in the original DC?
                    )
 
        #Select the Bitmap out of the memory DC by selecting a new
        #uninitialized Bitmap
        memDC.SelectObject(wx.NullBitmap)
    return rect, drag_bitmap


class BitmapPopup(wx.PopupWindow):
    """Adds a bit of text and mouse movement to the wx.PopupWindow"""
    def __init__(self, parent, pos, style=wx.SIMPLE_BORDER):
        wx.PopupWindow.__init__(self, parent, style)
        self.SetBackgroundColour("CADET BLUE")
        
        rect, self.bitmap = calc_bitmap_of_window(parent)
        x, y = parent.ClientToScreen(pos)
        rect.x = x
        rect.y = y
        self.SetSize(rect)
        self.Show()

        self.Bind(wx.EVT_PAINT, self.on_paint)

    def on_paint(self, evt):
        dc = wx.PaintDC(self)
        dc.DrawBitmap(self.bitmap, 0, 0)


class DockingRectangleHandler(object):
    def __init__(self):
        self.use_transparency = True
        self.overlay = None
        self.docking_rectangles = []
        self.event_window = None
        self.drag_window = None
        self.pen = wx.Pen(wx.BLUE)
        brush_color = wx.Colour(0xb0, 0xb0, 0xff, 0x80)
        self.brush = wx.Brush(brush_color)

    def start_docking(self, event_window, drag_window, event):
        # Capture the mouse and save the starting posiiton for the rubber-band
        event_window.CaptureMouse()
        event_window.SetFocus()
        self.event_window = event_window
        self.drag_window = BitmapPopup(drag_window, event.GetPosition())
        self.overlay = wx.Overlay()
        self.overlay.Reset()
        self.create_docking_rectangles(self.event_window)

    def create_docking_rectangles(self, event_window):
        rects = []
        for win in [event_window]:
            rects.extend(self.create_docking_rectangle_for_window(win))
        self.docking_rectangles = rects

    def create_docking_rectangle_for_window(self, win):
        rects = []
        win_rect = win.GetClientRect()
        w = win_rect.width // 4
        h = win_rect.height // 4
        t = win_rect.x + win_rect.height - h
        r = win_rect.y + win_rect.width - w
        rects.append(wx.Rect(win_rect.x, win_rect.y, w, win_rect.height))
        rects.append(wx.Rect(win_rect.x, win_rect.y, win_rect.width, h))
        rects.append(wx.Rect(r, win_rect.y, w, win_rect.height))
        rects.append(wx.Rect(win_rect.x, t, win_rect.width, h))
        return rects

    def process_dragging(self, event):
        pos = event.GetPosition()

        for rect in self.docking_rectangles:
            print("checking %s in rect %s" % (pos, rect))
            if rect.Contains(pos):
                break
        else:
            print("NOT IN RECT")
            rect = None

        dc = wx.ClientDC(self.event_window)
        odc = wx.DCOverlay(self.overlay, dc)
        odc.Clear()

        if wx.Platform == "__WXGTK__":
            # Copy background to overlay; otherwise the overlay seems to be
            # black? I don't know what I'm doing wrong to need this hack.
            dc.DrawBitmap(self.drag_window.bitmap, 0, 0)

        # Mac already using GCDC
        if 'wxMac' not in wx.PlatformInfo and self.use_transparency:
            dc = wx.GCDC(dc)

        if rect is not None:
            dc.SetPen(self.pen)
            dc.SetBrush(self.brush)
            dc.DrawRectangle(rect)

        pos = self.event_window.ClientToScreen(pos)
        self.drag_window.SetPosition(pos)

        del odc  # Make sure the odc is destroyed before the dc is.


    def cleanup_docking(self, evt):
        if self.event_window.HasCapture():
            self.event_window.ReleaseMouse()
        pos = evt.GetPosition()

        # When the mouse is released we reset the overlay and it
        # restores the former content to the window.
        dc = wx.ClientDC(self.event_window)
        odc = wx.DCOverlay(self.overlay, dc)
        odc.Clear()
        del odc
        self.overlay.Reset()
        self.overlay = None

        self.drag_window.Destroy()
        self.drag_window = None
        self.event_window.Refresh()  # Force redraw

        return pos


class TestPanel(wx.Panel):
    def __init__(self, parent, log):
        self.log = log
        wx.Panel.__init__(self, parent, wx.ID_ANY, style=wx.CLIP_CHILDREN)

        ## self.SetDoubleBuffered(True)

        self.background = wx.Brush(wx.WHITE)
        self.SetBackgroundColour(wx.RED)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_SIZE, self.OnSize)

        #--Rubberband Overlay
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_MOTION, self.OnMouseMove)
        self.dock_handler = DockingRectangleHandler()

        self.overlayPenWidth = wx.SpinCtrl(self, -1, value='',
                                           size=(75, -1),
                                           style=wx.SP_ARROW_KEYS,
                                           min=1, max=24, initial=1)
        # self.overlayPenWidth.SetToolTip('Pen Width')

        from wx.lib.colourselect import ColourSelect
        self.overlayPenColor = ColourSelect(self, -1, colour=wx.BLUE)
        # self.overlayPenColor.SetToolTip('Pen Color')

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.overlayPenWidth, 0, wx.ALL, 5)
        sizer.Add(self.overlayPenColor, 0, wx.ALL, 5)
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(sizer, 0)
        box.Add((1,1), 1)

        self.SetSizer(box)

        self.OnSize()

    def OnLeftDown(self, event):
        self.dock_handler.start_docking(self, self, event)

    def OnMouseMove(self, event):
        if event.Dragging() and event.LeftIsDown():
            self.dock_handler.process_dragging(event)

    def OnLeftUp(self, event):
        self.dock_handler.cleanup_docking(event)


    def OnSize(self, event=None):
        if event:
            event.Skip()

        x, y = self.GetSize()
        if x <= 0 or y <= 0:
            return

        self.buffer = wx.Bitmap(x, y)

        dc = wx.MemoryDC()
        dc.SelectObject(self.buffer)
        dc.SetBrush(wx.WHITE_BRUSH)
        dc.SetPen(wx.WHITE_PEN)
        dc.DrawRectangle(0, 0, x, y)

        dc.SetFont(wx.Font(wx.FontInfo(18)))
        dc.DrawText('Drag the mouse on this window.', 325, 100)

        del dc
        self.Refresh()
        #self.Update()

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        rect = self.GetClientRect()
        dc.DestroyClippingRegion()
        dc.SetClippingRegion(rect)
        print("painting", rect, dc.GetClippingRect())
        dc.SetBrush(wx.WHITE_BRUSH)
        dc.SetPen(wx.WHITE_PEN)
        dc.DrawRectangle(rect)

        dc.SetFont(wx.Font(wx.FontInfo(18)))
        dc.DrawText('Drag the mouse on this window.', 325, 100)
        event.Skip()

    def OnEraseBackground(self, evt):
        pass


if __name__ == "__main__":
    class DemoFrame(wx.Frame):
        def __init__(self, title = "Micro App"):
            wx.Frame.__init__(self, None , -1, title)

            btn = wx.Button(self, -1, "Do Stuff")
            btn.Bind(wx.EVT_BUTTON, self.on_stuff )

            panel = TestPanel(self, -1)
            
            sizer = wx.BoxSizer(wx.VERTICAL)
            sizer.Add(btn, 0, wx.ALIGN_CENTER|wx.ALL, 5)
            sizer.Add(panel, 1, wx.GROW)
            
            self.SetSizer(sizer)

        def on_stuff(self, evt):
            print("Stuff!")

    app = wx.App(False)
    frame = DemoFrame()
    frame.Show()
    app.MainLoop()
