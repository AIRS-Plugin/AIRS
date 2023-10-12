# -*- coding: utf-8 -*-
"""
/***************************************************************************
 AIRSDockWidget
                                 A QGIS plugin
 This plugin allows time series forecasting using deep learning models.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2023-10-04
        git sha              : $Format:%H$
        copyright            : (C) 2023 by H. Naciri; N. Ben Achhab; F.E. Ezzaher; N. Raissouni
        email                : airs.qgis@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
import sys
import struct
from osgeo import gdal
from osgeo import ogr 
from osgeo import osr
from functools import partial
import operator

from qgis.PyQt import QtGui, QtWidgets, uic, QtCore
from qgis.PyQt.QtGui import QDesktopServices
from qgis.PyQt.QtCore import pyqtSignal, Qt, pyqtSlot, QUrl
from qgis.PyQt.QtWidgets import QApplication, QFileDialog, QTreeWidgetItem, QTabWidget, QWidget, QDialog, QAbstractButton, QProgressBar, QButtonGroup, QMessageBox, QVBoxLayout, QHBoxLayout, QSizePolicy, QTableWidget, QTableWidgetItem, QCheckBox
from qgis.core import QgsRasterLayer,QgsProject,QgsProcessing, Qgis
from qgis.analysis import QgsRasterCalculator, QgsRasterCalculatorEntry
from qgis.utils import iface
import processing
import time

import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error, mean_absolute_percentage_error
import math
import io
import html2text
# from IPython.display import HTML

from tensorflow import keras
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from keras.layers import Flatten
from keras.layers import ConvLSTM2D
from keras.layers import Bidirectional

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'artificial_intelligence_forecasting_remote_sensing_dockwidget_base.ui'))

FORM_CLASS2, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'Dialog.ui'))
    
FORM_CLASS3, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'About.ui'))

# FORM_CLASS4, _ = uic.loadUiType(os.path.join(
    # os.path.dirname(__file__), 'Helpfile.ui'))
    
# class Help(QDialog, FORM_CLASS4):
    # def __init__ (self, parent=None):
        # super(Help, self).__init__(parent)
        # self.setupUi(self)   

class About(QDialog, FORM_CLASS3):
    def __init__ (self, parent=None):
        super(About, self).__init__(parent)
        self.setupUi(self)         
        self.pb_closeabout.clicked.connect(self.Close_About)
    def Close_About(self):
        self.close()
  
class Dialog(QDialog, FORM_CLASS2):

    closingPlugin = pyqtSignal()
    def __init__(self, parent=None):
        """Constructor."""
        super(Dialog, self).__init__(parent)
        self.setupUi(self) 
        self.test=AIRSDockWidget()
        
        # setting  the fixed height and width of window
        # self.setFixedHeight(1200)
        # self.setFixedWidth(1200)
        
        self.pb_saveResults.clicked.connect(self.save)
        self.pb_cancel.clicked.connect(self.dialog_close)
        self.pb_next.clicked.connect(self.next_tab)
        self.pb_prev.clicked.connect(self.previous_tab)
        #Set the tooltip for the save button
        self.pb_saveResults.setToolTip('save results')
        self.pb_cancel.setToolTip('close')

        # label : Title
        self.L_title.setText("Forecasting using " + model_name + " model")
        
        # Load existing QTabWidget created in Qt Designer
        self.tab_widget = self.findChild(QTabWidget, "tabWidget")

        # Find the QWidgets within the tab_widget
        tab_model_summary_widget = self.tab_widget.findChild(QWidget, "tab_1")
        tab_train_test_graphs_widget = self.tab_widget.findChild(QWidget, "tab_2")
        tab_prediction_graph_widget = self.tab_widget.findChild(QWidget, "tab_3")
        tab_accuracy_widget = self.tab_widget.findChild(QWidget, "tab_4")

        # Access the layouts within tabs widget
        self.model_layout = tab_model_summary_widget.findChild(QVBoxLayout, "modelLayout")
        self.plot_layout_1 = tab_train_test_graphs_widget.findChild(QHBoxLayout, "plotLayout_1")
        self.plot_layout_2 = tab_prediction_graph_widget.findChild(QVBoxLayout, "plotLayout_2")
        self.accuracy_layout = tab_accuracy_widget.findChild(QVBoxLayout, "accLayout")
        
        # Model Summary
        ## Canvas Here
        self.figure_1 = plt.figure()
        # self.figure_1.set_aspect('auto')
        self.canvas_1 = FigureCanvas(self.figure_1)
        self.canvas_1.setFixedSize(1400, 400)
        ## Add canvas to frame
        self.model_layout.addWidget(self.canvas_1)
        ## clear the canvas
        self.figure_1.clear()
        ## create the plot
        plt.text(0, 0.50, model_summary, ha='left', va='center')
        plt.axis('off')
        plt.tight_layout()
        ## refresh canvas
        self.canvas_1.draw()

        # GRAPHS PLOTTING : train and test
        # # Canvas Here
        self.figure_2 = plt.figure()
        self.canvas_2 = FigureCanvas(self.figure_2)
        self.canvas_2.setFixedSize(1400, 400)
        self.canvas_2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # # Add canvas to frame
        self.plot_layout_1.addWidget(self.canvas_2)
        # # clear the canvas
        self.figure_2.clear()
        # # create plots
        plt.subplot(1, 2, 1)
        plt.plot(train_dates, train_results['Predicted data'], label='Predicted Values')
        plt.plot(train_dates, train_results['Actual data'], label='Actual Values')
        plt.xticks(rotation=45)
        plt.ylabel('Train data')
        plt.legend(fontsize='small')
        plt.subplot(1, 2, 2)
        plt.plot(test_dates, test_results['Predicted data'], label='Predicted Values')
        plt.plot(test_dates, test_results['Actual data'], label='Actual Values')
        plt.xticks(rotation=45)
        plt.ylabel('Test data')
        plt.legend(fontsize='small')
        # Adjust layout to accommodate all three subplots
        plt.tight_layout()  
        # # refresh canvas
        self.canvas_2.draw()
        
        # GRAPHS PLOTTING : future prediction
        # # Canvas Here
        self.figure_3 = plt.figure()
        self.canvas_3 = FigureCanvas(self.figure_3)
        self.canvas_3.setFixedSize(1400, 400)
        # # Add canvas to frame
        self.plot_layout_2.addWidget(self.canvas_3)
        # # clear the canvas
        self.figure_3.clear()
        # # create plots
        plt.subplot(1, 1, 1)
        # # Create a list of colors for the segments
        colors = ['#FF7100', '#14AC18']
        # # Initialize variables to store the last point of the previous segment
        prev_x = x_before_predict[-1]
        prev_y = before_predict[-1]
        # # Plot the first segment
        plt.plot(x_before_predict, before_predict, color=colors[0])
        # # Plot the second segment
        plt.plot(x_future_predict, future_predict, color=colors[1], label='Future prediction')
        # # Connect the segments by adding a line from the last point of the first segment to the first point of the second segment
        plt.plot([prev_x, x_future_predict[0]], [prev_y, future_predict[0]], color='#14AC18')
        # # Add labels and a legend
        plt.xlabel('Time')
        plt.ylabel('Data')
        plt.legend()
        # Adjust layout to accommodate all three subplots
        plt.tight_layout()  
        # # refresh canvas
        self.canvas_3.draw()
        
        # LABELS : accuracy
        # Set the result_text in the QLabel
        self.L_result.setText(result_text)
        
    def next_tab(self):
        current_index = self.tab_widget.currentIndex()
        if current_index < self.tab_widget.count() - 1:
            self.tab_widget.setCurrentIndex(current_index + 1)

    def previous_tab(self):
        current_index = self.tab_widget.currentIndex()
        if current_index > 0:
            self.tab_widget.setCurrentIndex(current_index - 1)
        
    def save(self):
        # create a file dialog for selecting the directory to save the files
        file_dialog = QFileDialog()
        directory = file_dialog.getExistingDirectory(caption="Save results")
        # check if the user has selected a directory
        if directory:
            # save train/test results as a CSV file
            train_results.to_excel(f"{directory}/Train_results.xlsx", index=False)
            test_results.to_excel(f"{directory}/Test_results.xlsx", index=False)
            future_results.to_excel(f"{directory}/Future_results.xlsx", index=False)
            # save plots
            png_figure1 = directory + '/Graph1_train&test.png'
            self.figure_2.savefig(png_figure1)
            png_figure2 = directory + '/Graph2_future.png'
            self.figure_3.savefig(png_figure2)
            # save model summary
            with open(directory + '/model_summary.txt', 'w') as file:
                file.write(model_summary)
            # save accuracy
            with open(directory + '/Accuracy.txt', 'w') as file:
                file.write(plain_text)
                # file.write("Test Score: %s\n" % formatted_testScore)
        # self.close()
    def dialog_close(self):
        self.close()

class AIRSDockWidget(QtWidgets.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()


    def __init__(self, parent=None):
        """Constructor."""
        super(AIRSDockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://doc.qt.io/qt-5/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        
        #Dialog
        # self.pushButton.clicked.connect(self.show_Results)
        self.dialogs = list() 
        
        #uploadcsv
        self.tb_csvfile.clicked.connect(self.upload_CSVfile)
        
        #Radiobuttons
        self.rb_mod1.toggled.connect(self.onRadioBtn)
        self.rb_mod2.toggled.connect(self.onRadioBtn)
        self.rb_mod3.toggled.connect(self.onRadioBtn)
        self.rb_mod4.toggled.connect(self.onRadioBtn)
        self.rb_mod5.toggled.connect(self.onRadioBtn)
        
        #spinbox
        self.spinBox_1.setRange(1,1000000)
        self.spinBox_2.setRange(1,1000000)
        self.spinBox_3.setRange(1,1000000)
        self.spinBox_4.setRange(1,1000000)
        self.spinBox_1.valueChanged.connect(self.to_sequences)
        self.spinBox_2.valueChanged.connect(self.to_filters_layer1)
        self.spinBox_3.valueChanged.connect(self.to_filters_layer2)
        # self.spinBox_4.valueChanged.connect(self.to_epochs)
        self.spinBox_5.valueChanged.connect(self.to_Predictions)      
        
        #forecasting calculation
        self.pb_forecast.clicked.connect(self.choose_FC)
        
        #Help&About
        self.About_list=list()        
        self.pb_about.clicked.connect(self.open_about)
        self.pb_help.clicked.connect(self.open_help)
        
        #tooltip for the buttons
        self.pb_forecast.setToolTip('Forecasting')
        self.pb_about.setToolTip('About')
        self.pb_help.setToolTip('Help')

    def upload_CSVfile(self):
        global df
        global dates
        # open directory
        fileName=QFileDialog.getOpenFileName(self, 'Select file', '', '*.csv *.txt')
        self.le_csvfile.setText(fileName[0])
        self.pb_forecast.setEnabled(True)
        self.le_csvfile.setEnabled(True)
        try:
            # upload file
            if fileName[0].endswith('.csv'):
                DataFrame = pd.read_csv(fileName[0], delimiter=',', keep_default_na=False, error_bad_lines=False, header=0)
                # print(DataFrame)
            elif fileName[0].endswith('.txt'):
                DataFrame = pd.read_table(fileName[0], sep=',', keep_default_na=False, error_bad_lines=False, header=0)
                # print(DataFrame)
            
            # Date column availability
            if 'Date' not in DataFrame.columns:
                # Assign default dates using sequential numbering
                dates = range(1, len(DataFrame) + 1)
            else:
                # Use the 'Date' column from the DataFrame
                dates = DataFrame['Date']

            # Find the column containing the values
            values_column = None
            for column in DataFrame.columns:
                if column != 'Date':
                    values_column = column
                    break

            if values_column is not None:
                df = DataFrame[[values_column]]
            else:
                print("No column found for values")
        except UnboundLocalError:
            print("No file selected or error occurred during file upload.")
    
    def onRadioBtn(self):
        global model_name
        if self.rb_mod1.isChecked():
            self.spinBox_3.setEnabled(True)
            model_name = self.rb_mod1.text()
        elif self.rb_mod2.isChecked():
            self.spinBox_3.setEnabled(True)
            model_name = self.rb_mod2.text()
        elif self.rb_mod3.isChecked():
            self.spinBox_3.setEnabled(True)
            model_name = self.rb_mod3.text()
        elif self.rb_mod4.isChecked():
            self.spinBox_3.setEnabled(False)
            model_name = self.rb_mod4.text()
        elif self.rb_mod5.isChecked():
            self.spinBox_3.setEnabled(True)
            model_name = self.rb_mod5.text()
    
    def to_sequences(self):
        global seq_size
        seq_size = self.spinBox_1.value()

    def to_filters_layer1(self):
        global filters_1
        filters_1 = self.spinBox_2.value()
        
    def to_filters_layer2(self):
        global filters_2
        filters_2 = self.spinBox_3.value()
        
    def to_Predictions(self):
        global future_predict_size
        future_predict_size = self.spinBox_5.value()
    

    def choose_FC(self):
        global df
        global dates
        global seq_size
        global filters_1
        global filters_2
        global future_predict_size
        global train_results
        global test_results
        global train_dates
        global test_dates
        global x_before_predict
        global x_future_predict
        global before_predict
        global future_predict
        global future_results
        global model_summary
        global acc_name
        global formatted_trainScore
        global formatted_testScore
        global result_text
        global plain_text
        
        # Set variables to a default value of 1
        # seq_size = 1  
        # filters_1 = 1
        # filters_2 = 1
        
        # Check if df is defined (i.e., the user uploaded a file)
        if 'df' not in globals():
            # Display a custom error message box in QGIS
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Error: Please upload an input file before Forecast.")
            msg.setWindowTitle("Error")
            msg.exec_()
            return  # Exit the function
        
        # Check if a forecasting model is selected
        if not self.rb_mod1.isChecked() and not self.rb_mod2.isChecked() and not self.rb_mod3.isChecked() and not self.rb_mod4.isChecked() and not self.rb_mod5.isChecked():
            # Display a custom error message box in QGIS
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Error: Please select a forecasting model.")
            msg.setWindowTitle("Error")
            msg.exec_()
            return  # Exit the function
        
        # # Convert values to float
        dataset = df.values
        dataset = dataset.astype('float32')
        # # Normalize the dataset using MinMaxScaler 
        scaler = MinMaxScaler(feature_range=(0, 1))
        dataset = scaler.fit_transform(dataset)
        # # take first 60% values for train and the remaining 1/3 for testing
        train_size = int(len(dataset) * 0.66)
        test_size = len(dataset) - train_size
        # # split into train and test sets
        train, test = dataset[0:train_size,:], dataset[train_size:len(dataset),:]
        # # split dates into train and test dates
        train_dates_size = int(len(dates) * 0.66)
        test_dates_size = len(dates) - train_dates_size
        train_dates, test_dates = dates[seq_size:train_dates_size], dates[train_dates_size+seq_size:]

        # # Convert an array of values into a dataset matrix
        xi = []
        yi = []
        xj = []
        yj = []
        for i in range(len(train)-seq_size):
            window = train[i:(i+seq_size), 0]
            xi.append(window)
            yi.append(train[i+seq_size, 0])
            trainX = np.array(xi)
            trainY = np.array(yi)
        
        for j in range(len(test)-seq_size):
            window = test[j:(j+seq_size), 0]
            xj.append(window)
            yj.append(test[j+seq_size, 0])
            testX = np.array(xj)
            testY = np.array(yj) 
        print("Shape of training set: {}".format(trainX.shape))
        print("Shape of test set: {}".format(testX.shape))             
        
        # # Forecasting models:
        if self.rb_mod1.isChecked() == True:
            #Progress
            progressMessageBar = iface.messageBar().createMessage("Executing...")
            progress = QProgressBar()
            progress.setMaximum(10)
            progress.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
            progressMessageBar.layout().addWidget(progress)
            iface.messageBar().pushWidget(progressMessageBar, Qgis.Info)
            for i in range(10):
                time.sleep(1)
                progress.setValue(i+1)
            #Model calling
            model = Sequential()
            model.add(Dense(filters_1, input_dim=seq_size, activation='relu')) 
            model.add(Dense(filters_2, activation='relu')) 
            model.add(Dense(1))
            model.compile(loss='mean_squared_error', optimizer='adam')
            model.fit(trainX, trainY, validation_data=(testX, testY), verbose=0, epochs=self.spinBox_4.value())
            
            #Future forecasting
            val1= len(test) - seq_size 
            x_input=test[val1:].reshape(1,-1) #an array that have the last values in test dataset
            # x_input.shape
            temp_input=list(x_input) #converting the NumPy array "x_input" back into a Python list
            temp_input=temp_input[0].tolist()
            print(temp_input)
            lst_output=[]
            i=0
            while(i<future_predict_size):
                if(len(temp_input)>seq_size):
                    x_input=np.array(temp_input[1:])
                    print("{} input {}".format(i,x_input))
                    x_input=x_input.reshape(1,-1)
                    x_input = x_input.reshape((1, seq_size, 1))
                    yhat = model.predict(x_input, verbose=0)
                    print("{} output {}".format(i,yhat))
                    temp_input.extend(yhat[0].tolist())
                    temp_input=temp_input[1:]
                    lst_output.extend(yhat.tolist())
                    i=i+1
                else:
                    x_input = x_input.reshape((1, seq_size, 1))
                    yhat = model.predict(x_input, verbose=0)
                    print(yhat[0])
                    temp_input.extend(yhat[0].tolist())
                    lst_output.extend(yhat.tolist())
                    i=i+1
            print(lst_output)
            
            iface.messageBar().clearWidgets()
        elif self.rb_mod2.isChecked() == True:
            #Progress
            progressMessageBar = iface.messageBar().createMessage("Executing...")
            progress = QProgressBar()
            progress.setMaximum(10)
            progress.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
            progressMessageBar.layout().addWidget(progress)
            iface.messageBar().pushWidget(progressMessageBar, Qgis.Info)
            for i in range(10):
                time.sleep(1)
                progress.setValue(i+1)
                
            #Reshape input to be [samples, time steps, features]
            trainX = np.reshape(trainX, (trainX.shape[0], trainX.shape[1], 1))
            testX = np.reshape(testX, (testX.shape[0], testX.shape[1], 1))
            print("New Shape of training set: {}".format(trainX.shape))
            print("New Shape of test set: {}".format(testX.shape))

            #Model calling
            model = Sequential()
            model.add(LSTM(filters_1, input_shape=(seq_size, 1)))
            model.add(Dense(filters_2))
            model.add(Dense(1))
            model.compile(loss='mean_squared_error', optimizer='adam')
            model.fit(trainX, trainY, validation_data=(testX, testY), verbose=0, epochs=self.spinBox_4.value())
            
            #Future forecasting
            val1= len(test) - seq_size 
            x_input=test[val1:].reshape(1,-1) #an array that have the last values in test dataset
            # x_input.shape
            temp_input=list(x_input) #converting the NumPy array "x_input" back into a Python list
            temp_input=temp_input[0].tolist()
            print(temp_input)
            lst_output=[]
            i=0
            while(i<future_predict_size):
                if(len(temp_input)>seq_size):
                    x_input=np.array(temp_input[1:])
                    print("{} input {}".format(i,x_input))
                    x_input=x_input.reshape(1,-1)
                    x_input = x_input.reshape((1, seq_size, 1))
                    yhat = model.predict(x_input, verbose=0)
                    print("{} output {}".format(i,yhat))
                    temp_input.extend(yhat[0].tolist())
                    temp_input=temp_input[1:]
                    lst_output.extend(yhat.tolist())
                    i=i+1
                else:
                    x_input = x_input.reshape((1, seq_size, 1))
                    yhat = model.predict(x_input, verbose=0)
                    print(yhat[0])
                    temp_input.extend(yhat[0].tolist())
                    lst_output.extend(yhat.tolist())
                    i=i+1
            print(lst_output)
            
            iface.messageBar().clearWidgets()
        elif self.rb_mod3.isChecked() == True:
            #Progress
            progressMessageBar = iface.messageBar().createMessage("Executing...")
            progress = QProgressBar()
            progress.setMaximum(10)
            progress.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
            progressMessageBar.layout().addWidget(progress)
            iface.messageBar().pushWidget(progressMessageBar, Qgis.Info)
            for i in range(10):
                time.sleep(1)
                progress.setValue(i+1)

            #Reshape input to be [samples, time steps, features]
            trainX = np.reshape(trainX, (trainX.shape[0], trainX.shape[1], 1))
            testX = np.reshape(testX, (testX.shape[0], testX.shape[1],1))

            #Model calling
            model = Sequential()
            model.add(LSTM(filters_1, activation='relu', return_sequences=True, input_shape=(seq_size, 1)))
            model.add(LSTM(filters_1, activation='relu'))
            model.add(Dense(filters_2))
            model.add(Dense(1))
            model.compile(optimizer='adam', loss='mean_squared_error')
            model.fit(trainX, trainY, validation_data=(testX, testY), verbose=0, epochs=self.spinBox_4.value())
            
            #Future forecasting
            val1= len(test) - seq_size 
            x_input=test[val1:].reshape(1,-1) #an array that have the last values in test dataset
            # x_input.shape
            temp_input=list(x_input) #converting the NumPy array "x_input" back into a Python list
            temp_input=temp_input[0].tolist()
            print(temp_input)
            lst_output=[]
            i=0
            while(i<future_predict_size):
                if(len(temp_input)>seq_size):
                    x_input=np.array(temp_input[1:])
                    print("{} input {}".format(i,x_input))
                    x_input=x_input.reshape(1,-1)
                    x_input = x_input.reshape((1, seq_size, 1))
                    yhat = model.predict(x_input, verbose=0)
                    print("{} output {}".format(i,yhat))
                    temp_input.extend(yhat[0].tolist())
                    temp_input=temp_input[1:]
                    lst_output.extend(yhat.tolist())
                    i=i+1
                else:
                    x_input = x_input.reshape((1, seq_size, 1))
                    yhat = model.predict(x_input, verbose=0)
                    print(yhat[0])
                    temp_input.extend(yhat[0].tolist())
                    lst_output.extend(yhat.tolist())
                    i=i+1
            print(lst_output)
            
            iface.messageBar().clearWidgets()
        elif self.rb_mod4.isChecked() == True:
            #Progress
            progressMessageBar = iface.messageBar().createMessage("Executing...")
            progress = QProgressBar()
            progress.setMaximum(10)
            progress.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
            progressMessageBar.layout().addWidget(progress)
            iface.messageBar().pushWidget(progressMessageBar, Qgis.Info)
            for i in range(10):
                time.sleep(1)
                progress.setValue(i+1)

            #Reshape input to be [samples, time steps, features]
            trainX = np.reshape(trainX, (trainX.shape[0], trainX.shape[1], 1))
            testX = np.reshape(testX, (testX.shape[0], testX.shape[1], 1))

            #Model calling
            model = Sequential()
            model.add(Bidirectional(LSTM(filters_1, activation='relu'), input_shape=(seq_size, 1)))
            model.add(Dense(1))
            model.compile(optimizer='adam', loss='mean_squared_error')
            model.fit(trainX, trainY, validation_data=(testX, testY), verbose=0, epochs=self.spinBox_4.value())
            
            #Future forecasting
            val1= len(test) - seq_size 
            x_input=test[val1:].reshape(1,-1) #an array that have the last values in test dataset
            # x_input.shape
            temp_input=list(x_input) #converting the NumPy array "x_input" back into a Python list
            temp_input=temp_input[0].tolist()
            print(temp_input)
            lst_output=[]
            i=0
            while(i<future_predict_size):
                if(len(temp_input)>seq_size):
                    x_input=np.array(temp_input[1:])
                    print("{} input {}".format(i,x_input))
                    x_input=x_input.reshape(1,-1)
                    x_input = x_input.reshape((1, seq_size, 1))
                    yhat = model.predict(x_input, verbose=0)
                    print("{} output {}".format(i,yhat))
                    temp_input.extend(yhat[0].tolist())
                    temp_input=temp_input[1:]
                    lst_output.extend(yhat.tolist())
                    i=i+1
                else:
                    x_input = x_input.reshape((1, seq_size, 1))
                    yhat = model.predict(x_input, verbose=0)
                    print(yhat[0])
                    temp_input.extend(yhat[0].tolist())
                    lst_output.extend(yhat.tolist())
                    i=i+1
            print(lst_output)
            
            iface.messageBar().clearWidgets()
        elif self.rb_mod5.isChecked() == True:
            #Progress
            progressMessageBar = iface.messageBar().createMessage("Executing...")
            progress = QProgressBar()
            progress.setMaximum(10)
            progress.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
            progressMessageBar.layout().addWidget(progress)
            iface.messageBar().pushWidget(progressMessageBar, Qgis.Info)
            for i in range(10):
                time.sleep(1)
                progress.setValue(i+1)

            #Reshape input
            trainX = trainX.reshape((trainX.shape[0], 1, 1, 1, seq_size))
            testX = testX.reshape((testX.shape[0], 1, 1, 1, seq_size))

            #Model calling
            model = Sequential()
            model.add(ConvLSTM2D(filters_1, kernel_size=(1,1), activation='relu', input_shape=(1, 1, 1, seq_size)))
            model.add(Flatten())
            model.add(Dense(filters_2))
            model.add(Dense(1))
            model.compile(optimizer='adam', loss='mean_squared_error')
            model.fit(trainX, trainY, validation_data=(testX, testY), verbose=0, epochs=self.spinBox_4.value())
            
            #Future forecasting
            val1= len(test) - seq_size 
            x_input=test[val1:].reshape(1,-1) #an array that have the last values in test dataset
            # x_input.shape
            temp_input=list(x_input) #converting the NumPy array "x_input" back into a Python list
            temp_input=temp_input[0].tolist()
            print(temp_input)
            lst_output=[]
            i=0
            while(i<future_predict_size):
                if(len(temp_input)>seq_size):
                    x_input=np.array(temp_input[1:])
                    print("{} input {}".format(i,x_input))
                    x_input=x_input.reshape(1,-1)
                    x_input = x_input.reshape((1, 1, 1, 1, seq_size))
                    yhat = model.predict(x_input, verbose=0)
                    print("{} output {}".format(i,yhat))
                    temp_input.extend(yhat[0].tolist())
                    temp_input=temp_input[1:]
                    lst_output.extend(yhat.tolist())
                    i=i+1
                else:
                    x_input = x_input.reshape((1, 1, 1, 1, seq_size))
                    yhat = model.predict(x_input, verbose=0)
                    print(yhat[0])
                    temp_input.extend(yhat[0].tolist())
                    lst_output.extend(yhat.tolist())
                    i=i+1
            print(lst_output)
            
            iface.messageBar().clearWidgets()
            
        # # Make predictions
        trainPredict = model.predict(trainX, verbose=0)
        testPredict = model.predict(testX, verbose=0)
        
        # # Invert predictions back to prescaled values
        trainPredict = scaler.inverse_transform(trainPredict)
        trainY = scaler.inverse_transform([trainY])
        testPredict = scaler.inverse_transform(testPredict)
        testY = scaler.inverse_transform([testY])
        
        # # Plot results: train and test sets
        train_results = pd.DataFrame(data={'Predicted data':trainPredict[:,0], 'Actual data':trainY[0]})
        test_results = pd.DataFrame(data={'Predicted data':testPredict[:,0], 'Actual data':testY[0]})
        
        # # Plot results: future predictions
        #x-axis formatting
        x_before_predict=np.arange(1,seq_size+1)
        x_future_predict=np.arange(seq_size+1,seq_size+future_predict_size+1)
        #y-axis formatting
        val2 = len(dataset) - seq_size
        before_predict = scaler.inverse_transform(dataset[val2:])
        future_predict = scaler.inverse_transform(lst_output)
        #values in dataframe
        future_results = pd.DataFrame(data={'Future Predictions':future_predict[:,0]})
        
        # # Accuracies
        result_text = ""
        if self.cb_Ac1.isChecked()==True:
            # Calculate and display R-squared
            trainScore = r2_score(trainY[0], trainPredict[:,0])
            testScore = r2_score(testY[0], testPredict[:,0])
            print('Train Score: %.2f R2' % (trainScore))
            print('Test Score: %.2f R2' % (testScore))
            acc_name = self.cb_Ac1.text()
            # Format value with 2 decimal places
            formatted_trainScore = "{:.2f}".format(trainScore)
            formatted_testScore = "{:.2f}".format(testScore) 
            result_text += f"<b><font size='+1'>{acc_name}:</font></b><br>Train Score: {formatted_trainScore}<br>Test Score: {formatted_testScore}<br>"
        if self.cb_Ac2.isChecked()==True:
            # Calculate and display Root Mean Square Error (RMSE)
            trainScore = math.sqrt(mean_squared_error(trainY[0], trainPredict[:,0]))
            testScore = math.sqrt(mean_squared_error(testY[0], testPredict[:,0]))
            print('Train Score: %.2f RMSE' % (trainScore))
            print('Test Score: %.2f RMSE' % (testScore))
            acc_name = self.cb_Ac2.text()
            # Format value with 2 decimal places
            formatted_trainScore = "{:.2f}".format(trainScore)
            formatted_testScore = "{:.2f}".format(testScore)
            result_text += f"<b><font size='+1'>{acc_name}:</font></b><br>Train Score: {formatted_trainScore}<br>Test Score: {formatted_testScore}<br>"
        if self.cb_Ac3.isChecked() == True:
            # Calculate and display Mean Absolute Error (MAE)
            trainScore = mean_absolute_error(trainY[0], trainPredict[:, 0])
            testScore = mean_absolute_error(testY[0], testPredict[:, 0])
            print('Train Score: %.2f MAE' % (trainScore))
            print('Test Score: %.2f MAE' % (testScore))
            acc_name = self.cb_Ac3.text()
            # Format value with 2 decimal places
            formatted_trainScore = "{:.2f}".format(trainScore)
            formatted_testScore = "{:.2f}".format(testScore)
            result_text += f"<b><font size='+1'>{acc_name}:</font></b><br>Train Score: {formatted_trainScore}<br>Test Score: {formatted_testScore}<br>"
        if self.cb_Ac4.isChecked() == True:
            # Calculate and display Mean Absolute Percentage Error (MAPE)
            trainScore = mean_absolute_percentage_error(trainY[0], trainPredict[:, 0])
            testScore = mean_absolute_percentage_error(testY[0], testPredict[:, 0])
            print('Train Score: %.2f MAPE' % (trainScore))
            print('Test Score: %.2f MAPE' % (testScore))
            acc_name = self.cb_Ac4.text()
            # Format value with 2 decimal places
            formatted_trainScore = "{:.2f}".format(trainScore)
            formatted_testScore = "{:.2f}".format(testScore)
            result_text += f"<b><font size='+1'>{acc_name}:</font></b><br>Train Score: {formatted_trainScore}<br>Test Score: {formatted_testScore}<br>"
        if not any([self.cb_Ac1.isChecked(), self.cb_Ac2.isChecked(), self.cb_Ac3.isChecked(), self.cb_Ac4.isChecked()]):
            result_text = "No accuracy selected"
        # Create an instance of the html2text converter
        converter = html2text.HTML2Text()
        # Convert the result_text to plain text
        plain_text = converter.handle(result_text)
            
        
        # # model summary stockage
        s = io.StringIO()
        model.summary(line_length=70, print_fn=lambda x: s.write(x + '\n'))
        model_summary = s.getvalue()
        s.close()

   
        # # Dialog : Results Visualization  
        dialog=Dialog()
        self.dialogs.append(dialog)
        dialog.show()
        dialog.raise_()  # Bring the dialog to the front
  

    def open_help(self):
        file_path= os.path.join(os.path.dirname(__file__),'AIRS Help.chm')
        url= QUrl.fromLocalFile(file_path)
        QDesktopServices.openUrl(url)


    def open_about(self):  
        about=About()
        self.About_list.append(about)
        about.show() 

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()
