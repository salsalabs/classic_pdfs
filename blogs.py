"""App to retrieve the URLs for  Salsa classic public-facing pages then write
them to disk as PDFs.  Note that this app cannot handle targeted or multi-content
targeted actions."""

import argparse
import datetime
import json
import os
import pdfkit
import re
import requests
import yaml

from bs4 import BeautifulSoup
from pathlib import Path

# The PDF app, wkhtml2pdf, uses these options to format from HTML,
# Global to make it easy to make changes.  Used in OnePage.run().
wkhtml2pdfOptions = {
    'page-size': 'Letter',
    'margin-top': '0.50in',
    'margin-right': '0.50in',
    'margin-bottom': '0.50in',
    'margin-left': '0.50in',
	'load-error-handling': 'ignore',
	'load-media-error-handling': 'ignore',
	'disable-javascript': 'true',
	'disable-local-file-access': 'true',
    'zoom': '1.2'
}

class Spec:
	"""Accessory class to define a public-facing page type in Salsa.  The
	data elements are passed in the keyword argument list."""

	def __init__(self, **kwargs):
		"""  Initialize a Spec object.  The keyword arguments are

		url:          template for the URL of the public-facing page(s)
		table:        table name to read from
		titleField:   field name to use for the title
		keyField:     primary key name
		dateField:    the creation date, or None
		"""
		self.__dict__.update(kwargs)

	def __repr__(self):
		"""String/dump representation of this class. """
		return f"Spec({self.url!r}, {self.table!r}, {self.titleField!r}, {self.keyField!r}, {self.dateField!r})"

class OnePage:
	"""Class to process a single page."""

	def __init__(self, **kwargs):
		""" Initialize an instance of OnePage.  The keyword arguments are
		spec:         instance of Spec
		salsa:        instance of Salsa
		key:          primary key for the page
		pdfs:         directory to use for storing pdfs
		html:	      directory to use for storing htmls
		"""

		self.__dict__.update(kwargs)
		args = {
			'host': self.salsa.host,
			'organization_KEY': self.salsa.orgKey,
			'key': self.key
		}
		self.url = self.spec.url.format(**args)

	def __repr__(self):
		"""String/dump representation of this class. """
		return f"OnePage({self.spec}, {self.salsa}, {self.key}, {self.url})"

	def assureDir(self, filename):
		""" Make sure that the directory exists for the provided filename. """

		d = Path(filename).parent
		if not d.exists():
			try:
				os.makedirs(str(d))
			except FileExistsError:
				pass

	def getHtmlFilename(self, record):
		"""Fabricate a filename using the page spec and a record
		from the API.  The filename should end up containing a date,
		a primary key and the page title or blast subject."""
		return self.getFilename(self.html, record, '.html')

	def getPdfFilename(self, record):
		"""Fabricate a filename using the page spec and a record
		from the API.  The filename should end up containing a date,
		a primary key and the page title or blast subject."""
		return self.getFilename(self.pdfs, record, 'pdf')

	def getFilename(self, dir, record, ext):
		"""Fabricate a filename using the page spec and a record
		from the API.  The filename should end up containing a date,
		a primary key and the page title or blast subject."""

		date = ""
		k = self.key
		if self.spec.dateField != None:
			if len(record[self.spec.dateField]) > 0:
				date = self.parse_date(record[self.spec.dateField])
				k = f" {self.key}"
		pattern = re.compile("[^A-Za-z0-9\\s]")
		x = pattern.sub('', record[self.spec.titleField], 0)
		x = Path(dir).joinpath(self.spec.table, f"{date}{k} {x}.{ext}")
		return str(x)

	def parse_date(self, x):
		"""Parse Salsa Classic date into a datetime.
		Input is like "Mon Oct 09 2017 19:25:56 GMT-0400"
		Output is a datetime object."""

		x = x.split(" GMT")[0].strip()
		f = '%a %b %d %Y %X'
		t = datetime.datetime.strptime(x, f)
		return'{0:%Y-%m-%d}'.format(t)

	def run(self):
		"""Execute `wkhtml2pdf` using a buffer and a filename.  The buffer contains
		the page contents with modifications to correct old and dead Salsa domains. 
		wkhtml2pdf errors are ignored.  Internal errors are noisily fatal."""

		record = self.salsa.getRecord(self.spec, self.key)
		print(self.url)
		pdf = self.getPdfFilename(record)
		if os.path.isfile(pdf):
			print(f"{self.url} skipped")
			return
		self.assureDir(pdf)

		resp = requests.get(self.url)
		soup = BeautifulSoup(resp.text, 'html.parser')
		links = soup.select('a,link,img,script')
		for link in links:
			for k in ['href', 'src']:
				if k in link.attrs:
					v = link[k]
					x = self.scrub(v)
					if x != v:
						link.attrs[k] = x
		
		html = self.getHtmlFilename(record)
		self.assureDir(html)
		with open(html, 'w') as f:
			f.write(str(soup))
			f.close()
		try:
			pdfkit.from_string(str(soup), pdf, wkhtml2pdfOptions)
		except:
			pass

	def scrub(self, v):
		""" Replace old and dead domains with current domains and return the result."""

		v = v.replace('org2.democracyinaction.org', 'org2.salsalabs.com')
		v = v.replace('salsa.democracyinaction.org','org.salsalabs.com')
		v = v.replace('hq.demaction.org','org.salsalabs.com')
		v = v.replace('cid:', 'https:')
		v = re.sub('^/salsa', f"https://{self.salsa.host}/salsa", v)
		v = re.sub('^/o/', f"https://{self.salsa.host}/o/", v)
		v = re.sub('^/dia/', f"https://{self.salsa.host}/dia/", v)
		v = re.sub('^/var/', f"https://{self.salsa.host}/var/", v)
		v = re.sub('true', f"https://{self.salsa.host}/true/", v)
		v = v.replace('#', '%23')
		return v

