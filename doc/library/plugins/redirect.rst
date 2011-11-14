===========================================================
``redirect`` -- Base Plugin Class for Handling Redirections
===========================================================

.. automodule:: lib.browser.plugins.redirect

.. autoclass:: BaseRedirectionPlugin
    :members:
    
    .. automethod:: __init__
    .. automethod:: _is_valid_url
    .. automethod:: _is_valid_page
    .. automethod:: load_page
    .. automethod:: handle_redirect
    
.. autoclass:: BrowserMetaRefreshHander
    :members:
    
    .. automethod:: __init__
    .. automethod:: handle_redirect

.. autoclass:: PageRedirectionError
    :members:
    
    .. automethod:: __init__
