import wx
import wx.lib.editor
import wx.lib.editor.selection as selection

class FakeList(object):
    def __init__(self, count):
        self.num_items = count

    def __len__(self):
        return self.num_items

    def __getitem__(self, item):
        print(item, type(item))
        try:
            return "0A 0X 0Y FF sv-bdizc  00 00 00 LDA $%04x" % ((item * 4) + 0x600)
        except:
            return "slice"


class FixedFontDataWindow(wx.lib.editor.Editor):
    def __init__(self, parent, num_lines):
        wx.lib.editor.Editor.__init__(self, parent, -1)
        self.SetText(FakeList(num_lines))

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


if __name__ == "__main__":
    app = wx.App()

    frame = wx.Frame(None, -1, "Test", size=(400,400))
    s = FixedFontDataWindow(frame, 1000)
    frame.Show(True)
    app.MainLoop()
