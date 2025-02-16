import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn import preprocessing, metrics
from sklearn.model_selection import train_test_split
import xgboost as xgb
import shap
import os


pd.set_option("display.max_rows", 50)

UNWANTED_COLUMNS = [
    "hpwl",
    "overflow",
    "route_utilization",
    "convergent",
    "ID",
]

# xgb_params = {
#     "eta": 0.3,
#     "gamma": 0,
#     "max_depth": 6,
#     "min_child_weight": 1,
#     "subsample": 1,
#     "colsample_bytree": 1,
#     "lambda": 1,
#     "alpha": 0,
# }

# xgb_params_space = {
#     "eta": [0.01, 0.015, 0.025, 0.05, 0.1],
#     "gamma": [0.1, 0.3, 0.5, 0.7, 0.9, 1.0],
#     "max_depth": [3, 5, 7, 9],
#     "n_estimators": [100, 200, 500, 1000],
#     "learning_rate": [0.1, 0.01, 0.05],
#     "subsample": [0.5, 0.6, 0.7, 0.8],
#     "min_child_weight": [1, 3, 5, 7],
#     "colsample_bytree": [0.5, 0.6, 0.7, 0.8],
# }


def build_dataframe(result):
    id2conf = result.get_id2config_mapping()
    all_runs = result.get_all_runs(only_largest_budget=False)
    print(" all_runs: ", all_runs)
    all_ids, all_configs, all_infos = [], [], []
    for r in all_runs:
        all_ids.append(str(r.config_id))
        config = id2conf[r.config_id]["config"]
        all_configs.append(config)
        all_infos.append(r.info)
    print(" all_ids: ", all_ids)
    print(" all_configs: ", all_configs)
    print(" all_infos: ", all_infos)
    df = pd.concat(
        [pd.DataFrame(all_ids), pd.DataFrame(all_configs), pd.DataFrame(all_infos)],
        axis=1,
    )
    df.rename(columns={0: "ID"}, inplace=True)
    return df


def extract_paretos(df, axes):
    undominated = (df[axes].values[:, None] >= df[axes].values).all(axis=2).sum(axis=1) == 1
    return df[undominated]


def get_candidates(result, num: int = 5, ranking: str = "route_utilization"):
    axes = ["hpwl", "overflow", "route_utilization"]
    assert ranking in axes
    df = build_dataframe(result)
    # df = df[~df.isin([np.nan, np.inf, -np.inf]).any(1)]
    paretos = extract_paretos(df, axes)
    print(f"# Pareto-optimal points = {len(paretos)}")
    print(paretos[axes].to_markdown())
    # if single-objective
    if "cost" in df:
        candidates = paretos.nsmallest(num, "cost")
    else:
        # multi-objective
        kmeans = KMeans(n_clusters=num)
        scaled_points = preprocessing.StandardScaler().fit_transform(paretos[axes])
        paretos["group"] = kmeans.fit_predict(scaled_points)
        rank = paretos.groupby("group")[ranking]
        candidates = paretos[
            paretos[ranking] == paretos.assign(min=rank.transform(min))["min"]
        ]
    print("Pareto candidates:")
    print(candidates[axes].to_markdown())
    return candidates, paretos, df


def plot_pareto(df, paretos, candidates, filename):
    axes = ["hpwl", "overflow", "route_utilization"]
    dx, dy, dz = df[axes].values.T
    px, py, pz = paretos[axes].values.T
    cx, cy, cz = candidates[axes].values.T
    fig = plt.figure(figsize=(16, 16))
    ax = plt.axes(projection="3d")
    ax.set_xlim3d(0.9 * dx.min(), 1.1 * dx.max())
    ax.set_ylim3d(0.9 * dy.min(), 1.1 * dy.max())
    ax.set_zlim3d(0.9 * dz.min(), 1.1 * dz.max())
    ax.grid(b=True, color="black", linestyle="-.", linewidth=0.3, alpha=0.2)
    ax.scatter3D(dx, dy, dz, alpha=0.2, marker="o", color="orange", s=10, label="samples")
    ax.scatter3D(px, py, pz, alpha=0.5, marker="o", color="green", s=20,label="paretos",)
    ax.scatter3D(cx, cy, cz, alpha=1.0, marker="o", color="red", s=50, label="candidates",)
    ax.set_xlabel(axes[0], fontsize=15)
    ax.set_ylabel(axes[1], fontsize=15)
    ax.set_zlabel(axes[2], fontsize=15)
    ax.set_title("Pareto AutoDMPPCB", fontsize=15)
    ax.view_init(20, 70)
    ax.legend()
    path = "./plot/"
    os.makedirs(path, exist_ok=True)
    plt.savefig(os.path.join(path,filename), dpi=400)


