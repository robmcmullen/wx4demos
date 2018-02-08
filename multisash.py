#----------------------------------------------------------------------
# Name:         multisash
# Purpose:      Multi Sash control
#
# Author:       Gerrit van Dyk
#
# Created:      2002/11/20
# Version:      0.1
# License:      wxWindows license
#----------------------------------------------------------------------
# 12/09/2003 - Jeff Grimmett (grimmtooth@softhome.net)
#
# o 2.5 compatibility update.
#
# 12/20/2003 - Jeff Grimmett (grimmtooth@softhome.net)
#
# o wxMultiSash -> MultiSash
# o wxMultiSplit -> MultiSplit
# o wxMultiViewLeaf -> MultiViewLeaf
#

import wx

import six
MV_HOR = 0
MV_VER = not MV_HOR

SH_SIZE = 5
CR_SIZE = SH_SIZE * 3

#----------------------------------------------------------------------

class MultiSash(wx.Window):
    def __init__(self, *_args,**_kwargs):
        wx.Window.__init__(self, *_args, **_kwargs)
        self._defChild = EmptyChild
        self.child = MultiSplit(self,self,(0,0),self.GetSize())
        self.Bind(wx.EVT_SIZE,self.OnMultiSize)

    def SetDefaultChildClass(self,childCls):
        self._defChild = childCls
        self.child.DefaultChildChanged()

    def OnMultiSize(self,evt):
        self.child.SetSize(self.GetSize())

    def UnSelect(self):
        self.child.UnSelect()

    def Clear(self):
        old = self.child
        self.child = MultiSplit(self,self,(0,0),self.GetSize())
        old.Destroy()
        self.child.OnSize(None)

    def GetSaveData(self):
        saveData = {}
        saveData['_defChild_class'] = self._defChild.__name__
        saveData['_defChild_mod']   = self._defChild.__module__
        saveData['child'] = self.child.GetSaveData()
        return saveData

    def SetSaveData(self,data):
        mod = data['_defChild_mod']
        dChild = mod + '.' + data['_defChild_class']
        six.exec_('import %s' % mod)
        self._defChild = eval(dChild)
        old = self.child
        self.child = MultiSplit(self,self,wx.Point(0,0),self.GetSize())
        self.child.SetSaveData(data['child'])
        old.Destroy()
        self.OnMultiSize(None)
        self.child.OnSize(None)


#----------------------------------------------------------------------


