def url_routes(map):


	#Public Views
	map.connect('', controller = 'views:MainPage')
	map.connect('bot', controller = 'views:TwitterBot')
								
	#XML-RPC
	map.connect('/rpc', controller = 'rpc:RPCHandler')

																	 
	#Utils
	map.connect('404 error', '*url/:not_found', controller = 'utils.utils:NotFoundPageHandler')
	map.connect('404 error', '*url', controller = 'utils.utils:NotFoundPageHandler')
	   
    