def preprocess_df(df):
    # preprocess the dataframe
    # df[~df.isin([np.nan, np.inf, -np.inf]).any(1)]
    df["convergent"] = (df["hpwl"] != np.inf).astype(int)
    # encode categorical data
    if "GP_optimizer" in df.columns:
        le_opt = preprocessing.LabelEncoder().fit(df["GP_optimizer"])
        df["GP_optimizer"] = le_opt.transform(df["GP_optimizer"])
        print(le_opt.classes_)
    if "GP_wirelength" in df.columns:
        le_wl = preprocessing.LabelEncoder().fit(df["GP_wirelength"])
        df["GP_wirelength"] = le_wl.transform(df["GP_wirelength"])
        print(le_wl.classes_)
    if "GP_num_bins_x" in df.columns:
        le_binx = preprocessing.LabelEncoder().fit(df["GP_num_bins_x"])
        df["GP_num_bins_x"] = le_binx.transform(df["GP_num_bins_x"])
        print(le_binx.classes_)
    if "GP_num_bins_y" in df.columns:
        le_biny = preprocessing.LabelEncoder().fit(df["GP_num_bins_y"])
        df["GP_num_bins_y"] = le_biny.transform(df["GP_num_bins_y"])
        print(le_biny.classes_)


def analyze(result, classif, target):
    _, _, df = get_candidates(result)
    preprocess_df(df)
    # axes = ["rsmt", "congestion", "density"]
    # band = 1.1
    # df = df[(df[axes] <= df[axes].min() * band).all(axis=1)]
    # target_scaler = preprocessing.MinMaxScaler()
    # df[target] = target_scaler.fit_transform(df[target])
    features = list(set(df.columns) - set(UNWANTED_COLUMNS))
    stratify = df[target] if classif else None
    train, test = train_test_split(df, test_size=0.1, shuffle=True, stratify=stratify)
    Xtrain, ytrain = train[features], train[target]
    Xtest, ytest = test[features], test[target]
    dtrain = xgb.DMatrix(Xtrain, label=ytrain)
    dtest = xgb.DMatrix(Xtest, label=ytest)

    params = {"max_depth": 8, "eta": 0.1, "nthread": 4, "tree_method": "hist"}
    num_rounds = 2000
    early_stopping_rounds = 20

    if classif:
        metric = {"ams@0.15", "auc", "logloss", "error"}
        params["objective"] = "binary:logistic"

        def fpreproc(dtrain, dtest, param):
            label = dtrain.get_label()
            ratio = float(np.sum(label == 0)) / np.sum(label == 1)
            param["scale_pos_weight"] = ratio
            return (dtrain, dtest, param)

        xgb.cv(
            params,
            dtrain,
            num_rounds,
            stratified=True,
            nfold=3,
            metrics=metric,
            seed=0,
            fpreproc=fpreproc,
            early_stopping_rounds=early_stopping_rounds,
        )

        params = fpreproc(dtrain, dtest, params)[2]
        model = xgb.train(
            params,
            dtrain,
            num_rounds,
            evals=[(dtest, "test")],
            verbose_eval=100,
            early_stopping_rounds=early_stopping_rounds,
        )

        ypred = (model.predict(dtest) > 0.5).astype(int)
        print(metrics.classification_report(ytest, ypred))
        return model, df[features]
    else:
        # multi-output regression
        if ytrain.shape[1] > 1:
            params["num_target"] = ytrain.shape[1]

            def gradient(predt, dtrain):
                y = dtrain.get_label().reshape(predt.shape)
                return (predt - y).reshape(y.size)

            def hessian(predt, dtrain):
                return np.ones(predt.shape).reshape(predt.size)

            def squared_log(predt, dtrain):
                grad = gradient(predt, dtrain)
                hess = hessian(predt, dtrain)
                return grad, hess

            def rmse(predt, dtrain):
                y = dtrain.get_label().reshape(predt.shape)
                v = np.sqrt(np.sum(np.power(y - predt, 2)))
                return "MultiOutputRMSE", v

            xgb.cv(
                params,
                dtrain,
                num_rounds,
                obj=squared_log,
                custom_metric=rmse,
                nfold=3,
                early_stopping_rounds=early_stopping_rounds,
            )

            model = xgb.train(
                params,
                dtrain,
                num_rounds,
                obj=squared_log,
                custom_metric=rmse,
                evals=[(dtest, "test")],
                early_stopping_rounds=early_stopping_rounds,
            )
            # ypred = target_scaler.inverse_transform(model.inplace_predict(Xtest))
            # ytest = target_scaler.inverse_transform(ytest)
            ypred = model.inplace_predict(Xtest)
            print(
                metrics.mean_absolute_percentage_error(
                    ytest, ypred, multioutput="raw_values"
                )
            )
            return model, df[features]
            # (100 * (ytest - ypred) / ytest).describe()
        else:
            metric = {"rmse"}
            params["objective"] = "reg:squarederror"

            xgb.cv(
                params,
                dtrain,
                num_rounds,
                nfold=5,
                metrics=metric,
                seed=0,
                early_stopping_rounds=early_stopping_rounds,
            )

            model = xgb.train(
                params,
                dtrain,
                num_rounds,
                evals=[(dtest, "test")],
                verbose_eval=100,
                early_stopping_rounds=early_stopping_rounds,
            )

            ypred = model.inplace_predict(Xtest)
            print(metrics.mean_squared_error(ytest, ypred))
            print(metrics.mean_absolute_percentage_error(ytest, ypred))
            return model, df[features]
            # (100 * (ytest - ypred) / ytest).describe()


