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
import json
import logging
import jinja2
import os
import base64
import datetime

#load fileupload.py
#from fileupload import *

#from google.appengine.ext import webapp
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext.webapp import util

jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

logger = logging.getLogger('main')

"""Models an individual Guestbook entry with an author, content, and date."""
class Greeting(db.Model):
	author = db.UserProperty()
	content = db.StringProperty(multiline=True)
	date = db.DateTimeProperty(auto_now_add=True)

"""Constructs a datastore key for a Guestbook entity with guestbook_name."""
def guestbook_parent(guestbook_name=None):
	return db.Key.from_path('Guestbook', guestbook_name or 'default_guestbook')


"""Models a non profit shelter."""
class Organization(db.Model):
	name = db.StringProperty(required=True,multiline=False)
	description = db.StringProperty(multiline=True)
	address = db.StringProperty(multiline=True)
	phone = db.StringProperty(multiline=False)
	website = db.StringProperty(multiline=False)
	email = db.StringProperty(multiline=False)
	date = db.DateTimeProperty(auto_now_add=True)
	pic = db.BlobProperty()
	picMime = db.StringProperty(multiline=False)

def organization_parent(org_name=None):
	return db.Key.from_path('Organization', org_name or 'default_')

"""Models a user in an Organization for managing the organization (parent=Organization)."""
class OrganizationUser(db.Model):
	orguser = db.UserProperty(required=True)

"""Models a Dog in an Organization (parent=Organization)"""
class Dog(db.Model):
	creator = db.UserProperty()
	name = db.StringProperty(required=True,multiline=False)
	breed = db.StringProperty(required=True,multiline=False)
	date = db.DateTimeProperty(auto_now_add=True)
	pic = db.BlobProperty()
	picMime = db.StringProperty(multiline=False)
	deathRow = db.BooleanProperty()
	deathRowDate = db.DateProperty()

class MainHandler(webapp2.RequestHandler):
	def get(self):
		user = users.get_current_user()
		
		if user:
			url = users.create_logout_url(self.request.uri)
		else :
			url = users.create_login_url(self.request.uri)


		orgs = Organization.gql("WHERE ANCESTOR IS :1 ORDER BY date DESC LIMIT 100", organization_parent())
		dogs = db.GqlQuery("SELECT * FROM Dog ORDER BY date DESC"); #Dog.gql("WHERE date != NULL ORDER BY date DESC LIMIT 100")
		greetings = Greeting.gql("WHERE ANCESTOR IS :1 ORDER BY date DESC LIMIT 100",guestbook_parent())
		#greetings = db.GqlQuery("SELECT * FROM Greeting WHERE ANCESTOR IS :1 ORDER BY date DESC LIMIT 10", guestbook_parent())

		userOrgs = OrganizationUser.gql("WHERE orguser = :1 LIMIT 10", user)

		self.response.headers['Content-Type'] = 'text/html'

		template_values = {
            'user': user,
			'url': url,
            'greetings': greetings,
			'orgs': orgs,
			'userOrgs': userOrgs,
			'dogs': dogs,
        }

		template = jinja_environment.get_template('main.html')
		self.response.out.write(template.render(template_values))


class SignGuestbook(webapp2.RequestHandler):
    def post(self):
	
		greeting = Greeting(parent=guestbook_parent())
		if users.get_current_user():
			greeting.author = users.get_current_user()
		greeting.content = self.request.get('content')
		greeting.put()
		
		self.response.headers['Content-Type'] = 'text/html'

		self.response.out.write('You wrote:<pre>')
		self.response.out.write(cgi.escape(self.request.get('content')))
		self.response.out.write('</pre>')

		self.response.out.write("""<a href='/'>home</a>""")
		
class ViewOrg(webapp2.RequestHandler):
	def get(self):
		user = users.get_current_user()
		
		if user:
			url = users.create_logout_url(self.request.uri)
		else :
			url = users.create_login_url(self.request.uri)

		org = db.get(self.request.get('key'))
		dogs = Dog.gql("WHERE ANCESTOR IS :1 ORDER BY date DESC LIMIT 100", org)
		userOrgs = OrganizationUser.gql("WHERE ANCESTOR IS :1 AND orguser = :2 LIMIT 1", org, user)
		userOrg = None
		for t in userOrgs:
			userOrg = t
		
		self.response.headers['Content-Type'] = 'text/html'

		template_values = {
            'user': user,
			'url': url,
            'org': org,
            'dogs': dogs,
            'userOrg': userOrg,
        }

		template = jinja_environment.get_template('vieworg.html')

		self.response.out.write(template.render(template_values))


