# -*- coding: utf-8 -*-
"""Dengue-Group-AA.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1XxpxZztDM3gxeETlf3LIsptEnTyFueF-

#  DengAI: Predicting Disease Spread

Dengue fever is a mosquito-borne disease that occurs in tropical and sub-tropical parts of the world. In this notebook we are going to try to analize the data of the competition of prediction of the data of the Dengue. 
You can get more information from de dataset and the problem in [link](https://www.drivendata.org/competitions/44/dengai-predicting-disease-spread/)

This notebook has been made by:

1.   Agustín Mora Acosta
2.   Andrés González Díaz

# Setting Preliminares

Prior to starting any analysis, it is necessary to ensure that the basic and general purpose libraries (numpy, pandas, etc.) the we are going to use, are correctly imported.
"""

# Data load and manipulation
from google.colab import files
import io

# DataFrame librery
import pandas as pd

# Visualization 
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from tabulate import tabulate

# Basic Operations
import numpy as np
import itertools
from numpy import corrcoef, transpose, arange
from pylab import pcolor, show, colorbar, xticks, yticks

# Prepocessing
from sklearn import preprocessing 
from sklearn.impute import KNNImputer

# Models
from sklearn import metrics
from sklearn.cluster import KMeans
from scipy import cluster
from sklearn.decomposition import PCA
from sklearn import neighbors
from sklearn.cluster import DBSCAN

"""# Data Loading

First of all we load the data into the environment with the functionalities that Google Colab allows us.
"""

def upload_files (index_fields):
  uploaded = files.upload()
  for fn in uploaded.keys():
    print('User uploaded file "{name}" with length {length} bytes'.format(
        name=fn, length=len(uploaded[fn])))
    df = pd.read_csv(io.StringIO(uploaded[fn].decode('utf-8')), index_col = index_fields)
    return df

"""The first thing we do is upload the training data without a target field (dengue_features_train). Using pandas library you can explore the data, to set filters and grouping operations."""

train = upload_files(['city', 'weekofyear', 'year'])
train.head()

train.shape

"""# Preprocessing


Here would go all the functions and transformations that are going to allow the future application of machine learning algorithms, for example the transformation of categorical variables into numerical ones, etc. 
We must be careful in that step to remove redundancy and treat the lost values in the dataset. If we dont do ir properly oir work will be hard in the future, thats is the reason to think all options like how treat the lost values.
"""

train.drop("week_start_date", axis = 1, inplace = True)
train.head()

"""We are going to see if exist some lost value."""

pd.isnull(train).any()

"""We can process them automatically by completing them with the ffill method (with the previous value). If the data is organized chronologically it can be a very fast and useful method. But this time we have chosen to calculate the mean among the five nearest values."""

imputer = KNNImputer(n_neighbors=5)
train[:] = imputer.fit_transform(train)

pd.isnull(train).any()

"""# Filtering

We move on to the filtering stage where we will reduce the datasets to the records with city of origin "San Juan", localizated in the dataset like 'sj'. And the records between 1990 and 1996
"""

train_sj = train.loc['sj']

index_list = []
for i in train_sj.index:
  (_, y) = i
  if y >= 1990 and y <=1996:
    index_list.append(i)
train_filtered = train_sj.loc[index_list]
train_filtered

"""# Dimensionality Reduction

First of all, we are going to extract the correlation among features, to obtain some conclusions. That we make with corrcoef method.
"""

df_features = transpose(train_filtered)
names = df_features.index.values
df_features.head()

correlation = corrcoef(df_features)

# Generate a mask for the upper triangle
sns.set(style="white")
mask = np.zeros_like(correlation, dtype=np.bool)
mask[np.triu_indices_from(mask)] = True

# Set up the matplotlib figure
f, ax = plt.subplots(figsize=(11, 9))

# Generate a custom diverging colormap
cmap = sns.diverging_palette(200, 10, as_cmap=True)

