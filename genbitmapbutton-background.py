import wx
import wx.lib.buttons as buttons

class MainFrame(wx.Frame):

#----------------------------------------------------------------------
    def __init__(self):

        wx.Frame.__init__(self, None, title="Test",size=(800,800))
        panel = wx.Panel(self,-1,name="panel")  

        bmp = wx.Bitmap("Discord.png", wx.BITMAP_TYPE_ANY)

        self.Button1 = buttons.GenBitmapButton(panel,bitmap=bmp,pos=(200,400),size=(bmp.GetWidth()+10, bmp.GetHeight()+10),style=wx.NO_BORDER,name="Button1")
        self.Button1.SetBackgroundColour("Blue")

        self.Button2 = buttons.GenBitmapButton(panel,bitmap=bmp,pos=(600,400),size=(bmp.GetWidth()+10, bmp.GetHeight()+10),style=wx.NO_BORDER,name="Button2")
        self.Button2.SetBackgroundColour("Blue")
        self.Bind(wx.EVT_BUTTON, self.OnClick)

        self.BitmapButtons = [self.Button1,self.Button2]
        self.Show()

    def OnClick(self,event):
        parent = event.GetEventObject().GetParent().GetName()
        name = event.GetEventObject().GetName()

        if parent == "panel":
            for i in range(0,len(self.BitmapButtons)):
                buttonName = self.BitmapButtons[i].GetName()
                if buttonName == name:
                    self.BitmapButtons[i].SetBackgroundColour("Green")
                else:
                    self.BitmapButtons[i].SetBackgroundColour("Blue")


#----------------------------------------------------------------------
if __name__ == "__main__":
      app = wx.App(False)
      frame = MainFrame()
      app.MainLoop()
