"""
==============================================================================
 Copyright (C) 2024-present Alces Flight Ltd.

 This file is part of Concertim Openstack Service.

 This program and the accompanying materials are made available under
 the terms of the Eclipse Public License 2.0 which is available at
 <https://www.eclipse.org/legal/epl-2.0>, or alternative license
 terms made available by Alces Flight Ltd - please direct inquiries
 about licensing to licensing@alces-flight.com.

 Concertim Openstack Service is distributed in the hope that it will be useful, but
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, EITHER EXPRESS OR
 IMPLIED INCLUDING, WITHOUT LIMITATION, ANY WARRANTIES OR CONDITIONS
 OF TITLE, NON-INFRINGEMENT, MERCHANTABILITY OR FITNESS FOR A
 PARTICULAR PURPOSE. See the Eclipse Public License 2.0 for more
 details.

 You should have received a copy of the Eclipse Public License 2.0
 along with Concertim Openstack Service. If not, see:

  https://opensource.org/licenses/EPL-2.0

 For more information on Concertim Openstack Service, please visit:
 https://github.com/openflighthpc/concertim-openstack-service
==============================================================================
"""

import jwt
import os
import json
import time


def authenticate_headers(headers, logger):

    headers = dict(headers)
    logger.debug(f"Headers : {headers}")

    # Checking for presence of Authorization Header field
    if "Authorization" not in headers:
        return False
    
    # Checking for presence of 'Bearer' keyword
    bearer_token = headers["Authorization"]
    if bearer_token[0:7] != "Bearer ":
        logger.error("Bearer token not present")
        return False

    encoded_message = bearer_token[7:]

    if 'JWT_SECRET' not in os.environ:
        logger.error("JWT_SECRET env variable not set")
        return False
    
    secret_key = os.environ.get('JWT_SECRET', 'NULL')
        
    #Decrypting message
    try:
        payload = jwt.decode(encoded_message, key=secret_key, algorithms="HS256")
    except Exception as e:
        logger.error(f"Message decoding failed - {e}")
        return False

    logger.debug(f"Payload : {payload}")

    #Checking for token expiry
    if "exp" not in payload or payload["exp"] < time.time() :
        return False

    logger.debug("Authentication Successful")
    return True

