import csv
import numpy as np
import glob
import os.path
import pandas as pd
from keras.utils import np_utils

from keras.preprocessing.image import img_to_array, load_img

def GetArrayFromImage(image, target_shape):
    h, w, _ = target_shape
    image = load_img(image, target_size=(h, w))

    # Turn it into numpy, normalize and return.
    arr = img_to_array(image)
    x = (arr / 255.).astype(np.float32)

    return x

def GetData():
    with open('./workspace/FilesData.csv', 'r') as fin:
        reader = csv.reader(fin)
        data = list(reader)
    return data

class DataSetModel():

    def __init__(self, seq_length=40, data_type = 'Images', image_shape=(224, 224, 3)):
        # seq_length = the number of frames to consider
        self.seq_length = seq_length

        # Get the data.
        self.data = GetData()

        self.dataType = data_type
        self.sequence_path = './workspace/sequences/'

        # Get the classes.
        self.classes = self.GetClasses()
        self.data = self.CleanData()
        self.image_shape = image_shape

    def GetClasses(self):
        # Extract classes from data
        classes = []
        for item in self.data:
            if len(item) == 0 :
                continue
            if item[1] not in classes:
                classes.append(item[1])

        classes = sorted(classes)
        return classes

    def GetClassOneHot(self, class_str):
        """Given a class as a string, return its number in the classes
        list. This lets us encode and one-hot it for training."""
        # Encode it first.
        label_encoded = self.classes.index(class_str)
        # Now one-hot it.
        label_hot = np_utils.to_categorical(label_encoded, len(self.classes))
        label_hot = label_hot[0]  # just get a single row

        return label_hot

    def SplitDataToTrainAndTest(self):
        # Split the data into train and test groups.
        train = []
        test = []
        for item in self.data:
            if item[0] == 'Train' :
                train.append(item)
            else:
                test.append(item)
        return train, test

    def CleanData(self):
        data_clean = []
        for item in self.data:
            if len(item) == 0 :
                continue
            if int(item[3]) >= self.seq_length and item[1] in self.classes:
                data_clean.append(item)

        return data_clean

    def LoadSequencesToMemory(self, train_test):
        train, test = self.SplitDataToTrainAndTest()
        data = train if train_test == 'Train' else test
        
        print("Loading %d samples into memory for %sing." % (len(data), train_test))

        X, y = [], []
        for row in data:
            if self.dataType == 'Images' :
                frames = self.GetFramesFromSample(row)
                img_arr = self.BuildImageSequence(frames)

                sequence = []
                start = 0
                end = self.seq_length
                for _ in range(len(img_arr) // self.seq_length) :
                    X.append(img_arr[start : end])
                    start = end
                    end = end + self.seq_length
                    y.append(self.GetClassOneHot(row[1]))

            elif self.dataType == 'Features' :
                print(row)
                sequence = self.GetExtructedFeatures(self.dataType, row)
                sequence = self.RescaleList(sequence, 1)
                X.append(sequence)
                y.append(self.GetClassOneHot(row[1]))

        return np.array(X), np.array(y)

    def GetExtructedFeatures(self, data_type, sample):
        """Get the saved extracted features."""
        filename = sample[2]
        path = self.sequence_path + filename + '-' + str(self.seq_length) + \
            '-' + data_type + '.txt'
        if os.path.isfile(path):
            # Use a dataframe/read_csv for speed increase over numpy.
            features = pd.read_csv(path, sep=" ", header=None)
            return features.values
        else:
            return None

    def BuildImageSequence(self, frames):
        return [GetArrayFromImage(x, self.image_shape) for x in frames]

    @staticmethod
    def GetFramesFromSample(sample):
        """Given a sample row from the data file, get all the corresponding frame
        filenames."""
        path = './' + sample[0] + '/' + sample[1] + '/'
        filename = sample[2]
        images = sorted(glob.glob(path + filename + '*jpg'))
        return images

    @staticmethod
    def RescaleList(input_list, size):
        """Given a list and a size, return a rescaled/samples list. For example,
        if we want a list of size 5 and we have a list of size 25, return a new
        list of size five which is every 5th element of the origina list."""
        assert len(input_list) >= size
        # Get the number to skip between iterations.
        skip = len(input_list) // size

        # Build our new output.
        output = [input_list[i] for i in range(0, len(input_list), skip)]

        # Cut off the last one if needed.
        return output[:size]
