import io
import pandas as pd
import numpy as np

class RawDataPreprocessing:
    """
         Transform data representation from raw excel file to clear pandas DataFrame.
    """
    def __init__(self, path_file: str | io.BufferedIOBase) -> None:
        self.raw_data = pd.read_excel(path_file)
        self.part_data = self.process_raw_data(self.raw_data)
        self.data: pd.DataFrame = self.process_data(self.part_data)
    
    def getData(self) -> pd.DataFrame:
        return self.data
    
    def saveData(self, filepath):
        self.data.to_excel(filepath, index=False)

    @staticmethod
    def process_raw_data(df: pd.DataFrame) -> pd.DataFrame:
        """
            Performs initial transformations such as columns naming.
        """
        df = df.copy()

        df = df.drop(columns=["Наименование полигона", "Краткое наименование"])

        df = df.rename(columns={
            "Полигон": "polygon",
            "Номерной знак ТС": "id",
            "Наименование структурного подразделения": "subpolygon",
            "Тип закрепления": "stating_type",
            "Выполняемые функции": "functions",
            "Должность за кем закреплен ТС": "pos_assign",
            "дата путевого листа": "date_list",
            "Данные путевых листов, пробег": "mileage_list",
            "Дата сигнала телематики": "date_telematics",
            "Данные телематики, пробег": "mileage_telematics",
            "Штрафы": "penalty",
            "манера вождения": "driving_style"
        })

        df = df.drop(columns=["functions", "pos_assign"])

        return df

    @staticmethod
    def process_data(df: pd.DataFrame) -> pd.DataFrame:
        """
            Constructs clear and useful pandas table. 
        """
        df = df.copy()
        df['leader'] = ~df['polygon'].isna()

        cur_polygon = 0 
        cur_id = 0 
        cur_subpolygon = 0 
        cur_stating_type = 0 
        cur_driving_style = 0

        polygons = list()
        ids = list()
        subpolygons = list()
        stating_types = list()
        driving_styles = list()

        for idx, row in df.iterrows():
            if not pd.isna(row['polygon']):
                cur_polygon = row['polygon']
                cur_id = row['id']
                cur_subpolygon = row['subpolygon']
                cur_stating_type = row['stating_type']
                cur_driving_style = row['driving_style']


            polygons.append(cur_polygon)
            ids.append(cur_id)
            subpolygons.append(cur_subpolygon)
            stating_types.append(cur_stating_type)
            driving_styles.append(cur_driving_style)


        df['polygon'] = polygons
        df['id'] = ids
        df['subpolygon'] = subpolygons
        df['stating_type'] = stating_types
        df['driving_style'] = driving_styles


        df = df[['leader'] + list(df.drop(columns='leader').columns)]

        df = df[~(df.date_list.isna() & df.date_telematics.isna() & (~df.leader))]


        df['penalty'] = df['penalty'].fillna(1.)
        df.loc[df['penalty'] == 0, 'penalty'] = 1.

        return df


