# All the imports/libraries needed 
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.font_manager
import elasticsearch
from elasticsearch_dsl import Search, Q, A
import urllib3
import math
import datetime
import sklearn
from pandas.io.json import json_normalize
import pandas as pd
from datetime import timedelta

# Get rid of insecure warning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

es = elasticsearch.Elasticsearch(
        ['https://gracc.opensciencegrid.org/q'],
        timeout=300, use_ssl=True, verify_certs=False)

print("finished elastic")

def metrics():

  osg_summary_index = 'gracc.osg.summary'
  s = Search(using=es, index=osg_summary_index)
  
  end_time = datetime.datetime.now()   # The end time is today
  start_time = end_time - datetime.timedelta(days=365)   # Start day is a year ago from today
  
  s = s.query('bool',
          filter=[
              Q('range', EndTime={'gt': start_time, 'lt': end_time })
            & Q('term', ResourceType='Batch')
          ]
      )

  a = A("terms", field="SiteName", size=(2**31)-1)  
  b = A("terms", field="VOName", size=(2**31)-1) 
  curBucket = s.aggs.bucket("probe_terms", a)
  curBucket = curBucket.bucket("vonames", b)
  curBucket = curBucket.bucket("EndTime", 'date_histogram', field="EndTime", interval="7d")

  bkt = curBucket
  bkt = bkt.metric('WallDuration',       'sum', field='WallDuration', missing = 0)
  bkt = bkt.metric('NumberOfJobs',       'sum', field='Count', missing = 0)
  bkt = bkt.metric('EarliestEndTime',    'min', field='EndTime')
  bkt = bkt.metric('LatestEndTime',      'max', field='EndTime')
  bkt = bkt.metric('CoreHours',          'sum', field='CoreHours', missing = 0)
  response = s.execute() # Creates a bucket with different metrics such as wall duration, core hours, # jobs, etc.

  probes = {}
  for bucket in response.aggregations['probe_terms']['buckets']:
    probes[bucket['key']] = pd.DataFrame(columns=['Timestamp', 'VO', 'CoreHours'])
    for voname in bucket['vonames']['buckets']:
      for endtime in voname['EndTime']['buckets']:
        #print({'Timestamp': endtime['key'], 'VO': voname['key'], 'CoreHours': endtime['CoreHours']['value']})
        probes[bucket['key']] = probes[bucket['key']].append({'Timestamp': endtime['key'], 'VO': voname['key'], 'CoreHours': endtime['CoreHours']['value']}, ignore_index=True)

  print("metrics")

  return probes


all_ces = metrics()

from sklearn.ensemble import IsolationForest  # Need to learn what Isolation Forest does

test_days = 3
plot_num = 1
num_outliers = 0
new_array = []
plt.figure(figsize=(20, 140))
# print(len(probes))

