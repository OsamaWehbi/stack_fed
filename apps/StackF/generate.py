import xlsxwriter
import random
import json
from ofunctions import shanon


def generate_data():
    wr = xlsxwriter.Workbook("DATA.xlsx")
    ws = wr.add_worksheet('Clients')
    # leader section
    num_leader = 13
    for i in range(num_leader):
        cpu = random.randint(80, 100)
        ram = random.randint(80, 100)
        band = random.randint(80, 100)

        # generate a random integer between 1 and 5 for the list size
        list_size = random.randint(1, 2)

        # generate a random list of integers between 0 and 9 with the generated size
        random_list = random.sample(range(10), list_size)
        data_dct = {num: random.randint(100, 200) for num in random_list}
        # print(random_list)
        ws.write('A' + str(i + 1), "IOT" + str(i + 1))
        ws.write('B' + str(i + 1), cpu)
        ws.write('C' + str(i + 1), ram)
        ws.write('D' + str(i + 1), band)
        ws.write('E' + str(i + 1), json.dumps(data_dct))
        # computed in the read function based on the normalized data
        # ws.write('F' + str(i + 1), shanon(list(data_dct.values())))

    # follower section
    num_total_clients = 100
    for i in range(num_leader, num_total_clients):
        cpu = random.randint(10, 40)
        ram = random.randint(10, 40)
        band = random.randint(10, 40)

        # generate a random integer between 1 and 5 for the list size
        list_size = random.randint(1, 2)

        # generate a random unique list of integers between 0 and 9 with the generated size
        random_list = random.sample(range(10), list_size)
        # data size per class
        data_dct = {num: random.randint(100, 200) for num in random_list}
        # print(random_list)
        ws.write('A' + str(i + 1), "IOT" + str(i + 1))
        ws.write('B' + str(i + 1), cpu)
        ws.write('C' + str(i + 1), ram)
        ws.write('D' + str(i + 1), band)
        ws.write('E' + str(i + 1), json.dumps(data_dct))
        # computed in the read function based on the normalized data
        # ws.write('F' + str(i + 1), shanon(list(data_dct.values())))

    wr.close()


generate_data()
