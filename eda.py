import pandas as pd
import numpy as np
import time
import matplotlib.pyplot as plt
from scipy.stats import chi2_contingency
import seaborn as sns
sns.set(style="whitegrid", color_codes=True)
sns.set(font_scale=1)
import warnings
warnings.filterwarnings("ignore")

lable = 'click'
### 读取数据
train1 = pd.read_table('./data/train1.txt', sep='\t', encoding='utf-8')
train2 = pd.read_table('./data/train2.txt', sep='\t', encoding='utf-8')
train = pd.concat([train1, train2], axis=0, ignore_index=True)  ## 连接
train.drop_duplicates(subset=None, keep='first', inplace=False)  ## 去重
test = pd.read_table('./data/test_feature2.txt', sep='\t', encoding='utf-8')
data = pd.concat([train, test], axis=0, ignore_index=True)
print(data)

### 检查两表的userID是否有交集
print(len(np.intersect1d(train.index, test.index)))  ##无广告交集
print(train.info())    ##查看训练集信息
print(train.isnull().any())##获取含有缺失值的列:user_tags，make，model，osv，app_cate_id，f_channel，app_id
print(train.nunique())  ## 查看有没有单个值的特征：只有creative_is_js 是否为js素材 creative_is_voicead 是否是语音广告，app_paid，考虑剔除

# 训练集正负样本比例,约1：4
labels = [0,1]
sizes = train.click.value_counts().values
explode=[0.1,0]
colors = [ 'red','yellow']
patches, texts,autotexts= plt.pie(sizes, labels=labels,colors=colors,explode=explode,autopct="%1.1f%%",startangle=90)
plt.title("click")
plt.show()

sns.stripplot(train["click"],train["creative_height"],jitter=True,)#广告的长宽
plt.show()

### adid 广告id
adid_uni = len(train['adid'].unique())  ## 去重复数，2079个广告
print(adid_uni)
adid_size = np.size(train, 0)## train['adid'].size#3000000条记录
print(adid_size)
id_size = train.groupby('adid').size().sort_values()  ## 每条广告的记录数
print(id_size.describe()) ## 平均每个广告481条记录
plt.boxplot(id_size)  ## 箱线图
plt.hist(id_size, bins=40, alpha=0.75, label="")  ## 频数直方图
print(id_size.value_counts())  ## 广告记录数对应广告量
plt.scatter(id_size.value_counts().index, id_size.value_counts().values)  ## 散点图
plt.show()
id_test = train.groupby('adid').nunique()
print(id_test)
'''查看与广告id的对应关系，一个广告id唯一对应：advert_id,orderid，campaign_id,creative_id,creative_tp_dnf,
creative_type,creative_width,creative_height等具体广告特征,还有advert_name'''

###advert 广告主id
print(len(train['advert_id'].unique()))##39个广告主
y = train['advert_id']##3000000条记录
print(y)
print(train.groupby('advert_id').size())
print(train.groupby('advert_id')['click'].apply(lambda x: x.sum()/x.count()))## 观察不同广告主点击率的数值
##由于点击率差异比较大但不同广告主的曝光次数也差异比较大，所以我们用卡方检验来测评广告主对于点击率是否有影响
z = (chi2_contingency(pd.DataFrame({'a':train.groupby('advert_id')['click'].apply(lambda x: x.sum()),
                                    'b':train.groupby('advert_id')['click'].apply(lambda x: x.count()-x.sum())}))[:3])
print(z)## P＜0.05，差异有显著统计学意义

### time
print(train.groupby('adid')['time'].apply(lambda x:x.value_counts().iloc[0]).sort_values())##最大重复数#最大重复时间为62
print(train['time'].unique())
print(len(train['time'].unique()))
train['hour'] = train['time'].apply(lambda x:int(time.strftime("%H", time.localtime(x))))
X_gender = train['hour'].value_counts().sort_index().index## Y标签值
Y_gender = train['hour'].value_counts().sort_index()## Y标签值
Y_gender_0 = train[train['click']==0]['hour'].value_counts().sort_index()
Y_gender_1 = train[train['click']==1]['hour'].value_counts().sort_index()
plt.bar(X_gender,Y_gender_0, alpha=0.75, width=0.8)
plt.bar(X_gender,Y_gender_1, alpha=0.75, width=0.8, bottom=Y_gender_0)  ## 通过 bottom=Y_gender_0 设置柱叠加 ，堆叠图
plt.show()

### orderid订单id
print(train['orderid'].unique())
print(len(train['orderid'].unique()))## 908个订单id
'''
一个订单id唯一对应一个特征变量：
advert_id广告主id,orderid,campaign_id活动id,creative_type创意类型,creative_is_jump是否是落地页跳转,
creative_is_download是否是落地页下载,creative_has_deeplink响应素材是否有deeplink,advert_name广告主名称
'''
### campaign_id 活动id
print(len(train['campaign_id'].unique()))## 67个 #与advert_id唯一对应

