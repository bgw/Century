"""Knowing the ins-and-outs of this module is probably not very useful, but it
is probably good to have a basic understanding of how the
:class:`lib.browser.Browser`'s plugin system works."""

from .decorators import *
import inspect

class _AttributeManipulator(object):
    def __init__(self):
        self.__instance_functions = dict(
            inspect.getmembers(self, predicate=inspect.ismethod)
        )
    
    def _get_instance_functions(self):
        """Returns the object's list of methods, useful for the
        :meth:`_load_list` method."""
        return self.__instance_functions
    
    _instance_functions = property(_get_instance_functions)
    
    def _load_list(self, marker):
        """Finds all methods with a specific marker and returns them
        
        Keyword arguments:
        
        ``marker``
            A string representing the marker to look for on each function. If
            the value of this marker is `True`, the value is returned.
        
        """
        f = self._instance_functions
        r = {}
        for i in f:
            if hasattr(f[i], marker) and getattr(f[i], marker):
                r[i] = f[i]
        return r

class BaseBrowserPlugin(_AttributeManipulator):
    """A :class:`lib.browser.Browser` plugin is defined as a set of patches to
    be applied to a Browser object. This class defines a base for browser
    plugins."""
    
    def __init__(self):
        """Sets up everything the plugin needs. Subclasses should be sure to
        call this."""
        _AttributeManipulator.__init__(self)
        self.overrides = self._load_list("is_override")
        self.extensions = self._load_list("is_extension")
        self.property_extensions = self._load_list("is_property_extension")
        self.handlers = []
        self.addheaders = []

class Pluggable(_AttributeManipulator):
    """Takes in plugins, allowing one to configure an object on the fly, with a
    strutured monkey-patching like system"""
    
    def __init__(self, *plugins):
        """Sets up everything the object needs, and adds plugins specified by
        the positional arguments (they can be added later too). Subclasses
        should be sure to call this."""
        object.__setattr__(self, "_Pluggable__attr_extensions", {})
        _AttributeManipulator.__init__(self)
        self._plugins = []
        self.__plugin_attributes = {}
        for i in self._load_list("is_plugin_attribute").values():
            self._register_plugin_attribute(i.plugin_attribute_name, i)
        self.load_plugins(*plugins)
    
    def _register_plugin_attribute(self, name, handler):
        self.__plugin_attributes.setdefault(name, [])
        self.__plugin_attributes[name].append(handler)
    
    # Handle Property Overriding
    def __getattr__(self, name):
        """Used to intercept getting attributes with the :class:`Pluggable`
        instance, translating them to alternate "extended" attributes."""
        try:
            attr_extensions = self.__attr_extensions
            return attr_extensions[name].fget()
        except KeyError:
            return object.__getattribute__(self, name)
    
    def __setattr__(self, name, value):
        """Used to intercept setting attributes with the :class:`Pluggable`
        instance, translating them to alternate "extended" attributes."""
        if name not in self.__attr_extensions:
            object.__setattr__(self, name, value)
        else:
            self.__attr_extensions[name].fset(value)
    
    # Plugin loaders
    def load_plugins(self, *plugins):
        """Loads in one or a group of plugins. Rather than overriding this,
        subclasses should use the
        :func:`lib.browser.plugins.decorators.plugin_attribute` and
        :func:`lib.browser.plugins.decorators.plugin_attribute_handler`
        decorators. Attributes are loaded from plugins, and then parsed to be
        used in extending the :class:`Pluggable` subclass' object."""
        self._plugins += plugins
        for i in plugins:
            self._load_plugin(i)
    
    def _load_plugin(self, plugin):
        """A utility method called by :meth:`load_plugins`, which should load
        one individual plugin."""
        for attr_name in self.__plugin_attributes: # find each type of attribute
            if not hasattr(plugin, attr_name):
                continue
            attr_handlers = self.__plugin_attributes[attr_name]#list of handlers
            plugin_values = getattr(plugin, attr_name)
            # a plugin's value for the attribute type can either be a dictionary
            # or a list. A dictionary can typically be used for storing both the
            # name of what a function should override, and the function base,
            # while a list can represent a set of more simplistic, unnamed
            # patches to add
            
            if hasattr(plugin_values, "items"): # dict
                for handler in attr_handlers:
                    for i in plugin_values:
                        handler(i, plugin_values[i])
            else: # sequence type
                for handler in attr_handlers:
                    for i in plugin_values:
                        handler(i)
    
    @plugin_attribute
    def overrides(self, name, overriding_function):
        """The handler for the :func:`lib.browser.plugins.decorators.override`
        decorator. ``name`` is the name of the property it is set to override,
        ``overriding_function`` is the function that we should set to that name.
        It should take at least 2 arguments (in addition to ``self``, which
        would refer to the plugin instance), the browser instance and the
        function object that is being overridden."""
        base_function = getattr(self, name)
        def new_function(*args, **kwargs):
            return overriding_function(self, base_function, *args, **kwargs)
        new_function.__doc__ = overriding_function.__doc__
        setattr(self, name, new_function)
    
    @plugin_attribute
    def extensions(self, name, extending_function):
        """The handler for the :func:`lib.browser.plugins.decorators.extension`
        decorator. ``name`` is the name of the property it is set to extension,
        ``extending_function`` is the function that we should set to that name.
        It should take the browser instance as an argument in addition to
        ``self``, which would refer to the plugin instance. Any additional
        arguments are passed through."""
        if hasattr(self, name):
            raise ValueError(("We already have a property defined as %s either "
                              "by this class, or by an already loaded plugin.")
                              % name)
        def new_function(*args, **kwargs):
            return extending_function(self, *args, **kwargs)
        new_function.__doc__ = extending_function.__doc__
        setattr(self, name, new_function)
    
    @plugin_attribute
    def property_extensions(self, name, value):
        """The handler for the
        :func:`lib.browser.plugins.decorators.property_extension` decorator.
        Adds a virtual property with the given ``name``, by calling ``value``
        with the browser instance and recieving a property object."""
        if hasattr(self, name):
            raise ValueError(("We already have a property defined as %s either "
                              "by this class, or by an already loaded plugin.")
                              % name)
        self.__attr_extensions[name] = value(self)
