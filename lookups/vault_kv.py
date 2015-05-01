import os
import urllib2
try:
    import json
except ImportError:
    import simplejson as json

from ansible import utils, errors

class LookupModule(object):
  def __init__(self, basedir=None, **kwargs):
    self.basedir = basedir
    self.vault_url = "http://127.0.0.1:8200"

    if 'VAULT_ADDR' in os.environ:
      self.vault_url = os.environ['VAULT_ADDR']

  def get_value(self, key, token):
    url = "%s/v1/%s" % (self.vault_url, key)
    opener = urllib2.build_opener()
    opener.addheaders.append(('cookie', 'token=%s' % token))
    r = opener.open(url)
    data = r.read()

    try:
      item = json.loads(data)

      if 'data' in item:
        value = item['data']['value']
    except:
      raise
      pass

    return value

  def run(self, terms, inject=None, **kwargs):
    values = []
    terms  = utils.listify_lookup_plugin_terms(terms, self.basedir, inject)

    try:
      for term in terms:
        params = self.parse_params(term)
        results = self.get_value(params['key'], params['token'])

        values.append(results)

    except Exception, e:
      raise errors.AnsibleError("Term '%s'. Error %s" % (term, e))

    return values

  def parse_params(self, term):
    params = term.split(' ')

    paramvals = {
      'key':   None,
      'token': None
    }

    try:
      for param in params:
        name, value = param.split('=')
        assert name in paramvals, "% not a valid vault lookup parameter" % name
        paramvals[name] = value
    except(ValueError, AssertionError), e:
      raise errors.AnsibleError(e)

    if paramvals['token'] is None:
      if 'VAULT_TOKEN' in os.environ:
        paramvals['token'] = os.environ['VAULT_TOKEN']
      else:
        raise errors.AnsibleError('Vault token could not be loaded. The Vault '
                                  'token can be provided using the `VAULT_TOKEN` '
                                  'environment variable.')
    return paramvals
