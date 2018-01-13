import wx
from wx.lib.expando import ExpandoTextCtrl

class MainFrame(wx.Frame):

#----------------------------------------------------------------------
    def __init__(self):

        wx.Frame.__init__(self, None, title="Test",size=(800,800))
        self.parent = wx.Panel(self,-1,name="panel")  
        self.ctrl = self.create_control()
        self.ctrl2 = self.create_control()
        self.fill_data(self.ctrl)
        self.fill_data(self.ctrl2)
        self.Show()

    def fill_data(self, ctrl):
        text, color = self.get_error_text(ctrl)
        # FIXME: commented out background color changes due to crash in
        # wxPython:
        #

        if color is None:
            attr = self.parent.GetDefaultAttributes()
            color = wx.Colour(attr.colBg)
        print("SOHEURCOESUHOEUH", color, type(color))
        ctrl.SetBackgroundColour(color)
        ctrl.SetValue(str(text))
        print("Set text to: %s" % text)

    def get_error_text(self, ctrl):
        if ctrl == self.ctrl2:
            return "ctrl2", None
        return "test", wx.Colour((244,244,244))

    def create_control(self):
        c = ExpandoTextCtrl(self.parent, style=wx.ALIGN_LEFT | wx.TE_READONLY | wx.NO_BORDER)
        return c


#----------------------------------------------------------------------
if __name__ == "__main__":
      app = wx.App(False)
      frame = MainFrame()
      app.MainLoop()
