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
import pandas as pd

# Get rid of insecure warning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


es = elasticsearch.Elasticsearch(
        ['https://gracc.opensciencegrid.org/q'],
        timeout=300, use_ssl=True, verify_certs=False)

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
  response = s.execute() # Creates a bucket with different metrics such as wall duration, core hours, # of jobs, etc.

  probes = {}
  for bucket in response.aggregations['probe_terms']['buckets']:
    probes[bucket['key']] = pd.DataFrame(columns=['Timestamp', 'VO', 'CoreHours'])
    for voname in bucket['vonames']['buckets']:
      for endtime in voname['EndTime']['buckets']:
        #print({'Timestamp': endtime['key'], 'VO': voname['key'], 'CoreHours': endtime['CoreHours']['value']})
        probes[bucket['key']] = probes[bucket['key']].append({'Timestamp': endtime['key'], 'VO': voname['key'], 'CoreHours': endtime['CoreHours']['value']}, ignore_index=True)

  return probes

all_ces = metrics()

from sklearn.ensemble import IsolationForest

test_days = 3
plot_num = 1
num_outliers = 0
new_array = []
plt.figure(figsize=(500, 1250))

class ml:

  def __init__(self):
    self.voname_map = {}
    self.correctTuple = ()
    self.resultString = []

  def vo_record(self, current_ce):
    """
    This creates a VO map from human readable VO names to numeric ID values
    :param DataFrame current_ce: Dataframe of a CE’s usage with all VOs
    """
    for index, val in current_ce.iterrows():
      if val['VO'] not in self.voname_map:
        new_id = len(self.voname_map)
        self.voname_map[val['VO']] = new_id
      current_ce.at[index, 'VO'] = self.voname_map[val['VO']]


  def outlier(self, voname_map):
    """
    This will determine outliers from the VOs and CEs through the use of isolation forest
    :param Map voname_map: mapping of ce and vo
    """

    num_outliers = 0
    plot_num = 1
    for interested_probe in all_ces:
      current_ce = all_ces[interested_probe]
      # Enumerate the VONames
      self.vo_record(current_ce)
      
      num_days = len(current_ce)
      
      # Make sure there's enough days to test
      if num_days < (test_days*3):
        continue
        
      # Make sure the last days are within a few days of now
      last_day = datetime.datetime.fromtimestamp(current_ce.tail(1)['Timestamp']/1000)
      if last_day > (datetime.datetime.now() - datetime.timedelta(days=test_days*2)): # <--- Fix this line, I forget what it was before, all_ces needs to indexed into
        continue
      
      # Only use the columns 1 and 2
      #new_array = np.array(current_ce)
      
      #print(probes[interested_probe])   # What are these values supposed to represent?
      #for z in probes[interested_probe]:
      #  new_array.append([z[2], z[2]])
      #date_array = np.array(probes[interested_probe])
      date_array = np.array(current_ce)
      
      
      # Convert from milliseconds to seconds in the timestamp column
      # I'm sure you can do this with current_ce['Timestamp'] / 1000 or something.
      def convert_datetime(array):
        return np.array([datetime.datetime.fromtimestamp(array[0]/1000), array[1], array[2]])
              
      date_array = np.apply_along_axis(convert_datetime, 1, date_array)
      
      np_array = [] # training array
      test_array = []
      # Split the data into test and train
      for row in date_array:
        if row[0] < (datetime.datetime.now() - datetime.timedelta(days=test_days*7)):  
          np_array.append(row)
        else:
          test_array.append(row)  
      np_array = np.array(np_array)
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
        y_pred = iso_forest.fit(np_array[:][:,[1,2]]).predict(test_array[:][:,[1,2]])
      except:
        print("Failed array:", np_array)
        print("Test array:", test_array)
        raise
        continue
      colors = np.array(['#377eb8', '#ff7f00'])
      outlier = False

      # Converting from the numbers back to the VO names
      inverted_voname_map = dict([[v,k] for k,v in self.voname_map.items()])
      outlier_vos = []
      for idx, pred in enumerate(y_pred):
        if pred == -1:
          outlier_vo = test_array[idx][1]
          outlier_vos.append(outlier_vo)
          outlier = True

      # This will take only unique VO names and put them in an array
      uniqueOutlierVOs = []
      for x in outlier_vos:
        if x not in uniqueOutlierVOs:
          uniqueOutlierVOs.append(x)

      probeVoTuple = (interested_probe, uniqueOutlierVOs)

      # Reverse mapping of numbers to VO Names
      numToVO = {v: k for k, v in self.voname_map.items()}
      correctVOs = []
      for num in probeVoTuple[1]:
        if num in numToVO:
          # print(numToVO[num])
          correctVOs.append(numToVO[num])

      self.correctTuple = (interested_probe, correctVOs)

      # This will create a string of the correct site and vo
      for index, val in enumerate(self.correctTuple[1]):
        if self.correctTuple[1]:
          self.resultString.append(val + " @ " + self.correctTuple[0])
      
      outlier_vos = set(outlier_vos)
      # Add the "outlier" column to the arrays
      np_array = np.append(np_array, np.ones([len(np_array),1], dtype=np.int8),1)
      test_array = np.append(test_array, y_pred[...,None], 1)
      total_array = np.concatenate((np_array, test_array))
      
      for outlier_vo in outlier_vos:

        to_graph = []
        # Create the graphing array
        for row in total_array:
          if int(row[1]) != outlier_vo:
            #print(row[1], outlier_vo)
            continue
          to_graph.append(row)
            

        to_graph = np.array(to_graph)
        #print(to_graph.shape)
        ax_now = plt.subplot(30, 3, plot_num)
        #print(to_graph[:, 2])

        #new_plt = ax_now.scatter(date_array[:, 0].astype("datetime64[ns]"), date_array[:, 2])# , s=10, color=colors[(to_graph[:, 3].astype(int) + 1) // 2])
        new_plt = ax_now.bar(to_graph[:, 0].astype("datetime64[ns]"), to_graph[:, 2], width=0.99, color=colors[(to_graph[:, 3].astype(int) + 1) // 2]) # width=3
        #outliers = to_graph.loc[to_graph[3] == 1]
        #print(outliers)
        plt.title("{} @ {}".format(inverted_voname_map[int(outlier_vo)], interested_probe), size=18)
        #ax_now.text(.99, .01, "Outlier",
        #               transform=plt.gca().transAxes, size=15,
        #               horizontalalignment='right')
        months = mdates.MonthLocator()  # every month
        monthsFmt = mdates.DateFormatter('%b')
        ax_now.xaxis.set_major_locator(months)
        ax_now.xaxis.set_major_formatter(monthsFmt)
        plt.ylabel("Weekly Core Hours")

        plot_num += 1
        num_outliers += 1
        
        #return voname_map

      #print(num_outliers)

  def printingTuples(self):
    return self.resultString