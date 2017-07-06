/**
* Acorn javascript library for parsing the JSON databases to construct the
* front-end, in-memory collections.
* @module acorn
*/
var acorn = acorn || {};
Date.prototype.addDays = function (d) {
    return new Date(this.valueOf()+24*60*60*d);
};
/** Tests if the specified string is a uuid.
*/
acorn.isUUID = function(uuid) {
    if (typeof(uuid) == "string") {
	rx = /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/;
	return rx.test(uuid);
    } else {
	return false;
    }
};
/**
* @classdesc Represents an automatically generated computational lab notebook
* backed by the acorn python logging decorators.
* @class Notebook
* @arg {Number} blocksPerHour how many interval blocks to place in each hour.
*/
var Notebook = function (db, origin, blocksPerHour=6) {
    /** Path (or URL for Dropbox access) to the loaded database file. */
    this.origin = origin;
    // We need to convert all the dates and times into proper JS Date objects.
    for (var uuid in db.entities) {
	entries = db.entities[uuid];
	for (var ientry in entries) {
	    entry = entries[ientry];
	    if (typeof(entry.s) == "number") {
		entry.s = new Date(entry["s"]*1000);
	    }
	}
    }
    /** JSON object constructed from the database file. */
    this.db = db;
    this.dates = this.listDates();
    /** Array of {@link acorn.LogDay} instances representing the days available 
     * in this Notebook. */
    var nb = this;
    this.days = _.map(this.dates, function(date) {
	return nb.getLog(date, blocksPerHour);
    });

    taskarr = origin.split(".");
    this.project = taskarr[0];
    this.task = taskarr[1];
    
    return this;
};
acorn.Notebook = Notebook;
/**
* Lists all the unique dates present in the specified db.
* @arg db JSON object created by the acorn decorators.
*/
acorn.dbListDates = function (db) {
    // We basically scan the db instance (first and last entries, since they
    // appear sequentially) and interpolate the number of days.
    start = 0;
    end = 0;
    for (var uuid in db.entities) {
	entries = db.entities[uuid];
	first = entries[0].s;
	last = entries[entries.length-1].s;
	if (first < start || start == 0) {
	    start = first;
	};
	if (last > end) {
	    end = last;
	};
    };
    delta = end.getDay() - start.getDay();
    return _.map(_.range(0, Math.ceil(delta)+1), function (obj) {
	return start.addDays(obj);
    });
};
/**
* Lists all the unique dates present in the {@link acorn.Notebook.db}.
*/
Notebook.prototype.listDates = function () {
    return acorn.dbListDates(this.db);
};
/** Returns a dict of uuid: [entries] that were created on the specified date.
* @arg db JSON object created by the acorn decorators.
* @arg {Date} date day to return entries for.
*/
acorn.dbGetEntriesByDate = function (db, date) {
    //We just loop over all the db entries and look for those that have the same
    //date as the one they specified (correct to the day).
    result = {};
    for (var uuid in db.entities) {
	entries = db.entities[uuid];
	for (var ientry in entries) {
	    entry = entries[ientry];
	    if (entry.s.getDate() == date.getDate()) {
		if (!(uuid in result)) {
		    result[uuid] = [];
		};
		result[uuid].push(entry);
	    };
	};
    };
    return result;
};
/** Returns a dict of uuid: [entries] that were created on the specified date.
* @arg {Date} date day to return entries for.
 */
