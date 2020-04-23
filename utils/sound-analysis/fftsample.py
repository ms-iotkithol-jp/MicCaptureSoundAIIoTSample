# reference - https://qiita.com/slowsingle/items/36b6381124249d067026 
import librosa, librosa.display
from scipy.io.wavfile import read
import matplotlib.pyplot as plt
import numpy as np

def melspectrogram(wav_file_path, fft=2048, mels=128):
    fs, data = read(wav_file_path)
    fdata = np.array([float(d) for d in data])
    melspecs = librosa.feature.melspectrogram(
        y = fdata, sr = fs,
        n_fft = fft, n_mels = mels
    )
    return melspecs, fdata, fs

def showspectrogram(melspecs, fs):
    librosa.display.specshow(librosa.power_to_db(melspecs, ref=np.max),x_axis='time', y_axis='mel', fmax=fs)
    plt.colorbar(format='%+2.0f dB')
    plt.show()

