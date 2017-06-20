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
	    for (uuid in date_entries) {
		var uuid_date = new Date(date_entries[uuid][0]['s']);
		var temp_interval = new acorn.LogInterval(uuid_date.getHours(),uuid_date.getMinutes(),date_entries[uuid],nb);
		intervals[uuid_date.getHours()] = temp_interval;
	    }
	    ld = new acorn.LogDay(nb,intervals,new Date(dates[i]));
	    var Obj = document.getElementById('Calendar Day View');
	    if(Obj != null) {
		Obj.parentNode.removeChild(Obj);
	    }

	    // var day_view = document.createElement("table");
	    // day_view.setAttribute("id","Calendar Day View");
	    // day_view.style.width = '40%';
	    // day_view.style.border = 'thin solid #000000';
	    // var tbl = document.createElement('div');
	    // tbl.setAttribute('id', 'Calendar Day View');
	    // var dayTable = "<table border=1 style='width:35%; float:left;'><tr><th style='width:50%; text-align:center;' colspan='2'>Hour</th><th style='width:50%; text-align:center;'>Number of entries</th></tr>"
	    var view = {};
	    view["hours"] = [];
	    for (hour in intervals) {
		var temp_view = {};
		temp_view["hour"] = hour;
	    	var blocks = ld.getBlocks(hour);
		var first_blocks = [];
		var last_blocks = [];
	    	for (var i=0; i< blocks.length; i++) {
	    	    var time_str = String(blocks[i]["timestamp"]);
	    	    time_str = time_str.split(" ");
	    	    time_str = time_str[4].split(":");
		    if (+time_str[1] < 30) {
			first_blocks.push(blocks[i]);
		    } else {
			last_blocks.push(blocks[i]);
		    }
	    	}
		temp_view["first"] = first_blocks.length;
		temp_view["second"] = last_blocks.length;
		view["hours"].push(temp_view);
		// var details = get_detailed_view_html(first_blocks);
	    	// dayTable += "<tr><td style='text-align:center;' rowspan='2'>"+hour+"</td><td style='text-align:center;'> 00-29 </td><td style='text-align:center; cursor:pointer;' onmouseover='' onclick=function(){insert_detailed_view("+first_blocks+")}'>"+first_blocks.length+"</td></tr>"
		// var details = get_detailed_view_html(last_blocks);
		// dayTable += "<tr><td style='text-align:center;'> 30-59 </td><td style='text-align:center; cursor:pointer;' onmouseover='' onclick=function(){insert_detailed_view("+last_blocks+")}'>"+last_blocks.length+"</td></tr>"		
	    }
	    console.log(view);
	    $("#templates").load("template.html #templateDayView",function() {
		var template = document.getElementById('templateDayView').innerHTML;
		console.log(template);
		var output = Mustache.render(template,view);
		console.log(output);
		$("#DayView").html(output);		    
	    });
	    console.log("HHH");
	    // dayTable += "</table>"
	    // var detailTable = "<table id='Log Details' border=1 style='width:60%; float:right;'><tr><th  colspan='2' style='text-align:center;'>Log Interval Details</th></tr>"
	    // detailTable += "</table>"
	    // tbl.innerHTML = dayTable+detailTable;
	    // var parent = document.getElementById('body');
	    // parent.parentNode.insertBefore(tbl,parent.nextSibling);
	}
    }
}

function get_detailed_view_html(blocks) {
    html = "<tr><th  colspan='2' style='text-align:center;'>Log Interval Details</th></tr>"
    for (vari=0; i<blocks.length; i++) {
	html += "<tr><td colspan='2' style='text-align:center';>"+blocks[i]["timestamp"]+"</td></tr>";
	html += "<tr><td style='text-align:center;'>method</td><td style='text-align:center>"+blocks[i]["method"]+"</td></tr>";
	html += "<tr><td style='text-align:center;'>code</td><td style='text-align:center cursor:pointer;' onmouseover=''>view code</td></tr>";
	html += "<tr><td style='text-align:center;'>arguments</td><td style='text-align:center' cursor:pointer;' onmouseover=''>view arguments</td></tr>";
        if (blocks[i]["instance"] != null) {
	        html += "<tr><td style='text-align:center;'>instance</td><td style='text-align:center'>"+blocks[i]["instance"]+"</td></tr>";
        }
        if (blocks[i]["elapsed"] != null) {
	        html += "<tr><td style='text-align:center;'>elapsed</td><td style='text-align:center'>"+blocks[i]["elpased"]+"</td></tr>";
        }
	html += "<tr><td style='text-align:center;'>returns</td><td style='text-align:center' cursor:pointer;' onmouseover=''>view result</td></tr>";
	console.log(blocks[i]);
    }
    return html
}

function insert_detailed_view(html) {
    console.log("Hello");
}
