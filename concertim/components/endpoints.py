ENDPOINTS = {
            'POST': {
                'endpoints': {
                    'LOGIN_AUTH': {
                        'endpoint': '/users/sign_in.json',
                        'required_vars': ['login', 'password'],
                        'data':{"user": {
                                "login": '{login}',
                                "password": '{password}'
                            }
                        }
                    },
                    'CREATE_DEVICE':{
                        'endpoint': '/api/v1/nodes',
                        'required_vars': ['template_id', 'name', 'description', 'facing', 'rack_id', 'start_u'],
                        'data': {"template_id": '{template_id}',
                                "device": {
                                    "name": '{name}',
                                    "description": '{description}',
                                    "location": {
                                        "facing": '{facing}',
                                        "rack_id": '{rack_id}',
                                        "start_u": '{start_u}'
                                    },
                                    "metadata" : {
                                        "openstack_instance_id" : "{openstack_instance_id}",
                                        "status" : "{status}"
                                    }

                                }}
                    },
                    'CREATE_RACK':{
                        'endpoint': '/api/v1/racks',
                        'required_vars': ['user_id','name','u_height'],
                        'data': {"rack": {
                                    "user_id": '{user_id}',
                                    "name": '{name}',
                                    "u_height": '{u_height}',
                                    "metadata" : {
                                        "openstack_stack_id" : "{openstack_stack_id}",
                                        "status" : "{status}"
                                    }
                                }}
                    },
                    'CREATE_TEMPLATE':{
                        'endpoint': '/api/v1/templates',
                        'required_vars': ['name','description','height'],
                        'data': {"template": {
                                    "name": '{name}',
                                    "description": '{description}',
                                    "height": '{height}'
                                }}
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
                        'data': {"device": {
                                    "location": {
                                        "facing": '{facing}',
                                        "rack_id": '{rack_id}',
                                        "start_u": '{start_u}'
                                    }
                                }}
                    },
                    'UPDATE_DEVICE':{
                        'endpoint': '/api/v1/devices/{}',
                        'required_vars': ['name','description'],
                        'data': {"device": {
                                    "name": '{name}',
                                    "description": '{description}'
                                }}
                    },
                    'UPDATE_RACK':{
                        'endpoint': '/api/v1/racks/{}',
                        'required_vars': ['name','u_height'],
                        'data': {"rack": {
                                    "name": '{name}',
                                    "u_height": '{u_height}'
                                }}
                    },
                    'UPDATE_TEMPLATE':{
                        'endpoint': '/api/v1/templates/{}',
                        'required_vars': ['name','description'],
                        'data': {"template": {
                                    "name": '{name}',
                                    "description": '{description}'
                                }}
                    }
                },
                'headers': {"Content-Type": "application/json", "Accept": "application/json"}
            },
            'PUT': {
                'endpoints':{
                    'METRIC':{
                        'endpoint': '/mrd/{}/metrics',
                        'required_vars': ['type','name','value','units','slope','ttl'],
                        'data': {"type": '{type}',
                                 "name": '{name}',
                                 "value": '{value}',
                                 "units": '{units}',
                                 "slope": '{slope}',
                                 "ttl": '{ttl}'}
                    }
                },
                'headers': {"Content-Type": "application/json"}
            }
        }