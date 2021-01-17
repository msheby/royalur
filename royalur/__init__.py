# Copyright (C) 2018 Joseph Heled.
# Copyright (c) 2019-2021 Matthew Sheby.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
.. automodule:: royalur.urcore
  :members:

.. automodule:: royalur.play
  :members:

.. automodule:: royalur.humanStrategies
  :members:

.. automodule:: royalur.probsdb
  :members:

"""
from __future__ import absolute_import

from .dice import *
from .urcore import *
from .probsdb import *
from .play import *
from .humanStrategies import bestHumanStrategySoFar

import os.path
royalURdataDir = os.path.realpath(os.path.join(os.path.dirname(__file__), "data"))

__version__ = "0.2.2a1"
"""The version of royalUr"""