class DataPreprocessing:
    """
        Constructs various data representations and collects various statistics. 
    """
    def __init__(self, data: pd.DataFrame) -> None:
        """
            @param data Data comes as output of RawDataPreprocessing class. 
        """
        self.data = data

    @staticmethod 
    def get_polygons_rate(df_group) -> pd.DataFrame:
        """
            Rates massive structures such as polygons or subpolygons.
            @param df_group Data grouped by polygon of subpolygon. 
        """
        rate_polygons = df_group[['mileage_list', 'mileage_telematics', 'penalty']].sum()
        rate_polygons = rate_polygons.join(df_group[['driving_style']].mean())
        rate_polygons = rate_polygons.join(df_group[['driving_style']].count().rename(columns={'driving_style': 'cnt'}))

        rate_polygons['mileage_deviation'] = (1 - (rate_polygons['mileage_list'] / rate_polygons['mileage_telematics'])).abs()
        rate_polygons['mileage_deviation_score'] = 1 / (np.e ** rate_polygons['mileage_deviation'])

        rate_polygons['driving_style_score'] = rate_polygons['driving_style'] / 6

        rate_polygons['penalty_score'] = 1 / (rate_polygons['penalty'] / rate_polygons['cnt'])

        return rate_polygons

    def rate_by_polygons(self) -> pd.DataFrame:
        """
            Rates polygons
        """
        df = self.data
        rate_polygons_group = df[df['leader'] == True].groupby('polygon')
        rate_polygons = self.get_polygons_rate(rate_polygons_group)

        rate_polygons['result_score'] = rate_polygons['mileage_deviation_score'] * 0.57 + rate_polygons['penalty_score'] * 0.21 + rate_polygons['driving_style_score'] * 0.21

        rate_polygons = rate_polygons.reset_index()

        return rate_polygons

    @staticmethod
    def exchangeToSubpolygons(df: pd.DataFrame) -> pd.DataFrame:
        """
                Retrieves subpolygons from data. Final dataframe contains subpolygons, cars in subpolygons, ratio between subpolygon cars and polygon.
        """ 
        init_stract = df[df.leader == True].groupby('polygon')[['polygon']].count().rename(columns={'polygon': 'count_car'})
        init_stract = init_stract.reset_index()
        for elem in df['subpolygon'].unique(): 
            init_stract[elem] = [len(df[(df.leader == True) & (df['subpolygon'] == elem) & (df['polygon'] == i)]) for i in init_stract['polygon'].unique()]

        data_col_stract = {
            'polygon': [],
            'polygon_count': [],
            'subpolygon': [],
            'subpolygon_count': [],
            'res': [],
        }
        for i in init_stract['polygon']:
            tmp = init_stract[init_stract['polygon'] == i]
            tmp = tmp.loc[:, (tmp != 0).any(axis=0)]
            for elem in tmp.columns[2:]:
                data_col_stract['polygon'].append(i)
                data_col_stract['polygon_count'].append(tmp['count_car'].values[0])
                data_col_stract['subpolygon'].append(elem)
                data_col_stract['subpolygon_count'].append(tmp[elem].values[0])
                data_col_stract['res'].append(tmp[elem].values[0] / tmp['count_car'].values[0])

        data_init_stract = pd.DataFrame(data_col_stract)
        data_init_stract = data_init_stract.set_index('subpolygon')

        return data_init_stract

    def rate_by_subpolygons(self) -> pd.DataFrame:
        """
            Rates subpolygons. 
        """
        df = self.data
        rate_subpolygons_group = df[df.leader == True].groupby('subpolygon')
        rate_subpolygons = self.get_polygons_rate(rate_subpolygons_group)
        data_init_stract = self.exchangeToSubpolygons(df)

        rate_subpolygons = rate_subpolygons.join(data_init_stract.rename(columns={'res': 'subpolygon_cars_deviation'})[['subpolygon_cars_deviation']])

        rate_subpolygons['polygon'] = data_init_stract.loc[rate_subpolygons.index]['polygon']

        rate_subpolygons['subpolygon_cars_score'] = rate_subpolygons['subpolygon_cars_deviation']

        rate_subpolygons['result_score'] = rate_subpolygons['mileage_deviation_score'] * 0.4 + rate_subpolygons['subpolygon_cars_score'] * 0.3 + rate_subpolygons['penalty_score'] * 0.15 + rate_subpolygons['driving_style_score'] * 0.15

        rate_subpolygons = rate_subpolygons.reset_index()
        return rate_subpolygons

    @staticmethod
    def collect_groups_by_date(df: pd.DataFrame) -> pd.DataFrame:
        """
            Collects data for polygons by dates. 
        """
        df = df.copy()
        tdf = df[df.leader == False].groupby(['polygon', 'date'])[['penalty', 'mileage_list', 'mileage_telematics']].sum()
        tdf = tdf.join(df[df.leader == False].groupby(['polygon', 'date'])[['driving_style']].mean())

        return tdf

    def stats_by_date(self) -> pd.DataFrame:
        """
            Collects statistics for polygons by date. 
        """
        df = self.data 

        poldatel_gb = self.collect_groups_by_date(df.rename(columns={'date_list': 'date'}))
        poldatet_gb = self.collect_groups_by_date(df.rename(columns={'date_telematics': 'date'}))

        poldate_data = poldatel_gb.join(poldatet_gb, on=['polygon', 'date'], lsuffix='_list', rsuffix='_telematics')

        poldate_data['penalty_error'] = (poldate_data['penalty_list'] - poldate_data['penalty_telematics']) ** 2
        poldate_data['driving_style_error'] = (poldate_data['driving_style_list'] - poldate_data['driving_style_telematics']) ** 2
        poldate_data['mileage_error_list'] = (poldate_data['mileage_list_list'] - poldate_data['mileage_telematics_list']) ** 2
        poldate_data['mileage_error_telematics'] = (poldate_data['mileage_list_telematics'] - poldate_data['mileage_telematics_telematics']) ** 2

        return poldate_data

    def telematics_leaked_stats(self):
        """
            Allows to collect data about abnormals in telematics data (when telematics is None).
            This data allows do determine whether the telematics device is not used or the driver has
            not completed the quest. 

            @return has_telematics, no_telematics. Has telematics dataframe corresponds for drivers
            that had had the telematics device but the it was broken or the driver did not complain
            the quest.
        """
        df = self.data

        # Если в списках дата есть, а в телематике нет - либо сломана телематика, либо никто не поехал на задание
        telematics_leak_state = (df.leader == False) & (df.date_telematics.isna())
        telematics_unleak_state = (df.leader == False) & (~df.date_telematics.isna())
        telematics_leak = df[telematics_leak_state]
        telematics_unleak = df[telematics_unleak_state]


        telematics_leak_group = telematics_leak[['subpolygon', 'id', 'leader', 'penalty']].groupby(['subpolygon', 'id'])
        telematics_leak_idxs = telematics_leak_group[['leader']].count().rename(columns={'leader': 'count'})
        telematics_leak_idxs = telematics_leak_idxs.join(telematics_leak_group[['penalty']].sum())

        telematics_unleak_group = telematics_unleak[['subpolygon', 'id', 'leader', 'penalty']].groupby(['subpolygon', 'id'])
        telematics_unleak_idxs = telematics_unleak_group[['leader']].count().rename(columns={'leader': 'count'})
        telematics_unleak_idxs = telematics_unleak_idxs.join(telematics_unleak_group[['penalty']].sum())

        has_telematics_idxs = np.intersect1d(telematics_leak_idxs.index, telematics_unleak_idxs.index)
        has_telematics = telematics_leak_idxs.loc[has_telematics_idxs].join(telematics_unleak_idxs.loc[has_telematics_idxs], lsuffix='_leaked', rsuffix='_fixed')
        no_telematics = telematics_leak_idxs[~telematics_leak_idxs.index.isin(has_telematics_idxs)]


        adf = df[~df.leader].set_index(['subpolygon', 'id']).loc[has_telematics_idxs].reset_index()
        adf_max_teledate = adf[~adf.date_telematics.isna()].groupby(['subpolygon', 'id'])[['date_list']].max().rename(columns={'date_list': 'max_teledate'})
        adf_min_nateledate = adf[adf.date_telematics.isna()].groupby(['subpolygon', 'id'])[['date_list']].min().rename(columns={'date_list': 'min_nateledate'})

        adf_teledate = adf_max_teledate.join(adf_min_nateledate)


        adf_teledate['probably_broken'] = adf_teledate['max_teledate'] <= adf_teledate['min_nateledate']
        has_telematics = has_telematics.join(adf_teledate)
        has_telematics['penalty_leaked'] -= has_telematics['count_leaked']
        has_telematics['penalty_fixed'] -= has_telematics['count_fixed']

        has_telematics['importance_score'] = has_telematics['count_leaked'] + has_telematics['penalty_leaked']*4 + (~has_telematics['probably_broken']) * 50
        has_telematics = has_telematics.sort_values('importance_score', ascending=False)

        no_telematics = no_telematics.sort_values('count', ascending=False)
        no_telematics['count'] = no_telematics['count'].astype(np.int32)

        return has_telematics, no_telematics

    def car_list_leaked_state(self):
        """
            Allows to collect statistics about abnormals in list data corresponding to telematics data.
            When this situation occures the cars lists has been lost or the driver has used the car
            without the quest (in self interests).
        """
        df = self.data
        # Если данные есть в телематике, но нет в листе, водитель использовал машину в своих интересах или списки были утеряны.
        list_leak_state = (df.leader == False) & (df['date_list'].isna())

        list_leak = df[list_leak_state]
        list_leak_group = list_leak.groupby(['subpolygon', 'id'])

        list_leak_view = list_leak_group[['leader']].count().rename(columns={'leader': 'count'})
        list_leak_view = list_leak_view.join(list_leak_group[['mileage_telematics', 'penalty']].sum())

        list_leak_view = list_leak_view.sort_values('mileage_telematics', ascending=False)

        return list_leak_view

