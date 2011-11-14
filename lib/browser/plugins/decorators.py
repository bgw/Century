"""A set of decorator functions designed to make building a plugin or extending
:class:`lib.browser.plugins.Pluggable` a snap. If you're writing either, this is
the API you'll probably work with the most."""

def _build_type(type_marker, docstring=None):
    def decorator(f):
        setattr(f, type_marker, True)
        return f
    decorator.__doc__ = docstring
    return decorator

# BaseBrowserPlugin
override = _build_type("is_override",
    """When given a function, adds an attribute to the function,
    ``is_override``. An overriding function should take 3 arguments, ``self``
    (or ``plugin``), ``browser``, and an argument representing the function they
    are overriding.
    
    ::
    
        @override
        def load_page(plugin, browser, old_function, *args, **kwargs):
            # do something here
            return old_function(*args, **kwargs)
    
    ..
    """)
extension = _build_type("is_extension",
    """When given a function, adds an attribute to the function,
    ``is_extension``. An extending function should take 2 arguments, ``self``
    (or ``plugin``) and ``browser``.
    
    ::
    
        @extension
        def new_functionality(plugin, browser, first_argument, second_argument):
            # do something here
            pass
    
    ..
    """)
property_extension = _build_type("is_property_extension",
    """When given a function, adds an attribute to the function,
    ``is_property_extension``. The function should take 2 arguments, ``self``
    (or ``plugin``) and ``browser``. It should return an instance of
    ``property``.
    
    ::
    
        @property_extension
        def tribbles_count(plugin, browser):
            
            number = 9001
            
            def getter():
                return number
            
            def setter(value):
                assert value > 9000
                number = value
            
            return property(getter, setter)
    """)

# Pluggable
def plugin_attribute_handler(name):
    """A decorator factory, allowing you to set multiple handler functions for
    the same attribute type. A handler should take both name and value
    arguments, or just a value argument if the plugin's attribute is just a
    list."""
    def decorator(f):
        f.is_plugin_attribute = True
        f.plugin_attribute_name = name
        return f
    return decorator

def plugin_attribute(f):
    """A decorator which makes the passed function a handler for an attribute
    type with it's name. A handler should take both name and value arguments, or
    just a value argument if the plugin's attribute is just a list."""
    return plugin_attribute_handler(f.__name__)(f)