class MultiSplit(wx.Window):
    def __init__(self,multiView,parent,pos,size,view1 = None):
        wx.Window.__init__(self,id = -1,parent = parent,pos = pos,size = size,
                          style = wx.CLIP_CHILDREN)
        self.multiView = multiView
        self.view2 = None
        if view1:
            self.view1 = view1
            self.view1.Reparent(self)
            self.view1.Move(0,0)
        else:
            self.view1 = MultiViewLeaf(self.multiView,self,
                                         (0,0),self.GetSize())
        self.direction = None

        self.Bind(wx.EVT_SIZE,self.OnSize)

    def GetSaveData(self):
        saveData = {}
        if self.view1:
            saveData['view1'] = self.view1.GetSaveData()
            if isinstance(self.view1,MultiSplit):
                saveData['view1IsSplit'] = 1
        if self.view2:
            saveData['view2'] = self.view2.GetSaveData()
            if isinstance(self.view2,MultiSplit):
                saveData['view2IsSplit'] = 1
        saveData['direction'] = self.direction
        v1,v2 = self.GetPosition()
        saveData['x'] = v1
        saveData['y'] = v2
        v1,v2 = self.GetSize()
        saveData['w'] = v1
        saveData['h'] = v2
        return saveData

    def SetSaveData(self,data):
        self.direction = data['direction']
        self.SetSize(int(data['x']), int(data['y']), int(data['w']), int(data['h']))
        v1Data = data.get('view1',None)
        if v1Data:
            isSplit = data.get('view1IsSplit',None)
            old = self.view1
            if isSplit:
                self.view1 = MultiSplit(self.multiView,self,
                                          (0,0),self.GetSize())
            else:
                self.view1 = MultiViewLeaf(self.multiView,self,
                                             (0,0),self.GetSize())
            self.view1.SetSaveData(v1Data)
            if old:
                old.Destroy()
        v2Data = data.get('view2',None)
        if v2Data:
            isSplit = data.get('view2IsSplit',None)
            old = self.view2
            if isSplit:
                self.view2 = MultiSplit(self.multiView,self,
                                          (0,0),self.GetSize())
            else:
                self.view2 = MultiViewLeaf(self.multiView,self,
                                             (0,0),self.GetSize())
            self.view2.SetSaveData(v2Data)
            if old:
                old.Destroy()
        if self.view1:
            self.view1.OnSize(None)
        if self.view2:
            self.view2.OnSize(None)

    def UnSelect(self):
        if self.view1:
            self.view1.UnSelect()
        if self.view2:
            self.view2.UnSelect()

    def DefaultChildChanged(self):
        if not self.view2:
            self.view1.DefaultChildChanged()

    def AddLeaf(self,direction,caller,pos):
        if self.view2:
            if caller == self.view1:
                self.view1 = MultiSplit(self.multiView,self,
                                          caller.GetPosition(),
                                          caller.GetSize(),
                                          caller)
                self.view1.AddLeaf(direction,caller,pos)
            else:
                self.view2 = MultiSplit(self.multiView,self,
                                          caller.GetPosition(),
                                          caller.GetSize(),
                                          caller)
                self.view2.AddLeaf(direction,caller,pos)
        else:
            self.direction = direction
            w,h = self.GetSize()
            if direction == MV_HOR:
                x,y = (pos,0)
                w1,h1 = (w-pos,h)
                w2,h2 = (pos,h)
            else:
                x,y = (0,pos)
                w1,h1 = (w,h-pos)
                w2,h2 = (w,pos)
            self.view2 = MultiViewLeaf(self.multiView, self, (x,y), (w1,h1))
            self.view1.SetSize((w2,h2))
            self.view2.OnSize(None)

    def DestroyLeaf(self,caller):
        if not self.view2:              # We will only have 2 windows if
            return                      # we need to destroy any
        parent = self.GetParent()       # Another splitview
        if parent == self.multiView:    # We'r at the root
            if caller == self.view1:
                old = self.view1
                self.view1 = self.view2
                self.view2 = None
                old.Destroy()
            else:
                self.view2.Destroy()
                self.view2 = None
            self.view1.SetSize(self.GetSize())
            self.view1.Move(self.GetPosition())
        else:
            w,h = self.GetSize()
            x,y = self.GetPosition()
            if caller == self.view1:
                if self == parent.view1:
                    parent.view1 = self.view2
                else:
                    parent.view2 = self.view2
                self.view2.Reparent(parent)
                self.view2.SetSize(x,y,w,h)
            else:
                if self == parent.view1:
                    parent.view1 = self.view1
                else:
                    parent.view2 = self.view1
                self.view1.Reparent(parent)
                self.view1.SetSize(x,y,w,h)
            self.view1 = None
            self.view2 = None
            self.Destroy()

    def CanSize(self,side,view):
        if self.SizeTarget(side,view):
            return True
        return False

    def SizeTarget(self,side,view):
        if self.direction == side and self.view2 and view == self.view1:
            return self
        parent = self.GetParent()
        if parent != self.multiView:
            return parent.SizeTarget(side,self)
        return None

    def SizeLeaf(self,leaf,pos,side):
        if self.direction != side:
            return
        if not (self.view1 and self.view2):
            return
        if pos < 10: return
        w,h = self.GetSize()
        if side == MV_HOR:
            if pos > w - 10: return
        else:
            if pos > h - 10: return
        if side == MV_HOR:
            self.view1.SetSize(0,0,pos,h)
            self.view2.SetSize(pos,0,w-pos,h)
        else:
            self.view1.SetSize(0,0,w,pos)
            self.view2.SetSize(0,pos,w,h-pos)

    def OnSize(self,evt):
        if not self.view2:
            self.view1.SetSize(self.GetSize())
            self.view1.OnSize(None)
            return
        v1w,v1h = self.view1.GetSize()
        v2w,v2h = self.view2.GetSize()
        v1x,v1y = self.view1.GetPosition()
        v2x,v2y = self.view2.GetPosition()
        w,h = self.GetSize()

        if v1x != v2x:
            ratio = float(w) / float((v1w + v2w))
            v1w *= ratio
            v2w = w - v1w
            v2x = v1w
        else:
            v1w = v2w = w

        if v1y != v2y:
            ratio = float(h) / float((v1h + v2h))
            v1h *= ratio
            v2h = h - v1h
            v2y = v1h
        else:
            v1h = v2h = h

        self.view1.SetSize(int(v1x), int(v1y), int(v1w), int(v1h))
        self.view2.SetSize(int(v2x), int(v2y), int(v2w), int(v2h))
        self.view1.OnSize(None)
        self.view2.OnSize(None)


