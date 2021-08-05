import os
import sys

import msal
import requests
from rich.console import Console
from rich.table import Table

PBI_CLIENT_ID = os.getenv('PBI_CLIENT_ID')
PBI_USER = os.getenv('PBI_USER')
PBI_PASSWORD = os.getenv('PBI_PASSWORD')

PBI_DATASET_ID = os.getenv('PBI_DATASET_ID')

PBI_AUTHORITY = 'https://login.microsoftonline.com/organizations'
PBI_SCOPES = ['https://analysis.windows.net/powerbi/api/.default']

DEFAULT_DAX_QUERY_FILE = './dax_query.dax'

def get_dax_query_from_file():
    '''Get a DAX query from a file passed as the first argument or DEFAULT_DAX_QUERY_FILE'''

    dax_query_file = sys.argv[1] if len(sys.argv) >= 2 else DEFAULT_DAX_QUERY_FILE

    with open(dax_query_file, encoding='utf-8') as f:
        dax_query = f.read()
    
    return dax_query

def get_access_token():
    '''Returns an AAD token using MSAL'''

    response = None
    try:
        clientapp = msal.PublicClientApplication(PBI_CLIENT_ID, authority=PBI_AUTHORITY)
        accounts = clientapp.get_accounts(username=PBI_USER)
        if accounts:                
            # Retrieve Access token from cache if available
            response = clientapp.acquire_token_silent(PBI_SCOPES, account=accounts[0])
        if not response:
            # Make a client call if Access token is not available in cache
            response = clientapp.acquire_token_by_username_password(PBI_USER, PBI_PASSWORD, scopes=PBI_SCOPES)

        try:
            return response['access_token']
        except KeyError:
            raise Exception(response['error_description'])

    except Exception as ex:
        raise Exception('Error retrieving Access token\n' + str(ex))


def execute_dax(access_token, dataset_id, dax_query):
    '''Execute a DAX query using the Power BI REST API'''

    api_url = f'https://api.powerbi.com/v1.0/myorg/datasets/{dataset_id}/executeQueries'

    headers = {
        'Content-Type': 'application/json', 
        'Authorization': 'Bearer ' + access_token
    }

    r = requests.post(
        api_url,
        headers = headers,
        json = { 
            'queries': [
                {
                    'query': f'{dax_query}'
                }
            ]
        }
    )

    r.raise_for_status()
    r.encoding = 'utf-8-sig'
    return r.json()


def print_dax_query(dax_query):
    '''Print the DAX query'''

    table = Table('DAX query', expand=True)
    table.add_row(dax_query)
    console = Console()
    console.print(table)

def print_dax_result(dax_result):
    '''Print the results from the Power BI REST API as a table using Rich'''

    table = Table(show_header=True, header_style='bold')
    
    is_first_row = True
    for row in dax_result['results'][0]['tables'][0]['rows']:
        if is_first_row:
            is_first_row = False
            for column_name in row.keys():
                table.add_column(column_name)
        table.add_row(*list(map(lambda x: str(x), row.values())))
    
    console = Console()
    console.print(table)


dax_query = get_dax_query_from_file()
print_dax_query(dax_query)

access_token = get_access_token()
r = execute_dax(access_token, PBI_DATASET_ID, dax_query)

print_dax_result(r)