### creative_id 创意id
print(len(train['creative_id'].unique()))## 908个
## 与advert_id，creative_tp_dnf,creative_type,creative_width,creative_height,creative__has_deeplink,advert_name唯一对应

##creative_type 创意类型
print(len(train['creative_type'].unique()))## 5#无唯一对应特征，和创意id是一对多

### advert_industry_inner 广告主行业
## 上面有看见一个订单id对应了2个广告行业，查看分布
print(train['advert_industry_inner'].unique())## 大行业有24种#无唯一对应特征

### advert_name 广告主名称
print(len(train['advert_name'].unique()))## 34个
## 34个广告主名称对应38个广告主id，但都不是有缺失的特征
## 广告主名称与广告主id不是一一对应，id底下唯一对应一个名字，名字不唯一对应一个id，所以一个广告主名字可能有多个id

### creative_width 创意宽
### creative_height 创意高
print(train['creative_width'].unique())## 20个
print(train['creative_height'].unique())## 13个
##离散数值
print(chi2_contingency(
        pd.DataFrame({'a':train.groupby('creative_width')['click'].apply(lambda x: x.sum()),
        'b':train.groupby('creative_width')['click'].apply(lambda x: x.count()-x.sum())}))[:3])
## 创意宽，高对于点击率有显著的影响

### inner_slot_id 媒体广告位
print(len(train['inner_slot_id'].unique()))## 1169个广告位，而我们有2079个广告id
inner_slot_test = train.groupby('inner_slot_id').nunique()## 没有一一对应值
## 广告位的长宽是不固定，但是不变的占多数，最多一个广告位有3个尺度
inner_slot_test['creative_width'].value_counts()
inner_slot_test['creative_height'].value_counts()

### app_cate_id app分类
### f_channel 一级频道
### app_id
print(len(train['app_cate_id'].unique()))## 23个
print(len(train['f_channel'].unique()))## 74个
print(len(train['app_id'].unique()))## 439个
app_cate_test = train.groupby('app_cate_id').nunique()## 与creative_has_deeplink 响应素材是否有deeplink唯一对应
app_id_test = train.groupby('app_id').nunique()## 与app_cate_id和creative_has_deeplink唯一对应
channel_test = train.groupby('f_channel').nunique()
'''f_channel与'carrier'运行商, 'devtype'设备类型, 'app_cate_id'app分类, 'app_id'媒体id,'creative_is_jump',
 'creative_is_download', 'creative_has_deeplink'唯一对应, make品牌全是0，即有一级频道的记录没有品牌数据'''
'''
f_channel                76390 non-null object
app_id                   999383 non-null float64
由于f_channel下一个频道对应一个app_id，由于缺失值过多，考虑将f_channel去除，只使用app_id
'''

### model 机型
### make 品牌
print(len(train['model'].unique()))## 14054个
print(len(train['make'].unique()))## 3141个
## 994248 non-null object/1001650
print(train['model'].count()/train['model'].size)## 99.2%的非缺失率
print(train['make'].count()/train['make'].size)## 90.1%的非缺失率
print(train['model'].value_counts())
train.groupby('model')['click'].apply(lambda x: x.sum()/x.count()).sort_values()
train.groupby('make')['click'].apply(lambda x: x.sum()/x.count()).sort_values()
## 很多的点击率是100%，明显是由于基数过大与过少，这样的数据不具有泛化能力
## 手机品牌太多，粒度太细容易过拟合，考虑后续合并手机类型

### user_tags 用户标签信息，以逗号分隔
print(train['user_tags'])
train[train['user_tags'].notnull()]['user_tags'].nunique()
train[train['user_tags'].notnull()]['click'].value_counts()
## 点击为0有557869，点击为1有134011
print(train[(train['user_tags'].notnull())&(train['click']==0)][['user_tags','click']])
## 发现有用户点击也是0
train[train['user_tags'].isnull()]['click'].value_counts()#0    244994  1     64776
## 用户缺失不影响点击与否
## 用户标签信息理解为用户的属性和动作，考虑后续用词向量的方式提取相关信息

###  city 城市
###  province 省份
print(len(train['city'].unique()))## 333个 6——12位不同
print(len(train['province'].unique()))## 35个，前缀后缀完全一样，只有6-9位不同

### nnt 联网类型
print(train['nnt'].unique())## 6种

### devtype 设备类型
print(len(train['devtype'].unique()))## 14054个
## 查看与devtype唯一对应的特征，除去只有一个数值的变量，没有

### os_name 操作系统名称
print(len(train['os_name'].unique()))## 14054个

### osv 操作系统版本
print(len(train['osv'].unique()))## 301个
## 查看与osv唯一对应的特征，无
train.groupby('osv')['click'].apply(lambda x: x.sum()/x.count())## 数据需要清洗统一起来

### os 操作系统
print(len(train['os'].unique()))## 3个
print(train['os'].value_counts())## 第三类只有18个，考虑融合到另外一个里
train.groupby('os')['click'].apply(lambda x: x.sum()/x.count())## 与os_name完全一致，考虑去掉一个


