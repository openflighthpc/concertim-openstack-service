# Openstack Packages
from keystoneauth1.identity import v2, v3
from keystoneauth1 import session
from openstack.exceptions import OpStkAuthenticationError

class OpenStackAuth:
    def __init__(self, auth_dict):
        self.auth_dict = auth_dict
        self.auth_methods = {
            v3.Password: [
                {'auth_url', 'user_id', 'password', 'project_id'},
                {'auth_url', 'username', 'password', 'project_id', 'user_domain_name'},
                {'auth_url', 'username', 'password', 'project_name', 'user_domain_name', 'project_domain_name'}
            ],
            v2.Password: [
                {'auth_url', 'username', 'password', 'tenant_id'},
                {'auth_url', 'username', 'password', 'tenant_name'}
            ]
        }

    def get_session(self):
        try:
            for method, required_params_list in self.auth_methods.items():
                for required_params in required_params_list:
                    if required_params.issubset(self.auth_dict.keys()):
                        return session.Session(auth=method(**self.auth_dict))
        except Exception as e:
            self.__LOGGER.error(f"An unexpected error : {type(e).__name__} - {e}")
            raise e
        raise OpStkAuthenticationError(f"Invalid auth_dict provided. It must contain one of the valid sets of parameters: {self.auth_methods}")