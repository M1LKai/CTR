import numpy as np
import pandas as pd
import time
import datetime
import gc
from sklearn.preprocessing import OneHotEncoder, LabelEncoder
from sklearn.model_selection import KFold, cross_val_score, train_test_split
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score, log_loss
import lightgbm as lgb
from scipy import sparse
from sklearn.feature_extraction.text import CountVectorizer

import warnings
warnings.filterwarnings("ignore")


def getStackFeature(df_, seed_):
    skf = StratifiedKFold(n_splits=5, random_state=seed_, shuffle=True)
    train = df_.loc[train_index]
    test = df_.loc[test_index]
    train_user = pd.Series()
    test_user = pd.Series(0, index=list(range(test_x.shape[0])))
    for train_part_index, evals_index in skf.split(train, train_y):
        EVAL_RESULT = {}
        train_part = lgb.Dataset(train.loc[train_part_index], label=train_y.loc[train_part_index])
        evals = lgb.Dataset(train.loc[evals_index], label=train_y.loc[evals_index])
        bst = lgb.train(params_initial, train_part,
                        num_boost_round=2500, valid_sets=[train_part, evals],
                        valid_names=['train', 'evals'], early_stopping_rounds=200,
                        evals_result=EVAL_RESULT, verbose_eval=50)
        train_user = train_user.append(pd.Series(bst.predict(train.loc[evals_index]), index=evals_index))
        test_user = test_user + pd.Series(bst.predict(test))
    return train_user, test_user

# 加载数据
train1 = pd.read_table('./data/train1.txt',sep='\t',encoding='utf-8')
train2 = pd.read_table('./data/train2.txt',sep='\t',encoding='utf-8')
train = pd.concat([train1, train2], axis=0, ignore_index=True)#连接
train.drop_duplicates(subset=None, keep='first', inplace=False)#去重
test = pd.read_table('./data/test_feature1.txt',sep='\t',encoding='utf-8')
res = test.loc[:, ['instance_id']]
test['label'] = -1
train = train.fillna(-1)
test = test.fillna(-1)
data = pd.read_csv('./data/data_pre.csv',encoding='utf-8')

#######################
###   只有单个值的特征，剔除
del data['creative_is_js']
del data['creative_is_voicead']
del data['app_paid']

#######################
type_feature = ['city', 'province', 'carrier', 'devtype', 'make', 'nnt', 'osv',
                'model', 'make_new', 'model_new',
                'os', 'os_name', 'os_name1', 'user_id', 'inner_slot_id1',
                'adid', 'advert_id', 'orderid', 'campaign_id', 'advert_industry_inner',
                'creative_id', 'creative_tp_dnf', 'app_cate_id', 'f_channel', 'app_id',
                'inner_slot_id', 'creative_type',
                'advert_name', 'hour', 'advert_industry_inner1',
                'advert_industry_inner2']

for feature in type_feature:
    try:
        data[feature] = LabelEncoder().fit_transform(data[feature].fillna(-1).apply(int))
    except:
        data[feature] = LabelEncoder().fit_transform(data[feature].fillna(-1))

print('enc over')
#### LabelEncoder实现标准化标签
#### fit(x,y)传两个参数的是有监督学习的算法，fit(x)传一个参数的是无监督学习的算法，比如降维、特征提取、标准化
#### fit_transform()的作用就是先拟合数据，然后转化它将其转化为标准形式

cols = ['city', 'province', 'carrier', 'devtype', 'make', 'model', 'nnt', 'os',
        'osv', 'os_name', 'adid', 'advert_id', 'orderid',
        'advert_industry_inner', 'campaign_id', 'creative_id',
        'creative_tp_dnf', 'app_cate_id', 'app_id', 'inner_slot_id',
        'creative_type', 'creative_width', 'creative_height',
        'creative_is_jump', 'creative_is_download', 'creative_has_deeplink',
        'advert_name', 'day', 'hour']
train_index = data[data['click'] != -1].index.tolist()
test_index = data[data['click'] == -1].index.tolist()
train_y = pd.Series(data['click'].loc[train_index].values)

cv = CountVectorizer()
arr = sparse.hstack((pd.DataFrame(), cv.fit_transform(data['user_tags']))).tocsr()
print('cv over')

