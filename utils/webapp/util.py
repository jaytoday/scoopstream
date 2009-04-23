#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""Convience functions for the Webapp framework."""





__all__ = ["login_required", "run_wsgi_app", "admin_only"]

import logging
import os
import sys
import wsgiref.util
from utils.appengine_utilities.sessions import Session
from google.appengine.api import users
from google.appengine.ext import webapp


def login_required(handler_method):   # this should be altered. 
  """A decorator to require that a user be logged in to access a handler.

  To use it, decorate your get() or post() method like this:

    @login_required
    def get(self):
      user = users.GetCurrentUser(self)
      self.response.out.write('Hello, ' + user.nickname())

  We will redirect to a login page if the user is not logged in. We always
  redirect to the request URI, and Google Accounts only redirects back as a GET request,
  so this should not be used for POSTs.
  """
  def check_login(self, *args):
    if self.request.method != 'GET':
      raise webapp.Error('The check_login decorator can only be used for GET '
                         'requests')
    session = Session()  
    if not session['user']: 
        self.session['continue'] = self.request.path
        self.redirect('/login/')
        return
    else:
      handler_method(self, *args)
  return check_login


# PQ Variation that checks if a user is not a sponsor.  

def quiztaker_required(handler_method):   # this should be altered. 
  """A decorator to require that a user be logged in to access a handler.

  To use it, decorate your get() or post() method like this:

    @login_required
    def get(self):
      user = users.GetCurrentUser(self)
      self.response.out.write('Hello, ' + user.nickname())

  We will redirect to a login page if the user is not logged in. We always
  redirect to the request URI, and Google Accounts only redirects back as a GET request,
  so this should not be used for POSTs.
  """
  def check_login(self, *args):
    if self.request.method != 'GET':
      raise webapp.Error('The check_login decorator can only be used for GET '
                         'requests')
    session = Session()
    from model.user import Profile
    this_user = Profile.get_by_key_name(self.session['user'].unique_identifier)
    if this_user.is_sponsor is True:
        self.session['user'] = False
        self.session['continue'] = self.request.path
        self.redirect('/login/?sponsor=true')
        return
        
        
    else:
      handler_method(self, *args)
  return check_login









def run_wsgi_app(application):
  """Runs your WSGI-compliant application object in a CGI environment.

  Compared to wsgiref.handlers.CGIHandler().run(application), this
  function takes some shortcuts.  Those are possible because the
  app server makes stronger promises than the CGI standard.
  """
  env = dict(os.environ)
  env["wsgi.input"] = sys.stdin
  env["wsgi.errors"] = sys.stderr
  env["wsgi.version"] = (1, 0)
  env["wsgi.run_once"] = True
  env["wsgi.url_scheme"] = wsgiref.util.guess_scheme(env)
  env["wsgi.multithread"] = False
  env["wsgi.multiprocess"] = False
  result = application(env, _start_response)
  if result is not None:
    for data in result:
      sys.stdout.write(data)


def _start_response(status, headers, exc_info=None):
  """A start_response() callable as specified by PEP 333"""
  if exc_info is not None:
    raise exc_info[0], exc_info[1], exc_info[2]
  print "Status: %s" % status
  for name, val in headers:
    print "%s: %s" % (name, val)
  print
  return sys.stdout.write


def get_debug_mode():
	if os.environ.get('SERVER_SOFTWARE','').startswith('Devel'):
		return True
	elif os.environ.get('SERVER_SOFTWARE','').startswith('Goog'):
		return False
	else:
		return False



def admin_only(handler_method):   # this should be altered. 
  """A decorator to require that a user be logged in to access a handler.

  To use it, decorate your get() or post() method like this:

    @login_required
    def get(self):
      user = users.GetCurrentUser(self)
      self.response.out.write('Hello, ' + user.nickname())

  We will redirect to a login page if the user is not logged in. We always
  redirect to the request URI, and Google Accounts only redirects back as a GET request,
  so this should not be used for POSTs.
  """
  def check_admin(self, *args):
    raise webapp.Error('aaa')
    handler_method(self, *args)
    return check_admin
      	
    if authorized():
    	return self
    else:
    	self.redirect('/s/')


def authorized(handler):
	"""Return True if user is authenticated."""
	user = users.get_current_user()
	if not user:
		handler.redirect('/login')
	else:
		#auth_user = Admin.gql("where user = :1", user).get()
		auth_user = False
		if not auth_user:
		  logging.warning('An unauthorized user has attempted to enter an authorized page')
		  handler.redirect('/')
		  return False
		else:
			return True
			