def get_feature_importance(model, X):
    # tree importance
    plt.rcParams["figure.figsize"] = (14, 7)
    plt.clf()
    xgb.plot_importance(model)
    plt.title("xgboost.plot_importance(model)")
    path = "./plot/"
    os.makedirs(path, exist_ok=True)
    plt.savefig(os.path.join(path,"xgboost_importance.png"), dpi=400)
    # Shapley values
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)
    print(" X.shape: ",X.shape)
    print(" shap_values.shape: ",shap_values.shape)
    # pred = model.predict(dtrain, output_margin=True) # pred_contribs=True
    # np.abs(shap_values.sum(1) + explainer.expected_value - pred).max()
    plt.clf()
    shap.summary_plot(shap_values, X)
    # shap.plots.bar(shap_values.abs.mean(0))
    plt.savefig(os.path.join(path,"shapley_summary.png"), dpi=400)
    for index, name in enumerate(X.columns):
        plt.clf()
        print(" X.columns: ",name)
        print(" shap_values[:,:,0].shape: ",shap_values[:,:,0].shape)
        shap.dependence_plot(name, shap_values[:,:,0], X, show=False)
        plt.savefig(os.path.join(path,f"shapley_dep_{name}_hpwl.png"), dpi=400)
        plt.close()
        shap.dependence_plot(name, shap_values[:,:,1], X, show=False)
        plt.savefig(os.path.join(path,f"shapley_dep_{name}_overflow.png"), dpi=400)
        plt.close()
        shap.dependence_plot(name, shap_values[:,:,2], X, show=False)
        plt.savefig(os.path.join(path,f"shapley_dep_{name}_route_utilization.png"), dpi=400)
        plt.close()
