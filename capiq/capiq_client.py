import requests
import json
import logging
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.exceptions import InsecureRequestWarning


class CapIQClient:
    _endpoint = 'https://sdk.gds.standardandpoors.com/gdssdk/rest/v2/clientservice.json'
    _headers = {'Content-Type': 'application/x-www-form-urlencoded', 'Accept-Encoding': 'gzip,deflate'}
    _verify = True  # Disable SSL Checks for requests. Set to False to avoid SSL blocking in secured networks
    _username = None
    _password = None
    _debug = False

    def __init__(self, username, password, verify=True, debug=False):
        assert username is not None
        assert password is not None
        assert verify is not None
        assert debug is not None
        self._username = username
        self._password = password
        self._verify = verify
        self._debug = debug
        if not self._verify:
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        if self._debug:
            self.enable_request_debugging()
        else:
            self.enable_error_logging()

    # This function retrieves a single data point for a point in time value for a mnemonic either current or
    # historical. Default inputs include a Mnemonic and a Security/Entity Identifier
    #
    # Returns a nested dictionary, where the primary key is the identifier and the secondary key is the mnemonic.
    # In case of an error, a None value is returned for that mnemonic and Cap IQ's error is logged
    def gdsp(self, identifiers, mnemonics, return_keys, properties=None):
        req_array = []
        returnee = {}
        mnemonic_return_keys = self.build_mnemonic_return_key_index(mnemonics, return_keys, properties)

        for identifier in identifiers:
            for i, mnemonic in enumerate(mnemonics):
                req_array.append({"function": "GDSP", "identifier": identifier, "mnemonic": mnemonic,
                                  "properties": properties[i] if properties else {}})
        req = {"inputRequests": req_array}
        response = requests.post(self._endpoint, headers=self._headers, data='inputRequests=' + json.dumps(req),
                                 auth=HTTPBasicAuth(self._username, self._password), verify=self._verify)
        if self._debug:
            logging.info("Cap IQ response")
            logging.info(response.json())
        for ret in response.json()['GDSSDKResponse']:
            identifier = ret['Identifier']
            if identifier not in returnee:
                returnee[identifier] = {}
            if ret['ErrMsg']:
                logging.error(
                    'Cap IQ error for ' + identifier + ' + ' + ret['Mnemonic'] + ' query: ' + ret['ErrMsg'])
                returnee[identifier][self.get_return_key(ret['Mnemonic'], properties, mnemonic_return_keys)] = None
            else:
                for i_m, h_m in enumerate(ret["Headers"]):
                    returnee[identifier][
                        self.get_return_key(ret['Mnemonic'], properties, mnemonic_return_keys)
                    ] = ret['Rows'][i_m]['Row'][0]
        return returnee

    def gdspv(self, identifiers, mnemonics, return_keys, properties=None):
        req_array = []
        returnee = {}
        mnemonic_return_keys = self.build_mnemonic_return_key_index(mnemonics, return_keys, properties)
        for identifier in identifiers:
            for i, mnemonic in enumerate(mnemonics):
                req_array.append({"function": "GDSPV", "identifier": identifier, "mnemonic": mnemonic,
                                  "properties": properties[i] if properties else {}})
        req = {"inputRequests": req_array}
        response = requests.post(self._endpoint, headers=self._headers, data='inputRequests=' + json.dumps(req),
                                 auth=HTTPBasicAuth(self._username, self._password), verify=self._verify)
        if self._debug:
            logging.info("Cap IQ response")
            logging.info(response.json())
        for return_index, ret in enumerate(response.json()['GDSSDKResponse']):
            identifier = ret['Identifier']
            if identifier not in returnee:
                returnee[identifier] = {}
            if ret['ErrMsg']:
                logging.error(
                    'Cap IQ error for ' + identifier + ' + ' + ret['Mnemonic'] + ' query: ' + ret['ErrMsg'])
                returnee[identifier][self.get_return_key(ret['Mnemonic'], properties, mnemonic_return_keys)] = None
            else:
                for i_m, h_m in enumerate(ret["Headers"]):
                    returnee[identifier][
                        self.get_return_key(ret['Mnemonic'], properties, mnemonic_return_keys)
                    ] = ret['Rows'][i_m]['Row'][0]
        return returnee

    def gdst(self, identifiers, mnemonics, return_keys, start_date=None, end_date=None, frequency=None,
             properties=None):
        # properties or the start_date and frequency must be set
        if not properties:
            properties = []
            for i in range(0, len(mnemonics)):
                properties.append({})
        for p in properties:
            if frequency:
                p["FREQUENCY"] = frequency
            if start_date:
                p["STARTDATE"] = start_date
            if end_date:
                p["ENDDATE"] = end_date

        req_array = []
        returnee = {}
        mnemonic_return_keys = self.build_mnemonic_return_key_index(mnemonics, return_keys, properties)
        for identifier in identifiers:
            for i, mnemonic in enumerate(mnemonics):
                req_array.append(
                    {"function": "GDST", "identifier": identifier, "mnemonic": mnemonic, "properties": properties[i]})
        req = {"inputRequests": req_array}
        response = requests.post(self._endpoint, headers=self._headers, data='inputRequests=' + json.dumps(req),
                                 auth=HTTPBasicAuth(self._username, self._password), verify=self._verify)
        if self._debug:
            logging.info("Cap IQ response")
            logging.info(response.json())
        for return_index, ret in enumerate(response.json()['GDSSDKResponse']):
            identifier = ret['Identifier']
            if identifier not in returnee:
                returnee[identifier] = {}
            if ret['ErrMsg']:
                logging.error(
                    'Cap IQ error for ' + identifier + ' + ' + ret['Mnemonic'] + ' query: ' + ret['ErrMsg'])
                returnee[identifier][self.get_return_key(ret['Mnemonic'], properties, mnemonic_return_keys)] = None
            else:
                returnee[identifier][self.get_return_key(ret['Mnemonic'], properties, mnemonic_return_keys)] = []
                for row in ret["Rows"]:
                    returnee[identifier][
                        self.get_return_key(ret['Mnemonic'], properties, mnemonic_return_keys)
                    ].append(row['Row'])
        return returnee

    def gdshe(self, identifiers, mnemonics, return_keys, start_date=None, end_date=None, properties=None):
        if not properties:
            properties = []
            for i in range(0, len(mnemonics)):
                properties.append({})
        for p in properties:
            if start_date:
                p["STARTDATE"] = start_date
            if end_date:
                p["ENDDATE"] = end_date

        req_array = []
        returnee = {}
        mnemonic_return_keys = self.build_mnemonic_return_key_index(mnemonics, return_keys, properties)
        for identifier in identifiers:
            for i, mnemonic in enumerate(mnemonics):
                req_array.append(
                    {"function": "GDSHE", "identifier": identifier, "mnemonic": mnemonic, "properties": properties[i]})
        req = {"inputRequests": req_array}
        response = requests.post(self._endpoint, headers=self._headers, data='inputRequests=' + json.dumps(req),
                                 auth=HTTPBasicAuth(self._username, self._password), verify=self._verify)
        if self._debug:
            logging.info("Cap IQ response")
            logging.info(response.json())
        for return_index, ret in enumerate(response.json()['GDSSDKResponse']):
            identifier = ret['Identifier']
            if identifier not in returnee:
                returnee[identifier] = {}
            if ret['ErrMsg']:
                logging.error(
                    'Cap IQ error for ' + identifier + ' + ' + ret['Mnemonic'] + ' query: ' + ret['ErrMsg'])
                returnee[identifier][self.get_return_key(ret['Mnemonic'], properties, mnemonic_return_keys)] = None
            else:
                returnee[identifier][self.get_return_key(ret['Mnemonic'], properties, mnemonic_return_keys)] = []
                for row in ret["Rows"]:
                    returnee[identifier][
                        self.get_return_key(ret['Mnemonic'], properties, mnemonic_return_keys)
                    ].append(row['Row'])
        return returnee

    def gdshv(self, identifiers, mnemonics, return_keys, start_date=None, end_date=None, properties=None):
        if not properties:
            properties = []
            for i in range(0, len(mnemonics)):
                properties.append({})
        for p in properties:
            if start_date:
                p["STARTDATE"] = start_date
            if end_date:
                p["ENDDATE"] = end_date

        req_array = []
        returnee = {}
        mnemonic_return_keys = self.build_mnemonic_return_key_index(mnemonics, return_keys, properties)

        for identifier in identifiers:
            for i, mnemonic in enumerate(mnemonics):
                req_array.append(
                    {"function": "GDSHV", "identifier": identifier, "mnemonic": mnemonic, "properties": properties[i]})
        req = {"inputRequests": req_array}
        response = requests.post(self._endpoint, headers=self._headers, data='inputRequests=' + json.dumps(req),
                                 auth=HTTPBasicAuth(self._username, self._password), verify=self._verify)
        if self._debug:
            logging.info("Cap IQ response")
            logging.info(response.json())
        for return_index, ret in enumerate(response.json()['GDSSDKResponse']):
            identifier = ret['Identifier']
            if identifier not in returnee:
                returnee[identifier] = {}
            if ret['ErrMsg']:
                logging.error(
                    'Cap IQ error for ' + identifier + ' + ' + ret['Mnemonic'] + ' query: ' + ret['ErrMsg'])
                returnee[identifier][self.get_return_key(ret['Mnemonic'], properties, mnemonic_return_keys)] = None
            else:
                for i_m, h_m in enumerate(ret["Headers"]):
                    returnee[identifier][
                        self.get_return_key(ret['Mnemonic'], properties, mnemonic_return_keys)
                    ] = ret['Rows'][i_m]['Row'][0]
        return returnee

    def gdsg(self, identifiers, group_mnemonics, return_keys, properties=None):
        req_array = []
        returnee = {}
        mnemonic_return_keys = self.build_mnemonic_return_key_index(group_mnemonics, return_keys, properties)

        for identifier in identifiers:
            for i, mnemonic in enumerate(group_mnemonics):
                req_array.append({"function": "GDSG", "identifier": identifier, "mnemonic": mnemonic,
                                  "properties": properties[i] if properties else {}})
        req = {"inputRequests": req_array}
        response = requests.post(self._endpoint, headers=self._headers, data='inputRequests=' + json.dumps(req),
                                 auth=HTTPBasicAuth(self._username, self._password), verify=self._verify)
        if self._debug:
            logging.info("Cap IQ response")
            logging.info(response.json())
        for return_index, ret in enumerate(response.json()['GDSSDKResponse']):
            identifier = ret['Identifier']
            if identifier not in returnee:
                returnee[identifier] = {}
            if ret['ErrMsg']:
                logging.error(
                    'Cap IQ error for ' + identifier + ' + ' + ret['Mnemonic'] + ' query: ' + ret['ErrMsg'])
                returnee[identifier][self.get_return_key(ret['Mnemonic'], ret['Properties'], mnemonic_return_keys)] = None
            else:
                for i_m, h_m in enumerate(ret["Headers"]):
                    returnee[identifier][
                        self.get_return_key(ret['Mnemonic'], properties, mnemonic_return_keys)
                    ] = ret['Rows'][i_m]['Row'][0]
        return returnee

    @staticmethod
    def build_mnemonic_return_key_index(mnemonics, return_keys, properties):
        """
                mnemonic_return_keys = {
            k: {"key": return_keys[v], "properties": properties[v]} for v, k in enumerate(mnemonics)
        }
        """
        mnemonic_return_keys = {}
        for index, mnemonic in enumerate(mnemonics):
            if mnemonic in mnemonic_return_keys:
                mnemonic_return_keys[mnemonic].append({"key": return_keys[index], "properties": properties[index]})

            else:
                mnemonic_return_keys[mnemonic] = [{"key": return_keys[index], "properties": properties[index]}]
        return mnemonic_return_keys

    @staticmethod
    def get_return_key(mnemonic, properties, mnemonics_to_return_key_index):
        if len(mnemonics_to_return_key_index[mnemonic]) == 1:
            return mnemonics_to_return_key_index[mnemonic][0]["key"]
        else:
            for index, return_key in enumerate(mnemonics_to_return_key_index[mnemonic]):
                match = True
                for property_name, property_value in return_key["properties"].items():
                    if not (return_key.lower() in properties and properties[property_name.lower()] == property_value):
                        match = False
                if match:
                    return mnemonics_to_return_key_index[mnemonic][index]["key"]

    @staticmethod
    def enable_request_debugging():
        # Enabling debugging at http.client level (requests->urllib3->http.client)
        # you will see the REQUEST, including HEADERS and DATA, and RESPONSE with HEADERS but without DATA.
        # the only thing missing will be the response.body which is not logged.
        try:  # for Python 3
            from http.client import HTTPConnection
        except ImportError:
            from requests.packages.urllib3.connectionpool import HTTPConnection
        HTTPConnection.debuglevel = 1

        logging.basicConfig()  # you need to initialize logging, otherwise you will not see anything from requests
        logging.getLogger().setLevel(logging.DEBUG)
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True

    @staticmethod
    def enable_error_logging():
        logging.basicConfig()  # you need to initialize logging, otherwise you will not see anything from requests
        logging.getLogger().setLevel(logging.ERROR)