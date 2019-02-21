# classic_pdfs
Create PDFs for email blasts and most public-facing pages.

# Background
Sometimes, Salsa's clients would like to have PDFs of their email blasts and public-facing pages.  This application creates those PDFs.

## PDFs can be generated for these items
This application can create PDFs for these items in Salsa Classic.

* blind targeted action
* content_item
* donate_page
* email_blast
* event
* petition
* signup_page
* storefront
* unsubscribe_page

## PDFs cannot be generated for these items

* photo_library
* multi-content targeted actions (MCTA)
* post_card
* targeted actions
* tell_a_friend
* thank_you

(Okay, so technically the app can create PDFs for the first page of targeted
and multi-content targeted actions.  That's the address and ZIP page and is
generally not very interesting.  There's not a way to show the second page
of a Classic targeted action workflow.)

## Alternatives

* The easiest alternative is to visit each of the pages and save/print them as PDF files.
* Use a PDF generator like [`wkhtmltopdf`](https://wkhtmltopdf.org/) or [`weasyprint`](https://weasyprint.org/) to create PDFs without a browser.

## Cautions

* Time passes, systems change, domains are created and removed.

    That means that it's entirely possible that an image or script used in one of your
pages or blasts may have disappeared completely.  When that happens, this app
just ignores any errors and continues. You'll get the text and whatever
images can be found.

* This app does not run scripts.

    Web pages use scripts to make changes to their structure
    and appearance.  This app does its best to run scripts if
    they can be retrieved.  Sometimes that doesn't work. You
    will see the body and the plain structure of the page.  You
    may not see some of the fancy work.

Again, if stuff is missing, then you can always [use an alternative](#alternatives).

# Installation

Use this section to fully install the application.

## Prerequisites

#### Python 3
The application is designed with Python version 3 (`python3`).  The application _will not_ woth with Python 2.7.x.

Please [click here](https://www.python.org/downloads/) to install Python 3.

#### git
The application is stored on a GitHub repository.  You'll need
a copy of the `git` tools on your computer in order to retrieve
that repository.  Please [click here](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) to see a nice article about installing git.

### wkhtmltopdf
The application uses `wkhtmltopdf` to convert HTML into PDFs.  [Click here](https://wkhtmltopdf.org/) to download the wkhtmltopdf application.

It's a snap to install in Windows or Linux. OSX? Not that easy.

You'll need to read [OSX: About Gatekeeper](https://support.apple.com/en-us/HT202491). See the section named "How to open an app from a unidentified developer and exempt it from Gatekeeper". Use the instructions on the wkhtmltopdf package file. Right click on the package file and follow the instructions.

### Warning

**Do not contact Salsalabs Support for help with installing any of this stuff.**  Salsa is not in that business. There are tons of very good sites out there that you can use for help with getting the prequisites installed.

## installation

This installation works best in a shell environment.  Typically, that's `bash`.  The rough equivalent in Windows is a terminal window.

Commands in this section will be `bash` commands.  Sorry, but you're on your own if you're using Windows.

### TL;DR

 ```
cd SOMEWHERE
git clone https://github.com/salsalabs/classic_pdfs.git
cd classic_pdfs
python3 -m venv .
source ./bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 pages.py --help
```
### Installation steps

1. Start the shell.  Change to the directory where you want the applicaiton to be stored.

    ```
    cd SOMEWHERE
    ```

1. Clone the app's repository.  It will end up in a directory named `classic_pdefs`.

  ```
  git clone https://github.com/salsalabs/classic_pdfs.git
  ```

1. Change to the newly created directory.

  ```
  cd classic_pdfs
  ```

1. Install a virtual environment.  This is really helpful for managing the packages that need to be installed to make this app work.

  ```
  python3 -m venv .
  ```

1. Installing a virtual environment creates directories and fills them with useful stuff.  [Please click here](https://docs.python.org/3/library/venv.html) if you'd like to learn more about what gets installed.

1. Activate the virtual environment.

**Note: You'll need to do this every time you want to use the application.***

  ```
  source ./bin/activate
  ```

1. Install dependencies from the standard Python package repository.

  ```
  python3 -m pip install --upgrade pip
  python3 -m pip install -r requirements.txt
  ```

1. Software will be downloaded and installed.  Errors are noisy.  Handle any errors before going to the next step.

# Execution

Run the application using `python3`.  Use `--help` to see the command-line options.

```
cd SOMEWHERE/classic_pdfs
source ./bin/activate
python3 pages.py --help

usage: pages.py [-h] [--login LOGINFILE] [--dir DIR] [--just-blasts]

Find public facing pages and write them as PDFs

optional arguments:
  -h, --help         show this help message and exit
  --login LOGINFILE  YAML file with login credentials
  --dir DIR          directory to store PDFs. Created as needed
  --just-blasts      just generate pdfs for email blasts
  ```

## Command-line options

#### `--login LOGINFILE`

LOGINFILE is a YAML-formatted file that contains Salsa Classic API credentials.  Here's a sample:

```yaml
host: salsa4.salsalabs.com
email: your_name@your_org.com
password: cheeseburger_with_fries
```

The credentials are passed to Classic API authentication.  You canlearn more about authentication by [clicking here](https://help.salsalabs.com/hc/en-us/articles/115000341773-Salsa-Application-Program-Interface-API-#authenticatesjs).

#### --dir DIR

DIR is the directory where the PDFs will end up.  The directory will contain a single subdirectory for each type of PDF retrieved:

```
DIR
  + donate_page
  |
  + email_blast
  |
  + event
  |
  
  (And so on...)
```

The default value for DIR is `./pdfs`.  The app creates all directories that it needs if they do not already exist.

### --just-blasts

If this open is provided, then the app only processes email blasts.  The default behavior is to create PDFs for all pages.

## Sample Output

Here's a sample of what the application writes to the console.

```text
pages.py --login ~/.logins/scl.yaml
Salsa: creating PDFs for The Saturday Cake Literary Society
http://salsa.wiredforchange.com/o/666/p/dia/action4/common/public/?action_KEY=6607
http://salsa.wiredforchange.com/o/666/p/dia/action4/common/public/?action_KEY=8236
http://salsa.wiredforchange.com/o/666/p/dia/action4/common/public/?action_KEY=8345
http://salsa.wiredforchange.com/o/666/p/dia/action4/common/public/?action_KEY=9800
http://salsa.wiredforchange.com/o/666/p/dia/action4/common/public/?action_KEY=10484
http://salsa.wiredforchange.com/o/666/p/dia/action4/common/public/?action_KEY=8155
```

Here's a sample of what the application writes if something goes wrong.

```text
Traceback (most recent call last):
  File "/usr/local/lib/python3.7/site-packages/urllib3/connectionpool.py", line 377, in _make_request
    httplib_response = conn.getresponse(buffering=True)
TypeError: getresponse() got an unexpected keyword argument 'buffering'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "pages.py", line 359, in <module>
    main()
  File "pages.py", line 356, in main
    Main(pageSpecs).run()
  File "pages.py", line 289, in run
    task.run()
  File "pages.py", line 120, in run
    resp = requests.get(self.url)
  File "/usr/local/lib/python3.7/site-packages/requests/api.py", line 75, in get
    return request('get', url, params=params, **kwargs)
  File "/usr/local/lib/python3.7/site-packages/requests/api.py", line 60, in request
    return session.request(method=method, url=url, **kwargs)

  (And so on...)
```

Ugliness usually means that something went wrong.  You'll need to put on your bug miner hat and find out why.

# Domain fixes
Salsa used to have a domain named `democracyinaction.org`.  That domain was turned off in favor of using `salsalabs.com`. Clients that uploaded and used images and files when `democracyinaction.org` was alive still have email blasts and public-facing pages that reference that domain.

Attempting to retrieve images and files for the old domain doesn't work. The PDFs that use images and files from `deocracyinaction.org` are generally blank.

This app solves that problem by automatically modifying URLs that contain the old domain to point to `salsalabs.com`.  It also handles URL fragments by changing them to full URLs.  In that case, the URLs reference the `host` value from the login credentials.  For example, the fragment

'''/salsa/include/whatever.js```

Is changed to 

```https://salsa4.salsalabs.com/salsa/include/whatever.js```

when the `host` value from the login credentials is `salsa4.salsalabas.com`.

The result is a combination of fewer errors and better looking PDFs.
# Questions?  Comments?

For best results, uses the web to look up any problems that you may run into.  Support for questions will be spotty at best, and non-existent during the busy parts of the year for non-profits.

You can report app-specific issues by using the [Github repository's issues link](https://github.com/salsalabs/classic_pdfs/issues).

Do yourself a favor.  Don't bother Salsalabs Support with questions about this product.  They get surly and tend to bite if you put your fingers into their cages.  Use the link.  We'll get back to you.  Promise.
