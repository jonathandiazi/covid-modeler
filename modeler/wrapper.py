from datetime import timedelta

import pandas as pd
import numpy as np

import chart_studio
import chart_studio.plotly as py
import plotly.graph_objects as go

from . import countries, models

class Modeler:
    default_models = {
        'linear': models.LinearModel,
        'logistic': models.LogisticModel,
        'exponential': models.ExponentialModel
    }
    processed_models = {}

    record = ''

    def __init__(self, country=None, predict_len=2, use_default_models=True):
        self.predict_len = predict_len
        self.c = countries.CountryData()
        self.set_country(country)
        self.country_name = country
        if use_default_models:
            self.models = self.default_models
    
    def log(self, text):
        self.record += text
    
    def process(self):
        self.record = ''

        if len(self.data[1]) >= 7:
            current = self.data[1].astype(int)[-1]
            lastweek = self.data[1].astype(int)[-8]
            
            if current > lastweek:
                self.log(f'Resultados para *{self.country_name}*')
                self.log('\n** Basado en los datos de la última semana **\n')
                self.log(f'\n\tCasos confirmados en {self.data[2][-1]} \t {current}')
                self.log(f'\n\tCasos confirmados en {self.data[2][-8]} \t {lastweek}')
                ratio = current / lastweek
                self.log(f'\n\tProporción: {round(ratio, 2)}')
                self.log(f'\n\tIncremento semanal: {round( 100 * (ratio - 1), 1)}%')
                dailypercentchange = round( 100 * (pow(ratio, 1/7) - 1), 1)
                self.log(f'\n\tIncremento diario: {dailypercentchange}% por día')
                recentdbltime = round( 7 * np.log(2) / np.log(ratio), 1)
                self.log(f'\n\tTiempo que tarda en duplicarse (al ritmo actual): {recentdbltime} días')
        
        for name, model in self.models.items():
            self.processed_models[name] = model(
                x_train=self.data[0],
                y_train=self.data[1],
                predict_len=self.predict_len,
                start_date=self.data[2][0]
            )
        self.show_record()
        self.plot()
    
    def set_country(self, country):
        self.data = self.c.get_country(country)
    
    def show_record(self):
        best_r2 = 0
        best_model = ''
        print(self.record)
        for name, model in self.processed_models.items():
            print(model.record)
            if hasattr(model, 'r2') and model.r2 > best_r2:
                best_r2 = model.r2
                best_model = model.plot_name
        if best_r2 > 0:
            print(f"\nMejor modelo: {best_model} (R2 = {best_r2})")

        
    def plot(self):
        plot_data = []
        end_date = pd.to_datetime(self.data[2][0]).date() + timedelta(days=len(self.data[2]))
        original_data = go.Scatter(
            x=pd.date_range(start=self.data[2][0], end=end_date),
            y=self.data[1],
            mode='markers',
            name='Casos confirmados'
        )
        plot_data.append(original_data)
        for name, model in self.processed_models.items():
            plot_data.append(model.chart)
        
        layout = dict(
            title = self.country_name,
            xaxis_type='date'
        )
        fig = go.Figure(data=plot_data, layout=layout)
        fig.show()