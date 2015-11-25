from ansible import errors, utils
HAVE_REDIS=False
try:
    from redis.sentinel import Sentinel
    HAVE_REDIS=True
except ImportError:
    pass

class LookupModule(object):

    def __init__(self, basedir=None, **kwargs):
        self.basedir = basedir

        if HAVE_REDIS == False:
            raise errors.AnsibleError("Can't LOOKUP(sentinel_master): module redis is not installed")

    #{{ lookup('redis_master', "server=1:131 server=22:1213121 server=3333:123131 name=master") }}
    def run(self, terms, inject=None, **kwargs):
        values = []
        terms = utils.listify_lookup_plugin_terms(terms, self.basedir, inject)

        for term in terms:
            params = self.parse_params(term)

            try:
                conn = Sentinel(params['server'], socket_timeout=1)
                res = conn.discover_master(params['name'])
                if res is None:
                    res = ""
                values.append(":".join((str(v) for v in res)))
            except Exception, e:
                print(e)
        return values

    def parse_params(self, term):
        params = term.split()
        paramvals = {
          'server': [],
          'name': "",
        }

        try:
            for param in params:
                name, value = param.split('=')
                assert name in paramvals, "% not a valid lookup parameter" % name

                if name == 'server':
                    host, port = value.split(':')
                    if host == "":
                        host = '127.0.0.1'
                        port = '26379'
                    paramvals['server'].append((host, int(port)))

                if name == 'name':
                    paramvals['name'] = value

        except(ValueError, AssertionError), e:
            raise errors.AnsibleError(e)

        return paramvals
