import time

import wx
import numpy as np

import hexview

# Check wxpython demo for Editor to see a pure-python implementation of an on-
# demand renderer for lines of text: wx.lib.editor

class DummyScroller(object):
    def SetScrollbars(self, *args, **kwargs):
        pass

class AuxWindow(wx.ScrolledWindow):
    def __init__(self, parent, scroll_source, label_char_width=10):
        wx.ScrolledWindow.__init__(self, parent, -1)
        self.scroll_source = scroll_source
        self.label_char_width = label_char_width
        self.isDrawing = False
        self.EnableScrolling(False, False)
        self.ShowScrollbars(wx.SHOW_SB_NEVER, wx.SHOW_SB_NEVER)

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_MOUSEWHEEL, self.scroll_source.settings_obj.on_mouse_wheel)

    def OnSize(self, event):
        self.AdjustScrollbars()
        self.SetFocus()

    def UpdateView(self, dc = None):
        if dc is None:
            dc = wx.ClientDC(self)
        if dc.IsOk():
            self.Draw(dc)

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        if self.isDrawing:
            return
        self.isDrawing = True
        self.UpdateView(dc)
        self.isDrawing = False

    def OnEraseBackground(self, evt):
        pass


class LeftAuxWindow(AuxWindow):
    def DrawVertText(self, t, line, dc):
        s = self.scroll_source
        y = (line - s.sy) * s.cell_height_in_pixels
        dc.DrawText(t, 0, y)

    def Draw(self, odc=None):
        if not odc:
            odc = wx.ClientDC(self)

        dc = wx.BufferedDC(odc)
        s = self.scroll_source
        if dc.IsOk():
            dc.SetFont(s.settings_obj.header_font)
            dc.SetBackgroundMode(wx.SOLID)
            dc.SetTextBackground(s.settings_obj.row_header_bg_color)
            dc.SetTextForeground(s.settings_obj.text_color)
            dc.SetBackground(wx.Brush(s.settings_obj.row_header_bg_color))
            dc.Clear()
            for line, header in self.scroll_source.table.get_row_label_text(s.sy, s.sh):
                if s.IsLine(line):
                    self.DrawVertText(header, line, dc)

class TopAuxWindow(AuxWindow):
    def DrawHorzText(self, t, sx, num_cells, dc):
        s = self.scroll_source
        x = (sx - s.sx) * s.cell_width_in_pixels
        width = len(t) * s.fw
        offset = ((s.cell_width_in_pixels * num_cells) - width)/2  # center text in cell
        dc.DrawText(t, x + offset, 0)

    def Draw(self, odc=None):
        if not odc:
            odc = wx.ClientDC(self)

        dc = wx.BufferedDC(odc)
        s = self.scroll_source
        if dc.IsOk():
            dc.SetFont(s.settings_obj.header_font)
            dc.SetBackgroundMode(wx.SOLID)
            dc.SetTextBackground(s.settings_obj.col_header_bg_color)
            dc.SetTextForeground(s.settings_obj.text_color)
            dc.SetBackground(wx.Brush(s.settings_obj.col_header_bg_color))
            dc.Clear()
            for cell, num_cells, header in self.scroll_source.table.get_col_labels(s.sx):
                self.DrawHorzText(header, cell, num_cells, dc)


class TableViewParams(object):
    col_label_border_width = 3
    row_label_border_width = 3
    row_height_extra_padding = -3
    base_cell_width_in_chars = 2
    pixel_width_padding = 2
    label_char_width = 4


