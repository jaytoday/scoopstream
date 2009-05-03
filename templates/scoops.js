
var DEFAULT_USER_TEXT = "username";
var DEFAULT_PLEDGE_TEXT = "1";

$(function() {


$('div.flag').find('a').click(function(){
	var $scoop_key = $(this).attr('id')
	var $this_panel = $(this).parents('div.panel:first')
	$this_panel.animate({opacity: 0}, 300).slideUp(1000);

	
	$.ajax({
		type: "GET", 
		url: '/rpc',
		data:
			{
					action: "flag_scoop",
					scoop_key: $scoop_key
			},
		error: function() { container.html("Error Refreshing Subjects"); },
		success: function(response) { },
		complete: function(data) { }
	});  
	
		
});

	
});
