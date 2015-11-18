from ansible import errors, utils

try:
    import boto.ec2
    import boto.ec2.autoscale
except ImportError:
    raise errors.AnsibleError(
        "Can't LOOKUP(aws_asg): module boto is not installed")


class AWSAutoScalingGroup(object):
    def __init__(self, region):
        self.region = region
        self.ec2 = boto.ec2.connect_to_region(self.region)
        self.autoscale = boto.ec2.autoscale.connect_to_region(self.region)

    def get_instances(self, group_name, filter="private_ip_address"):
        group = self.autoscale.get_all_groups([group_name])

        # empty result
        if len(group) == 0:
            return ""

        instance_ids = [i.instance_id for i in group[0].instances
                        if i.health_status == 'Healthy']
        instances = self.ec2.get_only_instances(instance_ids)

        return [str(getattr(i, filter)) for i in instances]


class LookupModule(object):

    def __init__(self, basedir=None, **kwargs):
        self.basedir = basedir

    def run(self, terms, inject=None, **kwargs):
        values = []
        terms = utils.listify_lookup_plugin_terms(terms, self.basedir, inject)

        for term in terms:
            params = self.parse_params(term)
            self.sg = AWSAutoScalingGroup(params['region'])
            result = self.sg.get_instances(params['id'], params['filter'])
            values.append(result)

        return values

    def parse_params(self, term):
        filter_values = ['private_ip_address',
                         'ip_address',
                         'public_dns_name',
                         'private_dns_name']
        params = term.split()
        paramvals = {
          'region': 'us-west-1',
          'id': None,
          'filter': None
        }

        try:
            for param in params:
                name, value = param.split('=')
                assert name in paramvals, "% not a valid lookup parameter" % name

                if name == 'filter':
                    assert value in filter_values, "% not a valid filter" % value

                paramvals[name] = value
        except(ValueError, AssertionError), e:
            raise errors.AnsibleError(e)

        if paramvals['filter'] == None:
            paramvals['filter'] = 'private_ip_address'

        return paramvals
