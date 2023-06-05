# Name: Ayush Sharma

import io
import itertools

import numpy as np  # linear algebra
import pandas as pd  # data processing, CSV file I/O (e.g. pd.read_csv)
import sys

sys.path.append("the path")
import matplotlib.pyplot as plt
import matplotlib.pyplot as plt
import seaborn as sns
from xgboost import XGBRegressor
from sklearn.metrics import mean_squared_error
from sklearn.metrics import r2_score
from sklearn.metrics import mean_absolute_error
import requests

# constants
ITEM_CNT_MONTH = 'item_cnt_month'
ITEM_CATEGORY_ID = 'item_category_id'
ITEM_CNT = 'item_cnt'
ITEM_ID = 'item_id'
SHOP_ID = 'shop_id'
DATE_BLK = 'date_block_num'
DATE = 'date'
ITEM_PRICE = 'item_price'
ITEM_SOLD_PER_DAY = 'item_cnt_day'
YEAR = 'year'
MONTH = 'month'


# Preprocessing the dataset
def preprocess_data():
    # Reading the data from URL uploaded.
    base_url = "http://www.utdallas.edu/~vxk180030/MLProject/input/"
    categories_str = requests.get(base_url + "item_categories.csv").content
    categories = pd.read_csv(io.StringIO(categories_str.decode('utf-8')))
    items_str = requests.get(base_url + "items.csv").content
    items = pd.read_csv(io.StringIO(items_str.decode('utf-8')))
    shops_str = requests.get(base_url + "shops.csv").content
    shops = pd.read_csv(io.StringIO(shops_str.decode('utf-8')))
    train_str = requests.get(base_url + "sales_train.csv").content
    train = pd.read_csv(io.StringIO(train_str.decode('utf-8')))
    test_str = requests.get(base_url + "test.csv").content
    test = pd.read_csv(io.StringIO(test_str.decode('utf-8'))).set_index('ID')
    submission_str = requests.get(base_url + "sample_submission.csv").content
    submission = pd.read_csv(io.StringIO(submission_str.decode('utf-8')))
    # To View the data to get an idea.
    submission.head()
    categories.info()
    items.info()
    shops.info()
    train.info()
    categories.head()

    # Analyzing the train data
    print('To get the count of the shops', train[SHOP_ID].max())
    print('Total number of month: ', train[DATE_BLK].max())
    print('Total number of items in train dataset: ', train[ITEM_ID].max())
    print('Dimensions of the train: ', train.shape)
    # on Item category data
    print('The total item categories :` ', items[ITEM_CATEGORY_ID].max())

    # The train data should have all the data items so for that we join Items and shops with their id
    train = train.join(items, on=ITEM_ID, rsuffix='_').join(shops, on=SHOP_ID, rsuffix='_').join(categories,
                                                                                                 on=ITEM_CATEGORY_ID,
                                                                                                 rsuffix='_').drop(
        ['item_id_', 'shop_id_', ('%s_' % ITEM_CATEGORY_ID)], axis=1)
    # All the items and shops that are present in testing should be in training dataset to predict its value
    # to get the unique values of shops and items in test dataset
    # we will consider the shops and items that are present in test dataset to avoid overfitting

    test_shops = test[SHOP_ID]
    test_items = test[ITEM_ID]

    # To check is shop id in test dataset is in train
    filtered_train = train[train[SHOP_ID].isin(test_shops)]
    filtered_train = filtered_train[filtered_train[ITEM_ID].isin(test_items)]
    print("Number of records in train before filtering based on item ID and shop ID: ", train.shape[0])
    print("Number of records in train after filtering based on item ID and shop ID: ", filtered_train.shape[0])

    # To get an idea on maximum count of dataitems.
    num_month = train[DATE_BLK].max()
    print('No of Months: ', num_month)
    print('Maximum number of items in the category', len(categories))
    print('Maximum number of shops is: ', len(test_shops))
    print('To get the maximum block numbers: ', train.date_block_num.max())
    print('Maximum number of catageries is: ', len(categories))

    # need to change the item count day in training data to item count month
    filtered_train = filtered_train[
        [DATE, DATE_BLK, SHOP_ID, ITEM_CATEGORY_ID, ITEM_ID, ITEM_PRICE, ITEM_SOLD_PER_DAY]]

    train_by_month = filtered_train.sort_values(DATE).groupby(
        [DATE_BLK, SHOP_ID, ITEM_CATEGORY_ID, ITEM_ID], as_index=False)
    train_by_month = train_by_month.agg({ITEM_PRICE: ['sum', 'mean'], ITEM_SOLD_PER_DAY: ['sum', 'mean', 'count']})
    train_by_month.columns = [DATE_BLK, SHOP_ID, ITEM_CATEGORY_ID, ITEM_ID, ITEM_PRICE, 'mean_item_price',
                              ITEM_CNT, 'mean_item_cnt', 'transactions']
    # the month and year features need to be extracted from date block num
    shop_ids = train_by_month[SHOP_ID].unique()
    item_ids = train_by_month[ITEM_ID].unique()
    empty_df = itertools.product(range(34), shop_ids, item_ids)
    empty_df = pd.DataFrame(empty_df, columns=[DATE_BLK, SHOP_ID, ITEM_ID])

    train_by_month = pd.merge(empty_df, train_by_month, on=[DATE_BLK, SHOP_ID, ITEM_ID], how='left')
    train_by_month.fillna(0, inplace=True)

    train_by_month[YEAR] = (train_by_month[DATE_BLK] // 12) + 2013
    # train_by_month[YEAR] = train_by_month[DATE_BLK] // 12
    train_by_month[MONTH] = train_by_month[DATE_BLK] % 12

    # So we have to check the sales performance in the past 1 year.
    # gp_month_mean = train_by_month.groupby([MONTH], as_index=False)['item_cnt'].mean()
    # Grouping data for Estimation
    gp_month_sum = train_by_month.groupby([MONTH], as_index=False)[ITEM_CNT].sum()
    # The line plot for month and item count
    sns.lineplot(x=MONTH, y=ITEM_CNT, data=gp_month_sum, palette="GnBu_d").set_title("Monthly sum")
    plt.show()

    # Plot to check the item category id and item count
    plt.figure(figsize=(22, 2))
    gp_category_mean = train_by_month.groupby([ITEM_CATEGORY_ID], as_index=False)[ITEM_CNT].mean()
    sns.barplot(x=ITEM_CATEGORY_ID, y=ITEM_CNT, data=gp_category_mean, palette="GnBu_d").set_title("Monthly sum")
    plt.show()

    # So the sales according to the shops are to be checked, using plot on ship id and item count
    plt.figure(figsize=(15, 2))
    gp_shop_mean = train_by_month.groupby([SHOP_ID], as_index=False)[ITEM_CNT].mean()
    sns.barplot(x=SHOP_ID, y=ITEM_CNT, data=gp_shop_mean, palette="GnBu_d").set_title("Monthly sum")
    plt.show()

    # The outliers can be checked using box plot on item count
    plt.subplots(figsize=(22, 8))
    sns.boxplot(train_by_month[ITEM_CNT])
    plt.show()

    # To get train data based on month
    train_by_month = train_by_month.query('item_cnt >= 0 and item_cnt <= 20 and item_price < 400000')

    # Feature engineering on the data is done by adding extra features in the training data.
    train_by_month[ITEM_CNT_MONTH] = train_by_month.sort_values(DATE_BLK).groupby([SHOP_ID, ITEM_ID])[
        ITEM_CNT].shift(-1)
    # Item price unit is added to the dataset
    train_by_month['item_price_unit'] = train_by_month[ITEM_PRICE] // train_by_month[ITEM_CNT]
    train_by_month['item_price_unit'].fillna(0, inplace=True)

    # To check the delay in the dataset
    lag_list = [1, 2, 3]

    for lag in lag_list:
        name_feature = ('item_cnt_shifted%s' % lag)
        train_by_month[name_feature] = \
            train_by_month.sort_values(DATE_BLK).groupby([SHOP_ID, ITEM_CATEGORY_ID, ITEM_ID])[
                ITEM_CNT].shift(lag)
        # The null values are removed and replaced with 0.
        train_by_month[name_feature].fillna(0, inplace=True)

    train_by_month['item_trend'] = train_by_month[ITEM_CNT]

    for lag in lag_list:
        name_feature = ('item_cnt_shifted%s' % lag)
        train_by_month['item_trend'] -= train_by_month[name_feature]

    train_by_month['item_trend'] /= len(lag_list) + 1

    # From the dataset we have done preprocessing, we are splitting data for training and validation
    # Here we have considered month =5 and year as 2018 from that tenure it would be as validation set

    final_train_set = train_by_month.query('date_block_num >= 3 and date_block_num < 28').copy()
    final_validation_set = train_by_month.query('date_block_num >= 28 and date_block_num < 33').copy()
    final_test_set = train_by_month.query('date_block_num == 33').copy()

    # Item count month feature is no where required, so dropping it from both train and validation dataset.
    final_train_set.dropna(subset=[ITEM_CNT_MONTH], inplace=True)
    final_validation_set.dropna(subset=[ITEM_CNT_MONTH], inplace=True)

    final_train_set.dropna(inplace=True)
    final_validation_set.dropna(inplace=True)

    # Calculating the mean that is the aggregate value on Shop and item countsby calculating monthly mean aswell.
    gp_shop_mean = final_train_set.groupby([SHOP_ID]).agg({ITEM_CNT_MONTH: ['mean']})
    gp_shop_mean.columns = ['shop_mean']
    gp_shop_mean.reset_index(inplace=True)
    # Calculating the mean of the item by grouping it with item count month
    gp_item_mean = final_train_set.groupby([ITEM_ID]).agg({ITEM_CNT_MONTH: ['mean']})
    gp_item_mean.columns = ['item_mean']
    gp_item_mean.reset_index(inplace=True)
    # Then the mean of the item and shop are calculated by summing it together.
    gp_shop_item_mean = final_train_set.groupby([SHOP_ID, ITEM_ID]).agg({ITEM_CNT_MONTH: ['mean']})
    gp_shop_item_mean.columns = ['shop_item_mean']
    gp_shop_item_mean.reset_index(inplace=True)
    # The mean of the year is done where we have added this feature before.
    gp_year_mean = final_train_set.groupby([YEAR]).agg({ITEM_CNT_MONTH: ['mean']})
    gp_year_mean.columns = ['year_mean']
    # Resetting the mean index
    gp_year_mean.reset_index(inplace=True)
    # Similarly the mean of months are calculated using item_cnt_month in the dataset
    gp_month_mean = final_train_set.groupby([MONTH]).agg({ITEM_CNT_MONTH: ['mean']})
    gp_month_mean.columns = ['month_mean']
    # Resetting the mean index
    gp_month_mean.reset_index(inplace=True)

    # So all the features that are calculated should be added to the dataset
    final_train_set = pd.merge(final_train_set, gp_shop_mean, on=[SHOP_ID], how='left')
    final_train_set = pd.merge(final_train_set, gp_item_mean, on=[ITEM_ID], how='left')
    final_train_set = pd.merge(final_train_set, gp_shop_item_mean, on=[SHOP_ID, ITEM_ID], how='left')
    final_train_set = pd.merge(final_train_set, gp_year_mean, on=[YEAR], how='left')
    final_train_set = pd.merge(final_train_set, gp_month_mean, on=[MONTH], how='left')
    # Simularly adding it to the validation set.
    final_validation_set = pd.merge(final_validation_set, gp_shop_mean, on=[SHOP_ID], how='left')
    final_validation_set = pd.merge(final_validation_set, gp_item_mean, on=[ITEM_ID], how='left')
    final_validation_set = pd.merge(final_validation_set, gp_shop_item_mean, on=[SHOP_ID, ITEM_ID], how='left')
    final_validation_set = pd.merge(final_validation_set, gp_year_mean, on=[YEAR], how='left')
    final_validation_set = pd.merge(final_validation_set, gp_month_mean, on=[MONTH], how='left')

    # Creating the labels for trains and validation sets.
    X_train = final_train_set.drop([ITEM_CNT_MONTH, DATE_BLK], axis=1)
    Y_train = final_train_set[ITEM_CNT_MONTH].astype(int)
    X_validation = final_validation_set.drop([ITEM_CNT_MONTH, DATE_BLK], axis=1)
    Y_validation = final_validation_set[ITEM_CNT_MONTH].astype(int)

    final_latest_records = pd.concat([final_train_set, final_validation_set]).drop_duplicates(
        subset=[SHOP_ID, ITEM_ID], keep='last')
    X_test = pd.merge(test, final_latest_records, on=[SHOP_ID, ITEM_ID], how='left', suffixes=['', '_'])
    X_test[YEAR] = 2015
    X_test[MONTH] = 9
    X_test.drop(ITEM_CNT_MONTH, axis=1, inplace=True)
    # X_test[int_features] = X_test[int_features].astype('int32')
    X_test = X_test[X_train.columns]

    sets = [X_train, X_validation, X_test]
    for dataset in sets:
        for shop_id in dataset[SHOP_ID].unique():
            for column in dataset.columns:
                shop_median = dataset[(dataset[SHOP_ID] == shop_id)][column].median()
                dataset.loc[(dataset[column].isnull()) & (dataset[SHOP_ID] == shop_id), column] = shop_median

    # Replacing the null values in test with mean of the data.
    X_test.fillna(X_test.mean(), inplace=True)

    # Dropping the item category id as it isn't that required from train and validation sets.
    X_train.drop([ITEM_CATEGORY_ID], axis=1, inplace=True)
    X_validation.drop([ITEM_CATEGORY_ID], axis=1, inplace=True)
    X_test.drop([ITEM_CATEGORY_ID], axis=1, inplace=True)
    return X_train, X_validation, X_test, Y_train, Y_validation


def xg_boost():
    # XGBoost on the data we have pre processed.
    xgb_features = [ITEM_CNT, 'item_cnt_shifted1',
                    'item_cnt_shifted2', 'item_cnt_shifted3', 'shop_mean',
                    'shop_item_mean', 'item_trend', 'mean_item_cnt']
    xgb_train = X_train[xgb_features]
    xgb_val = X_validation[xgb_features]
    xgb_test = X_test[xgb_features]
    # Model creation of xgboost regressor
    xgb_model = XGBRegressor(max_depth=8,
                             n_estimators=50,
                             min_child_weight=100,
                             booster='gbtree',
                             colsample_bytree=0.7,
                             subsample=0.7,
                             eta=0.3,
                             nthread=None,
                             seed=0)
    # Fitting the model to train dataset
    xgb_model.fit(xgb_train,
                  Y_train,
                  eval_metric="rmse",
                  eval_set=[(xgb_train, Y_train), (xgb_val, Y_validation)],
                  verbose=20,
                  early_stopping_rounds=20)
    # Predicting the value on the model
    xgb_train_pred = xgb_model.predict(xgb_train)
    xgb_val_pred = xgb_model.predict(xgb_val)
    # Predicting the value on test dataset
    xgb_test_pred = xgb_model.predict(xgb_test)
    print('------------------------------------------------------------------------------')
    print('XGBoost')
    print('Train rmse: ', np.sqrt(mean_squared_error(Y_train, xgb_train_pred)))
    print('Validation rmse: ', np.sqrt(mean_squared_error(Y_validation, xgb_val_pred)))
    print('r2 score: ', r2_score(Y_validation, xgb_val_pred))
    print('Mean Absolute Error: ', mean_absolute_error(Y_validation, xgb_val_pred))


def random_forest():
    # Creating a random forest model on different featured
    from sklearn.ensemble import RandomForestRegressor
    selectedFeaturesRF = [SHOP_ID, ITEM_ID, ITEM_CNT, 'transactions', YEAR, 'item_cnt_shifted1', 'item_trend',
                          'shop_mean', 'item_mean', 'mean_item_cnt']
    trainRF = X_train[selectedFeaturesRF]
    validationRF = X_validation[selectedFeaturesRF]
    testRF = X_test[selectedFeaturesRF]

    modelRF = RandomForestRegressor(n_estimators=60, max_depth=8, random_state=0, min_samples_leaf=4,
                                    min_samples_split=3, max_features="auto", n_jobs=-1)
    # Fitting the data in the model
    modelRF.fit(trainRF, Y_train)
    # Predicting the value on train dataset
    trainPredRF = modelRF.predict(trainRF)
    # Predicting the value on test dataset
    validationPredRF = modelRF.predict(validationRF)
    testPredRF = modelRF.predict(testRF)
    print('------------------------------------------------------------------------------')
    print('Random Forest')
    print('Train rmse: ', np.sqrt(mean_squared_error(Y_train, trainPredRF)))
    print('Validation rmse: ', np.sqrt(mean_squared_error(Y_validation, validationPredRF)))
    print('r2 score: ', r2_score(Y_validation, validationPredRF))
    print('Mean Absolute Error: ', mean_absolute_error(Y_validation, validationPredRF))


def linear_regression():
    # linear regression model on the dataset preprocessed
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import StandardScaler, MinMaxScaler
    selectedFeaturesLR = [ITEM_CNT, 'item_cnt_shifted1', 'item_trend', 'mean_item_cnt', 'shop_mean']
    trainLR = X_train[selectedFeaturesLR]
    validationLR = X_validation[selectedFeaturesLR]
    testLR = X_test[selectedFeaturesLR]

    # Normalizing using min max scaling to get proper values.
    scalerLR = MinMaxScaler()
    scalerLR.fit(trainLR)
    trainLR = scalerLR.transform(trainLR)
    validationLR = scalerLR.transform(validationLR)
    testLR = scalerLR.transform(testLR)
    # Creation of Linear regression model
    modelLR = LinearRegression(n_jobs=-1)
    # Fitting the model
    modelLR.fit(trainLR, Y_train)
    trainPredLR = modelLR.predict(trainLR)
    validationPredLR = modelLR.predict(validationLR)
    # predicting it on test dataset
    testPredLR = modelLR.predict(testLR)

    # accurcy
    print('------------------------------------------------------------------------------')
    print('Linear Regression')
    print('Train rmse: ', np.sqrt(mean_squared_error(Y_train, trainPredLR)))
    print('Validation rmse: ', np.sqrt(mean_squared_error(Y_validation, validationPredLR)))
    print('r2 score: ', r2_score(Y_validation, validationPredLR))
    print('Mean Absolute Error: ', mean_absolute_error(Y_validation, validationPredLR))


if __name__ == '__main__':
    X_train, X_validation, X_test, Y_train, Y_validation = preprocess_data()
    xg_boost()
    random_forest()
    linear_regression()