#!/usr/bin/env python
import gst

class Pad:
	def __init__(self, plugin, element_factory, pad_template):
		self.plugin = plugin
		self.feature = element_factory
		self.template = pad_template
		caps = self.template.get_caps().to_string().split(",")
		self.mimetype = caps[0]
		self.build_properties(caps[1:])
		self.klasses = self.feature.get_klass()
		self.caps = self.template.get_caps()
		self.type = pad_template.name_template
	
	def build_properties(self, caps):
		#TODO: parse caps
		self.properties = caps
	



#read registry
reg = gst.registry_get_default()

#read plugins from registry
plugins = reg.get_plugin_list()

pads = []
muxers = []
encoders = []

#build pad_template list
for plugin in plugins:
	features = reg.get_feature_list_by_plugin(plugin.get_name())
	for feature in features:
		#tags = feature.get_klass().split("/")
		#feature.get_description(), feature.get_longname
		try:
			pads_templates = feature.get_static_pad_templates()
			for pad in pads_templates:
				p = Pad(plugin, feature, pad)
				pads += [p]
				if "uxer" in p.klasses:
					muxers += [p]
				if "Encoder" in p.klasses:
					encoders += [p]
		except:
			pass
#print pads
#print muxers

def print_list(list):
	print("( Muxer - Encoder )")
	for connection in list:
		print("( %s - %s )"%(connection[0].feature.get_name(), connection[1].feature.get_name()))

connections = []
unknowns = []


for muxer in muxers:
	for encoder in encoders:
		if not muxer.caps.intersect(encoder.caps).is_empty():
			if "src" in muxer.type and "sink" in encoder.type:
				connections += [[muxer, encoder]]
			else:
				unknowns += [[muxer, encoder]]

print_list(connections)
