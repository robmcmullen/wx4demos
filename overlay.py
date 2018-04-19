#!/usr/bin/env python

from collections import OrderedDict

import wx

#---------------------------------------------------------------------------


class TestPanel(wx.Panel):
    def __init__(self, parent, log):
        self.log = log
        wx.Panel.__init__(self, parent, wx.ID_ANY, style=wx.CLIP_CHILDREN)

        ## self.SetDoubleBuffered(True)

        self.background = wx.Brush(self.GetBackgroundColour())
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)

        #--Rubberband Overlay
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_MOTION, self.OnMouseMove)
        self.startPos = None
        self.endPos = None
        self.overlay = wx.Overlay()

        self.drag_bitmap = None

        self.overlayPenWidth = wx.SpinCtrl(self, -1, value='',
                                           size=(75, -1),
                                           style=wx.SP_ARROW_KEYS,
                                           min=1, max=24, initial=1)
        self.overlayPenWidth.SetToolTip('Pen Width')

        from wx.lib.colourselect import ColourSelect
        self.overlayPenColor = ColourSelect(self, -1, colour=wx.BLUE)
        self.overlayPenColor.SetToolTip('Pen Color')

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.overlayPenWidth, 0, wx.ALL, 5)
        sizer.Add(self.overlayPenColor, 0, wx.ALL, 5)
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(sizer, 0)
        box.Add((1,1), 1)

        self.SetSizer(box)

        self.OnSize()


    def make_bitmap(self):
        """ Takes a screenshot of the screen at give pos & size (rect). """
        rect = self.GetRect()
        print 'Taking screenshot... of %s' % str(rect)
        # see http://aspn.activestate.com/ASPN/Mail/Message/wxpython-users/3575899
        # created by Andrea Gavana
 
        sx, sy = self.ClientToScreen((0, 0))
        rect.x += sx
        rect.y += sy

        #Create a DC for the whole screen area
        dcScreen = wx.ScreenDC()
 
        #Create a Bitmap that will hold the screenshot image later on
        #Note that the Bitmap must have a size big enough to hold the screenshot
        #-1 means using the current default colour depth
        self.drag_bitmap = wx.Bitmap(rect.width, rect.height)
 
        #Create a memory DC that will be used for actually taking the screenshot
        memDC = wx.MemoryDC()
 
        #Tell the memory DC to use our Bitmap
        #all drawing action on the memory DC will go to the Bitmap now
        memDC.SelectObject(self.drag_bitmap)
 
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


    def OnLeftDown(self, event):
        # Capture the mouse and save the starting posiiton for the rubber-band
        self.CaptureMouse()
        self.startPos = event.GetPosition()
        ## print('self.startPos:', self.startPos)
        self.SetFocus()
        self.make_bitmap()
        ## print('OnLeftDown')


    def OnMouseMove(self, event):
        if event.Dragging() and event.LeftIsDown():
            evtPos = event.GetPosition()

            try:
                rect = wx.Rect(topLeft=self.startPos, bottomRight=evtPos)
            except TypeError as exc:  # topLeft = NoneType. Attempting to double click image or something
                return
            except Exception as exc:
                raise exc

            # Draw the rubber-band rectangle using an overlay so it
            # will manage keeping the rectangle and the former window
            # contents separate.
            dc = wx.ClientDC(self)
            odc = wx.DCOverlay(self.overlay, dc)
            odc.Clear()

            # Mac's DC is already the same as a GCDC, and it causes
            # problems with the overlay if we try to use an actual
            # wx.GCDC so don't try it.  If you do not need to use a
            # semi-transparent background then you can leave this out.
            if 'wxMac' not in wx.PlatformInfo:
                dc = wx.GCDC(dc)

            # Set the pen, for the box's border
            dc.SetPen(wx.Pen(colour=self.overlayPenColor.GetColour(),
                             width=self.overlayPenWidth.GetValue(),
                             style=wx.PENSTYLE_SOLID))

            # Create a brush (for the box's interior) with the same colour,
            # but 50% transparency.
            bc = self.overlayPenColor.GetColour()
            bc = wx.Colour(bc.red, bc.green, bc.blue, 0x80)
            dc.SetBrush(wx.Brush(bc))

            # Draw the rectangle
            dc.DrawRectangle(rect)

            dc.DrawBitmap(self.drag_bitmap, evtPos[0], evtPos[1])

            del odc  # Make sure the odc is destroyed before the dc is.
            ## print('OnMouseMove')


    def OnLeftUp(self, event):
        if self.HasCapture():
            self.ReleaseMouse()
        self.endPos = event.GetPosition()
        ## print('StartPos: %s' %self.startPos)
        ## print('EndPos: %s' %self.endPos)
        self.startPos = None
        self.endPos = None

        # When the mouse is released we reset the overlay and it
        # restores the former content to the window.
        dc = wx.ClientDC(self)
        odc = wx.DCOverlay(self.overlay, dc)
        odc.Clear()
        del odc
        self.overlay.Reset()
        ## print('OnLeftUp')


    def OnSize(self, event=None):
        if event:
            event.Skip()

        x, y = self.GetSize()
        if x <= 0 or y <= 0:
            return

        self.buffer = wx.Bitmap(x, y)

        dc = wx.MemoryDC()
        dc.SelectObject(self.buffer)
        dc.SetBackground(self.background)
        dc.Clear()

        dc.SetFont(wx.Font(wx.FontInfo(18)))
        dc.DrawText('Drag the mouse on this window.', 325, 100)

        del dc
        self.Refresh()
        #self.Update()

    def OnPaint(self, event):
        dc = wx.BufferedPaintDC(self, self.buffer)


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
