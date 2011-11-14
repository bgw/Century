==================================================================
``login`` -- Automatic and Semi-Automatic Gatorlink Login Handling
==================================================================

.. automodule:: lib.browser.plugins.uf.login

.. autoclass:: LoginBrowserPlugin
    
    .. automethod:: __init__
    .. automethod:: uf_login
    .. automethod:: uf_logout
    .. automethod:: uf_set_autologin
    .. automethod:: uf_username
    .. automethod:: uf_password
    .. automethod:: uf_session_cookie
    .. automethod:: handle_redirect

.. autoclass:: LoginContinueRedirect
    
    .. automethod:: __init__
    .. automethod:: handle_redirect
