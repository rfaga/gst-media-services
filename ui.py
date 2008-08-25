#!/usr/bin/env python
# -*- coding: UTF-8 -*-
###############################################################################
# This file is part of gst-media-services.                                    #
# Copyright (C) 2008 Roberto Faga Jr, Stefan Kost and Gstreamer team.         #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU General Public License as published by        #
# the Free Software Foundation, version 3.                                    #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU General Public License for more details.                                #
#                                                                             #
# You should have received a copy of the GNU General Public License           #
# along with this program.  See LICENSE file.                                 #
###############################################################################

import gstms, gst
import gtk, gtk.glade, gnomevfs
import gobject
import thread, sys

GLADE_PATH = "convert_anything.glade"

#TAGS
PIPELINE_ONLY = 1
INPUT_OFF = 2
TARGET_OFF = 3

widgets = gtk.glade.XML(GLADE_PATH)

icon_theme = gtk.icon_theme_get_default()
args = sys.argv[1:]

class FileChooserDialog:
    def __init__(self, parent):
        self.parent = parent
        self.widget = widgets.get_widget("widget_fc")
        self.dialog = widgets.get_widget("dialog_filechooser")
        self.check = widgets.get_widget("checkbutton_fc")
        widgets.signal_autoconnect(self)

    def show(self):
        self.dialog.show()

    def hide(self):
        self.dialog.hide()

    def on_button_fc_add_clicked(self, widget):
        self.parent.add_files(self.widget.get_uris())
        self.widget.unselect_all()
        if self.check.get_active():
            self.hide()

    def on_button_fc_cancel_clicked(self, widget):
        self.hide()

def time_to_string(value):
    """
    transform a value in nanoseconds into a human-readable string (got from gst.extend)
    """
    s = ""
    ms = value / gst.MSECOND
    sec = ms / 1000
    min = sec / 60
    h = min/60
    if h:
        s += "%3.dh"%h
    min = min%60
    if min:
        s += "%3.2dm"%min
    sec = sec % 60
    if sec:
        s += "%3.2ds"%sec
    return s#"%3.2dm%3.2ds" % (min, sec)


class InputObject(gstms.File):
    """
    A file / input stream
    """

    def __init__(self, uri, model):
        """
        Constructor.
        
        uri -- URI path, based in GnomeVFS
        """
        self.model = model
        gstms.File.__init__(self, gnomevfs.get_local_path_from_uri(uri))
        self.name = gnomevfs.get_file_info(uri).name
    
    def on_discover(self, discover, success):
        gstms.File.on_discover(self, discover, success)
        #if isn't a recognized file type, just don't add to list
        if self.mediatype == gstms.DATA_TYPE:
            return
        timestamp = time_to_string(max(discover.audiolength, discover.videolength))
        repr = "%s (%s)"%(self.name,timestamp)
        if self.mediatype == gstms.VIDEO_TYPE:
            self.icon = icon_theme.load_icon("video", 32, 0)

        elif self.mediatype == gstms.AUDIO_TYPE:
            self.icon = icon_theme.load_icon("sound", 32, 0)
        elif self.mediatype == gstms.IMAGE_TYPE:
            self.icon = icon_theme.load_icon("image", 32, 0)
        #print dir(discover), discover.videolength
        self.model.append((self.icon, repr, self))

    def get_path(self):
        return self.path



class FileList(object):
    """
    Manipulates gtk.TreeView from glade file to manage files
    """

    def __init__(self, parent):
        """
        Constructor.
        
        parent -- parent dialog
        """
        self.parent = parent
        self.widget = widgets.get_widget("filelist")
        self.widget.get_selection().set_mode(gtk.SELECTION_MULTIPLE)

        # our model shows the file, firstly it's string, followed by itself.
        #XXX: the string isn't being updated if any change occurs in the object
        self.model = gtk.ListStore(gtk.gdk.Pixbuf, gobject.TYPE_STRING, gobject.TYPE_PYOBJECT)
        self.widget.set_model(self.model)
        column = gtk.TreeViewColumn("icon", gtk.CellRendererPixbuf(), pixbuf=0)
        self.widget.append_column(column)

        renderer = gtk.CellRendererText()

        # create a column which uses markup
        column = gtk.TreeViewColumn("filename", renderer,  markup=1)
        self.widget.append_column(column)
        self.add_files(args)

    def add_files(self, files):
        for f in files:
            i = InputObject(f, self.model)
            #gstms.TypeFinder(i)
            #self.queue += [gstms.Decoder(i)]

    def remove_files(self):
        """
        remove files in the FileList
        """
        rows = self.widget.get_selection().get_selected_rows()[1]
        rows.reverse()
        for row in rows:
            self.model.remove(self.model.get_iter(row))

    def get_files_path(self):
        """
        return all file paths of current list
        """
        files_path = []
        for row in self.model:
            files_path += [row[2].get_path()]
        return files_path

