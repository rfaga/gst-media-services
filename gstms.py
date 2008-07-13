# -*- coding: UTF-8 -*-
#
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

import gobject, gst

import time

FILE_SOURCE = "gnomevfssrc"

class File(object):
    """
    A Media object, a file object with its properties
    """

    def __init__(self, uri):
        """
        Constructor.
        
        uri -- file uri
        """
        self.uri = uri
        self.mimetype = None
    
    def set_mimetype(self, mimetype):
        """
        
        mimetype -- Mimetype string of this file
        """
        self.mimetype = mimetype
        print mimetype        

class Pipeline:
    """
    Pipeline class, to simplify other pipeline uses
    """

    def __init__(self, name):
        """
        Constructor, don't forget to construct the pipeline before using it
        """
        self.pipeline = gst.Pipeline(name)
        self.stop()
        

    def on_message(self, bus, message):
        """
        Message from bus!
        """
        t = message.type
        print "Incoming message! - '%s'"%t
        # If process ended
        if t == gst.MESSAGE_EOS:
            pass#self.stop()
        elif t == gst.MESSAGE_ERROR:
            #TODO: send error message to a right place
            print message.parse_error()
        elif t == gst.MESSAGE_TAG:
            self.found_tag(element, message.parse_tag()) 

    def found_tag(self, element, message):
        print message

    def play(self):
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        self.watch_id = bus.connect("message", self.on_message)
        
        self.pipeline.set_state(gst.STATE_PLAYING)
        self.state = gst.STATE_PLAYING

    def stop(self):
        bus = self.pipeline.get_bus()
        bus.disconnect(self.watch_id)
        bus.remove_signal_watch()

        self.pipeline.set_state(gst.STATE_NULL)
        self.state = gst.STATE_NULL


class TypeFinder(Pipeline):
    """
    A class to make an object which find every type of files / streams.
    """

    def __init__(self ):
        """
        Constructor
        """
        # list of files to get info
        self.files = []
        Pipeline.__init__(self, "typefinder")

        self.source = gst.element_factory_make(FILE_SOURCE, "filesource")
        self.pipeline.add(self.source)

        typefind = gst.element_factory_make("typefind", "typefind")
        typefind.connect("have-type", self.have_type)
        self.pipeline.add(typefind)

        fakesink = gst.element_factory_make("fakesink", "fakesink")
        self.pipeline.add(fakesink)

        gst.element_link_many(self.source, typefind, fakesink)

    def have_type(self, typefind, probability, caps):
        """
        Method to happen when a have-type signal is given from typefind element

        typefind -- The typefind element
        probability -- Probability of the type found
        caps -- caps with information of mimetype
        """
        self.caps = caps.to_string().split(",")[0]
        if "current_file" in dir(self):
            self.current_file.set_mimetype(self.caps)

    def add_file(self, file):
        """
        add a file to the queue to detect what is its type.

        file -- file in File format

        returns the type
        """
        self.files += [file]
        if self.state == gst.STATE_NULL:
            self.process_next()

    def process_next(self):
        if self.files:
            file = self.files.pop(0)
            self.current_file = file
            self.source.set_property("location", file.uri)
            self.play()
            #self.stop()

class Decoder(Pipeline):
    """
    A pipeline factory to decode files and get info from them
    """

    def __init__(self):
        """
        Constructor
        """
        
        files = []
        Pipeline.__init__(self, "decoder")

        self.source = gst.element_factory_make(FILE_SOURCE, "filesource")
        self.pipeline.add(self.source)
        
        decodebin = gst.element_factory_make("decodebin2", "decodebin")
        #decodebin.connect("new-decoded-pad", self.new_decoded_pad)
        self.pipeline.add(decodebin)

        self.fakesink = gst.element_factory_make("fakesink", "fakesink")
        self.pipeline.add(self.fakesink)

        gst.element_link_many(self.source, decodebin)

    def new_decoded_pad(self, element, pad, boolean):
        """
        
        element -- Current element (decodebin)
        pad -- new pad created
        boolean -- ahm?
        """
        print "called new_decoded_pad: %s"%pad.get_caps().to_string()
        #gst.message_new_custom(gst.MESSAGE_EOS, self.pipeline, gst.Structure("finish it"))

    def decode(self, file):
        self.source.set_property("location", file.uri)
        self.play()
