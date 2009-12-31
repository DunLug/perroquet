#!/usr/bin/env python
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

import gettext

from core import Core
from gui import Gui

class Perroquet(object):

    application = "perroquet"

    def __init__(self):

        gettext.install(Perroquet.application)

        self.core = Core()
        self.gui = Gui()

        self.core.SetGui(self.gui)
        self.gui.SetCore(self.core)

        self.gui.Run()

def main():
    perroquet = Perroquet()

if __name__ == "__main__":
    main()


