# -*- coding: utf-8 -*-
"""
Created on Sat Jun 20 16:49:18 2020

@author: vaskar
"""

import wx, os
import wx.media
import wx.lib.buttons as buttons
import wx.lib.mixins.listctrl as mixins
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
import locale
locale.setlocale(locale.LC_ALL, 'C')


dirName = os.curdir
bitmapDir = os.path.join(dirName, 'bitmaps')

class Slider(wx.Slider):
    
    def __init__(self, leftGap, rightGap, *args, **kw):
        wx.Slider.__init__(self, *args, **kw)
        self.leftGap = leftGap
        self.rightGap = rightGap
        self.Bind(wx.EVT_LEFT_DOWN, self.OnClick)
    
    def findValue(self, x1, x2, y1, y2, x):
        return ((float(x - x1) / (x2 - x1))*(y2 - y1)) + y1
    
    def OnClick(self, event):
        clickMin = self.leftGap
        clickMax = self.GetSize()[0] - self.rightGap
        clickPos = event.GetX()
        resMin = self.GetMin()
        resMax = self.GetMax()
        if clickPos > clickMin and clickPos < clickMax:
            res = self.findValue(clickMin, clickMax, resMin, resMax, clickPos)
        elif clickPos <= clickMin:
            res = resMin
        else:
            res = resMax
        
        self.SetValue(res)
        event.Skip()

class ListCtrl(wx.ListCtrl, mixins.ListCtrlAutoWidthMixin):
    
    def __init__(self, parent):
        wx.ListCtrl.__init__(self, parent, style = wx.LC_REPORT)
        mixins.ListCtrlAutoWidthMixin.__init__(self)


