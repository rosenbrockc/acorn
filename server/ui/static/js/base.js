$(document).ready(function() {
    $("#projects").on("click", create_projects);
});

function create_projects() {
    var proj_nav = $('#projects_nav');
    if (proj_nav.length >0) {
	console.log(parseInt(proj_nav.css("top").split(".")[0]));
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
    console.log("HERE");
    var proj_name = '#'+proj
    console.log($(proj_name).length);
    $.ajax({
    	url: 'http://127.0.0.1:8000/sub_nav/',
    	success: function(result) {
	    taskres = $(result);
	    taskres.toggleClass("hidden");
    	    $('#projectsul').fadeOut(500, function() {
		$.ajax({
		    url: 'http://127.0.0.1:8000/sub_nav_list/',
		    data: proj,
		    success: function(result) {
			$('#tasks').append(result).toggleClass("hidden").fadeIn(500);
			//$('#tasks_nav').animate({top: "37pt",},"10");
		    }});
		$('#projectsul').before(taskres);
		$('#tasks_back').on('click', function () {
		    $('#tasks').fadeOut(500);
		    $('#projectsul').fadeIn(500);
		    $('#tasks').remove();
		    $('#tasks_back').remove();
		}).show().toggleClass("hidden");
	    });
	    
    	}
    });    
};
