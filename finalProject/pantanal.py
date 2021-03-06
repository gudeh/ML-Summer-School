# -*- coding: utf-8 -*-
"""pantanal (1).ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1vaBbIBOCN4G-cwKUj4zgRNcVTYm28QRD

# Ajuste de focos de incêndio com dados do Google Trends

### Augusto, Ana, Marllon e Alexandre

### Importando bibliotecas
"""

!pip install optuna
!pip install pytrends

#import csv
import pandas as pd
#import missingno as ms
import numpy as np
import matplotlib.pyplot as plt

import sklearn.datasets
import sklearn.model_selection
import sklearn.metrics
import sklearn.ensemble

import sklearn.linear_model
import sklearn.tree
import sklearn.ensemble
import sklearn.neural_network
import sklearn.svm
import sklearn.neighbors

import optuna

from pytrends.request import TrendReq
import time
#startTime = time.time()

#from treeinterpreter import treeinterpreter as ti
#import waterfall_chart

"""### Lendo os dados:"""

df_palavras_Y = pd.read_csv('/content/FrequenciaPantanal v4.csv') #numero de novos focos
df_palavras_X = pd.read_csv('/content/trends2.csv') #dados do google trends (9 meses)

"""### Visualizando os dados:

"""

df_all=df_palavras_X.join(df_palavras_Y)

df_all.info()

df_all["caso"].describe()

df_all.corr()["caso"].sort_values(ascending=False)

from pandas.plotting import scatter_matrix

attributes = ["caso", "umidade do ar", "queimada",
              "incendio no pantanal"]
scatter_matrix(df_all[attributes], figsize=(12, 8))

#df_all.plot(kind="scatter", x="date", y="umidade")
df_all.plot(kind="scatter", x="date", y="umidade", alpha=0.8,
    s=df_all["bolsonaro"]*10, label="bolsonaro", figsize=(50,10),
    c="caso", cmap=plt.get_cmap("jet"), colorbar=True,
    sharex=False) #sharex=false é só pra corrigir um bug de display https://github.com/pandas-dev/pandas/issues/10611
plt.legend()

#df_all.plot(kind="scatter", x="date", y="umidade")
df_all.plot(kind="scatter", x="date", y="umidade", alpha=0.8,
    s=df_all["pantanal"]*10, label="pantanal", figsize=(50,10),
    c="caso", cmap=plt.get_cmap("jet"), colorbar=True,
    sharex=False) #sharex=false é só pra corrigir um bug de display https://github.com/pandas-dev/pandas/issues/10611
plt.legend()

"""### Funções que serão usadas:"""

#Pré-processamento:
def pre_process (df):
    
    new_df = pd.DataFrame()
    
    for n,c in df.items():
                
        if pd.api.types.is_numeric_dtype(c):
            # substituindo NaN numericos pelas medianas de cada coluna
            new_df[n] = c.fillna(value=c.median())
        else:
            # interpretando o que nao for numerico como variaveis categoricas 
            # e transformando cada categoria em um numero
            new_df[n] = pd.Categorical(c.astype('category').cat.as_ordered()).codes
    
    return new_df  

#métrica de treino:
def rmse(x,y): 
    
    return np.sqrt(sklearn.metrics.mean_squared_error(x,y))

#Imprime métrica de treino:
def display_score(m):
    
    res = [[rmse(m.predict(X_treino), y_treino), m.score(X_treino, y_treino)],
          [rmse(m.predict(X_validacao), y_validacao), m.score(X_validacao, y_validacao)]]
    
    score = pd.DataFrame(res, columns=['RMSE','R2'], index = ['Treino','Validação'])
    
    if hasattr(m, 'oob_score_'): 
        score.loc['OOB'] = [rmse(y_treino, m.oob_prediction_), m.oob_score_]
        
    return score

