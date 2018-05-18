#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue May 15 12:04:17 2018

@author: Michal
"""

from pymongo import MongoClient


import numpy as np
import pandas as pd
from sklearn.cross_validation import train_test_split
from sklearn.cross_validation import cross_val_score
from sklearn.grid_search import GridSearchCV
from sklearn.svm import SVC
from sklearn.svm import SVR
from sklearn.metrics import confusion_matrix

client = MongoClient(host='mongodb',port=27017)

db = client.data_science_challenge

clinical_df = pd.DataFrame(list(db.clinical.find()))

radiation_df = pd.DataFrame(list(db.radiation.find()))

slides_df = pd.DataFrame(list(db.slides.find()))

clinical_patients = np.unique(clinical_df['submitter_id'])

radiation_patients = np.unique(radiation_df['bcr_patient_barcode'])

slides_patients = np.unique(slides_df['case_submitter_id'])

unique_patients = [id for id in clinical_patients if id in radiation_patients and id in slides_patients]

unique_patients = unique_patients[1:-1]
    
clinical_df_ordered = pd.DataFrame(np.nan,index=range(len(unique_patients)),columns=clinical_df.columns[1:])
for patient in range(len(unique_patients)):
    clinical_df_ordered.iloc[patient] = clinical_df.loc[clinical_df['submitter_id'] == \
                  unique_patients[patient]].reset_index().drop('index',axis=1).iloc[0,1:]
    
radiation_df_ordered = pd.DataFrame(np.nan,index=range(len(unique_patients)),columns=radiation_df.columns[5:])
for patient in range(len(unique_patients)):
    radiation_df_ordered.iloc[patient] = radiation_df.loc[radiation_df['bcr_patient_barcode'] == \
                  unique_patients[patient]].reset_index().drop('index',axis=1).iloc[0,5:]

slides_df_ordered = pd.DataFrame(np.nan,index=range(len(unique_patients)),columns=slides_df.columns[3:])
for patient in range(len(unique_patients)):
    slides_df_ordered.iloc[patient] = slides_df.loc[slides_df['case_submitter_id'] == \
                  unique_patients[patient]].reset_index().drop('index',axis=1).iloc[0,3:]
    
master_df = pd.DataFrame(np.nan,index = range(len(unique_patients)), columns = ['patient_id'] + 
                         list(clinical_df_ordered.columns) + list(radiation_df_ordered.columns) + \
                         list(slides_df_ordered.columns))

master_df[list(clinical_df_ordered.columns)] = clinical_df_ordered
master_df[list(radiation_df_ordered.columns)] = radiation_df_ordered
master_df[list(slides_df_ordered.columns)] = slides_df_ordered

master_df['patient_id'] = unique_patients

master_df = master_df.replace('[Not Available]',np.nan)
master_df = master_df.replace('[Not Applicable]',np.nan)
master_df = master_df.replace('--',np.nan)
master_df = master_df.replace('not reported',np.nan)
master_df = master_df.replace('[Unknown]',np.nan)
master_df = master_df.replace('[Discrepancy]',np.nan)


days_to_death_or_last_contact = []

for i in range(len(unique_patients)):
    if ~np.isnan(master_df['days_to_death'].iloc[i]):
        days_to_death_or_last_contact.append(master_df['days_to_death'].iloc[i])
    else:
        days_to_death_or_last_contact.append(master_df['days_to_last_follow_up'].iloc[i])
        
days = pd.DataFrame(data=days_to_death_or_last_contact,columns=['days_to_death_or_last_contact'])

master_df = pd.concat([master_df,days],axis=1)
        
master_df = master_df.drop(['days_to_death','days_to_last_contact'],axis=1)

therapy = []

for i in range(len(unique_patients)):
    if 'other' in str(master_df['therapy_regimen'].iloc[i]):
        therapy.append(master_df['therapy_regimen_other'].iloc[i])
    else:
        therapy.append(master_df['therapy_regimen'].iloc[i])
        
therapy_regimen_combined = pd.DataFrame(data=therapy,columns=['therapy_regimen_combined'])
        
master_df = pd.concat([master_df,therapy_regimen_combined],axis=1)

master_df = master_df.drop(['therapy_regimen','therapy_regimen_other'],axis=1)

master_df = master_df.drop(['case_id','days_to_birth','portion_id','form_completion_date','project_id',\
                'portion_submitter_id','radiation_therapy_site','sample_id','sample_submitter_id', \
                'section_location','site_of_resection_or_biopsy','slide_id','slide_submitter_id', \
                'state','year_of_birth', 'year_of_death'],axis=1) # unimportant
        
    
master_df = master_df.T.drop_duplicates().T

for col in master_df.columns[1:]:
     if type(master_df.count()[col]) == np.int64:
         if master_df.count()[col] <= 70:
             master_df = master_df.drop(col,axis=1)
     else:
         master_df = master_df.drop(col,axis=1)
                  
master_df_dummy = pd.DataFrame(index=range(len(unique_patients)))        

for i in range(len(master_df)):
    if master_df['radiation_adjuvant_units'].iloc[i] == 'cGy':
        master_df['radiation_total_dose'].iloc[i] = 0.01*master_df['radiation_total_dose'].iloc[i]
        
master_df = master_df.drop('radiation_adjuvant_units',axis=1) #accounted for

master_df['radiation_therapy_ongoing_indicator'] = master_df['radiation_therapy_ongoing_indicator'].replace(['YES','NO'], \
         ['radiation_therapy_ongoing', 'radiation_therapy_not_ongoing'])

master_df['radiation_therapy_type'] = master_df['radiation_therapy_type'].replace('EXTERNAL BEAM','External')                       

# Days to Years

master_df['age_at_diagnosis'] = master_df['age_at_diagnosis']/365

master_df['years_to_last_follow_up'] = master_df['days_to_last_follow_up']/365
master_df = master_df.drop('days_to_last_follow_up',axis=1)

master_df['years_to_death_or_last_contact'] = master_df['days_to_death_or_last_contact']/365
master_df = master_df.drop('days_to_death_or_last_contact',axis=1)

# Binarize alive/dead for ground truth values of model(s)

master_df['vital_status'] = master_df['vital_status'].replace(['alive','dead'],[1,0])

# Impute missing values

from sklearn.base import TransformerMixin

class DataFrameImputer(TransformerMixin):

    def __init__(self):
        """Impute missing values.

        Columns of dtype object are imputed with the most frequent value 
        in column.

        Columns of other types are imputed with median of column.

        """
    def fit(self, X, y=None):

        self.fill = pd.Series([X[c].value_counts().index[0]
            if X[c].dtype == np.dtype('O') else X[c].median() for c in X],
            index=X.columns)

        return self

    def transform(self, X, y=None):
        return X.fillna(self.fill)
    
    
master_df_imputed = DataFrameImputer().fit_transform(master_df)

# One Hot Encoding

for col in master_df_imputed.columns[1:]:
    if (type(master_df_imputed[col].iloc[0]) == unicode) | (type(master_df_imputed[col].iloc[0]) == str):
        master_df_dummy = pd.concat([master_df_dummy,pd.get_dummies(master_df_imputed[col])],axis=1)
    else:
        master_df_dummy = pd.concat([master_df_dummy,master_df_imputed[col]],axis=1)
  
# Testing that no observation is still encoded in unicode 
        
#for col in range(len(master_df_dummy.columns)):
#    for row in range(len(master_df_dummy)):
#        if type(master_df_dummy.iloc[row,col]) == unicode:
#            print master_df_dummy.iloc[:,col]
        
# Classification -- alive or dead after five years  

X = master_df_dummy.drop(['vital_status','years_to_death_or_last_contact'],axis=1)

y = master_df_dummy['vital_status']

# Split into train/test and eval -- train/test for grid search and eval for test

X_train,X_test,y_train,y_test = train_test_split(X,y,test_size=0.4)

parameters = {'kernel':('linear', 'rbf'), 'C':[0.001,0.01,0.1,1,10]}

clf = GridSearchCV(SVC(), parameters)

clf.fit(X_train,y_train)

clf_new = SVC(C=0.1,kernel='linear')

clf_new.fit(X_train,y_train)

y_pred = clf_new.predict(X_test)

scores = np.zeros((50))

for i in range(50):
   scores[i] = clf_new.score(X_test,y_test)

print(np.mean(scores))

print(confusion_matrix(y_test,y_pred).ravel())

# Dummy classifier for comparison -- accuracy is ~68%

from sklearn.dummy import DummyClassifier

clf_dummy = DummyClassifier(strategy='most_frequent',random_state=0)

dummy_scores = cross_val_score(clf_dummy, X, y, cv=10)

print(np.mean(dummy_scores))

# Regression -- how long from diagnosis until death/last contact
        
X = master_df_dummy.drop(['vital_status','years_to_death_or_last_contact'],axis=1)

y = master_df_dummy['years_to_death_or_last_contact']

# Split into train/test and eval -- train/test for grid search and eval for test

X_train,X_test,y_train,y_test = train_test_split(X,y,test_size=0.4)

parameters = {'kernel':('linear', 'rbf'), 'C':[0.001,0.01,0.1,1,10],'epsilon':[0.001,0.01,0.1,1]}

clf = GridSearchCV(SVR(), parameters)

clf.fit(X_train,y_train)

clf_new_r = SVR(C=0.1,kernel='linear',epsilon=0.01)

clf_new_r.fit(X_train,y_train)

y_pred = clf_new_r.predict(X_test)

X_test.to_csv('X_test.csv')

pd.DataFrame(y_pred,columns=['a']).to_csv('y_pred.csv')

pd.DataFrame(list(y_test),columns=['a']).to_csv('y_true.csv')

r_scores = np.zeros((50))

for i in range(50):
   r_scores[i] = clf_new_r.score(X_test,y_test)

print(np.mean(scores))

import pickle

r = pickle.dumps(clf_new_r)



