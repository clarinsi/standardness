import argparse
import copy
import csv
import logging
import os
import time

import gspread
from gspread.utils import a1_range_to_grid_range
from apiclient import discovery
from google.oauth2.service_account import Credentials

# FORMAT THE HEADERS AND COLUMNS OF THE TABULAR PART OF THE WORKSHEET
# COLORS TO BE USED
# BLUE - R: 156, G: 200, B: 255
blue = (round(156 / 255, 2), round(200 / 255, 2), round(255 / 255, 2))
second_blue = (round(213 / 255, 2), round(232 / 255, 2), round(255 / 255, 2))

# GREEN - R: 218, G: 255, B: 209
green = (round(218 / 255, 2), round(255 / 255, 2), round(209 / 255, 2))
second_green = (round(172 / 255, 2), round(239 / 255, 2), round(155 / 255, 2))
# ORANGE - R: 255, G: 240, B: 209
orange = (round(255 / 255, 2), round(240 / 255, 2), round(209 / 255, 2))
# YELLOW - R: 251, G: 255, B: 209
yellow = (round(251 / 255, 2), round(255 / 255, 2), round(209 / 255, 2))
# PURPLE - R: 222, G: 183, B: 255
purple = (round(222 / 255, 2), round(183 / 255, 2), round(255 / 255, 2))
# RED - R: 239, G: 175, B: 155
red = (round(239 / 255, 2), round(175 / 255, 2), round(155 / 255, 2))
# GRAY - R: 225, G: 225, B: 225
gray = (round(225 / 255, 2), round(225 / 255, 2), round(225 / 255, 2))

header_format = {
                    "backgroundColor": {
                        "red": 0.0,
                        "green": 0.0,
                        "blue": 0.0
                    },
                    "horizontalAlignment": "LEFT",
                    "textFormat": {
                        "foregroundColor": {
                            "red": 1.0,
                            "green": 1.0,
                            "blue": 1.0
                        },
                        "fontSize": 12,
                        "bold": True
                    }
                }

def create_column_settings(color):
    return {
            "backgroundColor": {
            "red": color[0],
            "green": color[1],
            "blue": color[2]
        },
        "horizontalAlignment": "LEFT",
        "textFormat": {
            "foregroundColor": {
                "red": 0.0,
                "green": 0.0,
                "blue": 0.0
            },
            "fontSize": 10,
            "bold": False
        }
    }

blue_column = create_column_settings(blue)
green_column = create_column_settings(green)
second_blue_column = create_column_settings(second_blue)
second_green_column = create_column_settings(second_green)
purple_column = create_column_settings(purple)
yellow_background = create_column_settings(yellow)
wrap_format = {"wrapStrategy": 'WRAP'}


def create_folder(drive_service, name, parent_id=None):
    # create root folder
    if parent_id is None:
        root_folder_metadata = {
            'name': name,
            "mimeType": "application/vnd.google-apps.folder",
        }
    else:
        root_folder_metadata = {
            'name': name,
            "mimeType": "application/vnd.google-apps.folder",
            'parents': [parent_id]
        }
    return drive_service.files().create(body=root_folder_metadata,
                                               fields='id').execute()['id']


def create_spreadsheet(drive_service, name, parent_id):
    file_metadata = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.spreadsheet',
        'parents': [parent_id]
    }
    return drive_service.files().create(body=file_metadata).execute()

def authenticate(credentials_file):
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    credentials = Credentials.from_service_account_file(
        credentials_file,
        scopes=scopes
    )

    return discovery.build('drive', 'v3', credentials=credentials)

def add_permissions(drive_service, root_folder, permission_emails):
    # add admin credentials to myself
    for email in permission_emails.split(';'):
        permission = {
            'type': 'user',
            'role': 'writer',
            'emailAddress': email,  # Please set the email address of the user that you want to share.
        }
        drive_service.permissions().create(fileId=root_folder, body=permission).execute()

def create_folders(drive_service):
    # create root folder
    root_folder_id = create_folder(drive_service, 'normalization_annotation')

    # create students
    student1_folder_id = create_folder(drive_service, 'student1', root_folder_id)
    student2_folder_id = create_folder(drive_service, 'student2', root_folder_id)

    # create editor
    editor_folder_id = create_folder(drive_service, 'editor', root_folder_id)

    return root_folder_id, student1_folder_id, student2_folder_id, editor_folder_id


def get_folder_ids(drive_service):
    children = drive_service.files().list().execute()
    for file_data in children['files']:
        if file_data['name'] == 'normalization_annotation':
            root_folder_id = file_data['id']
        elif file_data['name'] == 'student1':
            student1_folder_id = file_data['id']
        elif file_data['name'] == 'student2':
            student2_folder_id = file_data['id']
        elif file_data['name'] == 'editor':
            editor_folder_id = file_data['id']

    return root_folder_id, student1_folder_id, student2_folder_id, editor_folder_id