# Draw the heatmap with the mask and correct aspect ratio
sns.heatmap(correlation, mask=mask, cmap=cmap, vmax=.8,
            square=True, xticklabels=names, yticklabels=names,
            linewidths=.5, cbar_kws={"shrink": .5}, ax=ax)

"""We've obtained the following conclusions from the features analysis:
- The features nvdi_ne, nvdi_nw, nvdi_se, nvdi_sw are slightly correlated between them, but they are not correlated to any other feature. Maybe this features could be reduced in one feature.
-  The features from the reanalysis related to temperature, are strongly correlated between them, and also strongly correlated with other features as station temperature features (station_min_temp_c, station_max_temp_c...) and reanalysis_specific_humidity_g_per_kg.
- The features related to precipitation are highly correlated (precipitation_amt_mm, reanalysis_sat_precip_amt_mm and station_precip_mm)
- The relative humidity percent is inversely correlated with the thermal amplitude (reanalysis_tdtr_k) and the diurn temperature range (station_diur_temp_rng_c).

Normalize data, and execute PCA procedure to reduce dimensionality of the data.
"""

scaler = preprocessing.MinMaxScaler()
dengue_train = scaler.fit_transform(train_filtered)

pca = PCA ()
X_pca = pca.fit_transform(dengue_train)
X_pca.shape

"""We show the percentage of variance explained by each of the selected components."""

exp_var_cumul = np.cumsum(pca.explained_variance_ratio_)

px.area(
    x=range(1, exp_var_cumul.shape[0] + 1),
    y=exp_var_cumul,
    labels={"x": "# Components", "y": "Explained Variance"})

"""We decided to use 3 components to reduce the dimensionality of the data, so we can plot it in a 3D Scatter. This way, we keep almost the 80% of explained variance of the data ."""

pd.DataFrame(np.matrix.transpose(pca.components_[:3, :]), columns=['PC-1', 'PC-2', 'PC-3'], index=train_filtered.columns)

"""The first component (PC-1) is linearly related with te following features:
  - reanalysis_air_temp_k
  - reanalysis_avg_temp_k
  - reanalysis_dew_point_temp_k
  - reanalysis_max_air_temp_k
  - reanalysis_min_air_temp_k
  - reanalysis_specific_humidity_g_per_kg
  - station_avg_temp_c
  - station_max_temp_c
  - station_min_temp_c

We can say that this component is generally related to the temperature and humidity.

The second component (PC-2) is linearly related with te following features:
  - precipitation_amt_mm
  - reanalysis_relative_humidity_percent
  - reanalysis_sat_precip_amt_mm
  - reanalysis_tdtr_k

We can say that this component is more related to the precipitation, relative humidity and thermal amplitude, but is slightly linearly related with almost al of the features.

The third component (PC-3) is linearly related with te following features:
  - ndvi_ne
  - ndvi_nw
  - ndvi_se
  - ndvi_sw
  - precipitation_amt_mm

We can say that this component is highly related to the vegetation features, but also is related to the precipitation in mm.

We plot the results.
"""

fig = px.scatter_3d(
    X_pca[:, :3], x=0, y=1, z=2,
    title='Data Visualization by PCA with 3 components',
    labels = {'0':'PCA-1', '1':'PCA-2','2':'PCA-3'}
)
fig.show()

"""# Outlier Identification

We compute the similarity matrix of the data, and we plot it. We saw that it looked like a chess board, this can be because the weeks are more similar to weeks from the same month/station of other year, than from weeks from the same year but different month/station. This really have sense, and makes a beautiful pattern on the matrix.
"""

# We define euclidean distance as metric for compute the matrix
distance = neighbors.DistanceMetric.get_metric('euclidean')
similarity_matrix = distance.pairwise(dengue_train)

# Plot the matrix
fig = px.imshow(similarity_matrix)
fig.show()