#----------------------------------------------------------------------


class MultiViewLeaf(wx.Window):
    def __init__(self,multiView,parent,pos,size):
        wx.Window.__init__(self,id = -1,parent = parent,pos = pos,size = size,
                          style = wx.CLIP_CHILDREN)
        self.multiView = multiView

        self.sizerHor = MultiSizer(self,MV_HOR)
        self.sizerVer = MultiSizer(self,MV_VER)
        self.creatorHor = MultiCreator(self,MV_HOR)
        self.creatorVer = MultiCreator(self,MV_VER)
        self.detail = MultiClient(self,multiView._defChild)
        self.closer = MultiCloser(self)

        self.Bind(wx.EVT_SIZE,self.OnSize)

        self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DFACE))


    def GetSaveData(self):
        saveData = {}
        saveData['detailClass_class'] = self.detail.child.__class__.__name__
        saveData['detailClass_mod'] = self.detail.child.__module__
        if hasattr(self.detail.child,'GetSaveData'):
            attr = getattr(self.detail.child,'GetSaveData')
            if callable(attr):
                dData = attr()
                if dData:
                    saveData['detail'] = dData
        v1,v2 = self.GetPosition()
        saveData['x'] = v1
        saveData['y'] = v2
        v1,v2 = self.GetSize()
        saveData['w'] = v1
        saveData['h'] = v2
        return saveData

    def SetSaveData(self,data):
        mod = data['detailClass_mod']
        dChild = mod + '.' + data['detailClass_class']
        six.exec_('import %s' % mod)
        detClass = eval(dChild)
        self.SetSize(data['x'],data['y'],data['w'],data['h'])
        old = self.detail
        self.detail = MultiClient(self,detClass)
        dData = data.get('detail',None)
        if dData:
            if hasattr(self.detail.child,'SetSaveData'):
                attr = getattr(self.detail.child,'SetSaveData')
                if callable(attr):
                    attr(dData)
        old.Destroy()
        self.detail.OnSize(None)

    def UnSelect(self):
        self.detail.UnSelect()

    def DefaultChildChanged(self):
        self.detail.SetNewChildCls(self.multiView._defChild)

    def AddLeaf(self,direction,pos):
        if pos < 10: return
        w,h = self.GetSize()
        if direction == MV_VER:
            if pos > h - 10: return
        else:
            if pos > w - 10: return
        self.GetParent().AddLeaf(direction,self,pos)

    def DestroyLeaf(self):
        self.GetParent().DestroyLeaf(self)

    def SizeTarget(self,side):
        return self.GetParent().SizeTarget(side,self)

    def CanSize(self,side):
        return self.GetParent().CanSize(side,self)

    def OnSize(self,evt):
        def doresize():
            try:
                self.sizerHor.OnSize(evt)
                self.sizerVer.OnSize(evt)
                self.creatorHor.OnSize(evt)
                self.creatorVer.OnSize(evt)
                self.detail.OnSize(evt)
                self.closer.OnSize(evt)
            except:
                pass
        wx.CallAfter(doresize)

#----------------------------------------------------------------------