# Importâncias das variáveis:
def plotar_importancias(modelo, tags, n=10):
    
    fig, ax = plt.subplots(1,2, figsize = (20,4))

    coefs = []
    abs_coefs = []

    if hasattr(modelo,'coef_'):
        imp = modelo.coef_
    elif hasattr(modelo,'feature_importances_'):
        imp = modelo.feature_importances_
    else:
        print('sorry, nao vai rolar!')
        return

    coefs = (pd.Series(imp, index = tags))
    coefs.plot(use_index=False, ax=ax[0]);
    abs_coefs = (abs(coefs)/(abs(coefs).sum()))
    abs_coefs.sort_values(ascending=False).plot(use_index=False, ax=ax[1],marker='.')

    ax[0].set_title('Importâncias relativas das variáveis')
    ax[1].set_title('Importâncias relativas das variáveis - ordem decrescente')

    abs_coefs_df = pd.DataFrame(np.array(abs_coefs).T,
                                columns = ['Importancias'],
                                index = tags)

    df = abs_coefs_df['Importancias'].sort_values(ascending=False)
    
    print(df.iloc[0:n])
    plt.figure()
    df.iloc[0:n].plot(kind='barh', figsize=(15,0.25*n), legend=False)
    
    return df



# Dendograma:
def dendogram_spearmanr(df, tags):

    import scipy.cluster.hierarchy
    import scipy.stats
    
    corr = np.round(scipy.stats.spearmanr(df).correlation, 4)
    corr_condensed = scipy.cluster.hierarchy.distance.squareform(1-corr)
    z = scipy.cluster.hierarchy.linkage(corr_condensed, method='average')
    fig = plt.figure(figsize=(18,8))
    dendrogram = scipy.cluster.hierarchy.dendrogram(z, labels=tags, orientation='left', leaf_font_size=30)
    plt.show()

"""### Treinando e validando:

Salvando X e Y e dividindo entre treino e teste:
"""

y = df_palavras_Y.caso

df_palavras_X_pre = pre_process(df_palavras_X)
X = df_palavras_X_pre
X = df_palavras_X_pre.drop(['mato grosso','fogo','fuligem','clima','queimadas','chuva no pantanal',
                            'chuva pantanal','impacto das queimadas','umidade do ar','queimadas no pantanal',
                            'queimada','desmatamento','queimadas no brasil','brasil em chamas',
                            'calor','aquecimento global','floresta amazonica','biomas brasileiros',
                            'bioma','temperatura','meio ambiente','salve o pantanal','incendio na floresta'], axis=1)

"""Separando variáveis de treino e validação"""

X_treino, X_validacao, y_treino, y_validacao = sklearn.model_selection.train_test_split(X, y, test_size = 0.1, random_state = 0)
#X_treino, X_validacao, y_treino, y_validacao = sklearn.model_selection.train_test_split(X, y, test_size = 0.25, shuffle=False, stratify=None)

"""Treinando:"""

m = sklearn.ensemble.RandomForestRegressor(n_jobs=-1, oob_score = True, random_state = 0)
#m = sklearn.ensemble.RandomForestRegressor(n_estimators = 100, n_jobs=-1, oob_score = True, random_state = 0)
#m = sklearn.ensemble.RandomForestRegressor(max_depth=400, min_samples_leaf = 1, max_features = 0.4, n_jobs=-1, oob_score = True, random_state = 0)
m.fit(X_treino, y_treino)

"""Validando:"""

y_validacao_pred = m.predict(X_validacao)

sc=display_score(m)
sc

"""Importâncias e dendograma:"""

imp3 = plotar_importancias(m, X_treino.columns,30) #treino

dendogram_spearmanr(X_treino, X_treino.columns)

"""


### Validação cruzada:"""

m2 = sklearn.ensemble.RandomForestRegressor(min_samples_leaf = 3, max_features = 0.6, 
                                            n_estimators = 60, n_jobs=-1, oob_score = True, 
                                            random_state = 0)

results = sklearn.model_selection.cross_val_score(m2, X_treino, y_treino, scoring='r2')
results

results.mean()

"""### Comparando modelos"""

# especificando modelos 

modelos = [sklearn.linear_model.LinearRegression(),
           sklearn.neural_network.MLPRegressor(),
           sklearn.ensemble.RandomForestRegressor(),
           sklearn.neighbors.KNeighborsRegressor(),
           sklearn.svm.SVR()]


#lista para guardar resultados
results = [0]*len(modelos)

print('Modelo: média, desvio-padrão\n-------------------')

