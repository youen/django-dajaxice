import logging

from django.conf import settings
from django.utils.importlib import import_module

log = logging.getLogger('dajaxice.DajaxiceRequest')

class DajaxiceModule(object):
    def __init__(self, module , path=''):
        module = module.split('.')[0]
        if path == '' or module == '':
            self.path = module
        else:
            self.path = path + '.' + module
        self.name = module
        self.functions = []
        self.sub_modules = {}
        
   
    def get_sub_modules(self):
        return self.sub_modules.values()

    def has_sub_modules(self):
        return len(self.sub_modules) > 0
        
    def add_function(self, function):
        if not hasattr(function,'__iter__'):
            function = function.split('.')

        if function[0] == self.name :
            self.add_function(function[1:])

        elif len(function) == 1:
            self.functions.append(function[0])
        else:
            sub_module = self.sub_modules.get(function[0],DajaxiceModule(function[0],self.path))
            sub_module.add_function(function[1:])
            self.sub_modules[function[0]] = sub_module

    
class Dajaxice(object):
    def __init__(self):
        self._root_module = DajaxiceModule('')
        self._callable = []
        
        for function in getattr(settings, 'DAJAXICE_FUNCTIONS', ()):
            function = function.rsplit('.',1)
            self.register_function(function[0],function[1])
        
    def register(self, function):
        self.register_function(function.__module__, function.__name__)
    
    def register_function(self, module, name):
        callable_function = '%s.%s' % (module, name)
        if callable_function in self._callable:
            log.warning('%s already registered as dajaxice function.' % callable_function)
            return
        
        self._callable.append(callable_function)
        
        module_without_ajax = module.replace('.ajax','')
        function = '%s.%s' % (module_without_ajax, name)
        

        self._root_module.add_function(function)
        
    def is_callable(self, name):
        return name in self._callable
        
        
    def get_functions(self):
        return self._root_module.sub_modules.values()

LOADING_DAJAXICE = False

def dajaxice_autodiscover():
    """
    Auto-discover INSTALLED_APPS ajax.py modules and fail silently when
    not present.
    NOTE: dajaxice_autodiscover was inspired/copied from django.contrib.admin autodiscover
    """
    global LOADING_DAJAXICE
    if LOADING_DAJAXICE:
        return
    LOADING_DAJAXICE = True

    import imp
    from django.conf import settings

    for app in settings.INSTALLED_APPS:
       
        try:
            app_path = import_module(app).__path__
        except AttributeError:
            continue

        try:
            imp.find_module('ajax', app_path)
        except ImportError:
            continue

        import_module("%s.ajax" % app)
        
    LOADING_DAJAXICE = False
