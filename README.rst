================
What is Century?
================

Let's say you'd like to write a simple script to work with a certain page on the
University of Florida website. What may seem like a simple task could very well
prove quite complicated: you'll have to handle authentication, cookies,
redirects, and often times broken html. When it comes down to it, UF's webpages
don't play well with scripting.

Century handles automation of the UF site, and does it for you with an
extensible, documented API. Now you can write that app, without worrying about
where you're going to get the data from. Tasks that took a few thousand lines of
code now only take a couple hundred. We're here to make what should've been an
open system, open.

Please note that we are not affiliated with the University of Florida in any
way. This API is unofficial, and unsupported by UF. If you manage to get in
trouble while using it, it's your own fault.

========================
What Can I Do Right Now?
========================

If you look at the ``lib/tasks`` directory, you can find some already
implemented parsers for various UF sites. If there's already a parser for a
section of the UF site that you want to work with, you can get up and running
right away.

Unfortunately, as is the case with many enterprise systems, UF's site is
massive, and so we cannot easily include pre-made "task" classes for everything
you might want to do. UF-Tools is still of use though! If you end up writing
your own task module, you can still make use of other pieces of the UF-Tools
library, such as the ``browser`` module, which when combined with the proper
plugins, should be able to handle most of your authentication and redirection
needs. Additionally, it has a few handy tools, inspired from modules like
`Mechanize <http://wwwsearch.sourceforge.net/mechanize/>`_.

============
Dependencies
============

So far, the library requires Python 3.2, however it has been written with Python
2 in mind, and a backport to Python 2 is likely if interest is shown. Beyond
Python, pre-built task modules may have their own dependencies (typically only
lxml, however it is at the task-builder's discression). Consult the module's
documention for more information. Everything in ``lib/browser`` is completely
dependency free (with the exception of py3k), and will likely remain that way.
The idea here is that if you can spare the extra dependencies, you will be
rewarded, if not, that's fine too, but it will likely require some more effort
on your part.

Building documentation requires Sphinx 1.1 or greater (which isn't even in
Debian Sid as of writing!), as it adds Python 3 support. If your package manager
doesn't have it, or if you are on Windows or Mac OS X, you can install it
through `PyPI/easy_install <http://pypi.python.org/pypi/Sphinx/>`_.

==============================
Configuration and Installation
==============================

Directory Structure
-------------------

Right now, all tests are located in the root directory of the repository,
although as the number of tests grow, the repository's structure will likely
change. General configuration options for the tests should go in ``config.py``.
Anything within ``lib`` should not access ``config.py`` directly, but should
have information passed to them by the tests where applicable.

I Don't Like Entering in my Gatorlink Info Every Time I Run!
------------------------------------------------------------

You can modify the ``config.py`` file if you'd like, replacing the function
calls that get your username and password with literal strings, but be very
careful not to commit your changes, giving away your authentication information!
The file is in the repository's ``.gitignore`` to prevent you from doing
something stupid, but it's still possible.

Enough With This! Can I See a Demo?
-----------------------------------

Sure! ``cd`` into the proper directory, and simply run
``python3 test_schedule.py``. After entering your Gatorlink username and
password, you should see your schedule printed to the screen in the form of an
ascii-art table, with no further output.

How'd You Do That?
~~~~~~~~~~~~~~~~~~

There's actually more going on here than meets the eye. After authentication, we
pull up the user's schedule, parse the table, turn it into an easy-to-access
python dictionary, utilizing various datatypes to make the data more accessible
than their simple string formats (for example, a string showing the periods
"7-9" gets turned into the tuple of ints ``(7, 8, 9)`` such that something like
``8 in periods`` would give us ``True``.). We then take that beautifully parsed
data, and convert it all back into a table styled after the one we just ripped.

=============
Closing Notes
=============

This is Great! What Can I do to Get Involved?
---------------------------------------------

The two primary needs at this point are code and documentation, specifically in
the area of task modules. To submit a patch, either send me the information via
github, or fork the repository and submit a pull request. If you can't figure
out what to do, contact me through github anyways. We can figure something out!

Shut Up and Take My Money!
--------------------------

I'm not taking donations or payment at this point in time, and I have no plans
to in the near future. Take your money and send it to the
`Free Software Foundation <https://www.fsf.org/>`_ or the
`Electronic Frontier Foundation <https://www.eff.org>`_. They're both great
groups that fight for our freedom online.

Licensing
---------

This project is licensed under the AGPLv3. What that means is that if you decide
not to share your work with anyone, that's fine, but if you decide to release
your program at some point in time, you'll need to release your source as well.
I think it's only fair, but if you have a problem with it, feel free to contact
me. We may be able to work something out.