class ViewRegisterOrg(webapp2.RequestHandler):
    def get(self):

		user = users.get_current_user()
	
		template_values = {
            'user': user,
        }

		template = jinja_environment.get_template('registerorg.html')
		self.response.headers['Content-Type'] = 'text/html'
		self.response.out.write(template.render(template_values))

class RegisterOrgSubmit(webapp2.RequestHandler):
    def post(self):
	
		user = users.get_current_user()
		
		if user:
			url = users.create_logout_url(self.request.uri)
		else :
			self.error(401)
			return

		org = Organization(parent=organization_parent(),name=self.request.get('name'))
		org.description = self.request.get('description')
		org.address = self.request.get('address')
		org.phone = self.request.get('phone')
		org.email = self.request.get('email')
		org.put()
		
		orgUser = OrganizationUser(parent=org.key(), orguser=user);
		orgUser.put()
		
		template_values = {
            'user': user,
			'url': url,
            'org': org,
        }

		template = jinja_environment.get_template('vieworg.html')
		self.response.headers['Content-Type'] = 'text/html'
		self.response.out.write(template.render(template_values))

class AddDogSubmit(webapp2.RequestHandler):
    def post(self):
	
		user = users.get_current_user()
		
		org = db.get(self.request.get('org'))

		userOrgs = OrganizationUser.gql("WHERE ANCESTOR IS :1 AND orguser = :2 LIMIT 1", org, user)
		userOrg = None
		for t in userOrgs:
			userOrg = t

		dog = Dog(parent=org,name=self.request.get('name'),breed=self.request.get('breed'))		
		dog.creator = users.get_current_user()
		datetext = self.request.get('deathrowdate')
		if datetext:
			if len(datetext) > 0:
				dog.deathRow = True
				dog.deathRowDate =  datetime.datetime.strptime(datetext, "MM/DD/YYYY")
		dog.put()
		
		reply = self.request.get('reply');
		if 'json' == reply:
			self.response.headers['Content-Type'] = 'application/json'
			self.response.out.write(json.dumps({'success': 'true', 'id': dog.key().id()}))
		elif 'dog' == reply:
			
			template_values = {
				'user': user,
            	'dog': dog,
            	'userOrg': userOrg,
        	}

			self.response.headers['Content-Type'] = 'text/html'
			template = jinja_environment.get_template('parts/dog.html')
			self.response.out.write(template.render(template_values))
		else:
			self.response.headers['Content-Type'] = 'application/json'
			self.response.out.write(json.dumps({'success': 'true', 'id': dog.key().id()}))
		
class SetDogPic(webapp2.RequestHandler):
    def post(self):
	
		user = users.get_current_user()
		
		dog = Dog.get(self.request.get('dog'))

		# data:image/jpeg;base64,/9j/4AA....
		pic = self.request.get('pic');
		
		if pic.startswith('data:image/jpeg;base64,'):
			dog.pic = base64.b64decode(pic[23:])
			dog.picMime = 'image/jpeg'
			dog.put()

			self.response.headers['Content-Type'] = 'application/json'
			self.response.out.write(json.dumps({'success': 'true'}))

		else:
			self.error(500)

class GetDogPic(webapp2.RequestHandler):
    def get(self):
	
		user = users.get_current_user()
		
		dog = Dog.get(self.request.get('dog'))

		if dog.pic:
			self.response.headers['Content-Type'] = dog.picMime
			self.response.out.write(dog.pic)
		else:
			self.error(404)

def main():
    application = webapp2.WSGIApplication([
										('/', MainHandler),
										('/guestbook/sign', SignGuestbook),
										('/org/register', ViewRegisterOrg),
										('/org/registersubmit', RegisterOrgSubmit),
										('/org/view', ViewOrg),
										('/dog/addsubmit', AddDogSubmit),
										('/dog/setpic', SetDogPic),
										('/dog/pic', GetDogPic),
										#('/upload', UploadHandler),
										#('/img', DownloadHandler),
										], debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
