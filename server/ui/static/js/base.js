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
	    var dates = nb.listDates();
	    var eventdata = [];
	    for(i=0;i<dates.length; i++) {
		eventdata.push({"date": dateFormat(dates[i], "isoDate")});
	    }
	    $('#body').html('<div id="my-calendar"></div></div>');
	    $('#my-calendar').zabuto_calendar({ year: 2016, month: 10, data: eventdata, action: function() {getDayView(this.id, nb, dates); }});
	    var cols = document.getElementsByClassName('event');
	    for(i=0;i<cols.length; i++) {
		cols[i].style.backgroundColor=color;
	    }
	}
    });
}

function getDayView(id,nb,dates) {
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

	    var day_view = document.createElement("table");
	    day_view.setAttribute("id","Calendar Day View");
	    day_view.style.width = '40%';
	    day_view.style.border = 'thin solid #000000';
	    
	    // var dayTable = "<table><tr><th style='width: 100px;'>Hour</th>"
	    // dayTable += "<th style='width:200px;'>Number of entries</th></tr>"

	    var pos = 0;
	    for (hour in intervals) {
		var blocks = ld.getBlocks(hour);
		// for (var i=0; i< blocks.length; i++) {
		// 	console.log(blocks[i]);
		// 	var time_str = String(blocks[i]["timestamp"]);
		// 	console.log(time_str);
		// 	time_str = time_str.split(" ");
		// 	time_str = time_str[4].split(":");
		// 	console.log(time_str[2]);
		// }
		var row = day_view.insertRow(pos);
		var cell1 = row.insertCell(0);
		var cell2 = row.insertCell(1);
		cell1.innerHTML = hour;
		cell2.innerHTML = '<p onclick="get_detailed_view()">'+blocks.length + '</p>';
		cell1.style.border = 'thin solid #000000';
		cell2.style.border = 'thin solid #000000';
		pos += 1;
		// dayTable += "<tr><td style='width: 100px;'>"+hour+"</td>";
		// dayTable += "<td style='width: 100px;'>"+blocks.length+"</td></tr>"
		// console.log(hour);
		// console.log(ld.getBlocks(hour));
	    }
	    var header = day_view.createTHead();
	    var rowh = header.insertRow(0);
	    var cell1 = rowh.insertCell(0);
	    var cell2 = rowh.insertCell(1);
	    cell1.innerHTML = 'Hour';
	    cell2.innerHTML = 'Number of entries';
	    cell1.style.border = 'medium solid #000000';
	    cell2.style.border = 'medium solid #000000';
	    cell1.style.width = '50%';
	    cell2.style.width = '50%';
	    day_view.style.textAlign = 'center';
	    // dayTable += "</table>";
	    // day_view.innerHTML = dayTable;
	    document.getElementById("body").appendChild(day_view);
	}
    }
}

function get_detailed_view(blocks) {
    console.log("hello");
}
