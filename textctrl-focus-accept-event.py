import wx

wxEVT_TREE_END_LABEL_EDIT = wx.wxEVT_COMMAND_TREE_END_LABEL_EDIT

class TreeTextCtrl(wx.TextCtrl):
    def __init__(self, parent):
        self._itemEdited = None
        self._startValue = "Testing focus crash"
        self._finished = False
        self._aboutToFinish = False
        self._currentValue = self._startValue
        wx.TextCtrl.__init__(self, parent, wx.ID_ANY, self._startValue)

        self.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)


    def AcceptChanges(self):
        """
        Accepts/rejects the changes made by the user.

        :return: ``True`` if the changes to the item text have been accepted, ``False``
         if they have been rejected (i.e., vetoed by the user).
        """

        value = self.GetValue()

        if value == self._startValue:
            # nothing changed, always accept
            # when an item remains unchanged, the owner
            # needs to be notified that the user decided
            # not to change the tree item label, and that
            # the edit has been cancelled
            self.GetParent().OnCancelEdit(self._itemEdited)
            return True

        if not self.GetParent().OnAcceptEdit(self._itemEdited, value):
            # vetoed by the user
            return False

        # accepted, do rename the item
#        self.GetParent().SetItemText(self._itemEdited, value)

        return True


    def Finish(self):
        """ Finish editing. """

        if not self._finished:
            self._finished = True
            self.GetParent().SetFocusIgnoringChildren()
            self.GetParent().ResetEditControl()

    def OnKillFocus(self, event):
        """
        Handles the ``wx.EVT_KILL_FOCUS`` event for :class:`TreeTextCtrl`.

        :param `event`: a :class:`FocusEvent` event to be processed.
        """

        if not self._finished and not self._aboutToFinish:

            # We must finish regardless of success, otherwise we'll get
            # focus problems:

            if not self.AcceptChanges():
                self.GetParent().OnCancelEdit(self._itemEdited)

        # We must let the native text control handle focus, too, otherwise
        # it could have problems with the cursor (e.g., in wxGTK).
        event.Skip()


    def StopEditing(self):
        """ Suddenly stops the editing. """

        self.GetParent().OnCancelEdit(self._itemEdited)
        self.Finish()


class MainFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, title="Test")
        panel = wx.Panel(self,-1,name="panel")  
        vbox = wx.BoxSizer(wx.VERTICAL)
        self.focusctrl = TreeTextCtrl(self)
        vbox.Add(self.focusctrl, 1, wx.EXPAND)
        self.otherctrl = wx.TextCtrl(self)
        vbox.Add(self.otherctrl, 1, wx.EXPAND)
        self.SetSizer(vbox)
        self.Show()

    def OnAcceptEdit(self, item, value):
        """
        Called by :class:`TreeTextCtrl`, to accept the changes and to send the
        ``EVT_TREE_END_LABEL_EDIT`` event.

        :param `item`: an instance of :class:`GenericTreeItem`;
        :param string `value`: the new value of the item label.

        :return: ``True`` if the editing has not been vetoed, ``False`` otherwise.
        """

        le = wx.CommandEvent(wxEVT_TREE_END_LABEL_EDIT, self.GetId())
        le.SetEventObject(self)

        return not self.GetEventHandler().ProcessEvent(le)

#----------------------------------------------------------------------
if __name__ == "__main__":
      app = wx.App(False)
      frame = MainFrame()
      app.MainLoop()