acorn.Notebook.prototype.getEntriesByDate = function (date) {
    return acorn.dbGetEntriesByDate(this.db, date);
};
/**
* @class LogInterval
* @classdesc Represents a single block of time within a specified hour of the
* day.
* @arg {Number} hour hour of the day that the block belongs to.
* @arg {Number} minute minute of the day that the block starts at.
* @arg {Dict} entries dictionary of log entries; keys are UUID, values are Array
* of Dict with attributes related to the log entry.
*/
acorn.LogInterval = function (hour, minute, entries, nb) {
    this.hour = hour;
    this.minute = minute;
    this.entries = entries;
    this.nb = nb;
};
/** Returns a dictionary describing the object with specified uuid.
 * @arg {Dict} uuids keys are uuids for objects *globally* in the entire log
 * file. values are Dicts of descriptor attributes and values.
 * @arg {String} uuid id that the entry was indexed under.
*/
acorn.getUuidDetails = function(uuids, uuid) {
    if (uuid in uuids) {
	var detail = {"value": uuids[uuid]["fqdn"],
		      "uuid": uuid,
		      "details": uuids[uuid]};
	return detail;
    } else {
	return {};
    }
};

/** Formats the specified entry to produce a human readable version of the log
 * entry.
 * @arg {Dict} entry single entity log entry produced by acorn decorators.
 * @arg {Dict} uuids keys are uuids for objects *globally* in the entire log
 * file. values are Dicts of descriptor attributes and values.
 * @arg {String} uuid id that the entry was indexed under.
*/
acorn.formatCall = function(entry, uuids, uuid) {
    var method = entry.m;
    //First, we construct the args list; this entails first grabbing the
    // positional arguments and replacing any that are UUIDS by their attribute
    // dict from the global `uuids`.
    var args = {};
    var instance = null;
    i = 0;
    for (var iposarg in entry.a["_"]) {
	var posarg = entry.a["_"][iposarg];
	if (acorn.isUUID(posarg)) {
	    //This is a crude check, but variable names in python can't include
	    // '-', so it must be a uuid.
	    if (posarg in uuids) {
		var detail = acorn.getUuidDetails(uuids, posarg);
		if (i == 0 && posarg == uuid) {
		    instance = detail;
		} else {
		    args[i] = detail;
		}
	    }
	} else {
	    args[i] = {"value": posarg, "details": null, "uuid": null};
	}
	i += 1;
    };
    //Store the number of positional arguments that the front-end guy has to
    // look for.
    args["n_posargs"] = i;
    if (instance != null) {
	//The first argument was just the object instance, don't include it.
	args["n_posargs"] -= 1;
    }

    //Now, we can move on to the keyword arguments.
    for (var kwarg in entry.a) {
	if (kwarg != "_") {
	    var details = null;
	    var value = entry.a[kwarg];
	    var kwuuid = null;
	    
	    if (acorn.isUUID(entry.a[kwarg])) {
		kwuuid = entry.a[kwarg];
		if (kwuuid in uuids) {
		    details = uuids[kwuuid];
		    value = details.fqdn;
		}
	    }
	    args[kwarg] = {"value": value, "details": details, "uuid": null};
	}
    };
    
    if (method.includes("__new__")) {
	//This is a constructor call, ignore the __new__ part and just use the
	// type constructor.
	method = method.replace(/\.__new__/, "");
    }
    var returns = null;
    if (acorn.isUUID(entry.r)) {
	returns = acorn.getUuidDetails(uuids, entry.r);
    }
    else if (instance == null) {
	returns = acorn.getUuidDetails(uuids, uuid);
    }
    var elapsed = null;
    if ("e" in entry) {
	elapsed = entry.e*1000;
    }
    
    var result = {"method": method, "args": args, "timestamp": entry.s,
		  "instance": instance, "returns": returns, "code": entry.c,
		  "elapsed": elapsed};
    return result;
};
/** Formats the specified db entity entry for display in the notebook.
 * @arg {Dict} entry single log entry created by acorn decorators.
 * @arg {Dict} uuids global dict of all uuids referenced anywhere in the entire
 * JSON database object.
 * @arg {String} uuid id that the entry was indexed under.
 * @arg {Number} detail level of detail to return for the entry.
*/
acorn.formatEntry = function(entries, uuids, uuid) {
    var callarr = [];
    if (uuid in entries) {
	//Because the instance methods are all stacked under the same uuid,
	// we have an array of entries to describe at this level.
	for (var ientry in entries[uuid]) {
	    var entry = entries[uuid][ientry];
	    var call = acorn.formatCall(entry, uuids, uuid);
	    callarr.push(call);
	}
    } else {
	callarr.push({"method": null, "args": null, "timestamp": null,
		      "instance": null, "returns": null, "code": null,
		      "elapsed": null});
    };
    return callarr;
};
/**
* Returns a Dict with keys being UUIDs of object that were either created by
* function calls during this interval, or had their instance methods called.
*/
acorn.LogInterval.prototype.format = function (uuid) {
    return acorn.formatEntry(this.entries, this.nb.db.uuids, uuid);
};
/** Describes each of the entries in the specified list.
 * @arg {Array} entries list of entries to describe.
 * @arg {Dict} uuids global dict of all uuids referenced anywhere in the entire
 * JSON database object.
*/
acorn.describe = function(entries, uuids) {
    var descarr = [];
    for (var uuid in entries) {
	desc = acorn.formatEntry(entries, uuids, uuid);
	descarr.push.apply(descarr, desc);
    };
    return descarr.sort(function(a, b) {
	if (a.timestamp < b.timestamp) {
	    return -1;
	} else if (a.timestamp > b.timestamp) {
	    return 1;
	} else {
	    return 0;
	}	
    });
};
/** Returns a list describing each entry in the log interval.
*/
acorn.LogInterval.prototype.describe = function() {
    return acorn.describe(this.entries, this.nb.db.uuids);
};
/**
Returns the {@log acorn.LogDay} instance for the specified date.
* @arg {Date} date day to return a {@log acorn.LogDay} instance for.
* @arg {Number} blocksPerHour how many interval blocks to place in each hour.
*/
acorn.Notebook.prototype.getLog = function (date, blocksPerHour) {
    entries = this.getEntriesByDate(date);
    interval = 60/blocksPerHour;
    hours = {};
    for (var uuid in entries) {
	//As we loop through the entries, we just store them in the relevant
	//dictionary based on their hour and minute.
	for (var ientry in entries[uuid]) {
	    entry = entries[uuid][ientry];
	    hour = entry.s.getHours();
	    block = Math.floor(entry.s.getMinutes()/interval);
	    if (!(hour in hours)) {
		hours[hour] = {};
	    };
	    if (!(block in hours[hour])) {
		hours[hour][block] = {};		
	    };
	    if (!(uuid in hours[hour][block])) {
		hours[hour][block][uuid] = [];	
	    };
	    hours[hour][block][uuid].push(entry);
	}
    }
    //Now that we have blocked up the day, we just need to create interval
    //instances for each block.
    intervals = {};
    for (var hour in hours) {
	blocks = hours[hour];
	blockIntervals = [];
	for (var block in _.range(1, blocksPerHour+1)) {
	    entries = blocks[block];
	    blockIntervals.push(new acorn.LogInterval(hour, block*interval,
						      entries, this));
	}
	intervals[hour] = blockIntervals;
    }
    return new acorn.LogDay(this, intervals, date);
};

/** 
* @class LogDay
* @classdesc Represents the entries from a single day in the notebook.
*/
acorn.LogDay = function (nb, intervals, date) {
    /** Reference to the parent notebook that this instance belongs to. */
    this.nb = nb;
    /** Dict of {@log acorn.LogInterval} instances for the logged events.
     * Keys are hours of the day. Values are Arrays of {@log
     * acorn.LogInterval}. */
    this.intervals = intervals;
    this.date = date;
};
/**
* Returns an Array of the blocks *for display*, meaning that each block's 
* {@log acorn.LogInterval} objects has been queried for display information at 
* the lowest detail level.
* @arg {Number} hour hour of the day to return blocks for.
*/
acorn.LogDay.prototype.getBlocks = function(hour) {
    if (hour in this.intervals) {
	var blocks = [];
	for (var index in this.intervals[hour]) {
	    var interval = this.intervals[hour][index];
	    blocks.push(interval.describe(0));
	}
	return blocks;
    } else {
	return [];
    }
};
