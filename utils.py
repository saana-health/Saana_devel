#test
from mixpanel_api import Mixpanel
import csv
import pdb

def export_mixpanel_to_csv():
    TOKEN = '8cfc96a92162cdef9f20674d125c37f5'
    SECRET = '1261347a3eb35286683e32a2731e4f4d'

    mp = Mixpanel(SECRET, token = TOKEN)

    mp.export_people('test_event_export.csv',
                    {},
                    format='csv')

def process_mixpanel_csv():
    with open('test_event_export.csv') as csvfile:
        reader_list = list(csv.reader(csvfile))
        columns = [x.replace('$','') for x in reader_list[0]]

        matrix = [[0 for x in range(len(reader_list[0]))] for y in range(len(reader_list))]

        for i in range(len(reader_list)):
            for j in range(len(reader_list[i])):
                content = reader_list[i][j]
                if content and content[0] == '[':
                    if content[1] == 'u':
                        content = content.replace('$','').replace('[u','').replace('[','').replace(']','')
                matrix[i][j] = content

    with open ('mixpanelData.csv','wb',) as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(matrix)