for i in range(len(modelos)):
    
    # efetuando a validação cruzada!
    results[i] = sklearn.model_selection.cross_val_score(modelos[i], 
                                                         X_treino, y_treino, 
                                                         cv=10, 
                                                         scoring='r2',
                                                         n_jobs=-1)
    
    # imprimindo resultados
    print(f'{modelos[i].__class__.__name__}: {results[i].mean():.3}, {results[i].std():.3}')

# plotando resultados
fig, ax = plt.subplots()
ax.boxplot(results)

# formatando gráfico
ax.set_xticklabels([modelos[i].__class__.__name__ for i in range(len(modelos))], 
                   rotation = 45, ha="right")
ax.set_ylabel("R^2")
ax.set_title('Comparação entre modelos de regressão');

print('R^2\n--------------')

for m in modelos:
    m.fit(X_treino, y_treino)
    print(f'{m.__class__.__name__}: {sklearn.metrics.r2_score(y_validacao, m.predict(X_validacao)):.3}')

"""### Curvas de aprendizado"""

# adaptado de https://scikit-learn.org/stable/auto_examples/model_selection/plot_learning_curve.html

# especificando modelos 

modelos = [sklearn.linear_model.LinearRegression(),
           sklearn.neural_network.MLPRegressor(),
           sklearn.ensemble.RandomForestRegressor(),
           sklearn.neighbors.KNeighborsRegressor(),
           sklearn.svm.SVR()]


fig, ax = plt.subplots(3,2,figsize=(16,10))

for i in range(len(modelos)):
    
    # calculando a curva de aprendizado!
    train_sizes, train_scores, test_scores = sklearn.model_selection.learning_curve(modelos[i], 
                                                                                    X_treino, y_treino, 
                                                                                    cv=5, 
                                                                                    scoring='r2',
                                                                                    n_jobs=-1)
    
    # médias e desvios-padrão dos resultados da validação cruzada (para cada ponto da curva)
    train_scores_mean = np.mean(train_scores, axis=1)
    train_scores_std = np.std(train_scores, axis=1)
    test_scores_mean = np.mean(test_scores, axis=1)
    test_scores_std = np.std(test_scores, axis=1)
    
    # plotando curva correspondente ao treino
    ax.ravel()[i].plot(train_sizes, train_scores_mean, label="Treino")
    ax.ravel()[i].fill_between(train_sizes, train_scores_mean - train_scores_std,
                               train_scores_mean + train_scores_std, alpha=0.1)
    
    # plotando curva correspondente ao teste
    ax.ravel()[i].plot(train_sizes, test_scores_mean, label="Validação cruzada")
    ax.ravel()[i].fill_between(train_sizes, test_scores_mean - test_scores_std,
                               test_scores_mean + test_scores_std, alpha=0.1)
    
    # formatando gráfico
    ax.ravel()[i].set_title(modelos[i].__class__.__name__)
    ax.ravel()[i].set_ylabel('R2')
    ax.ravel()[i].set_xlabel('Número de amostras de treino')
    ax.ravel()[i].legend(loc="best")
    
ax.ravel()[-2].axis('off')
ax.ravel()[-1].axis('off')

fig.tight_layout();

"""### Sintonização de hiperparâmetros

#### Curvas de validação
"""

# adaptado de https://scikit-learn.org/stable/auto_examples/model_selection/plot_validation_curve.html

# definindo os valores de parâmetros a serem testados
param_range = [10, 20, 30, 40, 50, 60, 100, 200]

# definindo o modelo
m = sklearn.ensemble.RandomForestRegressor()

# calculando a curva de validação!
train_scores, test_scores = sklearn.model_selection.validation_curve(m, X_treino, y_treino, 
                                                                     param_name="n_estimators", 
                                                                     param_range=param_range,
                                                                     scoring="r2", 
                                                                     n_jobs=-1)

# médias e desvios-padrão dos resultados da validação cruzada (para cada ponto da curva)
train_scores_mean = np.mean(train_scores, axis=1)
train_scores_std = np.std(train_scores, axis=1)
test_scores_mean = np.mean(test_scores, axis=1)
test_scores_std = np.std(test_scores, axis=1)

# plotando curva correspondente ao treino
plt.plot(param_range, train_scores_mean, label="Treino")
plt.fill_between(param_range, train_scores_mean - train_scores_std,
                 train_scores_mean + train_scores_std, alpha=0.1)

