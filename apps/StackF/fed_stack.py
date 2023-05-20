import logging
import random
import statistics
import sys
from collections import defaultdict
import openpyxl
from src.data.data_container import DataContainer


class Client:
    def __init__(self, c_id, cpu, ram, bandwidth, dn_data, c_dd):
        self.c_id = c_id
        self.cpu = cpu
        self.ram = ram
        self.bandwidth = bandwidth
        # data dictionary as per excel sheet
        self.dn_data = dn_data
        # shanon index
        self.c_dd = c_dd
        # data set of the client ,minst/cifar.....
        self.c_data_container = None
        # individual data score
        self.c_ds = None
        # data score after being combined as data dictionary where keys represent the follower and values are the ds exits only on the leader side
        self.com_dic = {}
        # normalized total data size per client calculated based on min_max function
        # self.c_n_data_val = None
        # normalized version of the data dictionary using normalize_dicts function
        self.c_dn_data_nor = {}
        # the payment made by follower to leader
        self.f_l_pay = {}
        # follower utility computed in ofunctions
        self.u_f = {}
        # leader utility
        self.u_l = None
        # delta leader to follower
        self.l_f_pay_dic = {}
        # quota number
        self.c_q = None
        # selected or not
        self.c_s = 0
        # for followers only calculated in the game file
        self.eq18_dic = {}

    def load(self, distributedata):
        self.c_data_container = distributedata[self.c_id]

    def compute_ds(self, total):
        # print(total, (len(list(self.c_dn_data_nor.keys()))/10), sum(list(self.c_dn_data_nor.values())), total, sum(list(self.c_dn_data_nor.values())) / total, self.c_dd)
        self.c_ds = 0.33 * (len(list(self.c_dn_data_nor.keys())) / 10) * 0.33 * sum(
            list(self.c_dn_data_nor.values())) * 0.33 * self.c_dd

    def gen_d(self):
        self.c_q = random.randint(2, 4)

    def print_info(self):
        print("Name:", self.c_id, "resources:", self.cpu, self.ram, self.bandwidth)

    def print_log(self):
        if self.ram > 50:
            return f'Name: {self.c_id}, resources: {self.cpu}, {self.ram}, {self.bandwidth}, occupation: Leader'
        return f'Name: {self.c_id}, resources: {self.cpu}, {self.ram}, {self.bandwidth}, occupation: Follower'