class MultiClient(wx.Window):
    use_title_bar = True

    child_window_x = 2
    child_window_y = 2

    title_bar_height = 20
    title_bar_font = wx.NORMAL_FONT
    title_bar_font_height = None
    title_bar_x = 3
    title_bar_y = None

    focused_color = wx.Colour(0x2e, 0xb5, 0xf4) # Blue
    focused_brush = None
    focused_text_color = wx.WHITE

    unfocused_color = None
    unfocused_text_color = wx.BLACK
    focused_brush = None

    title_font = wx.NORMAL_FONT

    def __init__(self,parent,childCls):
        w,h = self.CalcSize(parent)
        wx.Window.__init__(self,id = -1,parent = parent,
                          pos = (0,0),
                          size = (w,h),
                          style = wx.CLIP_CHILDREN | wx.SUNKEN_BORDER)
        self.setup_paint()

        self.child = childCls(self)
        self.move_child()
        self.selected = False

        self.Bind(wx.EVT_SET_FOCUS,self.OnSetFocus)
        self.Bind(wx.EVT_CHILD_FOCUS,self.OnChildFocus)
        self.Bind(wx.EVT_PAINT, self.OnPaint)

    @classmethod
    def setup_paint(cls):
        if cls.title_bar_font_height is not None:
            return

        cls.unfocused_color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE)
        cls.focused_brush = wx.Brush(cls.focused_color, wx.SOLID)
        cls.unfocused_brush = wx.Brush(cls.unfocused_color, wx.SOLID)

        dc = wx.MemoryDC()
        dc.SetFont(cls.title_bar_font)
        cls.title_bar_font_height = max(dc.GetCharHeight(), 2)
        cls.title_bar_y = (cls.title_bar_height - cls.title_bar_font_height) // 2

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        dc.SetBackgroundMode(wx.SOLID)
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.SetFont(wx.NORMAL_FONT)
        if self.selected:
            dc.SetBrush(self.focused_brush)
            dc.SetTextBackground(self.focused_color)
            dc.SetTextForeground(self.focused_text_color)
        else:
            dc.SetBrush(self.unfocused_brush)
            dc.SetTextBackground(self.unfocused_color)
            dc.SetTextForeground(self.unfocused_text_color)

        w, h = self.GetSize()
        if self.use_title_bar:
            dc.DrawRectangle(0, 0, w, self.title_bar_height)
            dc.DrawText(self.child.GetName(), self.title_bar_x, self.title_bar_y)
        else:
            dc.DrawRectangle(0, 0, w, h)

        # dc.SetBrush(wx.WHITE_BRUSH)
        # dc.SetPen(wx.WHITE_PEN)
        # dc.DrawRectangle(0, 0, size.x, size.y)
        # dc.SetPen(wx.LIGHT_GREY_PEN)
        # dc.DrawLine(0, 0, size.x, size.y)
        # dc.DrawLine(0, size.y, size.x, 0)
        # dc.DrawText(s, (size.x-w)/2, (size.y-height*5)/2)
        # pos = self.GetPosition()
        # s = "Position: %d, %d" % (pos.x, pos.y)
        # w, h = dc.GetTextExtent(s)
        # dc.DrawText(s, (size.x-w)/2, ((size.y-(height*5))/2)+(height*3))

    def UnSelect(self):
        if self.selected:
            self.selected = False
            self.Refresh()

    def Select(self):
        self.GetParent().multiView.UnSelect()
        self.selected = True
        self.Refresh()

    def CalcSize(self,parent):
        w,h = parent.GetSize()
        w -= SH_SIZE
        h -= SH_SIZE
        return (w,h)

    def OnSize(self,evt):
        w,h = self.CalcSize(self.GetParent())
        self.SetSize(0,0,w,h)
        w,h = self.GetClientSize()
        if self.use_title_bar:
            self.child.SetSize((w, h - self.title_bar_height))
        else:
            self.child.SetSize((w - 2 * self.child_window_x, h - 2 * self.child_window_y))

    def SetNewChildCls(self,childCls):
        if self.child:
            self.child.Destroy()
            self.child = None
        self.child = childCls(self)
        self.move_child()

    def move_child(self):
        if self.use_title_bar:
            self.child.Move(0, self.title_bar_height)
        else:
            self.child.Move(self.child_window_x, self.child_window_y)

    def OnSetFocus(self,evt):
        self.Select()

    def OnChildFocus(self,evt):
        self.OnSetFocus(evt)