class Salsa:
	""" Class to do Salsa API things. """

	def __init__(self, cred):
		""" Authenticate with Salsa.  Die a noisy death if that fails.
		Store a requests.Session object with the required cookie(s) in it."""

		self.host = cred['host']
		self.email = cred['email']
		payload = {
			'email': self.email,
			'password': cred['password'],
			'json': True }
		self.session = requests.Session()
		u = f"https://{self.host}/api/authenticate.sjs"
		r = self.session.get(u, params=payload)
		j = r.json()
		if j['status'] == 'error':
			print('Authentication failed: ', j)
			exit(1)
		self.getOrganizationInfo()
		print(f"Salsa: creating PDFs for {self.orgName}")

	def __repr__(self):
		"""String/dump representation of this class. """
		return f"Salsa({self.host!r}, {self.email!r}, {self.orgKey}, {self.orgName})"

	def readKeys(self, spec):
		"""Use the provided spec to read all of the primary keys
		for a table. Returns a list of primary keys."""

		offset = 0
		count = 500
		u = f"https://{self.host}/api/getObjects.sjs"
		keys = []
		while count == 500:
			payload = {
				'json': True,
				'limit': f"{offset},{count}",
				'object': spec.table,
				'include': f"{spec.keyField},{spec.titleField},{spec.dateField}"
			}
			
			r = self.session.get(u, params=payload)
			j = r.json()
			[ keys.append(r[spec.keyField]) for r in j ]
			count = len(j)
			offset = offset + count
		return keys

	def getOrganizationInfo(self):
		"""Read the organization table to retrieve the key and name."""

		u = f"https://{self.host}/api/getObjects.sjs"
		payload = {
			'json': True,
			'offset': '0,2',
			'object': 'organization',
			'include': 'organization_KEY,name'
		}
		r = self.session.get(u, params=payload)
		j = r.json()
		if len(j) >= 0:
			# Need this to skip organization_KEY 0...
			for org in j:
				if org['organization_KEY'] > "0":
					self.orgKey = org['organization_KEY']
					self.orgName = org['name']
					return
		print("getOrganizationInfo: no matching organizations found")
		exit(1)

	def getRecord(self, spec, key):
		"""Use the API to retrieve a record using spec.  Returns the primary key,
		the "title" field and the date, typically Date_Created. Errors are noisily
		fatal."""

		u = f"https://{self.host}/api/getObject.sjs"
		includes = [
			spec.keyField,
			spec.titleField,
			spec.dateField ]

		payload = {
			'json': True,
			'key': key,
			'object': spec.table,
			'include': ",".join(includes)
		}
		r = self.session.get(u, params=payload)
		j = r.json()
		return j

class Main:
	"""Mainline application.  Does the work.  Dies a noisy death on errors."""

	def __init__(self, specs):
		"""Argument descriptions:

		self: Instance variable
		specs: Array of Spec instances to process.
		"""

		self.specList = specs

		parser = argparse.ArgumentParser(description='Find public facing pages and write them as PDFs')
		parser.add_argument('--login', dest='loginFile', action='store',
									help='YAML file with login credentials')
		parser.add_argument('--pdfs', dest='pdfs', action="store", default="./pdfs",
									help="directory to store PDFs.  Created as needed.")
		parser.add_argument('--html', dest='html', action="store", default="./html",
									help="directory to store HTML.  Created as needed.")
		parser.add_argument("--just-blasts", dest="justBlasts", action="store_true", default=False,
									help="just generate pdfs for email blasts")

		self.args = parser.parse_args()
		if self.args.loginFile == None:
			print("Error: --login is REQUIRED.")
			exit(1)
		cred = yaml.load(open(self.args.loginFile))
		self.salsa = Salsa(cred)

	def run(self):
		"""Main authenticates with Salsa and then calls the methods to
		find and "print" pages."""

		pages = []
		if self.args.justBlasts:
			self.specList = [ spec for spec in self.specList if spec.table == "email_blast"]
		for spec in self.specList:
			keys = self.salsa.readKeys(spec)
			for key in keys:
				kwargs = {
					'spec': spec,
					'salsa': self.salsa,
					'pdfs': self.args.pdfs,
					'html': self.args.html,
					'key': key
				}
				task = OnePage(**kwargs)
				pages.append(OnePage(**kwargs))
				task.run()
def main():
	pageSpecs = [
		# API call returns "invalid object/query" for these:
		# * photo_library
		# * post_card
		# * tell_a_friend
		# * thank_you
		Spec(**{
			'url': "https://{host}/o/{organization_KEY}/t/0/blastContent.jsp?email_blast_KEY={key}",
			'table': "email_blast",
			'titleField': "Subject",
			'keyField': "email_blast_KEY",
			'dateField': "Date_Created"
		}),
		Spec(**{
			'url': "http://{host}/o/{organization_KEY}/p/salsa/web/blog/public/index.sjs?blog_entry_KEY={key}",
			'table': "blog_entry",
			'titleField': "Title",
			'keyField': "blog_entry_KEY",
			'dateField': "Display_Date"
		})
	]

	Main(pageSpecs).run()

if __name__ == "__main__":
	main()
