from .. import browser

import abc
import threading

class BaseTaskManager(metaclass=abc.ABCMeta):
    """Forms a simple system that can be used to create task handlers. This is
    an abstract class, although it has no abstract methods."""
    def __init__(self, browser=None):
        if browser is None:
            self._browser = self._get_new_browser()
        else:
            self._browser = browser
    
    def get_browser(self):
        """Gets the value of :attr:`browser`."""
        return self._browser
    
    browser = property(get_browser,
                      doc="""The :class:`lib.browser.Browser` instance passed
                          into the constructor.""")
    
    def _get_new_browser(self):
        """An overridable factory to make a new :class:`lib.browser.Browser`
        instance there isn't one passed into :meth:`__init__`."""
        return browser.Browser()

class BaseRepeatedTaskManager(metaclass=abc.ABCMeta):
    """Designed to be used in multiple inheritance with BaseTaskManager, as to
    avoid a potential diamond-like inheritance hierarchy. This is an abstract
    class, with the abstract method, :meth:`_run`."""
    def __init__(self, delay=300):
        assert isinstance(self, BaseTaskManager)
        self._delay = delay
        self._interrupt is None
        self._thread = None
    
    def get_delay(self):
        """Gets the value of :attr:`delay`."""
        if hasattr(self._delay, "__call__"):
            return self._delay()
        return self._delay
    
    delay = property(get_delay,
                     doc="""The amount of time in seconds to wait between
                     executions. For example, a delay of ``300`` would wait 5
                     minutes between each execution.""")
    
    def start(self, separate_thread=False):
        """Starts a new execution cycle. Note that the current task should be
        stopped with :meth:`stop` before it is started (unless you are calling
        for the first time)."""
        assert self._interrupt is None or self._interrupt.is_set()
        self._interrupt = threading.Event()
        if separate_thread:
            assert self._thread is None
            threading.Thread(target=self.__run)
        else:
            self.__run()
    
    def stop(self):
        """Stops the current execution cycle."""
        self._interrupt.set()
        if self._thread is not None:
            self._thread.join() # wait for it to recieve the interrupt
            self._interrupt = threading.Event()
            self._thread = None
    
    def __run(self):
        while True:
            self._run()
            if self._interrupt.wait(delay):
                break
    
    @abc.abstractmethod
    def _run(self):
        """An :func:`abc.abstractmethod` that does the desired task when called
        on each execution cycle."""
        pass

class BaseUFTaskManager(metaclass=abc.ABCMeta):
    """Designed to be used in multiple inheritance with BaseTaskManager, as to
    avoid a potential diamond-like inheritance hierarchy."""
    def __init__(self):
        assert isinstance(self, BaseTaskManager)
    
    def _get_new_browser(self):
        """Uses :func:`lib.browser.get_new_uf_browser()` to make the default
        :attr:`BaseTaskManger.browser` instance."""
        return browser.get_new_uf_browser()