class MusicPlayer(wx.Frame):
    
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs, parent = None)
        
        self._bottomPanel = wx.Panel(self)
        self._rightPanel = wx.Panel(self)
        self._leftPanel = wx.Panel(self)
        
        self.volume = 20
        self.musicList = []
        self.playlist = {}
        self._musicMapDict = {}
        self._currentPos = 0
        self._font = wx.Font(pointSize = 12, family = wx.FONTFAMILY_DECORATIVE, style = 
                       wx.FONTSTYLE_ITALIC, weight = wx.FONTWEIGHT_LIGHT, underline = False)
        self._folder = dirName
        
        self.layoutControls()
        self.createSideControls()
        self.createMusicPanel(self.musicList)
        self.positionPanels()
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        
        self._musicBtn.SetFocus()
        self.GetSizer().Layout()
    
    def createMusicPanel(self, musicList):
        
        sizer = wx.BoxSizer()
        
        self._listCtrl = ListCtrl(self._rightPanel)
        font = self._font
        font.SetPointSize(10)
        font.SetStyle(wx.FONTSTYLE_NORMAL)
        
        self._listCtrl.SetFont(font)
        self._listCtrl.InsertColumn(0, 'Song Name', wx.LIST_FORMAT_LEFT, width = 300)
        self._listCtrl.InsertColumn(1, 'Artist Name', wx.LIST_FORMAT_LEFT, width = 200)
        self._listCtrl.InsertColumn(2, 'Length', wx.LIST_FORMAT_CENTER)
        
        idx = 0
        for i in musicList:
            value = i.split('$')
            index = self._listCtrl.InsertItem(idx, value[0])
            self._listCtrl.SetItem(index, 1, value[1])
            self._listCtrl.SetItem(index, 2, value[2])
            idx += 1
        
        self._listCtrl.EnableCheckBoxes(True)
        
        self._listCtrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnSelected)
        self._listCtrl.Bind(wx.EVT_LIST_ITEM_CHECKED, self.OnChecked)
        self._listCtrl.Bind(wx.EVT_LIST_ITEM_UNCHECKED, self.OnUnchecked)
        
        sizer.Add(self._listCtrl, proportion = 1, flag = wx.EXPAND)
        
        self._rightPanel.SetSizer(sizer)
        if self._listCtrl.GetItemCount() != 0:
            self._playPauseBtn.Enable(True)
    
    def createPlaylistPanel(self):
        
        sizer = wx.BoxSizer()
        
        self._listCtrl = ListCtrl(self._rightPanel)
        font = self._font
        
        font.SetPointSize(10)
        font.SetStyle(wx.FONTSTYLE_SLANT)
        font.SetFamily(wx.FONTFAMILY_DECORATIVE)
        
        self._listCtrl.SetFont(font)
        
        self._listCtrl.InsertColumn(0, 'Playlist Name', wx.LIST_FORMAT_LEFT, width = 400)
        self._listCtrl.InsertColumn(1, 'Number of Songs', wx.LIST_FORMAT_CENTER)
        
        idx = 0
        for i in self.playlist.keys():
            index = self._listCtrl.InsertItem(idx, i)
            self._listCtrl.SetItem(index, 1, str(len(self.playlist[i])))
            idx += 1
        
        self._listCtrl.EnableCheckBoxes(True)
        self._listCtrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnPlaylistSelected)
        self._listCtrl.Bind(wx.EVT_LIST_ITEM_CHECKED, self.OnPlaylistChecked)
        self._listCtrl.Bind(wx.EVT_LIST_ITEM_UNCHECKED, self.OnPlaylistUnchecked)
        
        sizer.Add(self._listCtrl, proportion = 1, flag = wx.EXPAND)
        
        self._rightPanel.SetSizer(sizer)
        
        self.GetSizer().Layout()
        
    def createSideControls(self):
        
        self._leftPanel.Freeze()
        
        colour = wx.Colour(145, 145, 145)
        self._leftPanel.SetBackgroundColour(colour)
        
        #Creating a Sizer for panel
        ans = False
        sizer = self._leftPanel.GetSizer()
        if sizer == None:
            ans = True
            sizer = wx.BoxSizer(wx.VERTICAL)
            
        sizer.Clear(True)
        
        sizer.Add(wx.StaticText(self._leftPanel), flag = wx.EXPAND, proportion = 1)
        
        #Creating Add Music Button
        bitmap = wx.Bitmap(os.path.join(bitmapDir, 'music.png'))
        self._musicBtn = buttons.GenBitmapButton(self._leftPanel,
                                                       name = 'Music',
                                                       bitmap = bitmap)
        self._musicBtn.SetBezelWidth(0)
        self._musicBtn.SetBackgroundColour(colour)
        
        #Adding the music button in sizer
        sizer.Add(self._musicBtn, flag = wx.TOP | wx.LEFT | wx.RIGHT, border = 10)
        sizer.Add(wx.StaticText(self._leftPanel), flag = wx.EXPAND, proportion = 1)
        
        #Setting the handler
        self._musicBtn.Bind(wx.EVT_BUTTON, self.OnMusic)
        
        bitmap = wx.Bitmap(os.path.join(bitmapDir, 'playlist.png'))
        self._playlistBtn = buttons.GenBitmapButton(self._leftPanel, name = 'Playlist',
                                                   bitmap = bitmap)
        self._playlistBtn.SetBackgroundColour(colour)
        self._playlistBtn.SetBezelWidth(0)
        self._playlistBtn.Bind(wx.EVT_BUTTON, self.OnPlaylist)
        
        sizer.Add(self._playlistBtn, flag = wx.TOP | wx.LEFT | wx.RIGHT, border = 10)
        
        bitmap = wx.Bitmap(os.path.join(bitmapDir, 'createPlaylist.png'))
        self._createPlaylistBtn = buttons.GenBitmapButton(self._leftPanel,
                                                         name = 'Create Playlist',
                                                         bitmap = bitmap)
        self._createPlaylistBtn.SetBackgroundColour(colour)
        self._createPlaylistBtn.SetBezelWidth(0)
        self._createPlaylistBtn.Bind(wx.EVT_BUTTON, self.OnCreatePlaylist)
        
        sizer.Add(wx.StaticText(self._leftPanel), flag = wx.EXPAND, proportion = 1)
        sizer.Add(self._createPlaylistBtn, flag = wx.TOP | wx.LEFT | wx.RIGHT,
                  border = 10)
        
        sizer.Add(wx.StaticText(self._leftPanel), flag = wx.EXPAND, proportion = 1)
        
        #Setting the sizer to the panel
        if ans:
            self._leftPanel.SetSizer(sizer)
        
        if self.GetSizer() != None:
            self.GetSizer().Layout()
            
        self._leftPanel.Thaw()
        
    def layoutControls(self):
        
        #Setting Background Colours
        backColour = wx.CYAN
        self._bottomPanel.SetBackgroundColour(backColour)
        
        try:
            self._mediaPlayer = wx.media.MediaCtrl(self._bottomPanel, 
                                                  style = wx.SIMPLE_BORDER,
                                                  szBackend = wx.media.MEDIABACKEND_WMP10)
        except:
            self._bottomPanel.Destroy()
            self._rightPanel.Destroy()
            self._leftPanel.Destroy()
            self.Destroy()
            raise
        self.Bind(wx.media.EVT_MEDIA_LOADED, self.OnPlayPause)
        self.Bind(wx.media.EVT_MEDIA_FINISHED, self.OnForward)
        
        #Creating Main Sizer
        hbox = wx.BoxSizer()
        
        #Creating a sizer
        sizer = wx.GridBagSizer(0, 20)
        
        #Static Text for showing Song name and Artist name
        self._st = wx.StaticText(self._bottomPanel, label = '')
        self._st.SetFont(self._font)
        
        self._st2 = wx.StaticText(self._bottomPanel, label = '')
        
        self._st3 = wx.StaticText(self._bottomPanel, label = '')
        
        #Adding the static text to sizer
        hbox.Add(self._st, proportion = 1, 
                  flag = wx.EXPAND | wx.TOP | wx.BOTTOM | wx.LEFT,
                  border = 20)
        
        sizer.Add(self._st2, pos = (1, 0), span = (1, 1),
                  flag = wx.TOP, border = 5)
        
        #Creating previous button for music control
        bitmap = wx.Bitmap(os.path.join(bitmapDir, 'previous.png'))
        self._backBtn = buttons.GenBitmapButton(self._bottomPanel, 
                                               bitmap = bitmap, name = 'Previous')
        self._backBtn.SetBackgroundColour(backColour)
        self._backBtn.SetBezelWidth(0)
        
        #Binding the button to the handler
        self._backBtn.Bind(wx.EVT_BUTTON, self.OnBack)
        
        #Adding the button in sizer
        sizer.Add(self._backBtn, pos = (0, 1), span = (1, 1), flag = wx.TOP,
                  border = 7)
        
        #Creating the play-pause button
        img = wx.Bitmap(os.path.join(bitmapDir, 'play-button.png'))
        self._playPauseBtn = buttons.GenBitmapToggleButton(self._bottomPanel, 
                                                    bitmap = img, name = 'Play')
        #If there is no music the button is disabled
        if len(self.musicList) == 0:
            self._playPauseBtn.Enable(False)
        
        img = wx.Bitmap(os.path.join(bitmapDir, 'pause-button.png'))
        self._playPauseBtn.SetBitmapSelected(img)
        self._playPauseBtn.SetBackgroundColour(backColour)
        self._playPauseBtn.SetBezelWidth(0)
        
        #Binding the play-pause button to the handler
        self._playPauseBtn.Bind(wx.EVT_BUTTON, self.OnPlayPause)
        
        #Adding the play-pause button to the sizer
        sizer.Add(self._playPauseBtn, pos = (0, 2), span = (1, 1))
        
        #Creating the forward button for music control
        bitmap = wx.Bitmap(os.path.join(bitmapDir, 'forward.png'))
        self._forwardBtn = buttons.GenBitmapButton(self._bottomPanel, bitmap = bitmap,
                                                  name = 'Forward')
        self._forwardBtn.SetBackgroundColour(backColour)
        self._forwardBtn.SetBezelWidth(0)
        
        #Binding the button to its handler
        self._forwardBtn.Bind(wx.EVT_BUTTON, self.OnForward)
        
        #Adding the button to the sizer
        sizer.Add(self._forwardBtn, pos = (0, 3), span = (1, 1), flag = wx.TOP,
                  border = 5)
        
        #Creating music slider
        self._musicSlider = Slider(parent = self._bottomPanel, leftGap = 8, 
                                  rightGap = 9)
        
        #Adding the slider to its handler
        self._musicSlider.Bind(wx.EVT_SLIDER, self.OnSeek)
        
        #Adding the slider to the sizer
        sizer.Add(self._musicSlider, pos = (1, 1), span = (1, 3), 
                  flag = wx.EXPAND | wx.BOTTOM, border = 10)
        
        self.timer = wx.Timer(self._bottomPanel)
        self.timer.Start(1000)
        
        #Binding the Timer
        self._bottomPanel.Bind(wx.EVT_TIMER, self.OnTimer)
        
        sizer.Add(self._st3, pos = (1, 4), span = (1, 1), flag = wx.TOP, border = 5)
        
        #Creating a button for mute
        bitmap = wx.Bitmap(os.path.join(bitmapDir, 'sound-level3.png'))
        self._soundBtn = buttons.GenBitmapToggleButton(self._bottomPanel,
                                                      bitmap = bitmap, name = 'Sound')
        self._soundBtn.SetBackgroundColour(backColour)
        self._soundBtn.SetBezelWidth(0)
        
        bitmap = wx.Bitmap(os.path.join(bitmapDir, 'no-sound.png'))
        self._soundBtn.SetBitmapSelected(bitmap)
        
        #Adding the button to its handler
        self._soundBtn.Bind(wx.EVT_BUTTON, self.OnMute)
        
        #Adding the button to the sizer
        sizer.Add(self._soundBtn, pos = (0, 5), span = (1, 1),
                  flag = wx.TOP, border = 5)
        
        #Creating a volume slider
        self._volumeSlider = Slider(parent = self._bottomPanel, leftGap = 8,
                                   rightGap = 9, style = wx.SL_VALUE_LABEL)
        self._volumeSlider.SetRange(0, 100)
        self._volumeSlider.SetValue(self.volume)
        
        #Adding the volume slider to its handler
        self._volumeSlider.Bind(wx.EVT_SLIDER, self.OnVolume)
        
        #Adding the volume slider to the sizer
        sizer.Add(self._volumeSlider, pos = (0, 6), span = (1, 2),
                  flag = wx.RIGHT | wx.TOP, border = 10)
        
        sizer.AddGrowableCol(4)
        hbox.Add(sizer, proportion = 3, flag = wx.EXPAND)
        self._bottomPanel.SetSizer(hbox)
        self._bottomPanel.SetBackgroundColour(backColour)
        
    
    def positionPanels(self):
        
        sizer = wx.GridBagSizer(0, 0)
        
        
        sizer.Add(self._leftPanel, pos = (0, 0), flag = wx.EXPAND)
        sizer.Add(self._rightPanel, pos = (0, 1), flag = wx.EXPAND)
        sizer.Add(self._bottomPanel, pos = (1, 0), span = (1, 2), flag = wx.EXPAND)
        
        sizer.AddGrowableCol(1)
        sizer.AddGrowableRow(0)
        
        self.SetSizer(sizer)
    
    def loadMusic(self):
        dlg = wx.DirDialog(self._rightPanel, message = 'Choose the Music Directory',
                               defaultPath = self._folder, name = 'Choose Directory')
            
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self._folder = path
        dlg.Destroy()
        
        self._st.SetLabel('Adding Music...')
        specialCharacters = '-[|(.'
        for files in os.listdir(self._folder):
            if files.endswith('.mp3') or files.endswith('.wav'):
                try:
                    audio = MP3(os.path.abspath(os.path.join(self._folder, files)))
                    length = audio.info.length
                except:
                    length = 0
                try:
                    audio = EasyID3(os.path.abspath(os.path.join(self._folder, files)))
                    artist = audio['artist'][0]
                except:
                    artist = 'Unknown Artist'
                newTitle = os.path.splitext(files)[0]
                newArtist = ''
                
                for char in artist:
                    if char in specialCharacters[:-1]:
                        break
                    else:
                        newArtist += char
                if length == 0:
                    length = ''
                else:
                    sec = '%2d'%(int(length%60))
                    sec = sec.replace(' ', '0')
                    length = str(int(length//60)) + ':' + sec
                
                self.musicList.append(newTitle + '$' + newArtist + '$' + length)
                self._musicMapDict[newTitle] = files
        try:
            self._listCtrl.Destroy()
        except RuntimeError:
            pass
        self.createMusicPanel(self.musicList)
        if len(self.musicList) != 0:
            self._st.SetLabel(f'{len(self.musicList)} songs added.')
        else:
            self._st.SetLabel('')
        self.GetSizer().Layout()
        
    #-------------------------------------------------------------------    
    def OnAddSong(self, event):
        choices = [i.split('$')[0] for i in self.musicList]
        dlg = wx.MultiChoiceDialog(None, 'Choose Songs', 'Songs',
                                   choices = choices,
                                   style = wx.OK | wx.CANCEL | wx.OK_DEFAULT)
        
        dlg.Centre()
        if dlg.ShowModal() == wx.ID_OK:
            songs = set(self.musicList[i] for i in dlg.GetSelections())
            
            for item in range(self._listCtrl.GetItemCount()):
                if self._listCtrl.IsItemChecked(item):
                    text = self._listCtrl.GetItemText(item)
                    self.playlist[text] = self.playlist[text].union(songs)
        
        self._leftPanel.Freeze()
        self._rightPanel.Freeze()
        self.createSideControls()
        try:
            self._listCtrl.Destroy()
        except RuntimeError:
            pass
        self.createPlaylistPanel()
        self._leftPanel.Thaw()
        self._rightPanel.Thaw()
        
    def OnAddTo(self, event):
        songs = set()
        for item in range(self._listCtrl.GetItemCount()):
            if self._listCtrl.IsItemChecked(item):
                songs.add(self.musicList[item])
        
        choices = list(self.playlist.keys())
        choices.insert(0, 'Create New Playlist')
        dlg = wx.MultiChoiceDialog(None, 'Choose Playlist', 'CHOOSE',
                                   choices = choices,
                                   style = wx.OK | wx.OK_DEFAULT | wx.CANCEL)
        
        dlg.Centre()
        if dlg.ShowModal() == wx.ID_OK:
            selections = dlg.GetSelections()
            for item in selections:
                if item == 0:
                    text = wx.GetTextFromUser('Enter Playlist Name', 'Enter Name')
                    if text != '':
                        if text in self.playlist.keys():
                            val = 1
                            for key in self.playlist.keys():
                                start = key.rfind('(')
                                end = key.rfind(')')
                                try:
                                    temp = int(key[start+1:end])
                                except ValueError:
                                    continue
                                val = max(val, temp)
                            text += f' ({val+1})'
                        self.playlist[text] = songs
                else:
                    self.playlist[choices[item]] = self.playlist[choices[item]].union(songs)
        
        dlg.Destroy()
        
        for item in range(self._listCtrl.GetItemCount()):
            self._listCtrl.CheckItem(item, False)
            
        self.createSideControls()
            
    
    def OnBack(self, event):
        length = self._listCtrl.GetItemCount()
        if self._currentPos == 0:
            self._listCtrl.SetItemState(self._currentPos, 0, wx.LIST_STATE_SELECTED)
            self._currentPos = length - 1
        else:
            self._listCtrl.SetItemState(self._currentPos, 0, wx.LIST_STATE_SELECTED)
            self._currentPos -= 1
        
        self._listCtrl.SetItemState(self._currentPos, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
    
    def OnCancel(self, event):
        for item in range(self._listCtrl.GetItemCount()):
            self._listCtrl.CheckItem(item, False)
            
        self.createSideControls()
    
    def OnChecked(self, event):

        leftSizer = self._leftPanel.GetSizer()
        if leftSizer.GetItemCount() == 7:
            self._leftPanel.Freeze()
            leftSizer.Clear(True)
            
            colour = wx.Colour(145, 145, 145)
            
            bitmap = wx.Bitmap(os.path.join(bitmapDir, 'cancel.png'))
            cancelBtn = buttons.GenBitmapTextButton(self._leftPanel, bitmap = bitmap,
                                                    label = '  Cancel')
            cancelBtn.SetBackgroundColour(colour)
            cancelBtn.SetBezelWidth(0)
            cancelBtn.Bind(wx.EVT_BUTTON, self.OnCancel)
            
            leftSizer.Add(cancelBtn, flag = wx.EXPAND | wx.TOP | wx.RIGHT,
                          proportion = 1, border = 10)
            
            bitmap = wx.Bitmap(os.path.join(bitmapDir, 'add-to.png'))
            addToBtn = buttons.GenBitmapTextButton(self._leftPanel, bitmap = bitmap,
                                                   label = '  Add To')
            addToBtn.SetBackgroundColour(colour)
            addToBtn.SetBezelWidth(0)
            addToBtn.Bind(wx.EVT_BUTTON, self.OnAddTo)
            
            leftSizer.Add(addToBtn, flag = wx.EXPAND | wx.TOP | wx.RIGHT,
                          proportion = 1, border = 10)
            
            bitmap = wx.Bitmap(os.path.join(bitmapDir, 'delete.png'))
            deleteBtn = buttons.GenBitmapTextButton(self._leftPanel,
                                                    bitmap = bitmap,
                                                    label = '  Delete')
            deleteBtn.SetBackgroundColour(colour)
            deleteBtn.SetBezelWidth(0)
            deleteBtn.Bind(wx.EVT_BUTTON, self.OnDelete)
            
            leftSizer.Add(deleteBtn, flag = wx.EXPAND | wx.TOP | wx.RIGHT,
                          proportion = 1, border = 10)
            
            bitmap = wx.Bitmap(os.path.join(bitmapDir, 'select-all.png'))
            selectAllBtn = buttons.GenBitmapTextToggleButton(self._leftPanel,id = wx.ID_SELECTALL,
                                                       bitmap = bitmap, size = (110, -1),
                                                       label = '  Select All')
            bitmap = wx.Bitmap(os.path.join(bitmapDir, 'deselect-all.png'))
            selectAllBtn.SetBitmapSelected(bitmap)
            selectAllBtn.SetBackgroundColour(colour)
            selectAllBtn.SetBezelWidth(0)
            selectAllBtn.Bind(wx.EVT_BUTTON, self.OnSelectDeselectAll)
            
            leftSizer.Add(selectAllBtn, flag = wx.EXPAND | wx.ALL,
                          proportion = 1, border = 10)
            
            
            self.GetSizer().Layout()
            self._leftPanel.Thaw()
        
    def OnClose(self, event):
        try:
            self.timer.Destroy()
            self._bottomPanel.Destroy()
            self._rightPanel.Destroy()
            self._leftPanel.Destroy()
        except RuntimeError:
            pass
        self.Destroy()
        
    def OnCreatePlaylist(self, event):
        text = wx.GetTextFromUser('Enter Playlist Name', 'Insert Name', 'Name this')
        if text != '':
            if text in self.playlist.keys():
                val = 1
                for key in self.playlist.keys():
                    start = key.rfind('(')
                    end = key.rfind(')')
                    try:
                        temp = int(key[start+1:end])
                    except ValueError:
                        continue
                    val = max(val, temp)
                text += f' ({val+1})'
            self.playlist[text] = set()
            choices = [item.split('$')[0] for item in self.musicList]
            dlg = wx.MultiChoiceDialog(self, 'Select', 
                                       'Songs', choices = choices)
            
            if dlg.ShowModal() == wx.ID_OK:
                songs = [self.musicList[i] for i in dlg.GetSelections()]
                self.playlist[text] = self.playlist[text].union(set(songs))

            dlg.Destroy()
        
        if self._listCtrl.GetColumnCount() == 2:
            self._rightPanel.Freeze()
            try:
                self._listCtrl.Destroy()
            except RuntimeError:
                pass
            self.createPlaylistPanel()
            self.GetSizer().Layout()
            self._rightPanel.Thaw()
    
    def OnDelete(self, event):
        pos = []
        for item in range(self._listCtrl.GetItemCount()):
            if self._listCtrl.IsItemChecked(item):
                pos.insert(0, item)
        
        if self._listCtrl.GetColumnCount() == 3:
            for item in pos:
                text = self._listCtrl.GetItemText(item)
                try:
                    self._musicMapDict.pop(text)
                except KeyError:
                    continue
                self._listCtrl.DeleteItem(item)
                song = self.musicList.pop(item)
                for key in self.playlist.keys():
                    try:
                        self.playlist[key].remove(song)
                    except KeyError:
                        continue
        else:
            for item in pos:
                text = self._listCtrl.GetItemText(item)
                try:
                    self.playlist.pop(text)
                except KeyError:
                    pass
                self._listCtrl.DeleteItem(item)
            
            
        self.createSideControls()
        
    def OnForward(self, event):
        length = self._listCtrl.GetItemCount()
        if self._currentPos == (length - 1):
            self._listCtrl.SetItemState(self._currentPos, 0, wx.LIST_STATE_SELECTED)
            self._currentPos = 0
        else:
            self._listCtrl.SetItemState(self._currentPos, 0, wx.LIST_STATE_SELECTED)
            self._currentPos += 1
        self._listCtrl.SetItemState(self._currentPos, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
           
    def OnMusic(self, event):
        if len(self.musicList) == 0:
            self.loadMusic()
        else:
            self._rightPanel.Freeze()
            try:
                self._listCtrl.Destroy()
            except RuntimeError:
                pass
            
            self.createMusicPanel(self.musicList)
            self.GetSizer().Layout()
            self._rightPanel.Thaw()
    
    def OnMute(self, event):
        if self._soundBtn.GetValue():
            self._mediaPlayer.SetVolume(0)
        else:
            self._mediaPlayer.SetVolume(self.volume/100)
        
    
    def OnPlaylist(self, event):
        self._rightPanel.Freeze()
        try:
            self._listCtrl.Destroy()
        except RuntimeError:
            return
        
        self.createPlaylistPanel()
        self._rightPanel.Thaw()
    
    def OnPlaylistChecked(self, event):
        leftSizer = self._leftPanel.GetSizer()
        if leftSizer.GetItemCount() == 7:
            self._leftPanel.Freeze()
            leftSizer.Clear(True)
            
            colour = wx.Colour(145, 145, 145)
            
            bitmap = wx.Bitmap(os.path.join(bitmapDir, 'cancel.png'))
            cancelBtn = buttons.GenBitmapTextButton(self._leftPanel, bitmap = bitmap,
                                                    label = '  Cancel')
            cancelBtn.SetBackgroundColour(colour)
            cancelBtn.SetBezelWidth(0)
            cancelBtn.Bind(wx.EVT_BUTTON, self.OnCancel)
            
            leftSizer.Add(cancelBtn, flag = wx.EXPAND | wx.TOP | wx.RIGHT,
                          proportion = 1, border = 10)
            
            bitmap = wx.Bitmap(os.path.join(bitmapDir, 'add-to.png'))
            addSongsBtn = buttons.GenBitmapTextButton(self._leftPanel, bitmap = bitmap,
                                                      label = '  Add Songs')
            addSongsBtn.SetBackgroundColour(colour)
            addSongsBtn.SetBezelWidth(0)
            addSongsBtn.Bind(wx.EVT_BUTTON, self.OnAddSong)
            leftSizer.Add(addSongsBtn, flag = wx.EXPAND | wx.TOP | wx.RIGHT,
                          proportion = 1, border = 10)
            
            bitmap = wx.Bitmap(os.path.join(bitmapDir, 'delete.png'))
            deleteBtn = buttons.GenBitmapTextButton(self._leftPanel,
                                                    bitmap = bitmap,
                                                    label = '  Delete')
            deleteBtn.SetBackgroundColour(colour)
            deleteBtn.SetBezelWidth(0)
            deleteBtn.Bind(wx.EVT_BUTTON, self.OnDelete)
            
            leftSizer.Add(deleteBtn, flag = wx.EXPAND | wx.TOP | wx.RIGHT,
                          proportion = 1, border = 10)
            
            bitmap = wx.Bitmap(os.path.join(bitmapDir, 'select-all.png'))
            selectAllBtn = buttons.GenBitmapTextToggleButton(self._leftPanel,
                                                       bitmap = bitmap, size = (110, -1),
                                                       label = '  Select All')
            bitmap = wx.Bitmap(os.path.join(bitmapDir, 'deselect-all.png'))
            selectAllBtn.SetBitmapSelected(bitmap)
            selectAllBtn.SetBackgroundColour(colour)
            selectAllBtn.SetBezelWidth(0)
            selectAllBtn.Bind(wx.EVT_BUTTON, self.OnSelectDeselectAll)
            
            leftSizer.Add(selectAllBtn, flag = wx.EXPAND | wx.ALL,
                          proportion = 1, border = 10)
            
            
            self.GetSizer().Layout()
            self._leftPanel.Thaw()
    
    def OnPlaylistSelected(self, event):
        
        obj = event.GetEventObject()
        item = obj.GetFirstSelected()
        name = self._listCtrl.GetItemText(item)
        listOfSongs = list(self.playlist[name])
        self._rightPanel.Freeze()
        try:
            self._listCtrl.Destroy()
        except RuntimeError:
            pass
        self.createMusicPanel(listOfSongs)
        self.GetSizer().Layout()
        self._rightPanel.Thaw()
        self._listCtrl.SetItemState(0, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
    
    def OnPlaylistUnchecked(self, event):
        ans = True
        for item in range(self._listCtrl.GetItemCount()):
            if self._listCtrl.IsItemChecked(item):
                ans = False
                break
        
        if ans:
            self._rightPanel.Freeze()
            self._leftPanel.Freeze()
            try:
                self._listCtrl.Destroy()
            except RuntimeError:
                pass
            self.createSideControls()
            self._rightPanel.Thaw()
            self._leftPanel.Thaw()
        
    def OnPlayPause(self, event):
        if isinstance(event, wx.media.MediaEvent):
            if self._soundBtn.GetValue():
                self._mediaPlayer.SetVolume(0)
            else:
                self._mediaPlayer.SetVolume(self.volume/100)
            if not self._mediaPlayer.Play():
                wx.MessageBox("Can't play Media File", caption = 'Error Playing Media',
                              style = wx.OK | wx.ICON_ERROR)
            else:
                length = self._mediaPlayer.Length()
                time = ''
                minute = int(length/60000)
                time += str(minute)
                time += ':'
                second = int(length/1000)%60
                if second//10 == 0:
                    second = '0' + str(second)
                time += str(second)
                self._st3.SetLabel(time)
                self._musicSlider.SetRange(0, length)
                self._playPauseBtn.SetValue(True)
        else:
            if self._playPauseBtn.GetValue():
                if self._soundBtn.GetValue():
                    self._mediaPlayer.SetVolume(0)
                else:
                    self._mediaPlayer.SetVolume(self.volume/100)
                if not self._mediaPlayer.Play():
                    self._listCtrl.SetItemState(0, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
                else:
                    self._musicSlider.SetRange(0, self._mediaPlayer.Length())
                    if self._soundBtn.GetValue():
                        self._mediaPlayer.SetVolume(0)
                    else:
                        self._mediaPlayer.SetVolume(self.volume/100)
                    if not self._mediaPlayer.Play():
                        wx.MessageBox("Can't play Media File", caption = 'Error Playing Media',
                              style = wx.OK | wx.ICON_ERROR)
                    else:
                        length = self._mediaPlayer.Length()
                        time = ''
                        minute = int(length/60000)
                        time += str(minute)
                        time += ':'
                        second = int(length/1000)%60
                        if second//10 == 0:
                            second = '0' + str(second)
                            time += str(second)
                            self._st3.SetLabel(time)

            else:
                self._mediaPlayer.Pause()
    
    def OnSeek(self, event):
        offset = self._musicSlider.GetValue()
        self._mediaPlayer.Seek(offset)
    
    def OnSelectDeselectAll(self, event):
        
        self._leftPanel.Freeze()
        self._rightPanel.Freeze()
        
        button = event.GetEventObject()
        if button.GetValue():
            button.SetLabel('Deselect All')
            button.SetBackgroundColour(wx.Colour(115, 115, 115))
            
            for item in range(self._listCtrl.GetItemCount()):
                self._listCtrl.CheckItem(item, True)
        else:
            button.SetLabel('  Select All')
            
            for item in range(self._listCtrl.GetItemCount()):
                self._listCtrl.CheckItem(item, False)
                
        self._leftPanel.Thaw()
        self._rightPanel.Thaw()
    
    def OnSelected(self, event):
        item = self._listCtrl.GetFirstSelected()
        string = self._listCtrl.GetItemText(item)
        artist = self._listCtrl.GetItemText(item, 1)
        if string.find(' ') >= int(self.GetSize()[0]/5) or string.find(' ') == -1:
            label = string[:20]
        else:
            label = string[:40]
        self._st.SetLabel(label + '\n' + artist)
        self._st.Wrap(self.GetSize()[0]/5)
        path = os.path.join(self._folder, self._musicMapDict[string])
        if not self._mediaPlayer.Load(path):
            wx.MessageBox("Can't Load file %s"%path, 'Error Loading Media',
                          style = wx.OK | wx.ICON_ERROR)
        else:
            self._currentPos = item
    
    def OnTimer(self, event):
        offset = self._mediaPlayer.Tell()
        if offset == -1:
            length = ''
        else:
            length = ''
            minute = int(offset/60000)
            length += str(minute)
            length += ':'
            second = int(offset/1000)%60
            if second//10 == 0:
                second = '0' + str(second) 
            length += str(second)
        self._musicSlider.SetValue(offset)
        self._st2.SetLabel(length)
        
    def OnUnchecked(self, event):
        
        ans = True
        for item in range(self._listCtrl.GetItemCount()):
            if self._listCtrl.IsItemChecked(item):
                ans = False
                break
        
        if ans:
            self.createSideControls()
            
            
    def OnVolume(self, event):
        self.volume = self._volumeSlider.GetValue()
        self._mediaPlayer.SetVolume(self.volume/100)
    
if __name__ == '__main__':
    app = wx.App()
    frame = MusicPlayer(size = (800, 600), title = 'Simple Music Player')
    frame.Show()
    app.MainLoop()