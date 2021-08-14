from json import load
import os
import sys
import argparse

import msal
import requests
import pandas as pd
from rich.console import Console
from rich.table import Table

PBI_CLIENT_ID = os.getenv('PBI_CLIENT_ID')
PBI_USER = os.getenv('PBI_USER')
PBI_PASSWORD = os.getenv('PBI_PASSWORD')

PBI_DATASET_ID = os.getenv('PBI_DATASET_ID')

PBI_AUTHORITY = 'https://login.microsoftonline.com/organizations'
PBI_SCOPES = ['https://analysis.windows.net/powerbi/api/.default']

DEFAULT_DAX_QUERY_FILE = './dax_query.dax'


def configure_cli_arguments():
    '''Configure the command line arguments'''

    parser = argparse.ArgumentParser()
    parser.add_argument('dax_query_file_path', nargs='?', default=DEFAULT_DAX_QUERY_FILE,
                        help=f'The path to the file containing the DAX query. Default value: {DEFAULT_DAX_QUERY_FILE}')
    parser.add_argument(
        '-csv', help='The path to a CSV file to store the results', metavar='csv_file_path')
    return parser


def parse_cli_arguments(parser):
    '''Parse the command line arguments'''
    return vars(parser.parse_args())


def print_help(parser):
    '''Print an usage mensaje to the console'''
    parser.print_help()


def get_dax_query_from_file(args):
    '''Get a DAX query from a file passed as argument in the command line or DEFAULT_DAX_QUERY_FILE'''

    dax_query_file = args['dax_query_file_path']
    with open(dax_query_file, encoding='utf-8') as f:
        dax_query = f.read()

    return dax_query


def get_output_csv_file_path(args):
    '''Get ths path of a CSV file to save the results, from the command line arguments. Or returns None if no argument was found'''
    return args['csv']


def get_access_token():
    '''Returns an AAD token using MSAL'''

    response = None
    try:
        clientapp = msal.PublicClientApplication(
            PBI_CLIENT_ID, authority=PBI_AUTHORITY)
        accounts = clientapp.get_accounts(username=PBI_USER)
        if accounts:
            # Retrieve Access token from cache if available
            response = clientapp.acquire_token_silent(
                PBI_SCOPES, account=accounts[0])
        if not response:
            # Make a client call if Access token is not available in cache
            response = clientapp.acquire_token_by_username_password(
                PBI_USER, PBI_PASSWORD, scopes=PBI_SCOPES)

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
        headers=headers,
        json={
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


def get_dax_result_rows(dax_result):
    '''Returns the rows from the result of the call to the API'''
    return dax_result['results'][0]['tables'][0]['rows']


def print_dax_result(dax_result):
    '''Print the results from the Power BI REST API as a table using Rich'''

    table = Table(show_header=True, header_style='bold')

    is_first_row = True
    for row in get_dax_result_rows(dax_result):
        if is_first_row:
            is_first_row = False
            for column_name in row.keys():
                table.add_column(column_name)
        table.add_row(*list(map(lambda x: str(x), row.values())))

    console = Console()
    console.print(table)


def load_dax_result_to_dataframe(dax_result):
    '''Load to a DataFrame with the results of the call to the API'''

    rows = get_dax_result_rows(dax_result)
    df_columns = rows[0].keys()
    df_data = [list(r.values()) for r in rows]
    return pd.DataFrame(df_data, columns=df_columns)


def save_dax_result_to_csv(dax_result, file_path):
    '''Save to a CSV file the results of the call to the API'''

    df = load_dax_result_to_dataframe(dax_result)
    df.to_csv(file_path, index=False)


args_parser = configure_cli_arguments()
args = parse_cli_arguments(args_parser)

try:

    dax_query = get_dax_query_from_file(args)
    print_dax_query(dax_query)

except FileNotFoundError:
    print('Error: The file with the DAX query was not found.')
    print()
    print_help(args_parser)
    exit(1)

access_token = get_access_token()
r = execute_dax(access_token, PBI_DATASET_ID, dax_query)

print_dax_result(r)

csv_file_path = get_output_csv_file_path(args)
if csv_file_path is not None:
    save_dax_result_to_csv(r, csv_file_path)
