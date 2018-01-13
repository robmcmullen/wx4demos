import wx
import wx.html
import wx.lib.agw.aui as aui

ID_SampleItem = wx.ID_HIGHEST + 1


class HtmlWindow(wx.html.HtmlWindow):
    def __init__(self, parent):
        print("calling HtmlWindow constructor")
        wx.html.HtmlWindow.__init__(self, parent, -1, style=wx.NO_FULL_REPAINT_ON_RESIZE)
        print("setting HtmlWindow fonts")
        self.SetStandardFonts()


class AuiFrame(wx.Frame):

    def __init__(self, parent, id=wx.ID_ANY, title="", pos= wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.DEFAULT_FRAME_STYLE|wx.SUNKEN_BORDER, log=None):

        wx.Frame.__init__(self, parent, id, title, pos, size, style)
        self._mgr = aui.AuiManager()
        
        # tell AuiManager to manage this frame
        self._mgr.SetManagedWindow(self)
        
        # create some toolbars
        tb1 = aui.AuiToolBar(self, -1, wx.DefaultPosition, wx.DefaultSize, agwStyle= aui.AUI_TB_DEFAULT_STYLE|aui.AUI_TB_VERTICAL)
        tb1.SetToolBitmapSize(wx.Size(48, 48))
        tb1.AddSimpleTool(ID_SampleItem+1, "Test", wx.ArtProvider.GetBitmap(wx.ART_ERROR))
        tb1.AddSeparator()
        tb1.AddSimpleTool(ID_SampleItem+2, "Test", wx.ArtProvider.GetBitmap(wx.ART_QUESTION))
        tb1.AddSimpleTool(ID_SampleItem+3, "Test", wx.ArtProvider.GetBitmap(wx.ART_INFORMATION))
        tb1.AddSimpleTool(ID_SampleItem+4, "Test", wx.ArtProvider.GetBitmap(wx.ART_WARNING))
        tb1.AddSimpleTool(ID_SampleItem+5, "Test", wx.ArtProvider.GetBitmap(wx.ART_MISSING_IMAGE))
        #tb1.SetCustomOverflowItems(prepend_items, append_items)
        tb1.Realize() 
               
        # Add toolbar
        self._mgr.AddPane(tb1,
                          aui.AuiPaneInfo().Name("Iconbar")
                          .ToolbarPane()
                          .Left()
                          .Gripper(False)
                          .Floatable(False)
                          .Dockable(False)
                          )        
        
        # Create some center pane
        center = HtmlWindow(self)
        self._mgr.AddPane(center, aui.AuiPaneInfo().Name("Center").CenterPane())        
        
        # create default perspective
        all_panes = self._mgr.GetAllPanes()
        for ii in xrange(len(all_panes)):
            if not all_panes[ii].IsToolbar():
                all_panes[ii].Hide()
        self._mgr.GetPane("Center").Show()
        perspective_default = self._mgr.SavePerspective()
        print perspective_default
        # If this is True the toolbar unexpectedly gets a gripper
        if True:            
            self._mgr.LoadPerspective(perspective_default)  
                    
        print self._mgr.GetPane("iconbar").HasGripper()
        self._mgr.Update()

def main():
    wxapp = wx.App(redirect=False)
    frame = AuiFrame(None, -1, "AUI Test Frame", size=(800, 600))
    frame.CenterOnScreen()
    frame.Show()        
    wxapp.MainLoop()
    
if __name__ == '__main__':
    main()