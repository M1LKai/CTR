import numpy as np
import pandas as pd
import datetime
import gc

import warnings
warnings.filterwarnings("ignore")

# 加载数据
train1 = pd.read_table('./data/train1.txt',sep='\t',encoding='utf-8')
train2 = pd.read_table('./data/train2.txt',sep='\t',encoding='utf-8')
train = pd.concat([train1, train2], axis=0, ignore_index=True)#连接
train.drop_duplicates(subset=None, keep='first', inplace=False)#去重
test = pd.read_table('./data/test_feature2.txt',sep='\t',encoding='utf-8')
data = pd.concat([train,test],axis=0,ignore_index=True)
del train1
del train2
del test
gc.collect()
#print(data)

###################
###      自定义函数
def getTimeList(arr):    #时间
    day = []
    hour = []
    for a in arr:
        t = datetime.datetime.fromtimestamp(a+3600*24*5)
        day.append(t.day)
        hour.append(t.hour)
    return day,hour
def getLst(co1,co2):    #获取列表
    arr2 = data[co2].astype(str).fillna(value='-1').values
    arr1 = data[co1].astype(str).values
    lst = []
    for i in range(len(arr1)):
        lst.append(arr1[i]+'_'+arr2[i])
    return lst



##################
###   时间细分
day,hour = getTimeList(data['time'].values)
data['day'] = day
data['hour'] = hour
data['hour_part'] =  (data['hour']//6).astype(int)
del data['time']


#########################
###  媒体广告位
lst  = []
for va in data['inner_slot_id'].values:
    lst.append(va.split('_')[0])
data['inner_slot_id1'] = lst

#######################
###  将advert_industry_inner的一级与二级行业细分
lst1 = []
lst2 = []
for va in data['advert_industry_inner'].values:
    lst1.append(va.split('_')[0])
    lst2.append(va.split('_')[1])
data['advert_industry_inner1'] = lst1
data['advert_industry_inner2'] = lst2


#######################
###   品牌清洗
lst = []
for va in data['make'].values:
    va = str(va)
    if ',' in va:
        lst.append(va.split(',')[0].lower())
    elif ' ' in va:
        lst.append(va.split(' ')[0].lower())
    elif '-' in va:
        lst.append(va.split('-')[0].lower())
    else:
        lst.append(va.lower())
for i in range(len(lst)):
    if 'iphone' in lst[i]:
        lst[i] = 'apple'
    elif 'redmi' in lst[i]:
        lst[i] = 'xiaomi'
    elif lst[i]=='mi':
        lst[i] = 'xiaomi'
    elif lst[i]=='meitu':
        lst[i] = 'meizu'
    elif lst[i]=='nan':
        lst[i] = np.nan
    elif lst[i]=='honor':
        lst[i] = 'huawei'
    elif lst[i]=='le' or lst[i]=='letv' or lst[i]=='lemobile' or lst[i]=='lephone' or lst[i]=='blephone':
        lst[i] = 'leshi'
data['make_new'] = lst

###    机型清洗
lst = []
for va in data['model'].values:
    va = str(va)
    if ',' in va:
        lst.append(va.replace(',',' '))
    elif '+' in va:
        lst.append(va.replace('+',' '))
    elif '-' in va:
        lst.append(va.replace('-',' '))
    elif 'nan'==va:
        lst.append(np.nan)
    else:
        lst.append(va)
data['model_new'] = lst

###  操作系统及版本清洗
data['os'].replace(0,2,inplace=True)
lst = []
for va in data['osv'].values:
    va = str(va)
    va = va.replace('iOS','')
    va = va.replace('android','')
    va = va.replace(' ','')
    va = va.replace('iPhoneOS','')
    va = va.replace('_','.')
    va = va.replace('Android5.1','.')
    try:
        int(va)
        lst.append(np.nan)
    except:
        sp = ['nan','11.39999961853027','10.30000019073486','unknown','11.30000019073486']
        if va in sp:
            lst.append(np.nan)
        elif va=='3.0.4-RS-20160720.1914':
            lst.append('3.0.4')
        else:
            lst.append(va)
temp = pd.Series(lst).value_counts()
temp = temp[temp<=2].index.tolist()
for i in range(len(lst)):
    if lst[i] in temp:
        lst[i] = np.nan
data['osv'] = lst
lst1 = []
lst2 = []
lst3 = []
for va in data['osv'].values:
    va = str(va).split('.')
    if len(va)<3:
        va.extend(['0','0','0'])
    lst1.append(va[0])
    lst2.append(va[1])
    lst3.append(va[2])
data['osv1'] = lst1
data['osv2'] = lst2
data['osv3'] = lst3
#  同类合并
data['os_name'] = getLst('os','osv')
data['os_name1'] = getLst('os','osv1')

#######################
###  将bool值转化为数值
bool_feature = ['creative_is_jump', 'creative_is_download', 'creative_has_deeplink']
for feature in bool_feature:
    data[feature] = data[feature].astype(int)

#######################
###    构造用户标签索引
se = pd.Series(data['user_tags'].drop_duplicates().values)
data['user_id'] = data['user_tags'].map(pd.Series(se.index,index=se.values))
data['user_tags'].fillna(value='-1',inplace=True)
lst = []
for va in data['user_tags'].values:
    va = va.replace(',',' ')
    lst.append(va)
data['user_tags'] = lst

###############
###  缺失值
data = data.fillna(-1)
data.to_csv('./data/data_pre.csv',index=False)
print('data preprocessing over!')