class ml:

  def __init__(self):
    self.voname_map = {}
    

  def vo_record(self, row):
    for record in all_ces[outlier]:  
      if record[1] not in all_ces[voname_map]:
        print(record[1])
        new_id = len(outlier(voname_map))
        voname_map[record[1]] = new_id
      record[1] = voname_map[record[1]]
    return record[1]


  def outlier(self, voname_map):
    num_outliers = 0
    plot_num = 1
    for interested_probe in all_ces:
      current_ce = all_ces[interested_probe]
      # Enumerate the VONames
      voname_map = {}
      for index, row in current_ce.iterrows():
        if row['VO'] not in voname_map:
          new_id = len(voname_map)
          voname_map[row['VO']] = new_id
        current_ce.at[index, 'VO'] = voname_map[row['VO']]
      
      new_array = []
      num_days = len(current_ce)
      
      # Make sure there's enough days to test
      if num_days < (test_days*3):
        continue
        
      # Make sure the last days are within a few days of now
      last_day = datetime.datetime.fromtimestamp(current_ce.tail(1)['Timestamp']/1000)
      if last_day > (datetime.datetime.now() - datetime.timedelta(days=test_days*2)): 
        continue

      # Convert from milliseconds to seconds in the timestamp column
      # I'm sure you can do this with current_ce['Timestamp'] / 1000 or something.
      def convert_datetime(array):
        return datetime.datetime.fromtimestamp(array[0]/1000), array[1], array[2]

      date_array = current_ce.apply(convert_datetime, axis=1, result_type="broadcast")

      for VO in date_array.VO.unique():
        sortedDate = date_array.loc[date_array['VO'] == VO].sort_values(by=['Timestamp'], ascending=True)
        minDate = sortedDate['Timestamp'].iloc[0]
        currentDate = minDate - timedelta(days=7)
        dateList = []

        while currentDate > datetime.datetime.now() - datetime.timedelta(days=365):
          dateList.append([currentDate, VO, 0])
          currentDate -= datetime.timedelta(days=7)

        df = pd.DataFrame(dateList, columns=['Timestamp', 'VO', 'CoreHours'])
        date_array = date_array.append(df)

      date_array = np.array(date_array)
      
      train_array = [] # training array
      test_array = []

      # Sort by VO and Date
      # For each unique VO, find min date, add rows that go back in time 
      # curDate = mindate - timedelta(days=7)
      # while curDate > datetime.datetime.now() - datetime.timedelta(days=365):
      # df.addrow([curDate, <vo>, 0])
      # curDate -= datetime.timedelta(days=7)

      date_array = np.array(date_array)
      sortDate = np.sort(date_array, axis=0)

      # Split the data into test and train
      for row in date_array:
        if row[0] < (datetime.datetime.now() - datetime.timedelta(days=test_days*7)):  
          train_array.append(row)
        else:
          test_array.append(row)

      train_array = np.array(train_array)
      test_array = np.array(test_array)

      # If we don't have enough test days, then ignore this CE
      # This can happen if the CE hasn't been active in a while, ie, no new data.
      # Really, we should extend 0's for all the days we don't have, and it should probably
      # show up as an outlier
      if len(test_array) < test_days:
        continue
      
      outliers_fraction = .01  # Percentage of observations we believe to be outliers
      iso_forest = IsolationForest(contamination=outliers_fraction, random_state=42)
      try:
        y_pred = iso_forest.fit(train_array[:,[1,2]]).predict(test_array[:,[1,2]])
      except:
        print("Failed array:", train_array)
        print("Test array:", test_array)
        raise
        continue
      colors = np.array(['#377eb8', '#ff7f00'])
      outlier = False

      # Converting from the numbers back to the VO names
      inverted_voname_map = dict([[v,k] for k,v in voname_map.items()])
      outlier_vos = []
      for idx, pred in enumerate(y_pred):
        if pred == -1:
          outlier_vo = test_array[idx][1]
          outlier_vos.append(outlier_vo)
          outlier = True
      
      outlier_vos = set(outlier_vos)
      # Add the "outlier" column to the arrays
      train_array = np.append(train_array, np.ones([len(train_array),1], dtype=np.int8),1)
      test_array = np.append(test_array, y_pred[...,None], 1)
      total_array = np.concatenate((train_array, test_array))

      
      for outlier_vo in outlier_vos:
        to_graph = []
        # Create the graphing array
        for row in total_array:
          if int(row[1]) != outlier_vo:
            continue
          to_graph.append(row)
            

        to_graph = np.array(to_graph)
        ax_now = plt.subplot(30, 3, plot_num)

        new_plt = ax_now.bar(to_graph[:, 0].astype("datetime64[ns]"), to_graph[:, 2], width=0.99, color=colors[(to_graph[:, 3].astype(int) + 1) // 2]) # width=3
        plt.title("{} @ {}".format(inverted_voname_map[int(outlier_vo)], interested_probe), size=18)
        months = mdates.MonthLocator()  # every month
        monthsFmt = mdates.DateFormatter('%b')
        ax_now.xaxis.set_major_locator(months)
        ax_now.xaxis.set_major_formatter(monthsFmt)
        plt.ylabel("Weekly Core Hours")

        plot_num += 1
        num_outliers += 1

  def outlierPicture(self, fileName):
    plt.savefig(fileName, bbox_inches='tight', dpi=100)

# ml = ml()
# ml.outlier(None)

  