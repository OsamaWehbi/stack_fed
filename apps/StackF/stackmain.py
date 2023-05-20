import logging
import sys
from collections import defaultdict

from apps.StackF.apis import dumb_db
from apps.StackF.distributor import Stackdis
from apps.StackF.ofunctions import readexcel, dbscan, compute_com, gen_pay, compute_utility_follower, \
    compute_utility_leader, compute_p_opt, gen_pay_leader, get_combinations, com_final, sorting_for_selec, sel_fun, \
    sel_fun_opt
from src.federated.subscribers import fed_plots
from src.federated.subscribers.sqlite_logger import SQLiteLogger

sys.path.append('../../')
from src.apis.extensions import Dict
from libs.model.linear.lr import LogisticRegression
from src.federated.events import Events
from src.federated.subscribers.logger import FederatedLogger, TqdmLogger
from src.federated.subscribers.timer import Timer
from src.data.data_loader import preload
from src.federated.components import metrics, client_selectors, aggregators, trainers, client_scanners
from src.federated.federated import FederatedLearning
from src.federated.protocols import TrainerParams
from src.federated.components.trainer_manager import SeqTrainerManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('main')

# read clients (list of clients object)
# clients = readexcel('C:/Users/Osama.Wehbi/Desktop/StackFed/apps/StackF/datad.xlsx')
clients = readexcel()
dis_data = preload('mnist', Stackdis(clients))

# min_max(clients)
total_nor = 0
total = 0
for i in clients:
    total_nor += sum(list(i.c_dn_data_nor.values()))
    # total += sum(list(i.dn_data.values()))
for client in clients:
    client.load(dis_data)
    client.compute_ds(total_nor)

leaders, followers = dbscan(clients)
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
# start the training
combinations = get_combinations(leaders, followers)
com_value = com_final(combinations)
combinations, com_value = sorting_for_selec(combinations, com_value)
# print(com_value)
# print(combinations)

selected = sel_fun(combinations)

for c in selected:
    logger.info(c.print_log())

clients_data = defaultdict(list)
# collect the data here
for client in selected:
    clients_data[client.c_id] = client.c_data_container
clients_data = Dict(clients_data)
test = preload('mnist10k')

trainer_params = TrainerParams(
    trainer_class=trainers.TorchTrainer,
    batch_size=50, epochs=10, optimizer='sgd',
    criterion='cel', lr=0.1)

# fl parameters
federated = FederatedLearning(
    trainer_manager=SeqTrainerManager(),
    trainer_config=trainer_params,
    aggregator=aggregators.AVGAggregator(),
    metrics=metrics.AccLoss(batch_size=50, criterion='cel'),
    client_scanner=client_scanners.DefaultScanner(clients_data),
    client_selector=client_selectors.All(),
    trainers_data_dict=clients_data,
    test_data=test.as_tensor(),
    initial_model=lambda: LogisticRegression(28 * 28, 10),
    num_rounds=20,
    desired_accuracy=0.99
)

# (subscribers)
tab_id = 'mnist'
federated.add_subscriber(TqdmLogger())
federated.add_subscriber(FederatedLogger([Events.ET_TRAINER_SELECTED, Events.ET_ROUND_FINISHED]))
federated.add_subscriber(Timer([Timer.FEDERATED, Timer.ROUND]))
federated.add_subscriber(SQLiteLogger(id=tab_id, db_path='perf.db'))
federated.add_subscriber(fed_plots.RoundAccuracy(plot_ratio=0))

logger.info("------------------------")
logger.info("start federated learning")
logger.info("------------------------")
federated.start()

dumb_db(tab_id=tab_id)
# prepare the data of the testing also
# create the federated learning
# make sure to include the needed subscribers
# use the random approach on the entire set