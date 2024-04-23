# Openstack Packages
from keystoneauth1.identity import v2, v3
from keystoneauth1 import session
import conser.exceptions as EXCP

class OpenStackAuth:
    # Auth mapping for openstack session arg names to config file names
    # config_field_name: openstack_arg_name
    AUTHENTICATION_MAPPING = {
        'auth_url': 'auth_url',
        'admin_user_id': 'user_id',
        'user_id': 'user_id',
        'admin_username': 'username',
        'username': 'username',
        'admin_user_password': 'password',
        'password': 'password',
        'admin_project_id': 'project_id',
        'project_id': 'project_id',
        'admin_project_name': 'project_name',
        'admin_tenant_id': 'tenant_id',
        'admin_tenant_name': 'tenant_name',
        'user_domain_name': 'user_domain_name',
        'project_domain_name': 'project_domain_name'
    }
    AUTHENTICATION_AUTHORIZED_SETS = {
        v3.Password: [
            {'auth_url', 'user_id', 'password', 'project_id'},
            {'auth_url', 'username', 'password', 'project_id', 'user_domain_name'},
            {'auth_url', 'username', 'password', 'project_name', 'user_domain_name', 'project_domain_name'},
            {'auth_url', 'user_id', 'password', 'project_name', 'project_domain_name'}
        ],
        v2.Password: [
            {'auth_url', 'username', 'password', 'tenant_id'},
            {'auth_url', 'username', 'password', 'tenant_name'}
        ]
    }

    def get_session(config_dict):
        password_obj, auth_dict = OpenStackAuth._get_auth_set(config_dict)
        return session.Session(auth=password_obj(**auth_dict))

    def _get_auth_set(config_dict):
        auth_dict = {}
        # BUILD
        for k,v in config_dict.items():
            if k in OpenStackAuth.AUTHENTICATION_MAPPING:
                auth_dict[OpenStackAuth.AUTHENTICATION_MAPPING[k]] = v
        # VALIDATE
        valid = False
        pass_obj = None
        for method, auth_sets in OpenStackAuth.AUTHENTICATION_AUTHORIZED_SETS.items():
            for auth_set in auth_sets:
                if auth_set.issubset(auth_dict.keys()):
                    valid = True
                    pass_obj = method
                    break
            if valid:
                break
        if not valid:
            auth_dict_string = ', '.join([f"{key}={value}" for key, value in auth_dict.items()])
            raise EXCP.CloudAuthenticationError(f"Invalid set of authorization parameters when building session {auth_dict_string}")
        # RETURN
        return pass_obj, auth_dict
        
