import sys, os
import torch
import torch.nn as nn
from torch_geometric.data import DataLoader

from gnn import GNNNet_2GCN_Layers, GNNNet_2GAT_Layers, GNNNet_3GCN_Layers, GNNNet_3GAT_Layers, GNNNet_1GCN_and_1GAT_Layer
from utils import *
from emetrics import *
from data_process import create_dataset_for_training


datasets = [['davis', 'kiba'][int(sys.argv[1])]]

cuda_name = ['cuda:0', 'cuda:1', 'cuda:2', 'cuda:3'][int(sys.argv[2])]
print('cuda_name:', cuda_name)
cross_validation_flag = True

TRAIN_BATCH_SIZE = 128
TEST_BATCH_SIZE = 128
LR = 0.001
NUM_EPOCHS = int(sys.argv[3])

print('Learning rate: ', LR)
print('Epochs: ', NUM_EPOCHS)

models_dir = 'models'
results_dir = 'results'

if not os.path.exists(models_dir):
    os.makedirs(models_dir)

if not os.path.exists(results_dir):
    os.makedirs(results_dir)

# Main program: iterate over different datasets
result_str = ''
USE_CUDA = torch.cuda.is_available()
device = torch.device(cuda_name if USE_CUDA else 'cpu')
model = [GNNNet_2GCN_Layers(), GNNNet_2GAT_Layers(), GNNNet_3GCN_Layers(), GNNNet_3GAT_Layers(), GNNNet_1GCN_and_1GAT_Layer()][int(sys.argv[4])]
model.to(device)
model_st = [GNNNet_2GCN_Layers.__name__, GNNNet_2GAT_Layers.__name__, GNNNet_3GCN_Layers.__name__, GNNNet_3GAT_Layers.__name__, GNNNet_1GCN_and_1GAT_Layer.__name__][int(sys.argv[4])]
print("model: ", model_st)
embedding = ['esm1b','esm2','protT5'][int(sys.argv[5])]
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(device)
loss_fn = nn.MSELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=LR)
for dataset in datasets:
    train_data, valid_data = create_dataset_for_training(dataset,embedding)
    train_loader = torch.utils.data.DataLoader(train_data, batch_size=TRAIN_BATCH_SIZE, shuffle=True,
                                               collate_fn=collate)
    valid_loader = torch.utils.data.DataLoader(valid_data, batch_size=TEST_BATCH_SIZE, shuffle=False,
                                               collate_fn=collate)

    best_mse = 1000
    best_test_mse = 1000
    best_epoch = -1
    model_file_name = 'models/model_' + model_st + '_' + dataset + '_' + embedding + '_' + str(NUM_EPOCHS) + '.model'
    print(model_file_name)
    for epoch in range(NUM_EPOCHS):
        train(model, device, train_loader, optimizer, epoch + 1)
        print('predicting for valid data')
        G, P = predicting(model, device, valid_loader)
        val = get_mse(G, P)
        print('valid result:', val, best_mse)
        if val < best_mse:
            best_mse = val
            best_epoch = epoch + 1
            torch.save(model.state_dict(), model_file_name)
            print('rmse improved at epoch ', best_epoch, '; best_test_mse', best_mse, model_st, dataset, fold)
        else:
            print('No improvement since epoch ', best_epoch, '; best_test_mse', best_mse, model_st, dataset, fold)
