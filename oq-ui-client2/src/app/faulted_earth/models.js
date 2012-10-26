Ext.namespace('faulted_earth');


faulted_earth.Model = function(prefixId, title, properties, conf) {
    this.prefixId = prefixId;
    this.title = title;
    this._properties = properties

    /* conf is an object. its keys are converted into private keys of
     * `this` */
    if (conf) {
	Ext.iterate(conf, function(field) {
	    this['_' + field] = conf[field]
	});
    }
    return this;
}

faulted_earth.Model.prototype.sourceName = function() {
    return "geonode:observations_" + this.prefixId;
}

faulted_earth.Model.prototype.gridId = function() {
    return this.prefixId + '_grid';
}

faulted_earth.Model.prototype.formId = function() {
    return this.prefixId + '_form';
}

faulted_earth.Model.prototype.snappingId = function() {
    return this.prefixId + '_snapping';
}


faulted_earth.Model.prototype.formToolId = function() {
    return this.prefixId + '_form_tool';
}

faulted_earth.Model.prototype.managerId = function() {
    return this.prefixId + '_manager';
}

faulted_earth.Model.prototype.editorId = function() {
    return this.prefixId + '_editor';
}

faulted_earth.Model.prototype.formTitle = function() {
    return this.title + " Form";
}

faulted_earth.Model.prototype.formPtype = function() {
    return 'fe_' + this.prefixId + '_form';
}

faulted_earth.Model.prototype.gridPtype = function() {
    return this._gridPtype || "gxp_featuregrid"
}


faulted_earth.Model.prototype.formTarget = function() {
    return 'fe_' + this.prefixId + '_tooltarget';
}

faulted_earth.Model.prototype.editorPtype = function() {
    return this._editorPtype || "fe_featureeditor";
}

faulted_earth.Model.prototype.managerPtype = function() {
    return this._managerPtype || "gxp_featuremanager";
}


faulted_earth.Model.prototype.hasForm = function() {
    return this.prefixId == 'trace';
}

faulted_earth.Model.prototype.properties = function() {
    var propertyNames = {}

    /* add a visual clue for compulsory fields */
    Ext.each(this._properties, function (field) {
	propertyNames[field.id] = field.label;

        if (field.isCompulsory) {
            propertyNames[field.id] += " <small>(*)</small>";
        }
    });
    return propertyNames;
}

faulted_earth.locatedObservationProperties = [
    { id: "scale", label: "Scale", isCompulsory: true },
    { id: "accuracy", label: "Accuracy", isCompulsory: true },
    { id: "notes", label: "Notes" }
];

faulted_earth.traceProperties = faulted_earth.locatedObservationProperties.concat([
    { id: "loc_meth", label: "Location Method" },
    { id: "geomorphic_expression", label: "Geomorphic Expression" }
]);

faulted_earth.models = [
    new faulted_earth.Model("event", 'Observations: Events'),
    new faulted_earth.Model("displacement", 'Observations: Displacement'),
    new faulted_earth.Model("sliprate", 'Observations: Slip Rates'),
    new faulted_earth.Model("faultgeometry", 'Observations: Fault Geometry'),
    new faulted_earth.Model("trace", 'Traces', faulted_earth.traceProperties),
    new faulted_earth.Model("faultsection", 'Fault Section Summary'),
    new faulted_earth.Model("fault", 'Faults'),
    new faulted_earth.Model("faultsource", 'Fault Sources')
];

faulted_earth.properties = faulted_earth.traceProperties;

/* an utility function to check if a field is compulsory */
faulted_earth.isCompulsory = function(fieldName) {
    compulsoryFields = [ 
	'fault_name', 'sec_name', 'compiled_by',
	'low_d_min', 'low_d_max', 'low_pref', 'low_d_com',
	'u_sm_d_min', 'u_sm_d_max', 'u_sm_d_pref', 'u_sm_d_com',
	'dip_min', 'dip_max', 'dip_pref', 'dip_com',
	'dip_dir', 'dip_dir_com',
	'slip_type', 'slip_type_com',
	'aseis_slip', 'aseis_com',
	'scale', 'accuracy', 's_feature'
    ];
    
    for (var i = 0; i < faulted_earth.properties.length; i++) {
	var field = faulted_earth.properties[i];
	if (field.id == fieldName && field.isCompulsory) {
	    return true
	}
    }
    return false
};

faulted_earth.isCalculated = function(fieldName) {
    autoComputedFields = [
	'width_min', 'width_max', 'width_pref',
	'area_min', 'area_max', 'area_pref',
	'net_slip_rate_min', 'net_slip_rate_max', 'net_slip_rate_pref',
	'mag_min', 'mag_max', 'mag_pref',
	'mom_min', 'mom_max', 'mom_pref',
	'all_com'
    ];
    for (var i = 0; i < faulted_earth.properties.length; i++) {
	var field = faulted_earth.properties[i];
	if (field.id == fieldName && field.isCalculated) {
	    return true
	}
    }
    return false
}


/*
  Copyright (c) 2010-2012, GEM Foundation.

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as
    published by the Free Software Foundation, either version 3 of the
    License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/agpl.html>. */