class HexGridWindow(wx.ScrolledWindow):
    def __init__(self, grid_cls, table, *args, **kwargs):
        wx.ScrolledWindow.__init__ (self, *args, **kwargs)
        self.SetAutoLayout(True)

        self.background_color = wx.WHITE
        self.text_color = wx.BLACK
        self.row_header_bg_color = wx.Colour(224, 224, 224)
        self.col_header_bg_color = wx.Colour(224, 224, 224)
        self.highlight_color = wx.Colour(100, 200, 230)
        self.unfocused_cursor_color = (128, 128, 128)
        self.data_color = (224, 224, 224)
        attr = self.GetDefaultAttributes()
        self.empty_color = attr.colBg.Get(False)
        self.match_background_color = (255, 255, 180)
        self.comment_background_color = (255, 180, 200)
        self.diff_text_color = (255, 0, 0)
        self.cursor_pen = wx.Pen(self.unfocused_cursor_color, 1, wx.SOLID)
        self.scroll_delay = 30  # milliseconds

        self.text_font = self.NiceFontForPlatform()
        self.header_font = wx.Font(self.text_font).MakeBold()

        self.update_dependents = self.update_dependents_null
        self.view_params = TableViewParams()
        self.main = grid_cls(self, self, table, self.view_params)
        self.top = TopAuxWindow(self, self.main)
        self.left = LeftAuxWindow(self, self.main)
        sizer = wx.FlexGridSizer(2,2,0,0)
        self.corner = sizer.Add(5, 5, 0, wx.EXPAND)
        sizer.Add(self.top, 0, wx.EXPAND)
        sizer.Add(self.left, 0, wx.EXPAND)
        sizer.Add(self.main, 0, wx.EXPAND)
        sizer.AddGrowableCol(1)
        sizer.AddGrowableRow(1)
        self.SetSizer(sizer)
        self.SetTargetWindow(self.main)
        self.set_pane_sizes(3000, 1000)
        self.SetBackgroundColour(self.col_header_bg_color)
        #self.SetScrollRate(20,20)
        self.Bind(wx.EVT_MOUSEWHEEL, self.on_mouse_wheel)
        self.Bind(wx.EVT_SCROLLWIN, self.on_scroll_window)
        self.Bind(wx.EVT_LEFT_UP, self.on_left_up)

        self.ShowScrollbars(wx.SHOW_SB_ALWAYS, wx.SHOW_SB_ALWAYS)
        self.main.ShowScrollbars(wx.SHOW_SB_NEVER, wx.SHOW_SB_NEVER)
        self.top.ShowScrollbars(wx.SHOW_SB_NEVER, wx.SHOW_SB_NEVER)
        self.left.ShowScrollbars(wx.SHOW_SB_NEVER, wx.SHOW_SB_NEVER)
        self.update_dependents = self.update_dependents_post_init

    def NiceFontForPlatform(self):
        point_size = 10
        family = wx.DEFAULT
        style = wx.NORMAL
        weight = wx.NORMAL
        underline = False
        if wx.Platform == "__WXMAC__":
            face_name = "Monaco"
        elif wx.Platform == "__WXMSW__":
            face_name = "Lucida Console"
        else:
            face_name = "monospace"
        font = wx.Font(point_size, family, style, weight, underline, face_name)
        return font

    def on_left_up(self, event):
        print()
        print("Title " + str(self))
        print("Position " + str(self.GetPosition()))
        print("Size " + str(self.GetSize()))
        print("VirtualSize " + str(self.GetVirtualSize()))
        event.Skip()
       
    def set_pane_sizes(self, width, height):
        """
        Set the size of the 3 panes as follow:
            - main = width, height
            - top = width, 40
            - left = 80, height
        """
        top_height = self.main.cell_height_in_pixels + self.view_params.col_label_border_width
        left_width = self.view_params.label_char_width * self.main.fw + self.view_params.row_label_border_width
        self.main.SetVirtualSize(wx.Size(width,height))
        #(wt, ht) = self.top.GetSize()
        self.top.SetVirtualSize(wx.Size(width, top_height))
        #(wl, hl) = self.left.GetSize()
        self.left.SetVirtualSize(wx.Size(left_width, height))
        self.corner.SetMinSize(left_width, top_height)
        #self.Layout()
        wx.CallAfter(self.main.SetScrollManager, self)

    def HorizScroll(self, event, eventType):
        if eventType == wx.wxEVT_SCROLLWIN_LINEUP:
            self.main.sx -= 1
        elif eventType == wx.wxEVT_SCROLLWIN_LINEDOWN:
            self.main.sx += 1
        elif eventType == wx.wxEVT_SCROLLWIN_PAGEUP:
            self.main.sx -= self.main.sw
        elif eventType == wx.wxEVT_SCROLLWIN_PAGEDOWN:
            self.main.sx += self.main.sw
        elif eventType == wx.wxEVT_SCROLLWIN_TOP:
            self.main.sx = self.main.cx = 0
        elif eventType == wx.wxEVT_SCROLLWIN_BOTTOM:
            self.main.sx = self.main.max_line_len - self.main.sw
            self.main.cx = self.main.max_line_len
        else:
            self.main.sx = event.GetPosition()

        self.main.HorizBoundaries()

    def VertScroll(self, event, eventType):
        if   eventType == wx.wxEVT_SCROLLWIN_LINEUP:
            self.main.sy -= 1
        elif eventType == wx.wxEVT_SCROLLWIN_LINEDOWN:
            self.main.sy += 1
        elif eventType == wx.wxEVT_SCROLLWIN_PAGEUP:
            self.main.sy -= self.main.sh
        elif eventType == wx.wxEVT_SCROLLWIN_PAGEDOWN:
            self.main.sy += self.main.sh
        elif eventType == wx.wxEVT_SCROLLWIN_TOP:
            self.main.sy = self.main.cy = 0
        elif eventType == wx.wxEVT_SCROLLWIN_BOTTOM:
            self.main.sy = self.main.LinesInFile() - self.main.sh
            self.main.cy = self.main.LinesInFile()
        elif eventType == wx.wxEVT_MOUSEWHEEL:
            # Not a normal scroll event. Wheel scrolling is handled by the
            # scrolled window by a wxEVT_SCROLLWIN_THUMBTRACK, but on GTK its
            # internal value didn't match the scrollbar so it was getting
            # repositioned. This value is only received through the call to
            # on_mouse_wheel below.
            if event < 0:
                self.main.sy += 4
            else:
                self.main.sy -= 4
        else:
            self.main.sy = event.GetPosition()

        self.main.VertBoundaries()

    def on_scroll_window(self, event):
        dir = event.GetOrientation()
        eventType = event.GetEventType()
        if dir == wx.HORIZONTAL:
            self.HorizScroll(event, eventType)
        else:
            self.VertScroll(event, eventType)
        self.main.UpdateView()

    def on_mouse_wheel(self, evt):
        w = evt.GetWheelRotation()
        if evt.ControlDown():
            if w < 0:
                self.main.zoom_out()
            elif w > 0:
                self.main.zoom_in()
        elif not evt.ShiftDown() and not evt.AltDown():
            self.VertScroll(w, wx.wxEVT_MOUSEWHEEL)
            self.main.UpdateView()
        else:
            evt.Skip()

    def update_dependents_null(self):
        pass

    def update_dependents_post_init(self):
        self.top.UpdateView()
        self.left.UpdateView()

    def set_data(self, data, *args, **kwargs):
        self.main.set_data(data, *args, **kwargs)


