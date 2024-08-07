from parse_args import args

import json
import numpy as np
from sklearn.cluster import KMeans
from sklearn.model_selection import KFold
from sklearn import linear_model
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error, mean_absolute_percentage_error
from sklearn.metrics import normalized_mutual_info_score
from sklearn.metrics import adjusted_rand_score

crime_counts = np.load(args.data_path + args.crime_counts, allow_pickle=True)
check_counts = np.load(args.data_path + args.check_counts, allow_pickle=True)

with open(args.data_path + args.mh_cd, 'r') as f:
    mh_cd = json.load(f)
mh_cd_labels = np.zeros(69)
for i in range(69):
    mh_cd_labels[i] = mh_cd[str(i)]


def regression(X_train, y_train, X_test, alpha):
    reg = linear_model.Ridge(alpha=alpha)

    reg.fit(X_train, y_train)

    y_pred = reg.predict(X_test)
    return y_pred


def kf_predict(X, Y):
    kf = KFold(n_splits=5)
    y_preds = []
    y_truths = []
    for train_index, test_index in kf.split(X):
        X_train, X_test = X[train_index], X[test_index]
        y_train, y_test = Y[train_index], Y[test_index]
        y_pred = regression(X_train, y_train, X_test, 1)
        y_preds.append(y_pred)
        y_truths.append(y_test)

    return np.concatenate(y_preds), np.concatenate(y_truths)


def compute_metrics(y_pred, y_test):
    y_pred[y_pred < 0] = 0
    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    return mae, np.sqrt(mse), r2


def predict_crime(emb):
    y_pred, y_test = kf_predict(emb, crime_counts)
    mae, rmse, r2 = compute_metrics(y_pred, y_test)
    return mae, rmse, r2


def predict_check(emb):
    y_pred, y_test = kf_predict(emb, check_counts)
    mae, rmse, r2 = compute_metrics(y_pred, y_test)
    return mae, rmse, r2


def classify(emb, rand):
    n = 12
    kmeans = KMeans(n_clusters=n, random_state=rand)
    emb_labels = kmeans.fit_predict(emb)
    nmi = normalized_mutual_info_score(mh_cd_labels, emb_labels)
    ari = adjusted_rand_score(mh_cd_labels, emb_labels)
    return nmi, ari


def clustering(emb):
    nmi, ari = classify(emb, 3)  # 9
    return nmi, ari


if __name__ == '__main__':
    emb = np.load('emb.npy', allow_pickle=True)
    nmi, ari = clustering(emb)
    print(nmi, ari)
    mae, rmse, r2 = predict_crime(emb)
    print("MAE:  %.3f" % mae)
    print("RMSE: %.3f" % rmse)
    print("R2:   %.3f" % r2)
    print('>>>>>>>>>>>>>>>>>   check')
    mae, rmse, r2 = predict_check(emb)
    print("MAE:  %.3f" % mae)
    print("RMSE: %.3f" % rmse)
    print("R2:   %.3f" % r2)
    print('>>>>>>>>>>>>>>>>>   clustering')
