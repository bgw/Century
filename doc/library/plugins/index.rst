===============================================
``plugins`` -- Extending the ``browser`` Module
===============================================

Plugins are things that add functionality to the browser. Some of them are not
site-specific, and could be used in a variety of applications, such as
the :mod:`lib.browser.plugins.cookies`, or the
:mod:`lib.browser.plugins.keepalive` plugins. UF-specific plugins are kept
within the :mod:`lib.browser.plugins.uf` package. Plugins are different from
:mod:`lib.tasks`, for a few reasons:

 - A plugin has direct access to more of the browser's features.
 - A plugin typically does something simpler than a task.
 - A plugin has to be careful about what it overrides, as it could create
   serious problems if poorly implemented.

If you don't know what you're doing, but you want to add more functionality to
the library, I'd suggest writing a task, but for certain things, a plugin
becomes a more elegant solution.

Plugins for :class:`lib.browser.Browser` can do a variety of things, such as
adding new methods to a :class:`lib.browser.Browser` instance, adding new
properties, overriding old methods or properties, adding handlers, and adding
headers to future HTTP requests. The :mod:`lib.browser.plugins.decorators`
module provides some useful decorators for making this happen.

.. toctree::
    plugin_arch
    decorators
    redirect
    cookies
    useragent
    keepalive
    uf/index
