# standardness

Benchmarking standardness model on Slovene, Croatian and Serbian

### Slovene

| model | dataset | Pearson Correlation | Spearman Correlation |
| --- | --- | --- | --- |
| Ridge | janes-norm | 0.6197 | 0.5985 |
| SVR-poly | janes-norm | 0.2689 | 0.3918 |
| SVR-linear | janes-norm | 0.5675 | 0.5115 |
| SVR-rbf | janes-norm | 0.7147 | 0.6569 |
| Multilingual BERT | janes-norm | 0.8533 | 0.7579 |
| CroSloEng BERT | janes-norm | **0.9043** | 0.7944 |
| sloBERTa | janes-norm | 0.8934 | **0.8029** |


### Croatian

| model | dataset | Pearson Correlation | Spearman Correlation |
| --- | --- | --- | --- |
| Ridge | reldi-hr | 0.4551 | 0.3691 |
| SVR-poly | reldi-hr | 0.1123 | 0.2794 |
| SVR-linear | reldi-hr | 0.3999 | 0.2345 |
| SVR-rbf | reldi-hr | 0.4245 | 0.3658 |
| Multilingual BERT | reldi-hr | 0.7421 | 0.5995 |
| CroSloEng BERT | reldi-hr | 0.8252 | 0.6850 |
| BERTić | reldi-hr | **0.8593** | **0.7615** |


### Serbian

| model | dataset | Pearson Correlation | Spearman Correlation |
| --- | --- | --- | --- |
| Ridge | reldi-sr | 0.2563 | 0.2898 |
| SVR-poly | reldi-sr | 0.1064 | 0.1914 |
| SVR-linear | reldi-sr | 0.1906 | 0.0554 |
| SVR-rbf | reldi-sr | 0.2559 | 0.2218 |
| Multilingual BERT | reldi-sr | 0.7106 | 0.5305 |
| CroSloEng BERT | reldi-sr | 0.6977 | 0.5519 |
| BERTić | reldi-sr | **0.8057** | **0.6500** |
