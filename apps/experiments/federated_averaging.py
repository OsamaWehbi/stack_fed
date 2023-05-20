import logging
import sys

import torch.cuda

from src.federated.subscribers import fed_plots

sys.path.append('../../')

from src.apis.extensions import Dict
from libs.model.linear.lr import LogisticRegression
from src.federated.events import Events

from src.federated.subscribers.logger import FederatedLogger, TqdmLogger
from src.federated.subscribers.timer import Timer
from src.data.data_distributor import ShardDistributor, LabelDistributor
from src.data.data_loader import preload
from src.federated.components import metrics, client_selectors, aggregators, trainers, client_scanners
from src.federated.federated import FederatedLearning
from src.federated.protocols import TrainerParams
from src.federated.components.trainer_manager import SeqTrainerManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('main')
# clients 20
# rounds 20
# epoc 10
# 100 5
# 20 3
# 50 4

# 5 100 200
# 4 50 130
# 3 50 100
# 2 1 50

# client_data = preload('mnist', ShardDistributor(100, 5)).select(range(20))

client_data = preload('mnist', LabelDistributor(20,2,1,50))

test = preload('mnist10k')

# client_data = preload('mnist', label(300, 2)).select(range(20))
# trainers configuration
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
    client_scanner=client_scanners.DefaultScanner(client_data),
    client_selector=client_selectors.All(),
    trainers_data_dict=client_data,
    test_data=test.as_tensor(),
    initial_model=lambda: LogisticRegression(28 * 28, 10),
    num_rounds=20,
    desired_accuracy=0.99
)

# (subscribers)
federated.add_subscriber(TqdmLogger())
federated.add_subscriber(FederatedLogger([Events.ET_TRAINER_SELECTED, Events.ET_ROUND_FINISHED]))
federated.add_subscriber(Timer([Timer.FEDERATED, Timer.ROUND]))
federated.add_subscriber(fed_plots.RoundAccuracy(plot_ratio=0))

logger.info("------------------------")
logger.info("start federated learning")
logger.info("------------------------")
federated.start()