def form_file_content(file_path):
    empty_row = []
    file = []

    # header
    file.append(['text_id', 'token_id', 'space_after', 'token_automatic', 'norm_manual', 'annotator_comment', '', '', ''])
    file.append([])
    with open(file_path, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter='\t', quoting=csv.QUOTE_NONE)
        for row in reader:
            file.append(row)

    file.append(['KONČANO'])

    return file


def create_student1_document(sh, num_of_lines, update_cells, merge_cells, sheet_id):
    first_worksheet = sh.get_worksheet(0)

    header_format_fields = "userEnteredFormat(%s)" % ','.join(header_format.keys())

    column_fields = "userEnteredFormat(%s)" % ','.join(blue_column.keys())

    email_address = [
        permission.get('emailAddress')
        for permission in sh.list_permissions()
        if permission.get('emailAddress')
    ]

    body_requests = [
            # create first sheet with sheetId 1
            {
                'addSheet': {
                    'properties': {
                        "sheetId": sheet_id,
                        'title': 'Document',
                        'sheetType': 'GRID',
                        'gridProperties': {
                            'rowCount': str(num_of_lines + 3),
                            'columnCount': 11,
                        },
                    }
                }
            },
            {'deleteSheet': {'sheetId': first_worksheet.id}},
            {"updateCells": update_cells},
            {
                "repeatCell": {
                    "range": a1_range_to_grid_range("A1:F1", sheet_id),
                    "cell": {"userEnteredFormat": header_format},
                    "fields": header_format_fields,
                }
            },
            {
                "repeatCell": {
                    "range": a1_range_to_grid_range(f"E3:E{str(num_of_lines)}", sheet_id),
                    "cell": {"userEnteredFormat": blue_column},
                    "fields": column_fields,
                }
            },
            {
                "repeatCell": {
                    "range": a1_range_to_grid_range(f"F3:F{str(num_of_lines)}", sheet_id),
                    "cell": {"userEnteredFormat": green_column},
                    "fields": column_fields,
                }
            },
            {
                "repeatCell": {
                    "range": a1_range_to_grid_range(f"A1:K{str(num_of_lines+2)}", sheet_id),
                    "cell": {"userEnteredFormat": wrap_format},
                    "fields": "userEnteredFormat(%s)" % ','.join(wrap_format.keys()),
                }
            },
            {
                "repeatCell": {
                    "range": a1_range_to_grid_range(f"E{str(num_of_lines+1)}:E{str(num_of_lines+1)}", sheet_id),
                    "cell": {"userEnteredFormat": yellow_background},
                    "fields": column_fields,
                }
            },
            {
                "addProtectedRange": {
                    'protectedRange': {
                        "protectedRangeId": 29,
                        "range": a1_range_to_grid_range(f"A1:D{str(num_of_lines)}", sheet_id),
                        "description": None,
                        "warningOnly": False,
                        "requestingUserCanEdit": False,
                        "editors": {
                            "users": email_address,
                        }
                    }
                }
            },

            {
                'updateDimensionProperties': {
                    'range': {
                                  "sheetId": sheet_id,
                                  "dimension": 'COLUMNS',
                                  "startIndex": 0,
                                  "endIndex": 6
                                },
                    'properties': {'pixelSize': 200},
                    'fields': 'pixelSize'
                }
            },
    ]
    merge_rows = [{'mergeCells': {
        'mergeType': 'MERGE_ALL',
        'range': {
            'endColumnIndex': 11,
            'endRowIndex': row+1,
            'sheetId': sheet_id,
            'startColumnIndex': 0,
            'startRowIndex': row
        }
    }} for row in merge_cells]

    body_requests += merge_rows

    body = {
        'requests': body_requests
    }

    log = sh.batch_update(body)
    print(log)
    return log


def create_student2_document(sh, num_of_lines, sheet_id):
    column_fields = "userEnteredFormat(%s)" % ','.join(blue_column.keys())

    body_requests = [
        # create first sheet with sheetId 1
        {
            "repeatCell": {
                "range": a1_range_to_grid_range(f"E3:E{str(num_of_lines)}", sheet_id),
                "cell": {"userEnteredFormat": second_blue_column},
                "fields": column_fields,
            }
        },
        {
            "repeatCell": {
                "range": a1_range_to_grid_range(f"F3:F{str(num_of_lines)}", sheet_id),
                "cell": {"userEnteredFormat": second_green_column},
                "fields": column_fields,
            }
        },
    ]

    body = {
        'requests': body_requests
    }

    log = sh.batch_update(body)
    print(log)
    return log


