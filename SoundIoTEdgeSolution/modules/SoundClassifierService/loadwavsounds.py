
import os
import librosa
import wave
from scipy.io.wavfile import read
import numpy as np
import random
import yaml

def take_fft(wav_rawdata, sample_rate, fft, mels):
    fdata = np.array([float(d) for d in wav_rawdata])
    melspec = librosa.feature.melspectrogram(
        y = fdata, sr = sample_rate,
        n_fft = fft, n_mels = mels
    )
    return melspec, fdata

def load_wavdata(wav_file_path, fft=2048, mels=128):
#    print(wav_file_path)
    wv = wave.open(wav_file_path,'rb')
    wvinfo = wv.getparams()
    fs, data = read(wav_file_path)
    melspecs = []
    rawdata = []
    tdata = []
    if (wvinfo.nchannels == 1):
        tdata.append(data)
    else:
        tdata = data.T
    if wvinfo.nchannels == len(tdata):
        for data in tdata:
            fftdata = take_fft(data, fs, fft, mels)
            melspecs.append(fftdata[0])
            rawdata.append(fftdata[1])
    
    result = {}
    result['fft-data'] = librosa.power_to_db(melspecs, ref=np.max)
    result['raw-data'] = rawdata
    result['sampling-rate'] = fs
    result['fft-freq'] = fft
    result['fft-mels'] = mels
    return result

def load_csvdata(file):
    m = load_wavdata(file)
    return np.array(m[1]).T.astype(np.int16) / 32768

# data_folder = 'data'
# data_folder_path = os.path.join(os.getcwd(), data_folder)

def load_data_definition(data_def_file_path):
    definition = {}
    with open(data_def_file_path, "r") as ymlFile:
        yml = yaml.safe_load(ymlFile)
        definition.update(yml)
    return definition

def reshape_dataset(sound_data, data_chunk):
    dataset = np.zeros((len(sound_data), 1, 1, data_chunk))
    for index, d in enumerate(sound_data):
        dataset[index][0][0] = d

    return dataset

def get_minimum_times(tdata):
    shps = []
    for l in tdata.keys():
        for d in tdata[l]:
            shps.append(d.shape[1])
    return np.array(shps).min()


def divid_data_by_minimum_shape(unit, dlen):
    resultset = []
    shp = unit.shape
#    print('original shape - {}'.format(shp))
    if shp[1] == dlen:
        resultset.append(unit)
    else:
        pl = 0
        while pl + dlen <= shp[1]:
#            print('++pl={}'.format(pl))
            divided = unit[:,pl:pl+dlen]
            resultset.append(divided)
#            print('divided shape - {}'.format(divided.shape))
            pl = pl + dlen
        if (shp[1] % dlen) != 0:
            pl = shp[1]
            while pl - dlen >= 0:
#                print('--pl={}'.format(pl))
                divided = unit[:,pl-dlen:pl]
                resultset.append(divided)
#                print('divided shape - {}'.format(divided.shape))
                pl = pl - dlen
    
    return np.array(resultset)



def load_data(data_folder_path, fft=2048, mels=128, minimum=0):
    tbdata ={}
    rate = 0
    num_of_data = 0
    for df in os.listdir(path=data_folder_path):
        if os.path.isfile(os.path.join(data_folder_path, df)):
            continue
            
        tbdata[df] = []
        ldata_folder_path = os.path.join(data_folder_path,df)
        for datafile in os.listdir(path=ldata_folder_path):
            datafile_path = os.path.join(ldata_folder_path, datafile)
            fftwav = load_wavdata(datafile_path, fft=fft, mels=mels)
            tbdata[df].extend(fftwav['fft-data'])
            fft = fftwav['fft-freq']
            mels = fftwav['fft-mels']
            rate = fftwav['sampling-rate']
    
    mintsize = get_minimum_times(tbdata)
    if mintsize < minimum:
        print('minimum time range of dataset is {} but select minimum arg value:{} '.format(mintsize, minimum))
        mintsize = minimum
    else:
        print('minimum time range of dataset is {}'.format(mintsize))
    tdata ={}
    num_of_data = 0
    for l in tbdata.keys():
        tdata[l] = []
#        print('label:{}'.format(l))
#        index = 0
        for u in tbdata[l]:
#            print('index:{}'.format(index))
#            index = index +1
            if u.shape[1] < mintsize:
                print('this data is too short - {}'.format(u.shape))
                continue
            divided = divid_data_by_minimum_shape(u, mintsize)
            tdata[l].extend(divided)
            num_of_data = num_of_data + len(divided)

    data_of_sounds = np.zeros((num_of_data,1, mels, mintsize),dtype=np.float)
    label_of_sounds = np.zeros(num_of_data,dtype=int)
    label_matrix_of_sounds = np.zeros((num_of_data, len(tdata.keys())))
    labelname_of_sounds = np.empty(num_of_data,dtype=object)
    index = 0
    lindex = 0
    labeling_for_train = {}
    for l in tdata.keys():
        for fftdata in tdata[l]:
            data_of_sounds[index][0] = fftdata
            label_of_sounds[index] = lindex
            label_matrix_of_sounds[index, lindex] = 1.
            labelname_of_sounds[index] = l
            index = index + 1
        labeling_for_train[l] = lindex
        lindex = lindex + 1

    print('num_of_data={},size of data_of_sounds={}'.format(num_of_data,len(data_of_sounds)))
    indexx = np.arange(num_of_data)
    random.shuffle(indexx)

    data_of_sounds = data_of_sounds[indexx]
    label_matrix_of_sounds = label_matrix_of_sounds[indexx]
    label_of_sounds = label_of_sounds[indexx]
    labelname_of_sounds = labelname_of_sounds[indexx]

    # dataShape = data_of_sounds[0].shape
    # data_of_sounds = data_of_sounds.reshape(len(data_of_sounds), dataShape[1], dataShape[2], dataShape[0])

    # train_dataset is labeled sound data set
    train_dataset = [data_of_sounds, label_of_sounds, labelname_of_sounds, rate, fft, mels]
    
    return train_dataset
