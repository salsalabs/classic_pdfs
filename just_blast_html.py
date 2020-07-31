"""App to retrieve the HTML for completed email blasts.  The HTML is 
written to a file that the user specifies.  Note that blasts that have
not been sent are not saved.  Note, too, that all of the links reference
a Salsa Classic account.  If the account goes away, then the emails will
not have any images."""

import argparse
import datetime
import os
import queue
import re
import requests
import threading
import time
import yaml

from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urljoin

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

class OnePage(threading.Thread):
	"""Class to process a single page."""

	def __init__(self, taskName, taskQueue, queueLock):
		""" Initialize an instance of OnePage.  The keyword arguments are
		spec:         instance of Spec. Defines the database parts.
		salsa:        instance of Salsa.  Defines how to get to Salsa.
		key:          primary key for the page
		html:	      directory to use for storing htmls
		"""
		threading.Thread.__init__(self)
		self.taskName = taskName
		self.taskQueue = taskQueue
		self.queueLock = queueLock
		self.exitFlag = 0

	def __repr__(self):
		"""String/dump representation of this class. """
		return f"OnePage:{self.taskName}({self.spec}, {self.salsa}, {self.key}, {self.url})"

	def assureDir(self, filename):
		""" Make sure that the directory exists for the provided filename. """

		d = Path(filename).parent
		if not d.exists():
			try:
				os.makedirs(str(d))
			except FileExistsError:
				pass

	def getHtmlFilename(self, dir, record, ext):
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
		x = pattern.sub('', record[self.spec.titleField], 0).strip()
		x = Path(self.html).joinpath(self.spec.table, f"{date}{k} {x}.{ext}")
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
		"""Process a queue of email_blast_KEYs. Create and print HTML for each key."""
		while not self.exitFlag:
			self.queueLock.acquire()
			if self.taskQueue.empty():
				self.queueLock.release()
				time.sleep(1)
			else:
				task = self.taskQueue.get()
				self.queueLock.release()
				self.handleTask(task)
	
	def handleTask(self, task):
		"""Process a task."""
		self.__dict__.update(task)

		record = self.salsa.getRecord(self.spec, self.key)
		args = {
			'host': self.salsa.host,
			'organization_KEY': self.salsa.orgKey,
			'key': self.key
		}
		self.url = self.spec.url.format(**args)

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

		html = self.getHtmlFilename(self.html, record, 'html')
		self.assureDir(html)
		with open(html, 'w') as f:
			f.write(str(soup))
			print(f"{self.taskName} {html}")
			f.close()

	def scrub(self, v):
		""" Replace old and dead domains with current domains and return the result."""
		host = f"https://{self.salsa.host}"
		v = v.replace('org2.democracyinaction.org', 'org2.salsalabs.com')
		v = v.replace('salsa.democracyinaction.org','org.salsalabs.com')
		v = v.replace('hq.demaction.org','org.salsalabs.com')
		v = v.replace('cid:', 'https:')
		v = urljoin(host, v)
		v = re.sub('^/salsa', f"https://{self.salsa.host}/salsa", v)
		v = re.sub('^/o/', f"https://{self.salsa.host}/o/", v)
		v = re.sub('^/dia/', f"https://{self.salsa.host}/dia/", v)
		v = re.sub('^/var/', f"https://{self.salsa.host}/var/", v)
		v = re.sub('true', f"https://{self.salsa.host}/true/", v)
		v = v.replace('#', '%23')
		return v

	def setExitFlag(self):
		"""Sets the exit flag.  This task will exit at the next pass."""
		self.exitFlag = 1
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
		print(f"Salsa: creating email blast HTML files for {self.orgName}")

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
				'include': f"{spec.keyField},{spec.titleField},{spec.dateField},Stage"
			}
			r = self.session.get(u, params=payload)
			j = r.json()
			[ keys.append(r[spec.keyField]) for r in j if r['Stage'] == 'Complete']
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

	def __init__(self):

		# Get command-line arguments.  Errors are fatal.

		parser = argparse.ArgumentParser(description='Write completed files to disk as HTML')
		parser.add_argument('--login', dest='loginFile', action='store',
									help='YAML file with login credentials and list of pages to process')
		parser.add_argument('--html', dest='html', action="store", default="./html",
									help="directory to store HTML.  Created as needed.")

		self.args = parser.parse_args()
		if self.args.loginFile == None:
			print("Error: --login is REQUIRED.")
			exit(1)
		cred = yaml.load(open(self.args.loginFile))
		self.salsa = Salsa(cred)
		self.spec = Spec(**{
			'url': "https://{host}/o/{organization_KEY}/t/0/blastContent.jsp?email_blast_KEY={key}",
		 	'table': "email_blast",
		 	'titleField': "Subject",
		 	'keyField': "email_blast_KEY",
		 	'dateField': "Date_Created"
		 })

		threadCount = 10
		taskQueue = queue.Queue()
		queueLock = threading.Lock()

		queueLock.acquire()
		self.fill(taskQueue)
		queueLock.release()		

		threads = [OnePage(f"Task-{(i+1):02}", taskQueue, queueLock) for i in range(0, threadCount)]
		[t.start() for t in threads]
		while not taskQueue.empty():
			pass

		[t.setExitFlag() for t in threads]
		[t.join() for t in threads]
		print("Done!")

	def fill(self, taskQueue):
		""" Read all blast keys and fill the queue with tasks for each key. """

		keys = self.salsa.readKeys(self.spec)
		print(f"Found {len(keys)} completed email blasts.")
		for key in keys:
			task = {
				'spec': self.spec,
				'salsa': self.salsa,
				'html': self.args.html,
				'key': key
			}
			taskQueue.put(task)

def main():
	Main()

if __name__ == "__main__":
	main()