def create_editor_document(sh, num_of_lines, sheet_id, student1_link, student2_link):
    column_fields = "userEnteredFormat(%s)" % ','.join(blue_column.keys())
    header_format_fields = "userEnteredFormat(%s)" % ','.join(header_format.keys())

    update_cells = {
        "rows": [{"values": [
                            {"userEnteredValue": {"formulaValue": f'=IMPORTRANGE("{student1_link}", "Document!E{i}:E{i}")'}},
                            {"userEnteredValue": {"formulaValue": f'=IMPORTRANGE("{student1_link}", "Document!F{i}:F{i}")'}},
                            {"userEnteredValue": {"formulaValue": f'=IMPORTRANGE("{student2_link}", "Document!E{i}:E{i}")'}},
                            {"userEnteredValue": {"formulaValue": f'=IMPORTRANGE("{student2_link}", "Document!F{i}:F{i}")'}},
                        ]} for i in range(4, num_of_lines+2)],
        "fields": "*",
        "start": {"sheetId": sheet_id, "rowIndex": 3, "columnIndex": 4}
    }

    body_requests = [
        # create first sheet with sheetId 1
        {
            "updateCells": {
                "rows": [
                    {"values":
                         [
                             {"userEnteredValue": {"stringValue": 'norm_A'}},
                             {"userEnteredValue": {"stringValue": 'comment_A'}},
                             {"userEnteredValue": {"stringValue": 'norm_B'}},
                             {"userEnteredValue": {"stringValue": 'comment_B'}},
                             {"userEnteredValue": {"stringValue": 'Final'}},
                         ]}
                ],
                "fields": "*",
                "start": {"sheetId": sheet_id, "rowIndex": 0, "columnIndex": 4}
            }
        },
        # set links
        {
            "updateCells": update_cells
        },
        {
            "repeatCell": {
                "range": a1_range_to_grid_range("A1:I1", sheet_id),
                "cell": {"userEnteredFormat": header_format},
                "fields": header_format_fields,
            }
        },
        {
            "repeatCell": {
                "range": a1_range_to_grid_range(f"E3:E{str(num_of_lines)}", sheet_id),
                "cell": {"userEnteredFormat": blue_column},
                "fields": column_fields,
            }
        },
        {
            "repeatCell": {
                "range": a1_range_to_grid_range(f"F3:F{str(num_of_lines)}", sheet_id),
                "cell": {"userEnteredFormat": green_column},
                "fields": column_fields,
            }
        },
        {
            "repeatCell": {
                "range": a1_range_to_grid_range(f"G3:G{str(num_of_lines)}", sheet_id),
                "cell": {"userEnteredFormat": second_blue_column},
                "fields": column_fields,
            }
        },
        {
            "repeatCell": {
                "range": a1_range_to_grid_range(f"H3:H{str(num_of_lines)}", sheet_id),
                "cell": {"userEnteredFormat": second_green_column},
                "fields": column_fields,
            }
        },
        {
            "repeatCell": {
                "range": a1_range_to_grid_range(f"I3:I{str(num_of_lines)}", sheet_id),
                "cell": {"userEnteredFormat": purple_column},
                "fields": column_fields,
            }
        },
        {
            'updateDimensionProperties': {
                'range': {
                    "sheetId": sheet_id,
                    "dimension": 'COLUMNS',
                    "startIndex": 0,
                    "endIndex": 9
                },
                'properties': {'pixelSize': 200},
                'fields': 'pixelSize'
            }
        },
        {
            "repeatCell": {
                "range": a1_range_to_grid_range(f"E{str(num_of_lines + 1)}:E{str(num_of_lines + 1)}", sheet_id),
                "cell": {"userEnteredFormat": yellow_background},
                "fields": column_fields,
            }
        },
        {
            "repeatCell": {
                "range": a1_range_to_grid_range(f"G{str(num_of_lines + 1)}:G{str(num_of_lines + 1)}", sheet_id),
                "cell": {"userEnteredFormat": yellow_background},
                "fields": column_fields,
            }
        },
        {
            "deleteProtectedRange": {
                "protectedRangeId": 29,
            }
        },
        {
            "addProtectedRange": {
                'protectedRange': {
                    "protectedRangeId": 30,
                    "range": a1_range_to_grid_range(f"A1:D{str(num_of_lines)}", sheet_id),
                    "description": None,
                    "warningOnly": True,
                    "requestingUserCanEdit": False,
                }
            }
        },
    ]

    body = {
        'requests': body_requests
    }

    log = sh.batch_update(body)
    print(log)
    return log


