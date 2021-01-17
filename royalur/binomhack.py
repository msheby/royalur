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

# Small binomial coefficients values: Use a direct mapping for minimal overhead.

__all__ = ["bmap"]


class memorize(dict):
    def __init__(self, func):
        self.func = func

    def __call__(self, *args):
        return self[args]

    def __missing__(self, key):
        result = self[key] = self.func(*key)
        return result


@memorize
def _binomial(n, k):
    if n < k:
        return 0
    if k == 0:
        return 1
    if n == k :
        return 1
    return _binomial(n - 1, k) + _binomial(n - 1, k - 1)


bmap = dict()
for _n in range(20):
    for _k in range(20):
        bmap[_n, _k] = _binomial(_n, _k)