class ProfileList:
    def __init__(self, widget, profiles):
        """
        Starts a Profile Rendered list.
        
        widget -- ComboBox widget
        profiles_list -- a python list of gstms.Profiles objects
        """
        self.widget = widget
        self.model = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_PYOBJECT)
        self.widget.set_model(self.model)
        for profile in profiles:
            self.model.append((str(profile), profile))

    def get_selected(self):
        return self.model[self.widget.get_active()][1]

class MainDialog:
    def __init__(self, *category):
        """
        
        category -- What category(ies) is(are) this(ese) conversion. Values can be:
            PIPELINE_ONLY -- constructs only the pipeline and give it back to
                the application which called GSTMS
            INPUT_OFF -- disable possibility to user add or remove files. If
                you choose it, don't forget to add files manually.
            TARGET_OFF -- disable possibility to user choose where to save the
                transcoded files/streams. If you don't specify manually a path,
                the original path will be assumed as the target folder.
            No values -- a default dialog app will appear.

        """
        self.category = category

        self.dialog = widgets.get_widget("dialog_gstms")
        self.filechooserdialog = FileChooserDialog(self)
        self.filelist = FileList(self)

        self.area_input = widgets.get_widget("table_input")
        self.area_video = widgets.get_widget("hbox_video")
        self.area_audio = widgets.get_widget("hbox_audio")
        self.area_image = widgets.get_widget("hbox_image")
        self.area_target = widgets.get_widget("hbox_target")

        self.combo_audio = widgets.get_widget("combobox_audio")
        self.combo_video = widgets.get_widget("combobox_video")
        self.combo_image = widgets.get_widget("combobox_image")

        self.button_transcode = widgets.get_widget("button_transcode")
        self.button_ok = widgets.get_widget("button_ok")
        self.button_cancel = widgets.get_widget("button_cancel")
        self.button_config = widgets.get_widget("button_profileeditor")
        self.button_open = widgets.get_widget("button_open")
        self.button_close = widgets.get_widget("button_close")
        
        self.vbox_filelist = widgets.get_widget("vbox_filelist")
        self.button_remove = widgets.get_widget("button_remove")

        self.dialog_preferences = widgets.get_widget("dialog_preferences")
       
        if PIPELINE_ONLY in self.category:
            self.button_ok.show()
            self.button_transcode.hide()

        if INPUT_OFF in self.category:
            self.area_input.hide()

        if TARGET_OFF in self.category:
            self.area_target.hide()
        
        widgets.signal_autoconnect(self)
        self.dialog.show()
        audio_profiles, video_profiles = gstms.get_profiles()
        self.audioprofiles = ProfileList(self.combo_audio, audio_profiles)
        self.videoprofiles = ProfileList(self.combo_video, video_profiles)

    ### Catching signals ###

    def close_maindialog(self, widget):
        """
        Closes the dialog and the convertion service
        """
        gtk.main_quit()

    def on_button_add_clicked(self, widget):
        self.filechooserdialog.show()

    def on_button_remove_clicked(self, widget):
        self.filelist.remove_files()

    def on_button_transcode_clicked(self, widget):
        self.profile = self.current_profile()
        #profile.transcode(self.update_progressbar)
        self.worklist = self.filelist.get_files_path()
        if self.worklist:
            print "now going to next file '%s'"%self.worklist[0]
            self.button_transcode.set_property("sensitive", False)
            self.vbox_filelist.set_property("visible", False)
            self.profile.transcode(self.worklist.pop(0), self.updater)

    ### Operations ###

    def add_files(self, files):
        """
        files -- A python list of files, in URI format. This URI uses GnomeVFS.
        """
        thread.start_new_thread(self.filelist.add_files, (files,))
        #self.filelist.add_files(files)

    def current_profile(self):
        """
        return current selected profiles, in gstms.Profile formats
        """
        if self.area_audio.get_property("visible"):
            return self.audioprofiles.get_selected()
        elif self.area_video.get_property("visible"):
            return self.videoprofiles.get_selected()
        else:
            print "Error: no profile is able to use conversion"
   
    def updater(self, message, fraction=0.0):
        self.update_progressbar(fraction)
        if message == gstms.CONVERSION_FINISHED:
            if self.worklist:
                print "now going to next file '%s'"%self.worklist[0]
                self.profile.transcode(self.worklist.pop(0), self.updater)
            else:
                self.button_transcode.set_property("visible", False)
                self.button_cancel.set_property("visible", False)
                self.button_config.set_property("visible", False)
                self.button_close.set_property("visible", True)
                self.button_open.set_property("visible", True)

    def update_progressbar(self, fraction):
        print fraction
main = MainDialog()
gtk.main()