def main(args):
    # create folder system, if it doesn't exist
    drive_service = authenticate(args.credentials_file)

    # DELETE ALL FILES/FOLDERS
    if args.delete_all:
        children = drive_service.files().list().execute()
        for file_data in children['files']:
            # if file_data['name'] == 'normalization_annotation':
            drive_service.files().delete(fileId=file_data['id']).execute()

    if args.create_folders:
        root_folder_id, student1_folder_id, student2_folder_id, editor_folder_id = create_folders(drive_service)
        add_permissions(drive_service, root_folder_id, args.permission_emails)
    else:
        root_folder_id, student1_folder_id, student2_folder_id, editor_folder_id = get_folder_ids(drive_service)

    children = drive_service.files().list().execute()


    student1_files = {dic['name']: dic['id'] for dic in drive_service.files().list(q=f"'{student1_folder_id}' in parents").execute()['files']}
    student2_files = {dic['name']: dic['id'] for dic in drive_service.files().list(q=f"'{student2_folder_id}' in parents").execute()['files']}
    editor_files = {dic['name']: dic['id'] for dic in drive_service.files().list(q=f"'{editor_folder_id}' in parents").execute()['files']}

    print(f"ROOT FOLDER ID: {root_folder_id}")
    gc = gspread.service_account(filename=args.credentials_file)

    with open(args.links_spreadsheet, 'w') as links_writer:
        links_writer.write(f'File\tStudent1_link\tStudent2_link\tEditor_link\n')
        for file in os.listdir(args.input_folder):
            print(f'CREATING FILE - {file}')
            if file in student1_files:
                sh = gc.open_by_key(student1_files[file])
            else:
                sh = gc.create(file, folder_id=student1_folder_id)

            # form file content from input
            file_content = form_file_content(os.path.join(args.input_folder, file))
            num_of_lines = len(file_content) - 1
            sheet_id = 1

            # merge cells with empty second column
            merge_cells = [i for i, line in enumerate(file_content) if len(line) <= 1][1:-1]

            # generate json
            fields = f"A1:H{len(file_content)}"
            update_cells = {
                "rows": [{"values": [{"userEnteredValue": {"stringValue": cell}} for cell in row]} for row in file_content],
                # "fields": fields,
                "fields": "*",
                "start": {"sheetId": sheet_id, "rowIndex": 0, "columnIndex": 0}
            }

            if file not in student1_files:
                sh.share(None, perm_type='anyone', role='writer')
                student1_file_id = create_student1_document(sh, num_of_lines, update_cells, merge_cells, sheet_id)['spreadsheetId']
            else:
                student1_file_id = student1_files[file]

            if file not in student2_files:
                student2_file = gc.copy(student1_file_id, file, copy_permissions=True)
                student2_file.share(None, perm_type='anyone', role='writer')
                student2_file_id = student2_file.id
                log = create_student2_document(student2_file, num_of_lines, sheet_id)
                drive_service.files().update(fileId=student2_file_id,
                                             addParents=student2_folder_id,
                                             removeParents=student1_folder_id,
                                             fields='id, parents').execute()
            else:
                student2_file_id = student2_files[file]

            student1_link = f'https://docs.google.com/spreadsheets/d/{student1_file_id}'
            student2_link = f'https://docs.google.com/spreadsheets/d/{student2_file_id}'

            if file not in editor_files:
                editor_file = gc.copy(student1_file_id, file, copy_permissions=True)
                editor_file.share(None, perm_type='anyone', role='writer')
                editor_file_id = editor_file.id
                log = create_editor_document(editor_file, num_of_lines, sheet_id, student1_link, student2_link)
                drive_service.files().update(fileId=editor_file_id,
                                                    addParents=editor_folder_id,
                                                    removeParents=student1_folder_id,
                                                    fields='id, parents').execute()
            else:
                editor_file_id = editor_files[file]

            editor_link = f'https://docs.google.com/spreadsheets/d/{editor_file_id}'
            links_writer.write(f'{file}\t{student1_link}\t{student2_link}\t{editor_link}\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Walk over results from regression bert and regression svm.')
    parser.add_argument('--input_folder', default='data/selected_tweets/output_split_data',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    parser.add_argument('--delete_all',
                        help='If used, words have to be in the same order as components.',
                        action='store_true')
    parser.add_argument('--create_folders',
                        help='If used, words have to be in the same order as components.',
                        action='store_true')
    parser.add_argument('--links_spreadsheet', default='data/selected_tweets/links_spreadsheet.tsv',
                        help='Store links for selected tweets!')
    parser.add_argument('--credentials_file', default='normalization-test-0ac74028eef9.json',
                        help='Store links for selected tweets!')
    parser.add_argument('--permission_emails', default='',
                        help='Store links for selected tweets!')
    args = parser.parse_args()

    start = time.time()
    main(args)
    logging.info("TIME: {}".format(time.time() - start))
