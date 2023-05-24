import logging
import sys
from collections import defaultdict

from torch import nn

import libs.model.cv.cnn
from apps.StackF.apis import dumb_db, final_val, write_ds
from apps.StackF.distributor import Stackdis
from apps.StackF.ofunctions import readexcel, dbscan, compute_com, gen_pay, compute_utility_follower, \
    compute_utility_leader, compute_p_opt, gen_pay_leader, get_combinations, com_final, sorting_for_selec, sel_fun, \
    sel_fun_opt
from libs.model.cv.resnet import resnet56
from src.apis import lambdas
from src.apis.rw import IODict
from src.federated.subscribers.fed_plots import EMDWeightDivergence
from src.federated.subscribers.resumable import Resumable
from src.federated.subscribers.sqlite_logger import SQLiteLogger

sys.path.append('../../')
from src.apis.extensions import Dict
from src.federated.events import Events
from src.federated.subscribers.logger import FederatedLogger, TqdmLogger
from src.federated.subscribers.timer import Timer
from src.data.data_loader import preload
from src.federated.components import metrics, client_selectors, aggregators, trainers, client_scanners
from src.federated.federated import FederatedLearning
from src.federated.protocols import TrainerParams
from src.federated.components.trainer_manager import SeqTrainerManager
from src.apis.extensions import Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('main')

# read clients (list of clients object)
# clients = readexcel('C:/Users/Osama.Wehbi/Desktop/StackFed/apps/StackF/datad.xlsx')
clients = readexcel()
test = Dict()
train, test['TEST'] = preload('cifar10').split(0.8)
dis_data = Stackdis(clients).distribute(train)
# test = Dict(test)


def create_model(name):
    if name == 'resnet':
        return resnet56(10, 3, 32)
    else:
        global dis_data
        global test
        # cifar10 data reduced to 1 dimension from 32,32,3. cnn32 model requires the image shape to be 3,32,32
        dis_data = dis_data.map(lambdas.reshape((-1, 32, 32, 3))).map(lambdas.transpose((0, 3, 1, 2)))
        test = test.map(lambdas.reshape((-1, 32, 32, 3))).map(lambdas.transpose((0, 3, 1, 2)))
        return libs.model.cv.cnn.Cifar10Model()


initialize_model = create_model('cnn')
test = test['TEST']
# min_max(clients)
total_nor = 0
total = 0
for i in clients:
    total_nor += sum(list(i.c_dn_data_nor.values()))
    # total += sum(list(i.dn_data.values()))
for client in clients:
    client.load(dis_data)
    client.compute_ds(total_nor)
write_ds(clients)
leaders, followers = dbscan(clients)

logger.info("Dbscan results")
print("leaders", len(leaders))
for leader in leaders:
    logger.info(leader.print_log())
print("followers", len(followers))
for follower in followers:
    logger.info(follower.print_log())
logger.info("end Dbscan result")

compute_com(leaders, followers)
gen_pay(followers, leaders)
gen_pay_leader(followers, leaders)
compute_utility_follower(followers, leaders)
compute_utility_leader(followers, leaders)
compute_p_opt(followers, leaders)

# should call here the game theory

# prepare the federated learning training envi
for leader in leaders:
    leader.c_q = 2
    # leader.gen_q()

combinations = get_combinations(leaders, followers)

com_value = com_final(combinations)
combinations, com_value = sorting_for_selec(combinations, com_value)
# print(com_value)
# print(combinations)

selected = sel_fun(combinations, leaders)
final_val(selected)
for c in selected:
    logger.info(c.print_log())

clients_data = defaultdict(list)
# collect the data here
for client in selected:
    clients_data[client.c_id] = client.c_data_container
clients_data = Dict(clients_data)

trainer_params = TrainerParams(trainer_class=trainers.TorchTrainer, batch_size=50, epochs=3, optimizer='sgd',
                               criterion='cel', lr=0.01)

federated = FederatedLearning(
    trainer_manager=SeqTrainerManager(),
    trainer_config=trainer_params,
    aggregator=aggregators.AVGAggregator(),
    metrics=metrics.AccLoss(batch_size=50, criterion=nn.CrossEntropyLoss()),
    client_selector=client_selectors.All(),
    trainers_data_dict=clients_data,
    test_data=test.as_tensor(),
    initial_model=lambda: initialize_model,
    num_rounds=15,
    # accepted_accuracy_margin=0.05,
    desired_accuracy=0.99
)
tab_id = "mycifar"
federated.add_subscriber(FederatedLogger([Events.ET_TRAINER_SELECTED, Events.ET_ROUND_FINISHED]))
federated.add_subscriber(Timer([Timer.FEDERATED, Timer.ROUND]))
federated.add_subscriber(EMDWeightDivergence(show_plot=0))
federated.add_subscriber(SQLiteLogger(id=tab_id, db_path='perfcifa.db', config='cifar10'))
# federated.add_subscriber(Resumable(IODict('./mycifarcache.cs')))
logger.info("----------------------")
logger.info("start federated our cifar")
logger.info("----------------------")
federated.start()

dumb_db(tab_id=tab_id, file_path='perfcifa.db')