# plotando curva correspondente ao teste
plt.plot(param_range, test_scores_mean, label="Validação cruzada")
plt.fill_between(param_range, test_scores_mean - test_scores_std,
                 test_scores_mean + test_scores_std, alpha=0.1)

# formatando gráfico
plt.title("Curva de Validação - Regressão")
plt.xlabel('n_estimators')
plt.ylabel("R2")
plt.legend(loc="best");

# definindo os valores de parâmetros a serem testados
param_range = [1, 2, 3, 4, 5, 6]

# definindo o modelo
m = sklearn.ensemble.RandomForestRegressor()

# calculando a curva de validação!
train_scores, test_scores = sklearn.model_selection.validation_curve(m, X_treino, y_treino, 
                                                                     param_name="min_samples_leaf", 
                                                                     param_range=param_range,
                                                                     scoring="r2", 
                                                                     n_jobs=-1)

# médias e desvios-padrão dos resultados da validação cruzada (para cada ponto da curva)
train_scores_mean = np.mean(train_scores, axis=1)
train_scores_std = np.std(train_scores, axis=1)
test_scores_mean = np.mean(test_scores, axis=1)
test_scores_std = np.std(test_scores, axis=1)

# plotando curva correspondente ao treino
plt.plot(param_range, train_scores_mean, label="Treino")
plt.fill_between(param_range, train_scores_mean - train_scores_std,
                 train_scores_mean + train_scores_std, alpha=0.1)

# plotando curva correspondente ao teste
plt.plot(param_range, test_scores_mean, label="Validação cruzada")
plt.fill_between(param_range, test_scores_mean - test_scores_std,
                 test_scores_mean + test_scores_std, alpha=0.1)

# formatando gráfico
plt.title("Curva de Validação - Regressão")
plt.xlabel('min_samples_leaf')
plt.ylabel("R2")
plt.legend(loc="best");

"""#### Sintonização automática"""

# função objetivo para otimização de hiperparâmetros
def objetivo(trial):

    # colocaremos dois modelos pra brigar: KNeighborsRegressor e RF
    
    sklearn.neighbors.KNeighborsRegressor
    
    classifier_name = trial.suggest_categorical("classifier", ["KNeighborsRegressor", "RandomForest"])
    
    if classifier_name == 'KNeighborsRegressor':
        # hiperparâmetros de busca
        rf_leaf_size = trial.suggest_int("rf_leaf_size", 1, 10)
        rf_p = trial.suggest_int("rf_p", 1, 3)
                
        # modelo
        m = sklearn.neighbors.KNeighborsRegressor(leaf_size = rf_leaf_size, 
                                                  p = rf_p)

        
    else:

        # hiperparâmetros de busca para o RF
        rf_min_samples_leaf = trial.suggest_int("rf_min_samples_leaf", 1, 10)
        rf_max_depth = trial.suggest_int("rf_max_depth", 2, 32, log = True)
        rf_n_estimators = trial.suggest_int("rf_n_estimators", 10,100)
        
        # modelo RF
        m = sklearn.ensemble.RandomForestRegressor(max_depth = rf_max_depth, 
                                                   min_samples_leaf = rf_min_samples_leaf, 
                                                   n_estimators = rf_n_estimators)

    # retornando R2
    R2 = sklearn.model_selection.cross_val_score(m, X_treino, y_treino, n_jobs = -1, cv = 3, scoring='r2')
    R2 = R2.mean()
    return R2

study = optuna.create_study(direction="maximize")
study.optimize(objetivo, n_trials = 100)

study.best_params

m = sklearn.ensemble.RandomForestRegressor(max_depth = study.best_params['rf_max_depth'],
                                           min_samples_leaf = study.best_params['rf_min_samples_leaf'],
                                           n_estimators = study.best_params['rf_n_estimators'])
R2 = sklearn.model_selection.cross_val_score(m, X_treino, y_treino, n_jobs = -1, cv = 3, scoring='r2')
R2 = R2.mean()
print(R2)

optuna.visualization.plot_optimization_history(study)

optuna.visualization.plot_slice(study)

optuna.visualization.plot_contour(study, params=['rf_max_depth','rf_min_samples_leaf','rf_n_estimators'])

optuna.visualization.plot_parallel_coordinate(study)

optuna.visualization.plot_edf(study)

optuna.visualization.plot_slice(study)