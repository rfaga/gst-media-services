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

import gobject; gobject.threads_init()

import gnomevfs, gst, os
from gst.extend.discoverer import Discoverer
import time
import xml.dom.minidom as xmldom


VIDEO_TYPE = 1
AUDIO_TYPE = 2
DATA_TYPE = 3

EMPTY = 'EMPTY'
ANY = 'ANY'

FILE_SOURCE = "gnomevfssrc"

################################# Misc #######################################

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
        self.decoder = Discoverer(gnomevfs.get_local_path_from_uri(uri))
        self.decoder.connect("discovered", self.on_discover)
        self.decoder.discover()
        self.mimetype = None
    
    def on_discover(self, discover, success):
        #if success:
        self.set_mimetype(discover.mimetype.split(",")[0])
        if discover.is_video:
            self.mediatype = VIDEO_TYPE
        elif discover.is_audio:
            self.mediatype = AUDIO_TYPE
        else:
            self.mediatype = DATA_TYPE
        print discover.is_video, discover.is_audio, success

    def set_mimetype(self, mimetype):
        """
        
        mimetype -- Mimetype string of this file
        """
        self.mimetype = mimetype
        #print mimetype


def error(message):
    print "error: %s"%message

################################ Registry ####################################

class ElementFactory
    def __init__(self, element_factory):
        self.element_factory = element_factory
        pads = element_factory.get_static_pad_templates()
        if not pads:
            return None
        for pad in pads:



    def check(self, sink, source):
        

registry = None

def load_registry():
    """
    Init registry list. Returns False if it's already initialized.
    """
    global registry
    if registry:
        return False
    #read registry only once
    registry = gst.registry_get_default()
    #read plugins from registry
    plugins = registry.get_plugin_list()
    
    #build pad_template list
    for plugin in plugins:
        features = reg.get_feature_list_by_plugin(plugin.get_name())
        for feature in features:
            try:
                element_factory = ElementFactory(feature)
            except:
                pass


#load_registry()

########################### XML Profile Parser ###############################
class Profile(object):
    """
    A profile class, with helpful properties and methods.
    This profile means variables and pipeline to a Gstreamer conversion.
    """

    id = None
    name = None
    output_file_extension = None
    elements_needed = []
    mimetypes = []
    pipeline_process = None
    variables = []
    type = DATA_TYPE

    def __init__(self, xmlnode):
        """
        Constructor.
        
        xmlnode -- the node in dom format, from xml.dom library.
        """
        if xmlnode.nodeName == "audio-profile":
            self.type = AUDIO_TYPE
        elif xmlnode.nodeName == "video-profile":
            self.type = VIDEO_TYPE

        self.id = xmlnode.getAttribute("id")
        self.name = xmlnode.getElementsByTagName("name")[0].firstChild.nodeValue
        self.description = xmlnode.getElementsByTagName("description")[0].firstChild.nodeValue
        self.output_file_extension = xmlnode.getElementsByTagName("output-file-extension")[0].firstChild.nodeValue

        process = xmlnode.getElementsByTagName("process")[0]
        elements = process.childNodes
        for e in elements:
            element = self.probe_element(e)
            if not element:


    def probe_element(self, elementxml):
        """
        elementxml -- element to be probed, in XML format

        return element in gstms.Element format
        """
        caps = elementxml.getElementsByTagName("source")[0].firstChild.nodeValue

        #let's read recommended-elements, this can help our element finder
        recommendedsxml = elementxml.getElementsByTagName("recommended-elements")
        favorites = []
        for r in recommendedsxml:
            favorites += [r.firstChild.nodeValue]

        #now we get the possible element in gstms.Element format.
        # oh, and this element can be None if no element was found
        element = get_possible_element(caps, favorites)
        if not element:
            return None
        element.type = elementxml.getAttribute("type")

        #TODO: parse properties options from elementxml
        return element


    #XXX: In the future, do a write method to write a profile into a file, so editing is easier.


