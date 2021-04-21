# Machine-Learning-GRACC-Outlier-Detection
	
## General:
	This program will take a look at datapoints from the open science grid such as “wall duration”, “end time”, and “core hours” to determine whether there are any partially failed sites or in other words if there are any outliers detected on any HCC sites. The way this is calculated is through looking at the past year of usage on each VO and comparing it to the last 3 weeks. Only the last 3 weeks is useful because we can’t fix any problems that occurred before that so the data is not very useful. To calculate the outliers, isolation forest is used because it is a quick way to determine them and has the ability to be scalable. We are looking at changes in core hours per VO per site but could add more areas to look at.
	The second part of this application is to send an email to an administrator that will be able to look at the graphs generated from the machine learning in order to see if they can mitigate the problem on HCC sites. This is deployed using Docker and Kubernetes with the goal of the programming running at a specified time every week. 

## TODO:
	Kubernetes Cronjob was running into errors connecting to gracc.opensciencegrid and needs to be looked into. This problem was encountered when using centOS that Derek had set up. Besides this, the file to run the cronjob should be correct, however the secret file will need to be updated with new user email credentials. To run the sendMail.py file, new developer will need to enter their email address and password as well
	For development, some tweaking of the isolation forest algorithm may be required because there were times that an outlier was displayed in a graph when it looked like normal behavior. Lastly, the sendMail.py file needs to create a table of the outliers from the strings that are returned in the printingTuples function in ml.py. 
	Potentially look into adding more ways to determine outliers such as CPU time or even look at changes in user behavior such as did someone suddenly stop submitting jobs, did they submit more jobs, or did they become longer on average. 
	There is a bug where somewhere in the outliers function the dataframe might be getting overwritten and the keys in voname_map are turning into numbers from strings. This was only found by using the colab notebook on Google drive. If you run the cell above the ml class, then it fixes the key value pairs, which is why we think there may be something happening to the dataframe later.


## Metrics Function:
	This function returns a pandas dataframe with the columns of Timestamp, VO, and CoreHours. These are the datapoints that will be used in the ml class and what we are using in order to determine outliers currently.

## Vo_record Function:
	This function creates a VO map from human readable (strings) VO names to numeric ID values. It is used in the next function, outlier. 

## Outlier Function:
	This function will determine outliers from the Vos and CEs through the use of isolation forest. This function is where outliers are calculated, and graphs are produced. To determine outliers, we take our data and split them into a training and testing set and allow isolation forest to go through the data we have provided. It will then determine which ones are outliers based on the fraction we have provided it, in our case .01 or 1%. After determining outliers, we do a reverse mapping on the voname_map in order to get the sites and VOs that are partially failing and we will use that in our email file.

## outlierPicture Function:
  This function takes the matplotlib graph and saves it as a png to then send as an attachment in the email.

## printingTuples Function:
	This function will take the reverse mapping we have done in the outlier function and return it in order to be used in sendMail.py

