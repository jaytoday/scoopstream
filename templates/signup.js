
var DEFAULT_USER_TEXT = "username";
var DEFAULT_PLEDGE_TEXT = "1";

$(function() {

var user_input = $('div#user').find('input');
user_input.val(DEFAULT_USER_TEXT);
var pledge_input = $('div#pledge').find('input');
pledge_input.val(DEFAULT_PLEDGE_TEXT);


$('div.add').find('button').click(function(){
	
	var user = user_input.val();
	var pledge = pledge_input.val();
	var container = $('div.add_autotip');
	
	if (user.length < 1 || user == DEFAULT_USER_TEXT) return alert("Please enter a username ");
	if (pledge.length < 1) return alert("Please enter a pledge ");
	
	$.ajax({
		type: "GET", 
		url: '/rpc',
		datatype: "html",
		data:
			{
					action: "add_autotip",
					user: user,
					pledge: pledge
			},
		error: function() { container.html("Error Refreshing Subjects"); },
		success: function(response) { alert(response); },
		complete: function(data) { container.data('refreshing', false); }
	});  
	
		
});

	
});
