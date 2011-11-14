====================
Web-Browser Services
====================

``browser`` -- Webbrowser-like Extensable State Machine
-------------------------------------------------------

.. automodule:: lib.browser

.. autoclass:: Browser
    
    .. automethod:: __init__
    .. automethod:: load_page
    .. automethod:: submit
    .. automethod:: back
    .. automethod:: forward
    .. autoattribute:: history
    .. autoattribute:: current_url
    .. automethod:: refresh
    .. automethod:: _load_relative
    .. automethod:: expand_relative_url
    .. automethod:: _parse_page
    .. automethod:: _simplify_url

.. autofunction:: get_new_uf_browser

Parsers and Plugins
-------------------

.. toctree::
    parsers
    plugins/index
