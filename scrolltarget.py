import wx 
import time 


# This is a test for a scrollable canvas, with some top and left sliding 
# sub-windows. Similar to the way a spreadsheet works... 

class TriPaneWindow(wx.ScrolledWindow): 
    """ 
    This is the main frame holding the other windows and the top level of the 
    application 
    """ 
    
    def __init__(self, *arguments, **keywords): 
        """ 
        Constructor 
        """ 
        wx.ScrolledWindow.__init__ (self, *arguments, **keywords) 
        self.SetAutoLayout(True) 
        self.SetSizer(self.buildSizer()) 
        self.SetTargetWindow(self.mainPanel) 
        self.SetScrollRate(20,20) 

        #Events 
        #wx.EVT_SIZE(self, self.OnSize) 
        self.Bind(wx.EVT_SCROLLWIN, self.OnScrollWindowEvent) 
        self.Bind(wx.EVT_LEFT_UP, self.OnClickEvent) 
        
    def OnClickEvent(self, event): 
        """ 
        For Debug... 
        """ 
        print() 
        print("Title " + str(self))
        print("Position " + str(self.GetPosition())) 
        print("Size " + str(self.GetSize())) 
        print("VirtualSize " + str(self.GetVirtualSize())) 
        event.Skip() 
        
                      
    def buildSizer(self): 
        """ 
        Create the 3 sub windows and the sizer that holds them together. 
        """ 
        #Create the panels 
        self.topPanel = MyCanvas(self, wx.RED, 40,40, 'Top', True, False) 
        self.leftPanel = MyCanvas(self, wx.GREEN, 80,80, 'Left', False, True) 
        self.mainPanel = MyCanvas(self, wx.WHITE, 100,100, 'Main', True, True) 
        self.mainPanel.topPanel = self.topPanel 
        self.mainPanel.leftPanel = self.leftPanel 
        self.topPanel.mainPanel = self.mainPanel
        self.leftPanel.mainPanel = self.mainPanel
        self.mainPanel.mainPanel = self.mainPanel
        self.topPanel.parentPanel = self
        self.leftPanel.parentPanel = self
        self.mainPanel.parentPanel = self
        
        #Create the sizer 
        sizer = wx.FlexGridSizer(2,2,0,0) 
        
        #Add the panels to the sizers 
        sizer.Add((100,30), 0, wx.EXPAND) 
        sizer.Add(self.topPanel, 0, wx.EXPAND) 
        sizer.Add(self.leftPanel, 0, wx.EXPAND) 
        sizer.Add(self.mainPanel, 0, wx.EXPAND) 
        sizer.AddGrowableCol(1) 
        sizer.AddGrowableRow(1) 
        
        return sizer 
        
    def SetCanvasSize(self, width, height): 
        """ 
        Set the size of the 3 panes as follow: 
            - main = width, height 
            - top = width, 40 
            - left = 80, height 
        """ 
        self.mainPanel.SetVirtualSize(wx.Size(width,height)) 
        (w,h) = self.topPanel.GetSize() 
        self.topPanel.SetVirtualSize(wx.Size(width,h)) 
        (w,h) = self.leftPanel.GetSize() 
        self.leftPanel.SetVirtualSize(wx.Size(w,height)) 
    
        
    def OnScrollWindowEvent(self, event): 
        """ 
        OnScrollWindow Event Callback. This should let the main panel scroll in 
        both direction but transmit the vertical scrolling to the left panel 
        and the horizontal scrolling to the top window 
        """
        sx,sy = self.GetScrollPixelsPerUnit()
        if event.GetOrientation() == wx.HORIZONTAL:
            dx = event.GetPosition()
            dy = self.GetScrollPos(wx.VERTICAL)
        else:
            dx = self.GetScrollPos(wx.HORIZONTAL)
            dy = event.GetPosition()
        
        pos = (dx ,dy) 
        print("scrolling..." + str(pos) + str(event.GetPosition()))
        # self.mainPanel.Scroll(dx, dy) 
        # self.topPanel.Scroll(dx, 0) 
        # self.leftPanel.Scroll(0, dy) 
        event.Skip() 