"""Once we got the similarity matrix, we use DBSCAN to classify the data and identify the outliers. For the parameterization, due to the lack of an expert in the domain, we used the ln(n) heuristic approachOn to set the minPts of the algorithm, where n is the total number of points to be clustered (347 in our case). 

Then, we compute the distance from each point to its neighbors and plot the sorted distance of every point to its kth nearest neighbor, in order to obtain the epsilon parameter for the DBSCAN algorithm.
"""

# We set minPts to ln(347) (Aprox. 6)
minPts=6

# We compute the distance from each point to its neighbors
dist_to_neighbor = neighbors.kneighbors_graph(dengue_train, minPts, include_self=False)
distneigh_array = dist_to_neighbor.toarray()

# We sort the distance of every point to its kth nearest neighbor
seq = []
for i,s in enumerate(dengue_train):
    for j in range(len(dengue_train)):
        if distneigh_array[i][j] != 0:
            seq.append(similarity_matrix[i][j])
            
seq.sort()

# Plot 
fig = px.line(x=np.arange(0, len(seq), 1), y=seq)
fig.show()

"""We choose to try different clusters from 0.5 to 0.8 with intervals of 0.5."""

results = []

# Try different clusters with different eps parameter
for eps in np.arange(0.5, 0.8, 0.05):
  db = DBSCAN(eps, min_samples=minPts).fit(dengue_train)

  core_samples_mask = np.zeros_like(db.labels_, dtype=bool)
  core_samples_mask[db.core_sample_indices_] = True
  labels = db.labels_
  n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
  n_outliers = list(labels).count(-1)
  results.append([eps, n_clusters_, n_outliers])

# We print the results
print(tabulate(results, headers = ("eps", "clusters", "outliers")))

"""We are going to keep the settings that offer a balanced numbre between outliers and groups, so we use 0.65 as eps parameter for the DBSCAN algorithm."""

db = DBSCAN(eps=0.65, min_samples=minPts).fit(dengue_train)
labels = db.labels_
labels

"""Once we identify outliers, we plot it on a 3D scatter."""

fig = px.scatter_3d(
    X_pca[:, :3], x=0, y=1, z=2,
    color=labels,
    title='Outlier Identification on PCA with 3 components',
    labels = {'0':'PCA-1', '1':'PCA-2','2':'PCA-3'}
)
fig.show()

"""After identify the outliers, we analyze thy these elements are outliers in order to decide whether or not consider them for further analysis."""

# Show data describe for analyzing the outliers
train_filtered.describe()

# Add a new column to the data 
train_filtered['dbscan_group'] = labels

# Show outliers
train_filtered[train_filtered['dbscan_group'] == -1]

"""We can say the following about each outlier:

- **weekofyear:21 year:1992** - Low satellite vegetation (ndvi_ne, ndvi_nw, ndvi_se, ndvi_sw), with a high total precipitation (precipitation_amt_mm), with a extreme total precipitation reanalysis (reanalysis_precip_amt_kg_per_m2) and a high relative humidity reanalysis (reanalysis_relative_humidity_percent). 

This outlier could be considered outlier because the extreme value in reanalysis_precip_amt_kg_per_m2, which seems like an error in the data because this value does not correspond to the precipitation in mm in the precipitation_amt_mm field.

- **weekofyear:53 year:1993** - Very high maximum air temperature (reanalysis_max_air_temp_k) and low minimum air temperature (reanalysis_min_air_temp_k), with a high relative humidity reanalysis (reanalysis_relative_humidity_percent) and a extreme diurnal temperature range (reanalysis_tdtr_k).

This outlier seems like a week with a great thermal amplitude, but looks factible so well consider this data for further analysis.

- **weekofyear:21 year:1995** - Very high total precipitation reanalysis (precipitation_amt_mm), with a low total precipitation k/m2 reanalysis(reanalysis_precip_amt_kg_per_m2), with a high total precipitation mm reanalysis(reanalysis_sat_precip_amt_mm) and a high total precipitation station measurements (station_precip_mm).

This outlier could be considered outlier because a high value on precipitation_amt_mm and reanalysis_sat_precip_amt_mm but a low value on reanalysis_precip_amt_kg_per_m2. This could be an error in the data so we dont consider this data for further analysis.

- **weekofyear:38 year:1996** - Extreme total precipitation (precipitation_amt_mm), with a high precipitation kg/m2 reanalysis(reanalysis_precip_amt_kg_per_m2), with high relative humidity reanalysis(reanalysis_relative_humidity_percent), with a very high humidity g/kg reanalysis (reanalysis_specific_humidity_g_per_kg), an extreme total precipitation reanalysis (reanalysis_sat_precip_amt_mm) and a (Total precipitation)

This data looks like an extreme rainy week, so we wont consider this data because it can distort data while aplying another clustering algorithm like Hierarchical Clustering Algorithm.
"""

