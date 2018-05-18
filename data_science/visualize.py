#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu May 17 21:56:01 2018

@author: Michal
"""

import pandas as pd
import matplotlib.pyplot as plt

y_pred = pd.read_csv('y_pred.csv')
y_true = pd.read_csv('y_true.csv')

plt.scatter(range(len(y_true)),y_true.iloc[:,1],  color='black')
plt.plot(range(len(y_pred)), y_pred.iloc[:,1], color='blue', linewidth=3)

plt.xticks()
plt.yticks()

plt.xlabel('Patients (Arranged Randomly)')
plt.ylabel('Years To Death/Last Contact')

plt.legend(['Actual','Predicted'])

plt.show()