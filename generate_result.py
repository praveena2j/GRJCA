import os
import shutil
from pathlib import Path
from base.utils import get_filename_from_a_folder_given_extension, get_all_files_recursively_by_ext
import numpy as np
import csv
import pandas as pd
import sys






#RJCAwith AVT
#valence_result_path = "/misc/scratch11/6th-ABAW_Competition_2024/6th-ABAW_Competition_23Feb2024/save/ABAW5_LFAN_RCMA_setup_new_TCN_AVT_RJCA_fold1_valence_seed3407/predict/extra/valence"
#arousal_result_path = "/misc/scratch11/6th-ABAW_Competition_2024/6th-ABAW_Competition_23Feb2024/save/ABAW8_LFAN_DCA_setup_new_TCN_AV_MGRCA_l_3_fold1_arousal_seed3407/predict/extra/arousal"
arousal_result_path = "/misc/scratch11/8th-ABAW_Competition/save/ABAW8_LFAN_DCA_setup_new_TCN_AV_GRCA_l_3_fold1_arousal_seed3407/predict_best/extra/arousal"


#RJCAwith AV
#valence_result_path = "/misc/scratch11/6th-ABAW_Competition_2024/6th-ABAW_Competition_23Feb2024/save/ABAW5_CAN_RCMA_setup_new_TCN_AV_l_4_fold1_valence_seed3407"
valence_result_path = "/misc/scratch11/8th-ABAW_Competition/save/ABAW8_LFAN_DCA_setup_new_TCN_AV_DCA_l_3_fold1_valence_seed3407/predict/extra/valence"
#valence_result_path = "/misc/scratch11/6th-ABAW_Competition_2024/6th-ABAW_Competition_23Feb2024/save/ABAW5_CAN_RCMA_setup_new_TCN_AV_fold1_valence_seed3407/predict/extra/valence"
#arousal_result_path = "/misc/scratch11/6th-ABAW_Competition_2024/6th-ABAW_Competition_23Feb2024/save/ABAW5_CAN_RCMA_setup_new_TCN_AV_fold1_arousal_seed3407/predict/extra/arousal"


#arousal_result_path = "/misc/scratch11/6th-ABAW_Competition_2024/6th-ABAW_Competition_23Feb2024/save/ABAW5_CAN_orig_setup_can_new_fold1_arousal_seed3407/predict/extra/arousal"
#valence_result_path = "/misc/scratch11/6th-ABAW_Competition_2024/6th-ABAW_Competition_23Feb2024/save/ABAW5_CAN_orig_setup_can_new_fold1_valence_seed3407/predict/extra/valence"
final_result_path = "GRJCA_AV_results_bestaro"
os.makedirs(final_result_path, exist_ok= True)
test_set_list_path = "Valence_Arousal_Estimation_Challenge_test_set_release.txt"
test_set_list = pd.read_csv(test_set_list_path, header=None).values[:, 0]

sample_path = "sample.txt"
sample_df = pd.read_csv(sample_path)
#raw_result_list = [os.path.join(raw_result_path, fpath) for fpath in  os.listdir(raw_result_path)]



for fold in range(6):
    fold =1
    #arousal_result_path = os.path.join(raw_result_path, "fold" + str(fold))
    valences, arousals, images = [], [], []
    for trial in test_set_list:
        #arousal_txt, valence_txt = get_all_files_recursively_by_ext(arousal_result_path, "txt", trial)
        arousal_txt = get_all_files_recursively_by_ext(arousal_result_path, "txt", trial)[0]
        valence_txt = get_all_files_recursively_by_ext(valence_result_path, "txt", trial)[0]
       
        assert "arousal" in arousal_txt and "valence" in valence_txt

        arousal = pd.read_csv(arousal_txt).values
        valence = pd.read_csv(valence_txt).values


        assert len(arousal) == len(valence)
        length = len(arousal)
        print(length)

        sample_length = len(sample_df[sample_df['image_location'].str.match(trial + "/")])

        diff = sample_length - length


        if diff > 0:

            length = sample_length
            arousal = np.concatenate((arousal, np.repeat(arousal[-1], diff)[:, np.newaxis]))
            valence = np.concatenate((valence, np.repeat(valence[-1], diff)[:, np.newaxis]))
        elif diff < 0:
            length = sample_length
            arousal = arousal[:sample_length, :]
            valence = valence[:sample_length, :]

        print("{} has diff = {} to {}".format(trial, str(diff), str(sample_length)))

        image = []
        for i in range(length):
            image.append(trial + "/" + str(i+1).zfill(5) + ".jpg")

        valences.extend(valence)
        arousals.extend(arousal)
        images.extend(image)

    result_path = os.path.join(final_result_path, "fold" + str(fold) + ".txt")
    result = np.c_[images, valences, arousals]

    result_df = pd.DataFrame(result, columns=["image_location","valence","arousal"])
    result_df.to_csv(result_path,sep=",", index=None)
    print("fold {} done!".format(str(fold)))
    sys.exit()
