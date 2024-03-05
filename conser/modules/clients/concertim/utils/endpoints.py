ENDPOINTS = {
            'POST': {
                'endpoints': {
                    'LOGIN_AUTH': {
                        'endpoint': '/users/sign_in.json',
                        'required_vars': ['login', 'password'],
                        'data': {
                            "user": {
                                "login": '{login}',
                                "password": '{password}'
                            }
                        }
                    },
                    'CREATE_DEVICE':{
                        'endpoint': '/api/v1/nodes',
                        'required_vars': ['template_id', 'name', 'description', 'facing', 'rack_id', 'start_u', 'status'],
                        'data': {
                            "template_id": '{template_id}',
                            "device": {
                                "name": '{name}',
                                "description": '{description}',
                                "status" : "{status}",
                                "location": {
                                    "facing": '{facing}',
                                    "rack_id": '{rack_id}',
                                    "start_u": '{start_u}'
                                },
                                "public_ips": '{public_ips}',
                                "private_ips": '{private_ips}',
                                "ssh_key": '{ssh_key}',
                                "volume_details": '{volume_details}',
                                "login_user": '{login_user}',
                                "metadata" : {
                                    "net_interfaces": "{net_interfaces}",
                                    "openstack_instance_id" : "{openstack_instance_id}",
                                    "openstack_stack_id": "{openstack_stack_id}"
                                }
                            }
                        }
                    },
                    'CREATE_RACK':{
                        'endpoint': '/api/v1/racks',
                        'required_vars': ['user_id','name','u_height', 'status'],
                        'data': {
                            "rack": {
                                "user_id": '{user_id}',
                                "name": '{name}',
                                "u_height": '{u_height}',
                                "status" : "{status}",
                                "network_details": '{network_details}',
                                "creation_output": '{creation_output}',
                                "order_id": '{order_id}',
                                "metadata" : {
                                    "openstack_stack_id" : "{openstack_stack_id}",
                                    "openstack_stack_owner" : "{openstack_stack_owner}",
                                    "openstack_stack_owner_id" : "{openstack_stack_owner_id}",
                                    "stack_status_reason": "{stack_status_reason}",
                                    'openstack_stack_output': '{openstack_stack_output}'
                                }
                            }
                        }
                    },
                    'CREATE_TEMPLATE':{
                        'endpoint': '/api/v1/templates',
                        'required_vars': ['name','description','height', 'ram', 'disk', 'vcpus', 'foreign_id'],
                        'data': {
                            "template": {
                                "name": '{name}',
                                "description": '{description}',
                                "height": '{height}',
                                "ram" : '{ram}',
                                "disk" :'{disk}',
                                "vcpus" : '{vcpus}',
                                "foreign_id" : '{foreign_id}'
                            }
                        }
                    }
                },
                'headers': {"Content-Type": "application/json", "Accept": "application/json"}
            },
            'DELETE': {
                'endpoints': {
                    'DELETE_DEVICE':{
                        'endpoint': '/api/v1/devices/{}'
                    },
                    'DELETE_RACK':{
                        'endpoint': '/api/v1/racks/{}'
                    },
                    'DELETE_TEMPLATE':{
                        'endpoint': '/api/v1/templates/{}'
                    }
                },
                'recurse': '?recurse=true',
                'headers': {"Accept": "application/json"}
            },
            'GET': {
                'endpoints':{
                    'LIST_DEVICES':{
                        'endpoint': '/api/v1/devices'
                    },
                    'LIST_RACKS':{
                        'endpoint': '/api/v1/racks'
                    },
                    'LIST_TEMPLATES':{
                        'endpoint': '/api/v1/templates'
                    },
                    'LIST_USERS':{
                        'endpoint': '/api/v1/users'
                    },
                    'GET_CURR_USER':{
                        'endpoint': '/api/v1/users/current'
                    },
                    'SHOW_DEVICE':{
                        'endpoint': '/api/v1/devices/{}'
                    },
                    'SHOW_RACK':{
                        'endpoint': '/api/v1/racks/{}'
                    }
                },
                'headers': {"Accept": "application/json"}
            },
            'PATCH': {
                'endpoints':{
                    'MOVE_DEVICE':{
                        'endpoint': '/api/v1/devices/{}',
                        'required_vars': ['facing','rack_id','start_u'],
                        'data': {
                            "device": {
                                "location": {
                                    "facing": '{facing}',
                                    "rack_id": '{rack_id}',
                                    "start_u": '{start_u}'
                                }
                            }
                        }
                    },
                    'UPDATE_USER':{
                        'endpoint': '/api/v1/users/{}',
                        'required_vars': [],
                        'data': {
                            "user": {
                                "cost": '{cost}',
                                "billing_period_start": '{billing_period_start}',
                                "billing_period_end": '{billing_period_end}',
                                "credits": '{credits}'
                            }
                        }
                    },
                    'UPDATE_DEVICE':{
                        'endpoint': '/api/v1/devices/{}',
                        'required_vars': [],
                        'data': {
                            "device": {
                                "name": '{name}',
                                "description": '{description}',
                                "cost": '{cost}',
                                "status" : '{status}',
                                "public_ips": '{public_ips}',
                                "private_ips": '{private_ips}',
                                "ssh_key": '{ssh_key}',
                                "volume_details": '{volume_details}',
                                "login_user": '{login_user}',
                                "metadata" : {
                                    "net_interfaces": "{net_interfaces}",
                                    'openstack_instance_id': '{openstack_instance_id}',
                                    "openstack_stack_id": "{openstack_stack_id}"
                                }
                            }
                        }
                    },
                    'UPDATE_RACK':{
                        'endpoint': '/api/v1/racks/{}',
                        'required_vars': [],
                        'data': {
                            "rack": {
                                "name": '{name}',
                                "u_height": '{u_height}',
                                "cost": '{cost}',
                                "status" : '{status}',
                                "network_details": '{network_details}',
                                "creation_output": '{creation_output}',
                                "metadata" : {
                                    "openstack_stack_id" : "{openstack_stack_id}",
                                    "openstack_stack_owner" : "{openstack_stack_owner}",
                                    "openstack_stack_owner_id" : "{openstack_stack_owner_id}",
                                    "stack_status_reason": "{stack_status_reason}",
                                    'openstack_stack_output': '{openstack_stack_output}'
                                }
                            }
                        }
                    },
                    'UPDATE_TEMPLATE':{
                        'endpoint': '/api/v1/templates/{}',
                        'required_vars': ['name'],
                        'data': {
                            "template": {
                                "name": '{name}',
                                "description": '{description}'
                            }
                        }
                    }
                },
                'headers': {"Content-Type": "application/json", "Accept": "application/json"}
            },
            'PUT': {
                'endpoints':{
                    'METRIC':{
                        'endpoint': '/mrd/{}/metrics',
                        'required_vars': ['type','name','value','units','slope','ttl'],
                        'data': {
                            "type": '{type}',
                            "name": '{name}',
                            "value": '{value}',
                            "units": '{units}',
                            "slope": '{slope}',
                            "ttl": '{ttl}'
                        }
                    }
                },
                'headers': {"Content-Type": "application/json"}
            }
        }