class MyCanvas(wx.ScrolledCanvas): 
    """ 
    Custom colored panel for testing 
    """ 
    def __init__(self, parent, colour, width, height, name = "", dx=True, dy=True): 
        wx.ScrolledCanvas.__init__(self, parent, -1) 
        self.SetBackgroundColour(colour) 
        self.SetSize(wx.Size(width, height)) 
        self.SetVirtualSize(wx.Size(width, height)) 
        self.use_x = 1 if dx else 0
        self.use_y = 1 if dy else 0
        self.Bind(wx.EVT_LEFT_DOWN, self.OnClickEvent) 
        self.Bind(wx.EVT_PAINT, self.OnPaint) 
        self.Bind(wx.EVT_SIZE, self.on_size) 

    def on_size(self, event ): 
        """ 
        OnSize event callback. Currently not used 
        """ 
        print("Size " + str(self.GetSize())) 
        print("VirtualSize " + str(self.GetVirtualSize()))
        size = self.GetSize()
        vsize = self.GetVirtualSize()
        if self.use_x and self.use_y:
            # main window, no adjustment
            pass
        elif self.use_x:
            # scrolls in X dir
            self.SetVirtualSize(vsize.x, size.y)
        else:
            self.SetVirtualSize(size.x, vsize.y)

        #self.Layout() 

    def OnPaint(self, event):

        dc = wx.PaintDC(self)
        #self.parentPanel.PrepareDC(dc)
        size = self.GetVirtualSize()

        s = "Size: %d x %d"%(size.x, size.y)
        vbX, vbY = self.parentPanel.GetViewStart()
        posX, posY = self.parentPanel.CalcUnscrolledPosition (0, 0)
        vbX, vbY = vbX * self.use_x, vbY * self.use_y
        posX, posY = posX * self.use_x, posY * self.use_y
        # vbX, vbY = self.GetViewStart()
        # posX, posY = self.CalcUnscrolledPosition (0, 0) 
        upd = wx.RegionIterator(self.GetUpdateRegion())  # get the update rect list
        r = []
        while upd.HaveRects():
            rect = upd.GetRect()

            # Repaint this rectangle
            #PaintRectangle(rect, dc)
            r.append("rect: %s" % str(rect))
            upd.Next()
        print(s, (posX, posY), (vbX, vbY), " ".join(r))
        dc.SetLogicalOrigin(posX, posY)

        dc.SetFont(wx.NORMAL_FONT)
        w, height = dc.GetTextExtent(s)
        height += 3
        dc.SetBrush(wx.WHITE_BRUSH)
        dc.SetPen(wx.WHITE_PEN)
        dc.DrawRectangle(0, 0, size.x, size.y)
        dc.SetPen(wx.LIGHT_GREY_PEN)
        dc.DrawLine(0, 0, size.x, size.y)
        dc.DrawLine(0, size.y, size.x, 0)
        dc.DrawText(s, (size.x-w)/2, (size.y-height*5)/2)
      
    def OnClickEvent(self, event): 
        print() 
        print("Title " + str(self))
        print("Position " + str(self.GetPosition())) 
        print("ViewStart " + str(self.GetViewStart())) 
        print("Size " + str(self.GetSize())) 
        print("VirtualSize " + str(self.GetVirtualSize())) 


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
        #OnPaint callback draws the wrong area on screen... 
        id = wx.NewId() 
        frame = wx.Frame(None, id, "Test Tri-pane frame" ) 
        scroll = TriPaneWindow(frame, wx.NewId()) 
        scroll.SetCanvasSize(3000, 1000) 
        scroll.SetScrollRate(20,20) 
        frame.Show() 
        # self.SetTopWindow(frame) 
        
        print("wx.VERSION = " + wx.VERSION_STRING) 
        return True 
        
#For testing 
if __name__ == '__main__': 
    app = MyApp(False) 
    app.MainLoop() 
