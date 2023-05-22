import logging
import sys
from collections import defaultdict

from torch import nn

import libs.model.cv.cnn
from apps.StackF.apis import dumb_db
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
# client_slice = list(dis_data.keys())
# client_slice = client_slice[0:51]
# sliced_dict = Dict({key: dis_data[key] for key in client_slice})

# trainers configuration
trainer_params = TrainerParams(trainer_class=trainers.TorchTrainer, batch_size=50, epochs=3, optimizer='sgd',
                               criterion='cel', lr=0.01)

federated = FederatedLearning(
    trainer_manager=SeqTrainerManager(),
    trainer_config=trainer_params,
    aggregator=aggregators.AVGAggregator(),
    metrics=metrics.AccLoss(batch_size=50, criterion=nn.CrossEntropyLoss()),
    client_selector=client_selectors.Random(0.6),
    trainers_data_dict=dis_data,
    test_data=test.as_tensor(),
    initial_model=lambda: initialize_model,
    num_rounds=5,
    # accepted_accuracy_margin=0.05,
    desired_accuracy=0.99
)
tab_id = "vancifar"
federated.add_subscriber(FederatedLogger([Events.ET_TRAINER_SELECTED, Events.ET_ROUND_FINISHED]))
federated.add_subscriber(Timer([Timer.FEDERATED, Timer.ROUND]))
federated.add_subscriber(EMDWeightDivergence(show_plot=0))
federated.add_subscriber(SQLiteLogger(id=tab_id, db_path='vancifa.db', config='cifar10'))
# federated.add_subscriber(Resumable(IODict('./vancifarcache.cs')))
logger.info("----------------------")
logger.info("start federated our cifar")
logger.info("----------------------")
federated.start()

dumb_db(tab_id=tab_id, file_path='vancifa.db')
