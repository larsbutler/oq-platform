# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2013, GEM Foundation.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/agpl.html>.

from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url
from exposure.views import export_building
from exposure.views import export_population
from exposure.views import get_exposure_building_form
from exposure.views import get_exposure_population_form
from exposure.views import validate_export


urlpatterns = patterns(
    'geonode.exposure.views',
    url(r'^validate_export', validate_export),
    url(r'^get_exposure_building_form', get_exposure_building_form),
    url(r'^get_exposure_population_form', get_exposure_population_form),
    url(r'^export_building', export_building),
    url(r'^export_population', export_population),
)