skf = StratifiedKFold(n_splits=5, random_state=2020, shuffle=True)
params_initial = {
    'objective': 'binary'
}
train_x = arr[train_index, :]
test_x = arr[test_index, :]
num = 1
train_user = pd.Series()
test_user = pd.Series(0, index=list(range(test_x.shape[0])))
fscore_se = pd.Series(0, index=list(range(arr.shape[1])))
for train_part_index, evals_index in skf.split(train_x, train_y):
    EVAL_RESULT = {}
    train_part = lgb.Dataset(train_x[train_part_index, :], label=train_y.loc[train_part_index])
    evals = lgb.Dataset(train_x[evals_index, :], label=train_y.loc[evals_index])
    bst = lgb.train(params_initial, train_part,
                    num_boost_round=2500, valid_sets=[train_part, evals],
                    valid_names=['train', 'evals'], early_stopping_rounds=200,
                    evals_result=EVAL_RESULT, verbose_eval=50)
    fscore_se = fscore_se + pd.Series(bst.feature_importance())
    train_user = train_user.append(pd.Series(bst.predict(train_x[evals_index, :]), index=evals_index))
    test_user = test_user + pd.Series(bst.predict(test_x))
    print(num)
    num += 1

fscore_se = fscore_se.sort_values(ascending=False)#### ascending：默认True升序排列；False降序排列
###########################################
col_cvr = cols[:]
train_x = data[col_cvr].loc[train_index].reset_index()### .loc通过行索引 "Index" 中的具体值来取行数据
test_x = data[col_cvr].loc[test_index].reset_index()
train_x['user_stack'] = train_user.sort_index().values
test_x['user_stack'] = (test_user.values) / 5
del train_x['index']
del test_x['index']


##########################################

###########################################
data['cnt'] = 1
col_ratio = []
num = 0
s = time.time()
df = pd.DataFrame()
print('Ratio clcik...')
col_type = type_feature.copy()
n = len(col_type)
for i in range(n):
    col_name = "ratio_click_of_" + col_type[i]
    s = time.time()
    df[col_name] = (data[col_type[i]].map(data[col_type[i]].value_counts()) / len(data) * 100).astype(int)
    num += 1
    print(num, col_name, int(time.time() - s), 's')
    col_ratio.append(col_name)
stack = 1
n = len(col_type)
for i in range(n):
    for j in range(n):
        if i != j:
            col_name = "ratio_click_of_" + col_type[j] + "_in_" + col_type[i]
            se = data.groupby([col_type[i], col_type[j]])['cnt'].sum()
            dt = data[[col_type[i], col_type[j]]]
            cnt = data[col_type[i]].map(data[col_type[i]].value_counts())
            df[col_name] = ((pd.merge(dt, se.reset_index(), how='left', on=[col_type[i], col_type[j]]).sort_index()[
                                 'cnt'].fillna(value=0) / cnt) * 100).astype(int).values
            num += 1
            col_ratio.append(col_name)
            if len(df.columns) == 200:
                print(num, col_name, int(time.time() - s), 's')
                train_user, test_user = getStackFeature(df, stack)
                train_x['ratio_' + str(stack)] = train_user.sort_index().values
                test_x['ratio_' + str(stack)] = (test_user.values) / 5
                stack += 1
                df = pd.DataFrame()
                s = time.time()
                gc.collect()
###################################
k = 100
num = 1
col_select = fscore_se.index.tolist()
df = pd.DataFrame()
for ind in col_select[:100]:
    data['temp'] = arr[:, ind].toarray()[:, 0]
    for co in type_feature:
        col_name = co + '_user_tags_' + str(ind) + '_ratio'
        se = data.groupby([co])['temp'].mean()
        df[col_name] = ((data[co].map(se)) * 10000).astype(int)
        if len(df.columns) == 200:
            print(num, col_name, int(time.time() - s), 's')
            print('\n')
            print('\n')
            train_user, test_user = getStackFeature(df, stack)
            train_x['cvr_' + str(stack)] = train_user.sort_index().values
            test_x['cvr_' + str(stack)] = (test_user.values) / 5
            stack += 1
            df = pd.DataFrame()
            s = time.time()
            gc.collect()
    num += 1
###################################

for i in range(n):
    col_name = "cnt_click_of_" + col_type[i]
    s = time.time()
    se = (data[col_type[i]].map(data[col_type[i]].value_counts())).astype(int)
    semax = se.max()
    semin = se.min()
    df[col_name] = ((se - se.min()) / (se.max() - se.min()) * 100).astype(int).values
    num += 1


##########减小内存
for i in data.columns:
    if (i != 'instance_id'):
        if (data[i].dtypes == 'int64'):
           data[i] = data[i].astype('int16')
        if (data[i].dtypes == 'int32'):
            data[i] = data[i].astype('int16')

