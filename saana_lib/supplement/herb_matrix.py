import pdb
import csv

def process_herb_matrix(filename):
    herb_dict = {}
    with open(filename) as csvfile:
        reader_list = list(csv.reader(csvfile))
        columns = [x.lower() for x in reader_list[0]]
        for column in columns:
            if column == '':
                continue
            herb_dict[column] = []
        for row_num in range(1,len(reader_list)):
            herb_name = reader_list[row_num][0].lower()
            for cell_num in range(1,len(reader_list[row_num])):
                if reader_list[row_num][cell_num] != '':
                    herb_dict[columns[cell_num]].append(herb_name)
    #         herb_dict[herb_name] = []
    #         for col_num in range(1,len(reader_list[row_num])):
    #             if reader_list[row_num][col_num] != '':
    #                 herb_dict[herb_name].append(columns[col_num])
    return herb_dict