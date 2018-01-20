import time

import wx
import wx.lib.editor
import wx.lib.editor.selection as selection

def ForceBetween(min, val, max):
    if val  > max:
        return max
    if val < min:
        return min
    return val

class Scroller:
    def __init__(self, parent):
        self.parent = parent
        self.ow = None
        self.oh = None
        self.ox = None
        self.oy = None

    def SetScrollbars(self, fw, fh, w, h, x, y):
        if (self.ow != w or self.oh != h or self.ox != x or self.oy != y):
            print("Setting scrollbar to: %s" % str([fw, fh, w, h, x, y]))
            self.parent.SetScrollbars(fw, fh, w, h, x, y)
            self.ow = w
            self.oh = h
            self.ox = x
            self.oy = y

class FakeList(object):
    def __init__(self, count):
        self.num_items = count

    def __len__(self):
        return self.num_items

    def __getitem__(self, item):
        #print(item, type(item))
        try:
            #return "0A 0X 0Y FF sv-bdizc  00 00 00 LDA $%04x" % ((item * 4) + 0x600)
            return "c0f3 f4e1 f2f4 cdcd cdcd 48ad c602 1869"
        except:
            return "slice"


class OldFixedFontDataWindow(wx.lib.editor.Editor):
    def __init__(self, parent, num_lines):
        wx.lib.editor.Editor.__init__(self, parent, -1)
        self.SetText(FakeList(num_lines))

    def SetScrollManager(self, parent):
        self.scroller = Scroller(parent)
        self.AdjustScrollbars()

    #### Overrides

    def CalcMaxLineLen(self):
        return 64

    def DrawEditText(self, t, x, y, dc):
        dc.DrawText(t, x * self.fw, y * self.fh)

    def DrawLine(self, sy, line, dc):
        if self.IsLine(line):
            l   = line
            t   = self.lines[l]
            dc.SetTextForeground(self.fgColor)
            fragments = selection.Selection(
                self.SelectBegin, self.SelectEnd,
                self.sx, self.sw, line, t)
            x = 0
            for (data, selected) in fragments:
                if selected:
                    dc.SetTextBackground(self.selectColor)
                    if x == 0 and len(data) == 0 and len(fragments) == 1:
                        data = ' '
                else:
                    dc.SetTextBackground(self.bgColor)
                self.DrawEditText(data, x, sy - self.sy, dc)
                x += len(data)

    def Draw(self, odc=None):
        if not odc:
            odc = wx.ClientDC(self)

        dc = wx.BufferedDC(odc)
        if dc.IsOk():
            dc.SetFont(self.font)
            dc.SetBackgroundMode(wx.SOLID)
            dc.SetTextBackground(self.bgColor)
            dc.SetTextForeground(self.fgColor)
            dc.SetBackground(wx.Brush(self.bgColor))
            dc.Clear()
            for line in range(self.sy, self.sy + self.sh + 1):
                self.DrawLine(line, line, dc)
            if len(self.lines) < self.sh + self.sy:
                self.DrawEofMarker(dc)
            self.DrawCursor(dc)



class FixedFontDataWindow(wx.ScrolledWindow):
    def __init__(self, parent, num_lines):

        wx.ScrolledWindow.__init__(self, parent, -1, style=wx.WANTS_CHARS)

        self.isDrawing = False

        self.InitCoords()
        self.InitFonts()
        self.SetColors()
        self.MapEvents()
        self.InitDoubleBuffering()
        self.InitScrolling(parent)
        self.SelectOff()
        self.SetFocus()
        self.SetText(FakeList(num_lines))
        self.SpacesPerTab = 4

##------------------ Init stuff

    def InitCoords(self):
        self.cx = 0
        self.cy = 0
        self.oldCx = 0
        self.oldCy = 0
        self.sx = 0
        self.sy = 0
        self.sw = 0
        self.sh = 0
        self.sco_x = 0
        self.sco_y = 0

    def MapEvents(self):
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_SCROLLWIN, self.OnScroll)
        #self.Bind(wx.EVT_CHAR, self.OnChar)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnDestroy)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)