print('Begin stat...')  ##再加入离散特征
n = len(col_type)
for i in range(n):
    for j in range(n - i - 1):
        col_name = "cnt_click_of_" + col_type[i + j + 1] + "_and_" + col_type[i]
        s = time.time()
        se = data.groupby([col_type[i], col_type[i + j + 1]])['cnt'].sum()
        dt = data[[col_type[i], col_type[i + j + 1]]]
        se = (pd.merge(dt, se.reset_index(), how='left',
                       on=[col_type[i], col_type[j + i + 1]]).sort_index()['cnt'].fillna(value=0)).astype(int)
        semax = se.max()
        semin = se.min()
        df[col_name] = ((se - se.min()) / (se.max() - se.min()) * 100).fillna(value=0).astype(int).values
        num += 1
        if len(df.columns) >= 200:
            print(num, col_name, int(time.time() - s), 's')
            print('\n')
            print('\n')
            train_user, test_user = getStackFeature(df, stack)
            train_x['click_' + str(stack)] = train_user.sort_index().values
            test_x['click_' + str(stack)] = (test_user.values) / 5
            stack += 1
            df = pd.DataFrame()
            s = time.time()
            gc.collect()
            print(num, col_name, int(time.time() - s), 's')
##################################
n = len(col_type)
num = 0
for i in range(n):
    for j in range(n):
        if i != j:
            s = time.time()
            col_name = "count_type_" + col_type[j] + "_in_" + col_type[i]
            se = data.groupby([col_type[i]])[col_type[j]].value_counts()
            se = pd.Series(1, index=se.index).sum(level=col_type[i])
            df[col_name] = (data[col_type[i]].map(se)).fillna(value=0).astype(int).values
            num += 1
            if len(df.columns) >= 200:
                print(num, col_name, int(time.time() - s), 's')
                print('\n')
                print('\n')
                train_user, test_user = getStackFeature(df, stack)
                train_x['nunique_' + str(stack)] = train_user.sort_index().values
                test_x['nunique_' + str(stack)] = (test_user.values) / 5
                stack += 1
                df = pd.DataFrame()
                s = time.time()
                gc.collect()
                print(num, col_name, int(time.time() - s), 's')

k = 100
col_select = fscore_se[:k].index.tolist()  ####特征选择F-score
train_x = sparse.hstack((train_x, arr[train_index, :].tocsc()[:, col_select])).tocsr()
test_x = sparse.hstack((test_x, arr[test_index, :].tocsc()[:, col_select])).tocsr()
###hstack ：将矩阵按照列进行拼接
###
print(train_x.shape)
print(test_x.shape)

################
################
################
params_initial = {
    'boosting_type':'gbdt','max_depth':-1,'num_leaves': 48,'n_estimators' : 6000,
    'objective': 'binary','learning_rate': 0.035,'max_bin': 425,'min_data_in_leaf': 10,
    'min_child_weight' : 5,'min_child_samples' : 10,'subsample' : 0.8,'subsample_freq': 1,
    'colsample_bytree' : 0.8,'feature_fraction': 0.5,
    'bagging_freq': 1,'bagging_seed': 0,'bagging_fraction': 0.9,
    'reg_alpha': 3,'reg_lambda': 5,'seed' : 1000,'n_jobs' :-1,'silent':'True'
}
score = []
res['predicted_score'] = 0
for train_part_index, evals_index in skf.split(train_x, train_y):
    EVAL_RESULT = {}
    train_part = lgb.Dataset(train_x[train_part_index, :], label=train_y.loc[train_part_index])
    evals = lgb.Dataset(train_x[evals_index, :], label=train_y.loc[evals_index])
    bst = lgb.train(params_initial, train_part,
                    num_boost_round=2500, valid_sets=[train_part, evals],
                    valid_names=['train', 'evals'], early_stopping_rounds=200,
                    evals_result=EVAL_RESULT, verbose_eval=50)
    lst = EVAL_RESULT['evals']['binary_logloss']
    best_score = min(lst)
    print(best_score)
    score.append(best_score)
    best_iter = lst.index(best_score) + 1
    print(best_iter)
    res['predicted_score'] = res['predicted_score'].values + bst.predict(test_x, num_iteration=best_iter)
res['predicted_score'] = res['predicted_score'] / 5


print(score)
print(sum(score) / 5)
print(res.head(10))
print(res['predicted_score'].describe())

res.to_csv( "./result/lgb_m1.csv" , index=False)