##        from Funcs import FindFocusedChild
##        child = FindFocusedChild(self)
##        child.Bind(wx.EVT_KILL_FOCUS,self.OnChildKillFocus)


#----------------------------------------------------------------------


class MultiSizer(wx.Window):
    def __init__(self,parent,side):
        self.side = side
        x,y,w,h = self.CalcSizePos(parent)
        wx.Window.__init__(self,id = -1,parent = parent,
                          pos = (x,y),
                          size = (w,h),
                          style = wx.CLIP_CHILDREN)

        self.px = None                  # Previous X
        self.py = None                  # Previous Y
        self.isDrag = False             # In Dragging
        self.dragTarget = None          # View being sized

        self.Bind(wx.EVT_LEAVE_WINDOW,self.OnLeave)
        self.Bind(wx.EVT_ENTER_WINDOW,self.OnEnter)
        self.Bind(wx.EVT_MOTION,self.OnMouseMove)
        self.Bind(wx.EVT_LEFT_DOWN,self.OnPress)
        self.Bind(wx.EVT_LEFT_UP,self.OnRelease)

        self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DFACE))


    def CalcSizePos(self,parent):
        pw,ph = parent.GetSize()
        if self.side == MV_HOR:
            x = CR_SIZE + 2
            y = ph - SH_SIZE
            w = pw - CR_SIZE - SH_SIZE - 2
            h = SH_SIZE
        else:
            x = pw - SH_SIZE
            y = CR_SIZE + 2 + SH_SIZE
            w = SH_SIZE
            h = ph - CR_SIZE - SH_SIZE - 4 - SH_SIZE # For Closer
        return (x,y,w,h)

    def OnSize(self,evt):
        x,y,w,h = self.CalcSizePos(self.GetParent())
        self.SetSize(x,y,w,h)

    def OnLeave(self,evt):
        self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))

    def OnEnter(self,evt):
        if not self.GetParent().CanSize(not self.side):
            return
        if self.side == MV_HOR:
            self.SetCursor(wx.Cursor(wx.CURSOR_SIZENS))
        else:
            self.SetCursor(wx.Cursor(wx.CURSOR_SIZEWE))

    def OnMouseMove(self,evt):
        if self.isDrag:
            DrawSash(self.dragTarget,self.px,self.py,self.side)
            self.px,self.py = self.ClientToScreen((evt.x, evt.y))
            self.px,self.py = self.dragTarget.ScreenToClient((self.px,self.py))
            DrawSash(self.dragTarget,self.px,self.py,self.side)
        else:
            evt.Skip()

    def OnPress(self,evt):
        self.dragTarget = self.GetParent().SizeTarget(not self.side)
        if self.dragTarget:
            self.isDrag = True
            self.px,self.py = self.ClientToScreen((evt.x, evt.y))
            self.px,self.py = self.dragTarget.ScreenToClient((self.px,self.py))
            DrawSash(self.dragTarget,self.px,self.py,self.side)
            self.CaptureMouse()
        else:
            evt.Skip()

    def OnRelease(self,evt):
        if self.isDrag:
            DrawSash(self.dragTarget,self.px,self.py,self.side)
            self.ReleaseMouse()
            self.isDrag = False
            if self.side == MV_HOR:
                self.dragTarget.SizeLeaf(self.GetParent(),
                                         self.py,not self.side)
            else:
                self.dragTarget.SizeLeaf(self.GetParent(),
                                         self.px,not self.side)
            self.dragTarget = None
        else:
            evt.Skip()

#----------------------------------------------------------------------


