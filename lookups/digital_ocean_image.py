#!/usr/bin/python

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
    self.search  = "https://api.digitalocean.com/v1/images/?client_id=%s&api_key=%s&filter=global"

    if 'DO_CLIENT_ID' in os.environ:
      self.client_id = os.environ['DO_CLIENT_ID']

    if 'DO_API_KEY' in os.environ:
      self.api_key = os.environ['DO_API_KEY']

  def get_value(self, distro, version):
    url = self.search % (self.client_id, self.api_key)
    opener = urllib2.build_opener()
    item = {}

    try:
      r = opener.open(url)
      data = r.read()
    except urllib2.HTTPError, err:
      data = err.read()
      msg = ""

    try:
      item = json.loads(data)
    except:
        msg = "error parsing json"
        raise errors.AnsibleError("error '%s'" % msg)

    try:
      value = self.search_dictionaries("slug", "%s-%s-x64" % (distro, version), item['images'])[0]['id']

    except:
      raise
      pass

    return value

  def search_dictionaries(self, key, value, list_of_dictionaries):
    return [element for element in list_of_dictionaries if element[key] == value]

  def run(self, terms, inject=None, **kwargs):
    values = []
    terms  = utils.listify_lookup_plugin_terms(terms, self.basedir, inject)

    try:
      for term in terms:
        params = self.parse_params(term)
        results = self.get_value(params['distro'], params['version'])

        values.append(results)

    except Exception, e:
      raise errors.AnsibleError("Term '%s'. Error %s" % (term, e))

    return values

  def parse_params(self, term):
    params = term.split(' ')

    paramvals = {
      'distro':  None,
      'version': None
    }

    try:
      for param in params:
        name, value = param.split('=')
        assert name in paramvals, "% not a valid vault lookup parameter" % name
        paramvals[name] = value
    except(ValueError, AssertionError), e:
      raise errors.AnsibleError(e)

    return paramvals

