import evaluation
import pickle
import math
import pandas as pd

'''
Kaggle CrowdFlower Search Results Relevance Competition - Ensembling Script

This file performs the ensembling I used for the Kaggle CrowdFlower Search
Results Relevance Competition (https://www.kaggle.com/c/crowdflower-search-relevance). 
My final submission ultimately scored 0.69764 on the private leaderboard (Kappa Loss Function)
which gave me a rank of 42 out of 1326 competitors.

The script first imports pickle files of the data frames gathered through the separate modelling 
script (you must run the modelling script first before you run this). 

It then calculates the optimal weights to use in ensembling for the five separate models by 
calculating the kappa loss function on the weighted predictions in
StratifiedKFold cross validation.

The ensembling then uses a simple linear combination of the model predictions, weighted by the optimal
weights, and then using simple rounding to the resulting median_relevance so it always takes the values
1, 2, 3, or 4.

Finally, it outputs the optimal, ensembled predictions to a file (ensembled_submission.csv), which is 
the csv file ultimately submitted to Kaggle.

__author__ : Mark Nagelberg
'''

#Load the StratifiedKFold cross validation prediction data for the five models.
rf_cv_predictions = pickle.load(open('rf_cv_test_data.pkl', 'r'))
svc_cv_predictions = pickle.load(open('svc_cv_test_data.pkl', 'r'))
adaboost_cv_predictions = pickle.load(open('adaboost_cv_test_data.pkl', 'r'))
tfidf_v1_cv_predictions = pickle.load(open('tfidf_v1_test_data.pkl', 'r'))
tfidf_v2_cv_predictions = pickle.load(open('tfidf_v2_test_data.pkl', 'r'))

preds = [rf_cv_predictions, svc_cv_predictions, adaboost_cv_predictions, tfidf_v1_cv_predictions, tfidf_v2_cv_predictions]

y_true = preds[0][0]['y']

#Define the allowable model weights.
wt = [0.0, .1, .25, .5, .2, 1.0]

#Create a vector of every possible tuple of weights.
wt_list = [(a,b,c,d,e) for a in wt for b in wt for c in wt for d in wt for e in wt]

#Select only the tuples in wt_list that sum to 1 (these are the weights that we will
#test to see which one is best).
wt_final = []
for w in wt_list:
	if sum(w) == 1.0:
		wt_final.append(w)

#Find the optimal weights.
max_average_score = 0
max_weights = None
for wt in wt_final:
	total_score = 0
	for i in range(5):
		y_true = preds[0][i]['y']
		weighted_prediction = sum([wt[x] * preds[x][i]['y_pred'].astype(int).reset_index() for x in range(5)])
		weighted_prediction = [round(p) for p in weighted_prediction['y_pred']]
		total_score += evaluation.quadratic_weighted_kappa(y = y_true, y_pred = weighted_prediction)
	average_score = total_score/5.0
	if average_score > max_average_score:
		max_average_score = average_score
		max_weights = wt
print "Best set of weights: " + str(max_weights)
print "Corresponding score: " + str(max_average_score)


#Now perform the best ensembling on the full dataset 
#using the optimanl weights determined above
rf_final_predictions = pickle.load(open('rf_final_predictions.pkl', 'r'))
svc_final_predictions = pickle.load(open('svc_final_predictions.pkl', 'r'))
adaboost_final_predictions = pickle.load(open('adaboost_final_predictions.pkl', 'r'))
tfidf_v1_final_predictions = pickle.load(open('tfidf_v1_final_predictions.pkl', 'r'))
tfidf_v2_final_predictions = pickle.load(open('tfidf_v2_final_predictions.pkl', 'r'))

preds = [rf_final_predictions, svc_final_predictions, adaboost_final_predictions, tfidf_v1_final_predictions, tfidf_v2_final_predictions]

weighted_prediction = sum([max_weights[x] * preds[x]["prediction"].astype(int) for x in range(5)])
weighted_prediction = [int(round(p)) for p in weighted_prediction]

test = pickle.load(open('test_extracted_df.pkl', 'r'))
submission = pd.DataFrame({"id": test["id"], "prediction": weighted_prediction})
submission.to_csv('ensembled_submission.csv', index=False)