class MyApp(wx.App):
    """
    Simple Application class for testing
    """
    def OnInit(self):
        """
        Initialize the Application
        """
        #This is the frame as I want to use it, with a tri-pane scroll window
        #However, the information sent to the sub-window is incorrect, so the
        #on_paint callback draws the wrong area on screen...
        id = wx.NewId()
        frame = wx.Frame(None, id, "Test Text Grid" )
        splitter = wx.SplitterWindow(frame, -1, style = wx.SP_LIVE_UPDATE)
        splitter.SetMinimumPaneSize(20)
        table = hexview.VariableWidthHexTable(np.arange(1024, dtype=np.uint8), 4, 0x602, [1, 2, 3, 4])
        scroll1 = HexGridWindow(hexview.FixedFontMultiCellNumpyWindow, table, splitter)
        table = hexview.HexTable(np.arange(1024, dtype=np.uint8), 16, 0x602)
        scroll2 = HexGridWindow(hexview.FixedFontNumpyWindow, table, splitter)

        splitter.SplitVertically(scroll1, scroll2)
        #(width, height) = dc.GetTextExtent("M")

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(splitter, 1, wx.EXPAND)

        focusbtn = wx.Button(frame, -1, "Press to set focus to TextCtrl")
        sizer.Add(focusbtn, 0, wx.EXPAND)
        focusbtn.Bind(wx.EVT_BUTTON, self.set_focus)

        frame.SetSizer(sizer)
        frame.Layout()

        self.t1 = wx.TextCtrl(frame, -1, "Test it out and see", size=(100,10), pos=(40,-40))
        self.t1.Bind(wx.EVT_TEXT, self.EvtText)
        self.t1.Bind(wx.EVT_CHAR, self.EvtChar)
        #wx.CallAfter(self.t1.Hide)

        frame.Show()
        # self.SetTopWindow(frame)
       
        print("wx.VERSION = " + wx.VERSION_STRING)
        return True

    def set_focus(self, evt):
        #self.t1.Hide()
        self.t1.SetFocus()

    def EvtText(self, event):
        print(('EvtText: %s' % event.GetString()))

    def EvtTextEnter(self, event):
        print('EvtTextEnter')
        event.Skip()

    def EvtChar(self, event):
        print(('EvtChar: %d' % event.GetKeyCode()))
        event.Skip()
       
#For testing
if __name__ == '__main__':
    app = MyApp(False)
    app.MainLoop()
