$(document).ready(function() {
    $("#projects").on("click", create_projects);
});

function create_projects() {
    var proj_nav = $('#projects_nav');
    if (proj_nav.length >0) {
	// console.log(parseInt(proj_nav.css("top").split(".")[0]));
	if (parseInt(proj_nav.css("top").split(".")[0]) > 0) {
	    $('#projects_nav').animate({top: "-37pt",},"10");
	} else {
	    $('#projects_nav').animate({top: "+37pt",},"10");
	}
    } else {
	$.ajax({
	    url: 'http://127.0.0.1:8000/nav/',
	    success: function(data) {
		$('body').prepend(data);
		$('#projects_nav').animate({top: "37pt",},"10");
	    }});
    }
};

function create_tasks(proj) {
    var proj_name = '#'+proj
    // console.log(proj);
    // console.log($(proj_name).length);
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
			//$('#tasks_nav').animate({top: "37pt",},"10");
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

function render_project(proj_path,color) {
    $.ajax({
	url: 'http://127.0.0.1:8000/view_proj/',
	data: proj_path,
	success: function(result) {
	    db = JSON.parse(result);
            nb = new acorn.Notebook(db, proj_path);
	    window.curr_nb = nb
	    var dates = nb.listDates();
	    var eventdata = [];
	    for(i=0;i<dates.length; i++) {
		eventdata.push({"date": dateFormat(dates[i], "isoDate"),"color":color});
	    }
	    $('#body').html('<div id="my-calendar"></div><div id="DayView"></div>');
	    $('#my-calendar').zabuto_calendar({ year: 2016, month: 10, data: eventdata, action: function() {getDayView(this.id, dates); }});
	}
    });
}

function getDayView(id,dates) {
    var nb = window.curr_nb
    var date = $("#"+id).data("date");
    for(i=0;i<dates.length;i++) {
	if (date == dateFormat(dates[i], "isoDate")) {
	    var date_entries = nb.getEntriesByDate(new Date(dates[i]));
	    var intervals = {};
	    var hours = [];
	    for (uuid in date_entries) {
		var d_entries = date_entries[uuid];
		var init_date = d_entries[0]['s'];
		var old_hour = init_date.getHours();
		var old_min = init_date.getMinutes();
		var temp_entries = [];
		for (var j=0; j<d_entries.length; j++ ) {
		    var uuid_date = new Date(d_entries[j]['s']);
		    var cur_hour = uuid_date.getHours();
		    var cur_min = uuid_date.getMinutes();
		    if (!(cur_hour in intervals)) {
			intervals[cur_hour] = [];
		    }
		    if (cur_hour == old_hour) {
			if (cur_min == old_min) {
			    temp_entries.push(d_entries[j]);
			} else {
			    var temp_interval = new acorn.LogInterval(cur_hour,old_min,temp_entries,nb)
			    intervals[cur_hour].push(temp_interval);
			    temp_entries = [d_entries[j]];
			    old_min = cur_min;
			}
			
		    } else {
			var temp_interval = new acorn.LogInterval(old_hour,old_min,temp_entries,nb)
			intervals[old_hour].push(temp_interval);
			old_hour = cur_hour;
			old_min = cur_min;
			temp_entries = [d_entries[j]];			
		    }
		    
		    
		}
		var temp_interval = new acorn.LogInterval(cur_hour,cur_min,temp_entries,nb)
		intervals[cur_hour].push(temp_interval);
	    }
	    ld = new acorn.LogDay(nb,intervals,new Date(dates[i]));

	    window.curr_log_day = ld;
	    var view = {};
	    view["hours"] = [];
	    for (hour in intervals) {
		var temp_view = {};
		temp_view["hour"] = hour;
	    	var blocks = ld.getBlocks(hour);
		var first_blocks = [];
		var last_blocks = [];
	    	for (var i=0; i< blocks.length; i++) {
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
		temp_view["first"] = first_blocks.length;
		temp_view["second"] = last_blocks.length;
		view["hours"].push(temp_view);
	    }
	    
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

function get_detailed_view(hour,spot) {
    var nb = window.curr_nb
    var ld = window.curr_log_day;
    var blocks = ld.getBlocks(hour);
    var first_blocks = [];
    var last_blocks = [];
    for (var i=0; i< blocks.length; i++) {
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
    if (spot === 'f') {
	blocks = first_blocks;
    } else {
	blocks = last_blocks;
    }

    var detail_dict = {};
    detail_dict["methods"] = [];
    var methods = [];
    for (var i=0; i<blocks.length; i++) {
	var def = blocks[i]["method"];
	def = def.split(".");
	def = def[def.length-1];
	if ($.inArray(def,methods) <0) {
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
	    if (blocks[i]["args"]["n_posargs"] < 1) {
		var args_list = [];
		var arg_dict = {};
		arg_dict["arg"] = "()"
		args_list.push(arg_dict);
		rep_dict["args"] = args_list;
	    } else {
		var args_list = [];
		for (var j= 0; j < blocks[i]["args"]["n_posargs"]; j++) {
		    var arg_dict = {};
		    arg_dict["arg"]= blocks[i]["args"][j]["value"];
		    args_list.push(arg_dict);
		}
		rep_dict["args"] = args_list;
	    }
	    rep_dict["return"] = blocks[i]["return"];
	    rep_dict["codeLines"] = [];
	    for (var k in blocks[i]["code"]) {
		var code = {};
		code["code"] = blocks[i]["code"][k];
		rep_dict["codeLines"].push(code);
	    }
	    method_dict["reps"].push(rep_dict);
	    for (var k=i+1; k<blocks.length; k++) {
		var def_j = blocks[k]["method"].split(".");
		def_j = def_j[def_j.length-1];
		if (def_j == def) {
		    rep_dict = {};
		    var time_str = String(blocks[k]["timestamp"]);
		    time_str = time_str.split(" ");
		    time_str = time_str[4];
		    rep_dict["time"] = time_str;
		    if (blocks[i]["args"]["n_posargs"] < 1) {
			var args_list = [];
			var arg_dict = {};
			arg_dict["arg"] = "()"
			args_list.push(arg_dict);
			rep_dict["args"] = args_list;
		    } else {
			var args_list = [];
			for (var j= 0; j < blocks[i]["args"]["n_posargs"]; j++) {
			    var arg_dict = {};
			    arg_dict["arg"]= blocks[i]["args"][j]["value"];
			    args_list.push(arg_dict);
			}
			rep_dict["args"] = args_list;
		    }
		    rep_dict["return"] = blocks[k]["return"];
		    rep_dict["codeLines"] = [];
		    for (var j in blocks[k]["code"]) {
			var code = {};
			code["code"] = blocks[k]["code"][j];
			rep_dict["codeLines"].push(code);
		    }
		    method_dict["reps"].push(rep_dict);
		    method_dict["rep"] += 1;
		}
	    }
	    detail_dict["methods"].push(method_dict);
	}
    }
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