##------------------- Platform-specific stuff

    def NiceFontForPlatform(self):
        if wx.Platform == "__WXMSW__":
            font = wx.Font(10, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        else:
            font = wx.Font(12, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False)
        return font

##-------------------- UpdateView/Cursor code

    def OnSize(self, event):
        self.AdjustScrollbars()
        self.SetFocus()

    def SetCharDimensions(self):
        # TODO: We need a code review on this.  It appears that Linux
        # improperly reports window dimensions when the scrollbar's there.
        self.bw, self.bh = self.GetClientSize()

        if wx.Platform == "__WXMSW__":
            self.sh = int(self.bh / self.fh)
            self.sw = int(self.bw / self.fw) - 1
        else:
            self.sh = int(self.bh / self.fh)
            if self.LinesInFile() >= self.sh:
                self.bw = self.bw - wx.SystemSettings.GetMetric(wx.SYS_VSCROLL_X)
                self.sw = int(self.bw / self.fw) - 1

            self.sw = int(self.bw / self.fw) - 1
            if self.CalcMaxLineLen() >= self.sw:
                self.bh = self.bh - wx.SystemSettings.GetMetric(wx.SYS_HSCROLL_Y)
                self.sh = int(self.bh / self.fh)

    def UpdateView(self, dc = None):
        if dc is None:
            dc = wx.ClientDC(self)
        if dc.IsOk():
            self.SetCharDimensions()
            print("scroll:", self.sx, self.sy, "cursor", self.cx, self.cy)
            if self.Selecting:
                self.KeepCursorOnScreen()
            else:
                self.AdjustScrollbars()
            self.DrawSimpleCursor(0,0, dc, True)
            self.Draw(dc)
            self.parent_scrolled_window.update_dependents()

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        if self.isDrawing:
            return
        self.isDrawing = True
        self.UpdateView(dc)
        wx.CallAfter(self.AdjustScrollbars)
        self.isDrawing = False

    def OnEraseBackground(self, evt):
        pass

##-------------------- Drawing code

    def InitFonts(self):
        dc = wx.ClientDC(self)
        self.font = self.NiceFontForPlatform()
        dc.SetFont(self.font)
        self.fw = dc.GetCharWidth()
        self.fh = dc.GetCharHeight()

    def SetColors(self):
        self.fgColor = wx.BLACK
        self.bgColor = wx.WHITE
        self.selectColor = wx.Colour(238, 220, 120)  # r, g, b = emacsOrange

    def InitDoubleBuffering(self):
        pass

##-------- Enforcing screen boundaries, cursor movement

    def KeepCursorOnScreen(self):
        self.sy = ForceBetween(max(0, self.cy-self.sh), self.sy, self.cy)
        self.sx = ForceBetween(max(0, self.cx-self.sw), self.sx, self.cx)
        self.AdjustScrollbars()

    def HorizBoundaries(self):
        self.SetCharDimensions()
        maxLineLen = self.CalcMaxLineLen()
        self.sx = ForceBetween(0, self.sx, max(self.sw, maxLineLen - self.sw + 1))

    def VertBoundaries(self):
        self.SetCharDimensions()
        self.sy = ForceBetween(0, self.sy, max(self.sh, self.LinesInFile() - self.sh + 1))

    def cVert(self, num):
        self.cy = self.cy + num
        self.cy = ForceBetween(0, self.cy, self.LinesInFile() - 1)
        self.sy = ForceBetween(self.cy - self.sh + 1, self.sy, self.cy)
        self.cx = min(self.cx, self.CurrentLineLength())

    def cHoriz(self, num):
        self.cx = self.cx + num
        self.cx = ForceBetween(0, self.cx, self.CurrentLineLength())
        self.sx = ForceBetween(self.cx - self.sw + 1, self.sx, self.cx)

    def AboveScreen(self, row):
        return row < self.sy

    def BelowScreen(self, row):
        return row >= self.sy + self.sh

    def LeftOfScreen(self, col):
        return col < self.sx

    def RightOfScreen(self, col):
        return col >= self.sx + self.sw

##----------------- data structure helper functions

    def GetText(self):
        return self.lines

    def SetText(self, lines):
        self.InitCoords()
        self.lines = lines
        self.AdjustScrollbars()
        self.UpdateView(None)

    def IsLine(self, lineNum):
        return (0<=lineNum) and (lineNum<self.LinesInFile())

    def GetTextLine(self, lineNum):
        if self.IsLine(lineNum):
            return self.lines[lineNum]
        return ""

    def CurrentLineLength(self):
        return len(self.lines[self.cy])

    def LinesInFile(self):
        return len(self.lines)

##-------------------------- Mouse scroll timing functions

    def InitScrolling(self, parent):
        # we don't rely on the windows system to scroll for us; we just
        # redraw the screen manually every time
        self.parent_scrolled_window = parent
        self.EnableScrolling(False, False)
        self.nextScrollTime = 0
        self.SCROLLDELAY = 0.050 # seconds
        self.scrollTimer = wx.Timer(self)
        self.scroller = Scroller(self)

    def SetScrollManager(self, parent):
        self.scroller = Scroller(parent)
        self.AdjustScrollbars()

    def CanScroll(self):
       if time.time() >  self.nextScrollTime:
           self.nextScrollTime = time.time() + self.SCROLLDELAY
           return True
       else:
           return False

    def SetScrollTimer(self):
        oneShot = True
        self.scrollTimer.Start(1000*self.SCROLLDELAY/2, oneShot)
        self.Bind(wx.EVT_TIMER, self.OnTimer)

    def OnTimer(self, event):
        screenX, screenY = wx.GetMousePosition()
        x, y = self.ScreenToClient((screenX, screenY))
        self.MouseToRow(y)
        self.MouseToCol(x)
        self.SelectUpdate()

##-------------------------- Mouse off screen functions

    def HandleAboveScreen(self, row):
        self.SetScrollTimer()
        if self.CanScroll():
            row = self.sy - 1
            row = max(0, row)
            self.cy = row

    def HandleBelowScreen(self, row):
        self.SetScrollTimer()
        if self.CanScroll():
            row = self.sy + self.sh + 1
            row  = min(row, self.LinesInFile() - 1)
            self.cy = row

    def HandleLeftOfScreen(self, col):
        self.SetScrollTimer()
        if self.CanScroll():
            col = self.sx - 1
            col = max(0,col)
            self.cx = col

    def HandleRightOfScreen(self, col):
        self.SetScrollTimer()
        if self.CanScroll():
            col = self.sx + self.sw
            col = min(col, self.CurrentLineLength())
            self.cx = col

##------------------------ mousing functions

    def MouseToRow(self, mouseY):
        row  = self.sy + int(mouseY / self.fh)
        if self.AboveScreen(row):
            self.HandleAboveScreen(row)
        elif self.BelowScreen(row):
            self.HandleBelowScreen(row)
        else:
            self.cy  = min(row, self.LinesInFile() - 1)

    def MouseToCol(self, mouseX):
        col = self.sx + int(mouseX / self.fw)
        if self.LeftOfScreen(col):
            self.HandleLeftOfScreen(col)
        elif self.RightOfScreen(col):
            self.HandleRightOfScreen(col)
        else:
            self.cx = min(col, self.CurrentLineLength())

    def MouseToCursor(self, event):
        self.MouseToRow(event.GetY())
        self.MouseToCol(event.GetX())

    def OnMotion(self, event):
        if event.LeftIsDown() and self.HasCapture():
            self.Selecting = True
            self.MouseToCursor(event)
            self.SelectUpdate()

    def OnLeftDown(self, event):
        self.MouseToCursor(event)
        self.SelectBegin = (self.cy, self.cx)
        self.SelectEnd = None
        self.UpdateView()
        self.CaptureMouse()
        self.SetFocus()

    def OnLeftUp(self, event):
        if not self.HasCapture():
            return

        if self.SelectEnd is None:
            self.OnClick()
        else:
            self.Selecting = False
            self.SelectNotify(False, self.SelectBegin, self.SelectEnd)

        self.ReleaseMouse()
        self.scrollTimer.Stop()


#------------------------- Scrolling

    def HorizScroll(self, event, eventType):
        maxLineLen = self.CalcMaxLineLen()

        if eventType == wx.wxEVT_SCROLLWIN_LINEUP:
            self.sx -= 1
        elif eventType == wx.wxEVT_SCROLLWIN_LINEDOWN:
            self.sx += 1
        elif eventType == wx.wxEVT_SCROLLWIN_PAGEUP:
            self.sx -= self.sw
        elif eventType == wx.wxEVT_SCROLLWIN_PAGEDOWN:
            self.sx += self.sw
        elif eventType == wx.wxEVT_SCROLLWIN_TOP:
            self.sx = self.cx = 0
        elif eventType == wx.wxEVT_SCROLLWIN_BOTTOM:
            self.sx = maxLineLen - self.sw
            self.cx = maxLineLen
        else:
            self.sx = event.GetPosition()

        self.HorizBoundaries()

    def VertScroll(self, event, eventType):
        if   eventType == wx.wxEVT_SCROLLWIN_LINEUP:
            self.sy -= 1
        elif eventType == wx.wxEVT_SCROLLWIN_LINEDOWN:
            self.sy += 1
        elif eventType == wx.wxEVT_SCROLLWIN_PAGEUP:
            self.sy -= self.sh
        elif eventType == wx.wxEVT_SCROLLWIN_PAGEDOWN:
            self.sy += self.sh
        elif eventType == wx.wxEVT_SCROLLWIN_TOP:
            self.sy = self.cy = 0
        elif eventType == wx.wxEVT_SCROLLWIN_BOTTOM:
            self.sy = self.LinesInFile() - self.sh
            self.cy = self.LinesInFile()
        else:
            self.sy = event.GetPosition()

        self.VertBoundaries()

    def OnScroll(self, event):
        dir = event.GetOrientation()
        eventType = event.GetEventType()
        if dir == wx.HORIZONTAL:
            self.HorizScroll(event, eventType)
        else:
            self.VertScroll(event, eventType)
        self.UpdateView()


    def AdjustScrollbars(self):
        if self:
            self.SetCharDimensions()
            self.scroller.SetScrollbars(
                self.fw, self.fh,
                self.CalcMaxLineLen()+3, max(self.LinesInFile()+1, self.sh),
                self.sx, self.sy)
        else:
            print("NOT ADJUSTING SCROLLBARS!")

#-------------- Keyboard movement implementations

    def MoveDown(self, event):
        self.cVert(+1)

    def MoveUp(self, event):
        self.cVert(-1)

    def MoveLeft(self, event):
        if self.cx == 0:
            if self.cy == 0:
                wx.Bell()
            else:
                self.cVert(-1)
                self.cx = self.CurrentLineLength()
        else:
            self.cx -= 1

    def MoveRight(self, event):
        linelen = self.CurrentLineLength()
        if self.cx == linelen:
            if self.cy == len(self.lines) - 1:
                wx.Bell()
            else:
                self.cx = 0
                self.cVert(1)
        else:
            self.cx += 1

    def MovePageDown(self, event):
        self.cVert(self.sh)

    def MovePageUp(self, event):
        self.cVert(-self.sh)

    def MoveHome(self, event):
        self.cx = 0

    def MoveEnd(self, event):
        self.cx = self.CurrentLineLength()

    def MoveStartOfFile(self, event):
        self.cy = 0
        self.cx = 0

    def MoveEndOfFile(self, event):
        self.cy = len(self.lines) - 1
        self.cx = self.CurrentLineLength()

##----------- selection routines

    def SelectUpdate(self):
        self.SelectEnd = (self.cy, self.cx)
        self.SelectNotify(self.Selecting, self.SelectBegin, self.SelectEnd)
        self.UpdateView()

    def SelectOff(self):
        self.SelectBegin = None
        self.SelectEnd = None
        self.Selecting = False
        self.SelectNotify(False,None,None)

#----------------------- Eliminate memory leaks

    def OnDestroy(self, event):
        self.mdc = None
        self.odc = None
        self.bgColor = None
        self.fgColor = None
        self.font = None
        self.selectColor = None
        self.scrollTimer = None
        self.eofMarker = None

#--------------------  Abstract methods for subclasses

    def OnClick(self):
        pass

    def SelectNotify(self, Selecting, SelectionBegin, SelectionEnd):
        pass

    #### Overrides

    def CalcMaxLineLen(self):
        return 64

    def DrawCursor(self, dc = None):
        if not dc:
            dc = wx.ClientDC(self)

        if (self.LinesInFile())<self.cy: #-1 ?
            self.cy = self.LinesInFile()-1
        s = self.lines[self.cy]

        x = self.cx - self.sx
        y = self.cy - self.sy
        self.DrawSimpleCursor(x, y, dc)

    def DrawSimpleCursor(self, xp, yp, dc = None, old=False):
        if not dc:
            dc = wx.ClientDC(self)

        if old:
            xp = self.sco_x
            yp = self.sco_y

        szx = self.fw
        szy = self.fh
        x = xp * szx
        y = yp * szy
        dc.Blit(x,y, szx,szy, dc, x,y, wx.XOR)
        self.sco_x = xp
        self.sco_y = yp

    def DrawEditText(self, t, x, y, dc):
        dc.DrawText(t, x * self.fw, y * self.fh)

    def DrawLine(self, sy, line, dc):
        if self.IsLine(line):
            l   = line
            t   = self.lines[l]
            dc.SetTextForeground(self.fgColor)
            fragments = selection.Selection(
                self.SelectBegin, self.SelectEnd,
                self.sx, self.sw, line, t)
            x = 0
            for (data, selected) in fragments:
                if selected:
                    dc.SetTextBackground(self.selectColor)
                    if x == 0 and len(data) == 0 and len(fragments) == 1:
                        data = ' '
                else:
                    dc.SetTextBackground(self.bgColor)
                self.DrawEditText(data, x, sy - self.sy, dc)
                x += len(data)

    def Draw(self, odc=None):
        if not odc:
            odc = wx.ClientDC(self)

        dc = wx.BufferedDC(odc)
        if dc.IsOk():
            dc.SetFont(self.font)
            dc.SetBackgroundMode(wx.SOLID)
            dc.SetTextBackground(self.bgColor)
            dc.SetTextForeground(self.fgColor)
            dc.SetBackground(wx.Brush(self.bgColor))
            dc.Clear()
            for line in range(self.sy, self.sy + self.sh + 1):
                self.DrawLine(line, line, dc)
            self.DrawCursor(dc)


if __name__ == "__main__":
    app = wx.App()

    frame = wx.Frame(None, -1, "Test", size=(400,400))
    s = FixedFontDataWindow(frame, 1000)
    frame.Show(True)
    app.MainLoop()