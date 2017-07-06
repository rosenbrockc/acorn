/**
* The javascript library used to parse tho acorn notebooks and populate the user interface.
*/
$(document).ready(function() {
    $("#projects").on("click", create_projects);
});

/**
* Creates the projects navigation bar and animates it's appearance/disppearance.
*/
function create_projects() {
    var proj_nav = $('#projects_nav');
    /** Make the projects bar appear or disapear */
    if (proj_nav.length >0) {
	if (parseInt(proj_nav.css("top").split(".")[0]) > 0) {
	    $('#projects_nav').animate({top: "-37pt",},"10");
	} else {
	    $('#projects_nav').animate({top: "+37pt",},"10");
	}
    } else {
    /** populate the projects bar */
	$.ajax({
	    url: 'http://127.0.0.1:8000/nav/',
	    success: function(data) {
		$('body').prepend(data);
		$('#projects_nav').animate({top: "37pt",},"10");
	    }});
    }
};

/**
* Creates the projects tasks navigation bar and controls it's appearance/disappearance.
* @arg proj The project name for which tastsk are to be listed.
*/
function create_tasks(proj) {
    var proj_name = '#'+proj
    $.ajax({
    	url: 'http://127.0.0.1:8000/sub_nav/',
    	success: function(result) {
	    taskres = $(result);
	    taskres.toggleClass("hidden");
    	    $('#projectsul').fadeOut(50, function() {
		$.ajax({
		    url: 'http://127.0.0.1:8000/sub_nav_list/',
		    data: proj,
		    success: function(result) {
			$('#tasks').append(result).toggleClass("hidden").fadeIn(50);
		    }});
		$('#projectsul').before(taskres);
		$('#tasks_back').on('click', function () {
		    $('#tasks').fadeOut(50);
		    $('#projectsul').fadeIn(50);
		    $('#tasks').remove();
		    $('#tasks_back').remove();
		}).show().toggleClass("hidden");
	    });
	    
    	}
    });    
};

/**
* Populates a calendar with the dates that the project/task were worked on.
* @arg proj_path The path to the JSON database for the project.
* @arg color A string of the color to be used in the HTML.
*/
function render_project(proj_path,color) {
    $.ajax({
	url: 'http://127.0.0.1:8000/view_proj/',
	data: proj_path,
	success: function(result) {
	    db = JSON.parse(result);
            nb = new acorn.Notebook(db, proj_path);
	    window.curr_nb = nb
	    var dates = nb.dates;
	    var eventdata = [];
	    for(i=0;i<dates.length; i++) {
		eventdata.push({"date": dateFormat(dates[i], "isoDate"),"color":color});
	    }
	    $('#body').html('<div id="my-calendar"></div><div id="DayView"></div>');
	    $('#my-calendar').zabuto_calendar({ data: eventdata, action: function() {getDayView(this.id, dates); }});
	}
    });
}

/**
* Creates a table in the HTML that displays the hours and half hours
* of the day and lists the number of times code for the project was executed in each half hour.
* @arg id The html id for the date in zabuto_calendar.
* @arg dates A list of dates that for which entries exist in the notebook.
*/
function getDayView(id,dates) {
    var nb = window.curr_nb
    var date = $("#"+id).data("date");
    for(i=0;i<dates.length;i++) {
	if (date == dateFormat(dates[i], "isoDate")) {

	    window.curr_log_day = nb.days[i];
	    var ld = nb.days[i];
	    var view = {};
	    view["hours"] = [];
	    /** Determine the number of entries in each half hour block. */
	    for (hour in ld.intervals) {
		var temp_view = {};
		temp_view["hour"] = hour;
	    	var blocks = ld.getBlocks(hour);
		var first_blocks = [];
		var last_blocks = [];
	    	for (var i=0; i< blocks.length; i++) {
		    if (blocks[i].length > 0) {
	    	    var time_str = String(blocks[i][0]["timestamp"]);
	    	    time_str = time_str.split(" ");
	    	    time_str = time_str[4].split(":");
		    if (+time_str[1] < 30) {
			for (var j in blocks[i]) {
			    first_blocks.push(blocks[i][j]);
			}
		    } else {
			for (var j in blocks[i]) {			
			    last_blocks.push(blocks[i][j]);
			}
		    }
		    }
	    	}
		temp_view["first"] = first_blocks.length;
		temp_view["second"] = last_blocks.length;
		view["hours"].push(temp_view);
	    }
	    /** populate the template */
	    (function(view){$.when($.ajax({url: 'http://127.0.0.1:8000/day_table/'}))
		.done(function(template) {
		    Mustache.parse(template);
		    var rendered = Mustache.render(template,view);
		    $("#DayView").html(rendered);		    
		})
		.fail(function(){
		    alert("sorry there was an error.");
		});})(view);
	}
    }
}