# Remove from data outliers considered

train_filtered = train_filtered.drop([(21, 1992), (21, 1995), (38, 1996)], axis = 0)
train_filtered

# We recompute PCA for this new data
scaler = preprocessing.MinMaxScaler()
dengue_train = scaler.fit_transform(train_filtered)

pca = PCA ()
X_pca = pca.fit_transform(dengue_train)
X_pca.shape

"""# Clustering by K-means

The k-means algorithm is based on the idea that a central point can represent a cluster, this point is called centroid. 

Usually this point is the mean or median of a group of points and therefore may not be an element of the set to be analyzed. 

The algorithm
k-means sets a distance between the elements by selecting a predefined number of centroids.

K-means uses these pre-selected centroids as "seeds" in the process of building the clusters. To do so, a cluster is assigned to each centroid, in an iterative process. The cluster assigned to each centroid is the "closest" to it, and the distance is measured between the element to be
included and the average value for all clusters. 

the objective of the k-means algorithm process is to minimize an error or distance function by example, the sum of squared errors.

### Parametrization

In this case we will also choose to cluster on the data projected by PCA.
"""

# parameters
init = 'random' # initialization method 

# to run 20 times with different random centroids 
# to choose the final model as the one with the lowest SSE
iterations = 10

# maximum number of iterations for each single run
max_iter = 300 

# controls the tolerance with regard to the changes in the 
# within-cluster sum-squared-error to declare convergence

tol = 1e-04 

 # random seed
random_state = 0

"""We are going to choose n depending on the values that the clustering takes in terms of Distortion from n = 2 to n = 11."""

distortions = []
silhouettes = []

for i in range(2, 13):
    km = KMeans(i, init, n_init = iterations ,max_iter= max_iter, tol = tol,random_state = random_state)
    labels = km.fit_predict(X_pca)
    distortions.append(km.inertia_)
    silhouettes.append(metrics.silhouette_score(X_pca, labels))

"""We have to choose approximately the higher Silouehette with the lower Distortion."""

x = [i for i in range(2,13)]
fig, ax1 = plt.subplots()

color = 'tab:red'
ax1.set_xlabel('k')
ax1.set_ylabel('sse', color=color)
ax1.plot(x, distortions, color=color)
ax1.tick_params(axis='y', labelcolor=color)

ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

color = 'tab:blue'
ax2.set_ylabel('silhouette', color=color)  # we already handled the x-label with ax1
ax2.plot(x, silhouettes, color=color)
ax2.tick_params(axis='y', labelcolor=color)

fig.tight_layout()  # otherwise the right y-label is slightly clipped
plt.show()

#@title Number of clusters {run: "auto"}
k = 3 #@param { type: "slider", min: 2, max: 7, step: 1}

print ("Number of clusters", k)
km = KMeans(k, init, n_init = iterations ,
            max_iter= max_iter, tol = tol, random_state = random_state)

y_km = km.fit_predict(X_pca)

