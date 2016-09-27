/**
* Acorn javascript library for parsing the JSON databases to construct the
* front-end, in-memory collections.
* @module acorn
*/
var acorn = acorn || {};
Date.prototype.addDays = function (d) {
    return new Date(this.valueOf()+24*60*60*d);
};
/**
* @classdesc Represents an automatically generated computational lab notebook
* backed by the acorn python logging decorators.
* @class Notebook
*/
acorn.Notebook = function (db, origin) {
    /** JSON object constructed from the database file. */
    this.db = db;
    /** Path (or URL for Dropbox access) to the loaded database file. */
    this.origin = origin;
    /** Array of {@link acorn.LogDay} instances representing the days available 
     * in this Notebook. */
    this.days = [];
};
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
	first = entries[0].start;
	last = entries[entries.length-1].start;
	if (first < start || start == 0) {
	    start = first;
	};
	if (last > end) {
	    end = last;
	};
    };
    delta = end - start;
    return _.map(_.range(1, Math.ceil(delta)+1), function (obj) {
	return start.addDays(obj);
    });
};
/**
* Lists all the unique dates present in the {@link acorn.Notebook.db}.
*/
acorn.Notebook.prototype.listDates = function () {
    return acorn.dbListDates(this.db)
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
	for (var entry in entries) {
	    if (entry.start.getDate() == date.getDate()) {
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
    return acorn.dbGetEntriesByDate(date);
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
acorn.LogInterval = function (hour, minute, entries) {
    this.hour = hour;
    this.minute = minute;
    this.entries = entries;
};
/** Formats the specified entry to produce a human readable version of the log
 * entry.
 * @arg {Dict} entry single entity log entry produced by acorn decorators.
 * @arg {Dict} uuids keys are uuids for objects *globally* in the entire log
 * file. values are Dicts of descriptor attributes and values.
*/
acorn.formatCall = function(entry, uuids) {
    method = entry["method"];
    //First, we construct the args list; this entails first grabbing the
    // positional arguments and replacing any that are UUIDS by their attribute
    // dict from the global `uuids`.
    args = {};
    i = 0;
    for (var posarg in entry["args"]["__"]) {
	if ('-' in posarg) {
	    //This is a crude check, but variable names in python can't include
	    // '-', so it must be a uuid.
	    if (posarg in uuids) {
		args[i] = {"value": uuids[posarg]["fqdn"],
			   "uuid": posarg,
			   "details": uuids[posarg]};
	    }
	} else {
	    args[i] = {"value": posarg, "details": null, "uuid": null};
	}
	i += 1;
    };
    //Store the number of positional arguments that the front-end guy has to
    // look for.
    args["positional"] = i-1;

    //Now, we can move on to the keyword arguments.
    for (var kwarg in entry["args"]) {
	if (kwarg != "__") {
	    details = null;
	    value = entry["args"][kwarg];
	    uuid = null;
	    
	    if ('-' in entry["args"][kwarg]) {
		uuid = entry["args"][kwarg];
		if (uuid in uuids) {
		    details = uuids[uuid];
		    value = details["fqdn"];
		}
	    }
	    args[kwarg] = {"value": value, "details": details, "uuid": null};
	}
    };
    
    if ("__new__" in method) {
	//This is a constructor call, ignore the __new__ part and just use the
	// type constructor.
	method = String.replace(method, /\.__new__/, "");
    }
    result = {"method": method, "args": args, "timestamp": entry["start"]};
    return result;
};
/** Formats the specified db entity entry for display in the notebook.
 * @arg {Dict} entry single log entry created by acorn decorators.
 * @arg {Dict} uuids global dict of all uuids referenced anywhere in the entire
 * JSON database object.
 * @arg {String} uuid id that the entry was indexed under.
 * @arg {Number} detail level of detail to return for the entry.
*/
acorn.formatEntry = function(entries, uuids, uuid, detail=0) {
    //We return dict instances with filtered levels of detail based on what the
    //user asked for.
    //0: Just return the initialization/call code signature for the uuid.
    //1: Return the instance method calls for the object with uuid.
    
    //Higher levels of detail can be displayed by examining the "details"
    //attribute of the dict returned for `detail=1` calls.
    switch (detail) {
    case 0:
	if (uuid in entries) {
	    return acorn.formatCall(entries[uuid], uuids);
	} else {
	    return {"method": null, "args": null, "timestamp": null};
	};
    case 1:
	if (uuid in entries) {

	} else {
	
	}	
    }
};
/**
* Returns a Dict with keys being UUIDs of object that were either created by
* function calls during this interval, or had their instance methods called.
* @arg {Number} detail level of detail to format the report with.
*/
acorn.LogInterval.prototype.format = function (uuid=null, detail=0) {
    return acorn.formatEntries(this.entries, uuid, detail);
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
	for (var entry in entries[uuid]) {
	    hour = entry.start.getHours();
	    block = Math.floor(entry.start.getMinutes()/interval);
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
    intervals = {}
    for (var hour in hours) {
	blocks = hours[hour];
	blockIntervals = []
	for (var block in _.range(1, blocksPerHour+1)) {
	    entries = blocks[block];
	    blockIntervals.push(new acorn.LogInterval(hour, block*interval, entries));
	}
	intervals[hour] = blockIntervals;
    }
    return new acorn.LogDay(this, intervals);
}

/** 
* @class LogDay
* @classdesc Represents the entries from a single day in the notebook.
*/
acorn.LogDay = function (nb, intervals) {
    /** Reference to the parent notebook that this instance belongs to. */
    this.nb = nb
    /** Dict of {@log acorn.LogInterval} instances for the logged events.
     * Keys are hours of the day. Values are Arrays of {@log
     * acorn.LogInterval}. */
    this.intervals = intervals
}
/**
* Returns an Array of the blocks *for display*, meaning that each block's 
* {@log acorn.LogInterval} objects has been queried for display information at 
* the lowest detail level.
@arg {Number} hour hour of the day to return blocks for.
*/
acorn.LogDay.prototype.getBlocks = function(hour) {
    if (hour in this.intervals) {
	return _.map(this.intervals[hour], function (interval) {
	    return interval.describe(0);
	});
    } else {
	return [];
    }
}
