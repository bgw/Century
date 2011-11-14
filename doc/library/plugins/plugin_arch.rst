=======================
The Plugin Architechure
=======================

.. automodule:: lib.browser.plugins

.. autoclass:: BaseBrowserPlugin
    :inherited-members:
    
    .. automethod:: __init__
    
    .. attribute:: overrides
        
        A list of methods overriden by this plugin instance.
    
    .. attribute:: extensions
        
        A list of methods adding to the browser's internal list of methods, but
        not overriding pre-existing methods. Note that if two functions attempt
        to extend with methods of the same name, :class:`Pluggable` will throw
        an exception.
    
    .. attribute:: property_extensions
        
        Like :attr:`extensions`, but refering to properties instead.
    
    .. attribute:: handlers
        
        A list of objects extended from :py:class:`urllib.request.BaseHandler`
        to add to the browser's interal :class:`urllib.request.OpenerDirector`
        instance automatically.
    
    .. attribute:: addheaders
        
        A list of headers to add to the browser's internal
        :class:`urllib.request.OpenerDirector` instance automatically, using
        :meth:`urllib.request.OpenerDirector.addheaders`
    
    .. automethod:: _get_instance_functions
    .. automethod:: _load_list

.. autoclass:: Pluggable
    :members:
    
    .. automethod:: __init__
    .. attribute:: plugins
    
        The list of plugins already loaded into the :class:`Pluggable`.
    
    .. automethod:: _register_plugin_attribute
    .. automethod:: __getattr__
    .. automethod:: __setattr__
    .. automethod:: load_plugins
    .. automethod:: overrides
    .. automethod:: extensions
    .. automethod:: property_extensions