/**
* Creats a table listing the functions used during the half hour black
* selected as well as the modals that will contain details about the
* code used, arguments passed, and values returned by any executed
* code.
* @arg hour integer of the hour of the day.
* @arg spot string 'f' if the first hald hour, anything else means the second half hour.
*/
function get_detailed_view(hour,spot) {
    var nb = window.curr_nb
    var ld = window.curr_log_day;
    var blocks = ld.getBlocks(hour);
    var first_blocks = [];
    var last_blocks = [];
    /** Seperate the blocks by half hour intervals */
    for (var i=0; i< blocks.length; i++) {
	if (blocks[i].length > 0) {
	var time_str = String(blocks[i][0]["timestamp"]);
	time_str = time_str.split(" ");
	time_str = time_str[4].split(":");
	if (+time_str[1] < 30) {
	    for (var j in blocks[i]) {			
		first_blocks.push(blocks[i][j]);
	    }
	} else {
	    for (var j in blocks[i]) {			
		last_blocks.push(blocks[i][j]);
	    }
	}
	}
    }
    /** save the blocks for the desired half hour. */
    if (spot === 'f') {
	blocks = first_blocks;
    } else {
	blocks = last_blocks;
    }
    /** Build the dictionary for the mustache template to build the detail view table and modules. */
    var detail_dict = {};
    detail_dict["methods"] = [];
    var methods = [];
    for (var i=0; i<blocks.length; i++) {
	var def = blocks[i]["method"];
	def = def.split(".");
	def = def[def.length-1];
	if ($.inArray(def,methods) <0) {
	    var idx = 1;
	    methods.push(def);
	    var method_dict = {};
	    method_dict["method"] = def;
	    method_dict["rep"] = 1;
	    method_dict["reps"] = [];
	    var rep_dict = {}
	    var time_str = String(blocks[i]["timestamp"]);
	    time_str = time_str.split(" ");
	    time_str = time_str[4];
	    rep_dict["time"] = time_str;
	    /** if there are args we want to list them and get the details that the user may want. */
	    if (blocks[i]["args"]["n_posargs"] < 1) {
		var args_list = [];
		var arg_dict = {};
		arg_dict["arg"] = ""
		args_list.push(arg_dict);
		rep_dict["args"] = args_list;
	    } else {
		var args_list = [];
		for (var j= 0; j < blocks[i]["args"]["n_posargs"]; j++) {
		    var arg_dict = {};
		    if (typeof blocks[i]["args"][j] !== 'undefined'){
			if (blocks[i]["args"][j]["details"] != null) {
			    var details = blocks[i]["args"][j]["details"]
			    var keys = Object.keys(details);
			    detail_list = [];
			    for (var t=0; t<keys.length; t++) {
				var loc_detail_dict = {};
				if (Object.prototype.toString.call(details[keys[t]]) === '[object Array]') {
				    if (keys[t] == 'fqdn') {
					loc_detail_dict["paramater"]='fully qualified name';
				    } else {
					loc_detail_dict["paramater"]=keys[t];
				    }
				    loc_detail_dict["value"]="(" + details[keys[t]]+")";
				} else {
				    if (keys[t] == 'fqdn') {
					loc_detail_dict["paramater"]='fully qualified name';
				    } else {
					loc_detail_dict["paramater"]=keys[t];
				    }
				    loc_detail_dict["value"] =details[keys[t]];
				}
				detail_list.push(loc_detail_dict);
			    }
			    arg_dict["usedetails"] = true;
			    arg_dict["details"] = detail_list;
			}
			arg_dict["arg_idx"] = j;
			arg_dict["arg"]= blocks[i]["args"][j]["value"];
			args_list.push(JSON.parse(JSON.stringify(arg_dict)));
		    }
		}
		/** We also want to get any positional arguments (optional arguments which are listed by their keys. */
		var opt_args = Object.keys(blocks[i]["args"]);
		for (var j=0; j<opt_args.length; j++) {
		    if ((opt_args[j]%1)!==0 && opt_args[j] != "n_posargs") {
			if (blocks[i]["args"][opt_args[j]] !=='undefined') {
			    if (blocks[i]["args"][opt_args[j]]["details"] != null) {
				var details = blocks[i]["args"][opt_args[j]]["details"];
				var keys = Object.keys(details);
				detail_list = [];
				for (var t=0; t<keys.length; t++) {
				    var loc_detail_dict = {};
				    if (Object.prototype.toString.call(details[keys[t]]) === '[object Array]') {
					if (keys[t] == 'fqdn') {
					    loc_detail_dict["paramater"]='fully qualified name';
					} else {
					    loc_detail_dict["paramater"]=keys[t];
					}
					loc_detail_dict["value"]="(" + details[keys[t]]+")";
				    } else {
					if (keys[t] == 'fqdn') {
					    loc_detail_dict["paramater"]='fully qualified name';
					} else {
					    loc_detail_dict["paramater"]=keys[t];
					}
					loc_detail_dict["value"] =details[keys[t]];
				    }
				    detail_list.push(loc_detail_dict);
				}
				arg_dict["usedetails"]=true;
				arg_dict["details"] = detail_list;
			    }
			    arg_dict["arg_idx"] = j;
			    arg_dict["arg"] = opt_args[j] + "="+blocks[i]["args"][opt_args[j]]["value"];
			    args_list.push(JSON.parse(JSON.stringify(arg_dict)));
			}
		    }
		}
		rep_dict["args"] = args_list;
	    }
	    /** We also want to get the details for the returned values. */
	    return_dict = {};
	    return_list = [];
	    if (blocks[i]["returns"] != null) {
		if (typeof blocks[i]["returns"]["value"] !== "undefined") {
		    return_dict["usedetails"] = true;
		    return_dict["return"] = blocks[i]["returns"]["value"];
		    var details = blocks[i]["returns"]["details"]
		    var keys = Object.keys(details);
		    detail_list = [];
		    for (var t=0; t<keys.length; t++) {
			var loc_detail_dict = {};
			if (Object.prototype.toString.call(details[keys[t]]) === '[object Array]') {
			    if (keys[t] == 'fqdn') {
				loc_detail_dict["paramater"]='fully qualified name';
			    } else {
				loc_detail_dict["paramater"]=keys[t];
			    }
			    loc_detail_dict["value"]="(" + details[keys[t]]+")";
			} else {
			    if (keys[t] == 'fqdn') {
				loc_detail_dict["paramater"]='fully qualified name';
			    } else {
				loc_detail_dict["paramater"]=keys[t];
			    }
			    loc_detail_dict["value"] =details[keys[t]];
			}
			detail_list.push(loc_detail_dict);
		    }
		    return_dict["details"] = detail_list;
		}
	    } else {
		return_dict["return"] = "";
	    };
	    return_list.push(return_dict);
	    rep_dict["returns"] = return_list;
	    /** get the source code */
	    rep_dict["codeLines"] = [];
	    for (var k in blocks[i]["code"]) {
	    	var code = {};
	    	code["code"] = blocks[i]["code"][k];
	    	rep_dict["codeLines"].push(code);
	    }
	    rep_dict["idx"] = idx;
	    idx = idx + 1;
	    method_dict["reps"].push(rep_dict);
	    /** search for any other times when the this same method
	     * was called or used.  Repeat the above process for each
	     * of them */
	    for (var k=i+1; k<blocks.length; k++) {
		var def_j = blocks[k]["method"].split(".");
		def_j = def_j[def_j.length-1];
		if (def_j == def) {
		    rep_dict = {};
		    var time_str = String(blocks[k]["timestamp"]);
		    time_str = time_str.split(" ");
		    time_str = time_str[4];
		    rep_dict["time"] = time_str;
		    if (blocks[k]["args"]["n_posargs"] < 1) {
			var args_list = [];
			var arg_dict = {};
			arg_dict["arg"] = ""
			args_list.push(arg_dict);
			rep_dict["args"] = args_list;
		    } else {
			var args_list = [];
			for (var j= 0; j < blocks[k]["args"]["n_posargs"]; j++) {
			    if (typeof blocks[k]["args"][j] !== "undefined") {
				var arg_dict = {};
				if (blocks[k]["args"][j]["details"] != null) {
				    var details = blocks[k]["args"][j]["details"]
				    var keys = Object.keys(details);
				    detail_list = [];
				    for (var t=0; t<keys.length; t++) {
					var loc_detail_dict = {};
					if (Object.prototype.toString.call(details[keys[t]]) === '[object Array]') {
					    if (keys[t] == 'fqdn') {
						loc_detail_dict["paramater"]='fully qualified name';
					    } else {
						loc_detail_dict["paramater"]=keys[t];
					    }
					    loc_detail_dict["value"]= "(" + details[keys[t]]+")";
					} else {
					    if (keys[t] == 'fqdn') {
						loc_detail_dict["paramater"]='fully qualified name';
					    } else {
						loc_detail_dict["paramater"]=keys[t];
					    }
					    loc_detail_dict["value"] = details[keys[t]];
					}
					detail_list.push(loc_detail_dict);
				    }
				    arg_dict["usedetails"] = true;
				    arg_dict["details"] = detail_list;
				}
				arg_dict["arg_idx"] = j;
				arg_dict["arg"]= blocks[k]["args"][j]["value"];
				args_list.push(JSON.parse(JSON.stringify(arg_dict)));
			    }
			}
			var opt_args = Object.keys(blocks[k]["args"]);
			for (var j=0; j<opt_args.length; j++) {
			    if ((opt_args[j]%1)!==0 && opt_args[j] != "n_posargs") {
				if (blocks[k]["args"][opt_args[j]] !=='undefined') {
				    if (blocks[k]["args"][opt_args[j]]["details"] != null) {
					var details = blocks[k]["args"][opt_args[j]]["details"];
					var keys = Object.keys(details);
					detail_list = [];
					for (var t=0; t<keys.length; t++) {
					    var loc_detail_dict = {};
					    if (Object.prototype.toString.call(details[keys[t]]) === '[object Array]') {
						if (keys[t] == 'fqdn') {
						    loc_detail_dict["paramater"]='fully qualified name';
						} else {
						    loc_detail_dict["paramater"]=keys[t];
						}
						loc_detail_dict["value"]="(" + details[keys[t]]+")";
					    } else {
						if (keys[t] == 'fqdn') {
						    loc_detail_dict["paramater"]='fully qualified name';
						} else {
						    loc_detail_dict["paramater"]=keys[t];
						}
						loc_detail_dict["value"] =details[keys[t]];
					    }
					    detail_list.push(loc_detail_dict);
					}
					arg_dict["usedetails"]=true;
					arg_dict["details"] = detail_list;
				    }
				    arg_dict["arg_idx"] = j;
				    arg_dict["arg"] = opt_args[j] + "="+blocks[k]["args"][opt_args[j]]["value"];
				    args_list.push(JSON.parse(JSON.stringify(arg_dict)))
				}
			    }
			}
			rep_dict["args"] = args_list;
		    }
		    return_dict = {};
		    return_list = [];
		    if (blocks[k]["returns"]["value"] != null) {
			return_dict["usedetails"] = true;
			return_dict["return"] = blocks[k]["returns"]["value"];
			var details = blocks[k]["returns"]["details"]
			var keys = Object.keys(details);
			detail_list = [];
			for (var t=0; t<keys.length; t++) {
			    var loc_detail_dict = {};
			    if (Object.prototype.toString.call(details[keys[t]]) === '[object Array]') {
				loc_detail_dict["paramater"]=keys[t];
				loc_detail_dict["value"]="(" + details[keys[t]]+")";
			    } else {
				loc_detail_dict["parameter"]=keys[t];
				loc_detail_dict["value"] = details[keys[t]];
			    }
			    detail_list.push(loc_detail_dict);
			}
			return_dict["details"] = detail_list;
		    } else {
			return_dict["return"] = "";
		    };
		    return_list.push(return_dict);
		    rep_dict["returns"] = return_list;
		    2
		    rep_dict["codeLines"] = [];
		    for (var j in blocks[k]["code"]) {
		    	var code = {};
		    	code["code"] = blocks[k]["code"][j];
		    	rep_dict["codeLines"].push(code);
		    }
		    rep_dict["idx"] = idx;
		    idx = idx + 1;
		    method_dict["reps"].push(rep_dict);
		    method_dict["rep"] += 1;
		}
	    }
	    detail_dict["methods"].push(method_dict);
	}
    }
    /** render the detail table and modals */
    var Obj = document.getElementById('templateLogView');
    if(Obj != null) {
    	Obj.parentNode.removeChild(Obj);
    }
    (function(detail_dict){$.when($.ajax({url: 'http://127.0.0.1:8000/detail_table/'}))
			   .done(function(template) {
			       Mustache.parse(template);
			       var rendered = Mustache.render(template,detail_dict);
			       $("#DayView").append(rendered);
			   })
			   .fail(function(){
			       alert("sorry there was an error.");
			   });})(detail_dict);

}  
/** Decorate the python source code so that it is easy to read
* @arg id The HTML id tag to be decorated.
*/
function decorateCode(id) {
    var block = document.getElementById(id);
    Prism.highlightElement(block);
}
