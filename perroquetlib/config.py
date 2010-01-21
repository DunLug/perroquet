# -*- coding: utf-8 -*-

# Copyright (C) 2009-2010 Frédéric Bertolus.
#
# This file is part of Perroquet.
#
# Perroquet is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Perroquet is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Perroquet.  If not, see <http://www.gnu.org/licenses/>.

import os, sys
import gettext
import ConfigParser

APP_NAME = 'perroquet'
APP_VERSION = '1.0.1'

class ConfigSingleton(object):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = object.__new__(cls)
            cls._instance.init()
        return cls._instance

class Config(ConfigSingleton):
    def init(self):
        self._properties = {}
        self._writableOptions = {}
        
        self.Set("version", APP_VERSION)
        self.Set("app_name", APP_NAME)
        self.Set("gettext_package", "perroquet")
        self.Set("executable", os.path.dirname(sys.executable))
        self.Set("script", sys.path[0])
        self.Set("localConfigDir", os.path.join(
            os.path.expanduser("~"), 
            ".config/perroquet"))
        self.Set("globalConfigDir", "/etc/perroquet") #FIXME ugly
        
        if os.path.isfile(os.path.join(self.Get("script"), 'data/perroquet.ui')):
            self.Set("ui_path", os.path.join(self.Get("script"), 'data/perroquet.ui'))
        elif  os.path.isfile(os.path.join(self.Get("script"), '../share/perroquet/perroquet.ui')):
            self.Set("ui_path", os.path.join(self.Get("script"), '../share/perroquet/perroquet.ui'))
        else:
            print "Error : gui file 'perroquet.ui' not found"
            sys.exit(1)

        # locale
        if os.path.exists(os.path.join(self.Get("script"), 'build/mo')):
            self.Set("localedir",  os.path.join(self.Get("script"), 'build/mo'))
        else:
            self.Set("localedir",  os.path.join(self.Get("script"), '../share/locale'))

        if os.path.isfile(os.path.join(self.Get("script"), 'data/perroquet.png')):
            self.Set("logo_path", os.path.join(self.Get("script"), 'data/perroquet.png'))
        else:
            self.Set("logo_path", os.path.join(self.Get("script"), '../share/perroquet/perroquet.png'))

        gettext.install (self.Get("gettext_package"),self.Get("localedir"))
        
        configParser = self._loadConfigFiles()
        self._properties.update( dict(configParser.items("string")) )
        self._properties.update( dict(
            ((s, int(i)) for (s,i) in configParser.items("int")) ))
        
    def _loadConfigFiles(self):
        "Load the config file and add it to configParser"
        self._localConfFilHref = os.path.join( self.Get("localConfigDir"), "config")
        self._globalConfFilHref = os.path.join( self.Get("globalConfigDir"), "config")
        
        self._localConfigParser = ConfigParser.ConfigParser()
        if len( self._localConfigParser.read(self._localConfFilHref)) == 0:
            print "No local conf file find"
        
        configParser = ConfigParser.ConfigParser()
        if len( configParser.read(self._globalConfFilHref)) == 0:
            print "Error : gui file "+self._globalConfFilHref+" not found"
            sys.exit(1)
        
        self._writableOptions = dict([(option, section)
                for section in configParser.sections()
                for option in configParser.options(section) ])
        
        for section in self._localConfigParser.sections():
            for (key, value) in self._localConfigParser.items(section):
                configParser.set(section, key, value)
        
        return configParser

    def Get(self, key):
        return self._properties[key]
    
    def Set(self, key, value):
        self._properties[key] = value

        if key in self._writableOptions.keys():
            section = self._writableOptions[key]
            if not self._localConfigParser.has_section(section):
                self._localConfigParser.add_section(section)
            self._localConfigParser.set(section, key, value)
    
    def Save(self):
        #FIXME: need to create the whole path, not only the final dir
        if not os.path.exists(self.Get("localConfigDir")):
           os.mkdir( self.Get("localConfigDir") )
        self._localConfigParser.write( open(self._localConfFilHref, "w"))