class MultiCreator(wx.Window):
    def __init__(self,parent,side):
        self.side = side
        x,y,w,h = self.CalcSizePos(parent)
        wx.Window.__init__(self,id = -1,parent = parent,
                          pos = (x,y),
                          size = (w,h),
                          style = wx.CLIP_CHILDREN)

        self.px = None                  # Previous X
        self.py = None                  # Previous Y
        self.isDrag = False           # In Dragging

        self.Bind(wx.EVT_LEAVE_WINDOW,self.OnLeave)
        self.Bind(wx.EVT_ENTER_WINDOW,self.OnEnter)
        self.Bind(wx.EVT_MOTION,self.OnMouseMove)
        self.Bind(wx.EVT_LEFT_DOWN,self.OnPress)
        self.Bind(wx.EVT_LEFT_UP,self.OnRelease)
        self.Bind(wx.EVT_PAINT,self.OnPaint)

    def CalcSizePos(self,parent):
        pw,ph = parent.GetSize()
        if self.side == MV_HOR:
            x = 2
            y = ph - SH_SIZE
            w = CR_SIZE
            h = SH_SIZE
        else:
            x = pw - SH_SIZE
            y = 4 + SH_SIZE             # Make provision for closer
            w = SH_SIZE
            h = CR_SIZE
        return (x,y,w,h)

    def OnSize(self,evt):
        x,y,w,h = self.CalcSizePos(self.GetParent())
        self.SetSize(x,y,w,h)

    def OnLeave(self,evt):
        self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))

    def OnEnter(self,evt):
        if self.side == MV_HOR:
            self.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        else:
            self.SetCursor(wx.Cursor(wx.CURSOR_POINT_LEFT))

    def OnMouseMove(self,evt):
        if self.isDrag:
            parent = self.GetParent()
            DrawSash(parent,self.px,self.py,self.side)
            self.px,self.py = self.ClientToScreen((evt.x, evt.y))
            self.px,self.py = parent.ScreenToClient((self.px,self.py))
            DrawSash(parent,self.px,self.py,self.side)
        else:
            evt.Skip()

    def OnPress(self,evt):
        self.isDrag = True
        parent = self.GetParent()
        self.px,self.py = self.ClientToScreen((evt.x, evt.y))
        self.px,self.py = parent.ScreenToClient((self.px,self.py))
        DrawSash(parent,self.px,self.py,self.side)
        self.CaptureMouse()

    def OnRelease(self,evt):
        if self.isDrag:
            parent = self.GetParent()
            DrawSash(parent,self.px,self.py,self.side)
            self.ReleaseMouse()
            self.isDrag = False

            if self.side == MV_HOR:
                parent.AddLeaf(MV_VER,self.py)
            else:
                parent.AddLeaf(MV_HOR,self.px)
        else:
            evt.Skip()

    def OnPaint(self,evt):
        dc = wx.PaintDC(self)
        dc.SetBackground(wx.Brush(self.GetBackgroundColour(),wx.BRUSHSTYLE_SOLID))
        dc.Clear()

        highlight = wx.Pen(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNHIGHLIGHT), 1, wx.PENSTYLE_SOLID)
        shadow = wx.Pen(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNSHADOW), 1, wx.PENSTYLE_SOLID)
        black = wx.Pen(wx.BLACK,1,wx.PENSTYLE_SOLID)
        w,h = self.GetSize()
        w -= 1
        h -= 1

        # Draw outline
        dc.SetPen(highlight)
        dc.DrawLine(0,0, 0,h)
        dc.DrawLine(0,0, w,0)
        dc.SetPen(black)
        dc.DrawLine(0,h, w+1,h)
        dc.DrawLine(w,0, w,h)
        dc.SetPen(shadow)
        dc.DrawLine(w-1,2, w-1,h)

#----------------------------------------------------------------------


