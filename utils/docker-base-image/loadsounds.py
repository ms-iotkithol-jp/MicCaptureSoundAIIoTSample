
import os
import csv
import numpy as np
import random

def load_csvdata(file):
    with open(file) as f:
        reader = csv.reader(f)
        l = [row for row in reader]
        l.pop(0)
        return np.array(l).T.astype(np.int16) / 32768

# data_folder = 'data'
# data_folder_path = os.path.join(os.getcwd(), data_folder)

def parse_file(file_path, labeled_dataset, data_chunk, by_channel=False):
    csvdata = load_csvdata(file_path)
    if by_channel:
        if len(csvdata) > 0:
            num_of_block = int(len(csvdata[0]) / data_chunk)
            if num_of_block > 0 :
                labeled_dataset = np.ndarray(shape=(len(csvdata),num_of_block,data_chunk))

    num_of_chunk = 0
    for index, umicdata in enumerate(csvdata):
        if len(umicdata) % data_chunk == 0:
            micdata1024 = np.split(umicdata, len(umicdata) / data_chunk)
            if by_channel:
                labeled_dataset[index] = micdata1024
            else:
                if len(labeled_dataset) == 0:
                    labeled_dataset = micdata1024
                else:
                    labeled_dataset = np.append(labeled_dataset, micdata1024,axis=0)
            num_of_chunk = num_of_chunk + len(micdata1024)

    # print('{}:{} units'.format(file_path, num_of_chunk))
    return num_of_chunk, labeled_dataset

def load_data_definition(data_def_file_path):
    data_chunk = 1024
    with open(data_def_file_path, "rt") as ymlFile:
        lineDef = ymlFile.readline().rstrip().split(':')
        if len(lineDef)==2 and lineDef[0] == 'data-chunk':
            data_chunk = int(lineDef[1])
    return data_chunk

def reshape_dataset(sound_data, data_chunk):
    dataset = np.zeros((len(sound_data), 1, 1, data_chunk))
    for index, d in enumerate(sound_data):
        dataset[index][0][0] = d

    return dataset

# data_chunk = 1024
def load_data(data_folder_path, data_def_file):
    data_chunk = 1024
    
    tdata ={}
    num_of_data = 0
    for df in os.listdir(path=data_folder_path):
        if df == data_def_file:
            ddefFile = os.path.join(data_folder_path, df)
            data_chunk = load_data_definition(ddefFile)
            print('data_chunk - {}'.format(data_chunk))
            continue
            
        tdata[df] = np.array([])
        ldata_folder_path = os.path.join(data_folder_path,df)
        for datafile in os.listdir(path=ldata_folder_path):
            datafile_path = os.path.join(ldata_folder_path, datafile)
            num_of_chunks, tdata[df] = parse_file(datafile_path, tdata[df], data_chunk)
            num_of_data = num_of_data + num_of_chunks
#            csvdata = load_csvdata(os.path.join(ldata_folder_path, datafile))
#            for umicdata in csvdata:
#                if len(umicdata) % data_chunk == 0:
#                    micdata1024 = np.split(umicdata, len(umicdata) / data_chunk)
#                    if len(tdata[df]) == 0:
#                        tdata[df] = micdata1024
#                    else:
#                        tdata[df] = np.append(tdata[df], micdata1024,axis=0)
#                    num_of_data = num_of_data + len(micdata1024)

    data_of_sounds = np.zeros((num_of_data, 1, 1, data_chunk))
    label_of_sounds = np.zeros(num_of_data,dtype=int)
    label_matrix_of_sounds = np.zeros((num_of_data, len(tdata.keys())))
    labelname_of_sounds = np.empty(num_of_data,dtype=object)
    index = 0
    lindex = 0
    labeling_for_train = {}
    for l in tdata.keys():
        for micdata1024 in tdata[l]:
            data_of_sounds[index][0][0] = micdata1024
            label_of_sounds[index] = lindex
            label_matrix_of_sounds[index, lindex] = 1.
            labelname_of_sounds[index] = l
            index = index + 1
        labeling_for_train[l] = lindex
        lindex = lindex + 1

    indexx = np.arange(num_of_data)
    random.shuffle(indexx)

    data_of_sounds = data_of_sounds[indexx]
    label_matrix_of_sounds = label_matrix_of_sounds[indexx]
    label_of_sounds = label_of_sounds[indexx]
    labelname_of_sounds = labelname_of_sounds[indexx]

    # train_dataset is labeled sound data set
    train_dataset = [data_of_sounds, label_of_sounds, labelname_of_sounds]
    
    return train_dataset