# Commented out IPython magic to ensure Python compatibility.
from sklearn import metrics
print("Silhouette Coefficient: %0.3f"
#       % metrics.silhouette_score(X_pca, y_km))
      
print('Distortion: %.2f' % km.inertia_)

"""The final values of the algorithm metrics and the visualization from the results(assigned group)."""

km.labels_

"""And plot the results using the PCA data"""

fig = px.scatter_3d(
    X_pca[:, :3], x=0, y=1, z=2,
    color = km.labels_,
    title='Label Visualization of k-Means Clustering result',
    labels = {'0':'PCA-1', '1':'PCA-2','2':'PCA-3'}
)
fig.show()

train_filtered['group'] = km.labels_
train_filtered

"""After visualization, we should make some representation of the data to assign a label to each group, based on the characteristics of each."""

res = train_filtered[['ndvi_ne', 'ndvi_nw', 'ndvi_se', 'ndvi_sw', 'group']].groupby('group').mean()
res.plot(kind='bar', legend=True)
res

res = train_filtered[['station_precip_mm', 'precipitation_amt_mm', 'reanalysis_precip_amt_kg_per_m2','reanalysis_sat_precip_amt_mm', 'group']].groupby('group').mean()
res.plot(kind='bar', legend=True)
res

res = train_filtered[['station_avg_temp_c', 'station_max_temp_c',	'station_min_temp_c',	'group']].groupby('group').mean()
res.plot(kind='bar', legend=True)
res

"""We assigned the following descriptions/labels to the different groups:

- **Group 0 - Low_Precipitation_Temperatures_SlightlyBelow**: Low precipitation and temperatures slightly below average.
- **Group 1 - Standard_Precipitation_Temperatures_Above**: Temperatures above average and standard precipitation. 
- **Group 2 - High_Precipitation_Vegetation_SlightlyBelow**: High precipitation, relative humidity and northwest's vegetation slightly below average.
"""

def get_group_label(g):
  if g == 1:
    return "Standard_Precipitation_Temperatures_Above"
  elif g == 2:
    return "High_Precipitation_Vegetation_SlightlyBelow"
  else :
    return "Low_Precipitation_Temperatures_SlightlyBelow"

train_filtered['group_label'] = train_filtered['group'].apply(lambda x: get_group_label(x))

fig = px.scatter_3d(
    X_pca[:, :3], x=0, y=1, z=2,
    color = train_filtered['group_label'],
    title='Label Visualization of k-Means Clustering result',
    labels = {'0':'PCA-1', '1':'PCA-2','2':'PCA-3'}
)
fig.show()

"""# Hierarchical Clustering Algorithm

To execute the hierarchical clustering algorithm, we need to compute the similarity matrix. This similarity matrix has been computed previously in 'Outlier identification' section, but we recompute it with the outliers removed from data.
"""

# We define euclidean distance as metric for compute the matrix
distance = neighbors.DistanceMetric.get_metric('euclidean')
similarity_matrix = distance.pairwise(dengue_train)

fig = px.imshow(similarity_matrix)
fig.show()

"""We executed the hierarchical clustering algorithm, testing different cluster_distances_measures and plotting the resulting dendrogram. 

In our opinion, the best solution is to use complete as linkage criterion as we got concentrated data and this criterion allow us to break up big groups. Using this linkage criterion we get a more balanced dendrogram with 2 small groups.
"""

cut = 13

clusters = cluster.hierarchy.linkage(similarity_matrix, method = 'complete')
dendogram = cluster.hierarchy.dendrogram(clusters, color_threshold=cut)

f = plt.figure()
plt.show()

"""We've decided to cut this dendrogram by 13, so we get a total of 5 groups, 3 big groups and 2 small groups."""

hier_clustering_labels = cluster.hierarchy.fcluster(clusters, cut , criterion = 'distance')

hier_clustering_labels

"""We can assess the quality of the clustering result using the silohouette coefficien. In this case, this result is not very good, maybe because data is concentrated."""

n_clusters_ = len(set(hier_clustering_labels)) - (1 if -1 in hier_clustering_labels else 0)
print('Estimated number of clusters: %d' % n_clusters_)
print("Silhouette Coefficient: %0.3f" % metrics.silhouette_score(dengue_train, hier_clustering_labels))

fig = px.scatter_3d(
    X_pca[:, :3], x=0, y=1, z=2,
    color = hier_clustering_labels,
    title='Data Visualization by PCA with 3 components',
    labels = {'0':'PCA-1', '1':'PCA-2','2':'PCA-3'}
)
fig.show()

"""Now we've got the best dendrogram/cut in our opinion, we have to characterize the obtained groups. 

For this, we have some representation of the data, which will allow us to assign a label to each group, based on the characteristics of each.
"""

# Assign clustering labels to data
train_filtered['group'] = hier_clustering_labels

train_filtered.describe()

res = train_filtered[['ndvi_ne', 'ndvi_nw', 'ndvi_se', 'ndvi_sw', 'group']].groupby('group').mean()
res.plot(kind='bar', legend=True, ylim = [0.075,0.210])

res = train_filtered[['reanalysis_air_temp_k', 'reanalysis_avg_temp_k', 'reanalysis_dew_point_temp_k', 'reanalysis_max_air_temp_k', 'reanalysis_min_air_temp_k', 'station_avg_temp_c', 'group']].groupby('group').mean()
res

res = train_filtered[['reanalysis_air_temp_k', 'reanalysis_avg_temp_k', 'reanalysis_dew_point_temp_k', 'reanalysis_max_air_temp_k', 'reanalysis_min_air_temp_k', 'group']].groupby('group').mean()
res.plot(kind='bar', legend=True, ylim = [290,305])

res = train_filtered[['precipitation_amt_mm', 'reanalysis_precip_amt_kg_per_m2', 'reanalysis_sat_precip_amt_mm', 'station_precip_mm', 'group']].groupby('group').mean()
res.plot(kind='bar', legend=True)

res = train_filtered[['reanalysis_relative_humidity_percent', 'group']].groupby('group').mean()
res.plot(kind='bar', legend=True, ylim=[70, 90])

res = train_filtered[['reanalysis_tdtr_k', 'group']].groupby('group').mean()
res.plot(kind='bar', legend=True)

"""We assigned the following descriptions/labels to the different groups:

- **Group 1 - Low_Precipitation_Temperatures_Below**: Vegetation on the west above average, very low precipitation and temperatures below average.
- **Group 2 - Standard_Precipitation_Temperatures_Above**: Temperatures above average and standard precipitation. 
- **Group 3 - Standard_Precipitation_Temperatures_ThermalAmplitude_Below**: Vegetation and thermal amplitude below average and standard precipitation/temperature.
- **Group 4 - High_Precipitation_RelativeHumidity**: High precipitation and high relative humidity.
- **Group 5 - Low_Precipitation_RelativeHumidity_Below**: Low precipitation and relative humidity below average.
"""

def get_group_label(g):
  if g == 1:
    return "Low_Precipitation_Temperatures_Below"
  elif g == 2:
    return "Standard_Precipitation_Temperatures_Above"
  elif g == 3:
    return "Standard_Precipitation_Temperatures_ThermalAmplitude_Below"
  elif g == 4:
    return "High_Precipitation_RelativeHumidity"
  else:
    return "Low_Precipitation_RelativeHumidity_Below"

train_filtered['group_label'] = train_filtered['group'].apply(lambda x: get_group_label(x))

"""Plot the graphical result of the clustering, with the labels assigned to the groups."""

fig = px.scatter_3d(
    X_pca[:, :3], x=0, y=1, z=2,
    color = train_filtered['group_label'],
    title='Label Visualization of Hierarchical Clustering result',
    labels = {'0':'PCA-1', '1':'PCA-2','2':'PCA-3'}
)
fig.show()