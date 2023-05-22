import random
from collections import defaultdict
import numpy as np
from src.apis.extensions import Dict
from src.data.data_container import DataContainer
from src.data.data_distributor import Distributor


class Stackdis(Distributor):
    def __init__(self, dc_client):
        super().__init__()
        self.dc_client = dc_client
        # extract num of clients
        self.num_clients = len(dc_client)

    # this is the core distributor take as input the data set
    def distribute(self, data: DataContainer) -> Dict[int, DataContainer]:
        # convert it to numpy
        data = data.as_numpy()
        self.log(f'distributing {data}', level=0)
        # prepare the dictionary that will hold the clients data as Dict
        clients_data = defaultdict(list)
        # group the labels to the images
        grouper = self.Grouper(data.x, data.y)
        # iterate over the clients and distribute the data
        for val in self.dc_client:

            label_per_client = val.dn_data.keys()
            # extract the labels of the client from the dictionary (excel sheet)
            selected_labels = list(map(int, val.dn_data.keys()))
            # selected_labels = val.dn_data.keys()
            self.log(f'generating data for {val.c_id}-{selected_labels}')
            # prepare the list the will hod each client label and images
            client_x = []
            client_y = []
            # iterate over the labels of each client
            for shard in selected_labels:
                # select the data per label based on the value in the dictionary (Excel sheet)
                # selected_data_size = int(val.dn_data[str(shard)] / len(selected_labels)) or 1
                selected_data_size = int(val.dn_data[str(shard)])
                rx, ry = grouper.get(shard, selected_data_size)
                # if the data set is not enough throw exception
                if len(rx) == 0:
                    self.log(f'shard {round(shard)} have no more available data to distribute, skipping...',
                             level=0)
                else:
                    client_x = rx if len(client_x) == 0 else np.concatenate((client_x, rx))
                    client_y = ry if len(client_y) == 0 else np.concatenate((client_y, ry))
                # save the client data to the dictionary  and move the next client
                clients_data[val.c_id] = DataContainer(client_x, client_y).as_tensor()
        return Dict(clients_data)

    class Grouper:
        def __init__(self, x, y):
            self.grouped = defaultdict(list)
            self.selected = defaultdict(lambda: 0)
            self.label_cursor = 0
            for label, data in zip(y, x):
                self.grouped[label].append(data)
            self.all_labels = list(self.grouped.keys())

        def groups(self, count=None):
            if count is None:
                return self.all_labels
            selected_labels = []
            for i in range(count):
                selected_labels.append(self.next())
            return selected_labels

        def next(self):
            if len(self.all_labels) == 0:
                raise Exception('no more data available to distribute')

            temp = 0 if self.label_cursor >= len(self.all_labels) else self.label_cursor
            self.label_cursor = (self.label_cursor + 1) % len(self.all_labels)
            return self.all_labels[temp]

        def clean(self):
            for label, records in self.grouped.items():
                if label in self.selected and self.selected[label] >= len(records):
                    print('cleaning the good way')
                    del self.all_labels[self.all_labels.index(label)]

        def get(self, label, size=0):
            if size == 0:
                size = len(self.grouped[label])
            #  added
            if self.selected[label] + size > len(self.grouped[label]):
                self.selected[label] = 0
            x = self.grouped[label][self.selected[label]:self.selected[label] + size]
            y = [label] * len(x)
            self.selected[label] += size
            if len(x) == 0:
                print("No Data ......!!!!!!!!!!!!!!!")
                self.selected[label] = 0
                # del self.all_labels[self.all_labels.index(label)]
            return x, y

    # this method return the name of the file to be saved to get the same results each run
    def id(self):
        return f'label_{self.num_clients}' + 'c_Excel' + 'fed_stack'