def get_profiles():
    """
    Get all possible profiles from XML databases.
    """
    #TODO: I need to read XMLs from the /usr/share folder (or some other system folder) and from a home folder (like ~/.gstms in UNIX-like)
    HOME_PATH = os.path.expanduser("~/.gstms")
    SYSTEM_PATH = "profiles/" #local path, same of source file, for now...

    profiles_path = os.listdir(SYSTEM_PATH)
    profiles = []
    for path in profiles_path:
        fullpath = os.path.join(os.path.abspath(SYSTEM_PATH), path)
        try:
            doc = xmldom.parse(fullpath)
        except:
            error("file %s is not a valid XML file"%fullpath)
            continue

        try:
            possible_profiles = doc.firstChild.childNodes
            for profile in possible_profiles:
                #if node is a child
                if profile.nodeType == 1:
                    profiles += [Profile(profile)]
        except:
            error("xml file at '%s' is not in EncodingProfiles format"%fullpath)

#TODO: Parse string data into profiles
    return profiles


##################### UNUSED CODE #######################
# For now this code above is not being used
# but I'll let them there because I'll use pipelines...
class Pipeline:
    """
    Pipeline class, to simplify other pipeline uses
    """

    def __init__(self, name):
        """
        Constructor, don't forget to construct the pipeline before using it
        """
        self.pipeline = gst.Pipeline(name)
        #self.stop()
        

    def on_message(self, bus, message):
        """
        Message from bus!
        """
        t = message.type
        #print "Incoming message! - '%s'"%t
        # If process ended
        if t == gst.MESSAGE_EOS:
            self.stop()
        #elif t == gst.MESSAGE_ERROR:
            #TODO: send error message to a right place
            #print message.parse_error()
        elif t == gst.MESSAGE_TAG:
            self.found_tag(message.parse_tag()) 

    def found_tag(self, message):
        print message.keys()

    def play(self):
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        self.watch_id = bus.connect("message", self.on_message)
        
        self.pipeline.set_state(gst.STATE_PLAYING)
        self.state = gst.STATE_PLAYING

    def stop(self):
        try:
            bus = self.pipeline.get_bus()
            bus.disconnect(self.watch_id)
            bus.remove_signal_watch()
            del self.watch_id
        except:
            pass #do nothing
        self.pipeline.set_state(gst.STATE_NULL)
        self.state = gst.STATE_NULL


class TypeFinder(Pipeline):
    """
    A class to make an object which find every type of files / streams.
    """

    def __init__(self, file):
        """
        Constructor
        """
        Pipeline.__init__(self, "typefinder")

        self.source = gst.element_factory_make(FILE_SOURCE, "filesource")
        self.pipeline.add(self.source)

        self.current_file = file
        self.source.set_property("location", file.uri)
        typefind = gst.element_factory_make("typefind", "typefind")
        typefind.connect("have-type", self.have_type)
        self.pipeline.add(typefind)

        fakesink = gst.element_factory_make("fakesink", "fakesink")
        self.pipeline.add(fakesink)

        gst.element_link_many(self.source, typefind, fakesink)
        self.play()

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
            del self


class Decoder_(Pipeline):
    """
    A pipeline factory to decode files and get info from them
    """

    def __init__(self, file):
        """
        Constructor
        """
        
        Pipeline.__init__(self, "decoder")

        self.source = gst.element_factory_make(FILE_SOURCE, "filesource")
        self.pipeline.add(self.source)
        
        decodebin = gst.element_factory_make("decodebin2", "decodebin")
        decodebin.connect("new-decoded-pad", self.new_decoded_pad)
        self.pipeline.add(decodebin)

        self.fakesink = gst.element_factory_make("fakesink", "fakesink")
        self.pipeline.add(self.fakesink)

        gst.element_link_many(self.source, decodebin)
        self.current_file = file
        self.source.set_property("location", file.uri)
        self.play()

    def new_decoded_pad(self, element, pad, boolean):
        """
        element -- Current element (decodebin)
        pad -- new pad created
        boolean -- ahm?
        """
        print "called new_decoded_pad: %s"%pad.get_caps().to_string().split(",")[0]
        self.current_file.add_caps(pad.get_caps().to_string())
        #gst.message_new_custom(gst.MESSAGE_EOS, self.pipeline, gst.Structure("finish it"))