class MultiCloser(wx.Window):
    def __init__(self,parent):
        x,y,w,h = self.CalcSizePos(parent)
        wx.Window.__init__(self,id = -1,parent = parent,
                          pos = (x,y),
                          size = (w,h),
                          style = wx.CLIP_CHILDREN)

        self.down = False
        self.entered = False

        self.Bind(wx.EVT_LEFT_DOWN,self.OnPress)
        self.Bind(wx.EVT_LEFT_UP,self.OnRelease)
        self.Bind(wx.EVT_PAINT,self.OnPaint)
        self.Bind(wx.EVT_LEAVE_WINDOW,self.OnLeave)
        self.Bind(wx.EVT_ENTER_WINDOW,self.OnEnter)

    def OnLeave(self,evt):
        self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
        self.entered = False

    def OnEnter(self,evt):
        self.SetCursor(wx.Cursor(wx.CURSOR_BULLSEYE))
        self.entered = True

    def OnPress(self,evt):
        self.down = True
        evt.Skip()

    def OnRelease(self,evt):
        if self.down and self.entered:
            self.GetParent().DestroyLeaf()
        else:
            evt.Skip()
        self.down = False

    def OnPaint(self,evt):
        dc = wx.PaintDC(self)
        dc.SetBackground(wx.Brush(wx.RED,wx.BRUSHSTYLE_SOLID))
        dc.Clear()

    def CalcSizePos(self,parent):
        pw,ph = parent.GetSize()
        x = pw - SH_SIZE
        w = SH_SIZE
        h = SH_SIZE + 2
        y = 1
        return (x,y,w,h)

    def OnSize(self,evt):
        x,y,w,h = self.CalcSizePos(self.GetParent())
        self.SetSize(x,y,w,h)


#----------------------------------------------------------------------


class EmptyChild(wx.Window):
    def __init__(self,parent):
        wx.Window.__init__(self,parent,-1, style = wx.CLIP_CHILDREN)


#----------------------------------------------------------------------

# TODO: Switch to wx.Overlay instead of screen DC

def DrawSash(win,x,y,direction):
    dc = wx.ScreenDC()
    dc.StartDrawingOnTop(win)
    bmp = wx.Bitmap(8,8)
    bdc = wx.MemoryDC()
    bdc.SelectObject(bmp)
    bdc.DrawRectangle(-1,-1, 10,10)
    for i in range(8):
        for j in range(8):
            if ((i + j) & 1):
                bdc.DrawPoint(i,j)

    brush = wx.Brush(wx.Colour(0,0,0))
    brush.SetStipple(bmp)

    dc.SetBrush(brush)
    dc.SetLogicalFunction(wx.XOR)

    body_w,body_h = win.GetClientSize()

    if y < 0:
        y = 0
    if y > body_h:
        y = body_h
    if x < 0:
        x = 0
    if x > body_w:
        x = body_w

    if direction == MV_HOR:
        x = 0
    else:
        y = 0

    x,y = win.ClientToScreen((x,y))

    w = body_w
    h = body_h

    if direction == MV_HOR:
        dc.DrawRectangle(x,y-2, w,4)
    else:
        dc.DrawRectangle(x-2,y, 4,h)

    dc.EndDrawingOnTop()


#For testing
if __name__ == '__main__':
    class SizeReportCtrl(wx.Control):

        def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                    size=wx.DefaultSize):

            wx.Control.__init__(self, parent, id, pos, size, style=wx.NO_BORDER)
            self.Bind(wx.EVT_PAINT, self.OnPaint)
            self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
            self.Bind(wx.EVT_SIZE, self.OnSize)

        def OnPaint(self, event):
            dc = wx.PaintDC(self)
            size = self.GetClientSize()

            s = "Size: %d x %d"%(size.x, size.y)

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
            pos = self.GetPosition()
            s = "Position: %d, %d" % (pos.x, pos.y)
            w, h = dc.GetTextExtent(s)
            dc.DrawText(s, (size.x-w)/2, ((size.y-(height*5))/2)+(height*3))

        def OnEraseBackground(self, event):
            pass

        def OnSize(self, event):
            self.Refresh()


    app = wx.App()
    frame = wx.Frame(None, -1, "Test", size=(400,400))
    multi = MultiSash(frame, -1, pos = (0,0), size = (640,480))
    multi.SetDefaultChildClass(SizeReportCtrl)
    frame.Show(True)
    app.MainLoop()
