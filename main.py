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

import cgi
import datetime
import urllib
import webapp2

import jinja2
import os

#from google.appengine.ext import webapp
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext.webapp import util

jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


class Greeting(db.Model):
	"""Models an individual Guestbook entry with an author, content, and date."""
	author = db.UserProperty()
	content = db.StringProperty(multiline=True)
	date = db.DateTimeProperty(auto_now_add=True)

def guestbook_key(guestbook_name=None):
	"""Constructs a datastore key for a Guestbook entity with guestbook_name."""
	return db.Key.from_path('Guestbook', guestbook_name or 'default_guestbook')

class MainHandler(webapp2.RequestHandler):
	def get(self):
		user = users.get_current_user()
		
		if user:
			url = users.create_logout_url(self.request.uri)
		else :
			url = users.create_login_url(self.request.uri)

		greetings = Greeting.gql("WHERE ANCESTOR IS :1 ORDER BY date DESC LIMIT 10",guestbook_key())
		#greetings = db.GqlQuery("SELECT * FROM Greeting WHERE ANCESTOR IS :1 ORDER BY date DESC LIMIT 10", guestbook_key())

		self.response.headers['Content-Type'] = 'text/html'
		
		template_values = {
            'user': user,
            'greetings': greetings,
            'url': url,
        }

		template = jinja_environment.get_template('main.html')
		self.response.out.write(template.render(template_values))

class Guestbook(webapp2.RequestHandler):
    def post(self):
	
		greeting = Greeting(parent=guestbook_key())
		if users.get_current_user():
			greeting.author = users.get_current_user()
		greeting.content = self.request.get('content')
		greeting.put()
		
		self.response.headers['Content-Type'] = 'text/html'

		self.response.out.write('You wrote:<pre>')
		self.response.out.write(cgi.escape(self.request.get('content')))
		self.response.out.write('</pre>')

		self.response.out.write("""<a href='/'>home</a>""")
		
def main():
    application = webapp2.WSGIApplication([('/', MainHandler),('/guestbook/sign', Guestbook)], debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
