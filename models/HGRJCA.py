from __future__ import absolute_import
from __future__ import division

from torch.nn import init
import torch
import math
from torch import nn
from torch.nn import functional as F
import sys
from .av_crossatten import DCNLayer
from .layer import LSTM

#from .audguide_att import BottomUpExtract
#from .şelfattention import SelfAttentionModel

class HGRJCA_cam(nn.Module):
    def __init__(self):
        super(HGRJCA_cam, self).__init__()
        #self.corr_weights = torch.nn.Parameter(torch.empty(
        #        1024, 1024, requires_grad=True).type(torch.cuda.FloatTensor))


        #self.coattn = DCNLayer(opt.video_size, opt.audio_size, opt.num_seq, opt.dropout)
        #self.coattn = DCNLayer(512, 512, 2, 0.6)
        self.coattn = DCNLayer(256, 128, 2, 0.6)

        #self.audio_extract = LSTM(512, 512, 2, 0.1, residual_embeddings=True)
        #self.video_extract = LSTM(512, 512, 2, 0.1, residual_embeddings=True)

        #self.audio_extract = SelfAttentionModel(512, 4,  512, 512, 3)
        #self.video_extract = SelfAttentionModel(512, 4,  512, 512, 3)

        #self.encoder1 = nn.Linear(512, 256)
        #self.encoder2 = nn.Linear(512, 256)
        #self.video_attn = BottomUpExtract(512, 512)
        self.vregressor = nn.Sequential(nn.Linear(512, 128),
                                        nn.ReLU(inplace=True),
                                     nn.Dropout(0.6),
                                 nn.Linear(128, 1))

        #self.Joint = SelfAttentionModel(1024, 8,  256, 256, 3)
        self.Joint = LSTM(1024, 512, 2, dropout=0, residual_embeddings=True)

        self.aregressor = nn.Sequential(nn.Linear(512, 128),
                                        nn.ReLU(inplace=True),
                                     nn.Dropout(0.6),
                                 nn.Linear(128, 1))

        self.audio_gating_fc_layer_stage2 = nn.Linear(128, 3)
        self.softmax = nn.Softmax(dim=-1)
                                    
        self.video_gating_fc_layer_stage2 = nn.Linear(256, 3)
        self.text_gating_fc_layer_stage2 = nn.Linear(128, 3)

        self.video_gating_fc_layer_stage1 = nn.Linear(256, 2)
        self.text_gating_fc_layer_stage1 = nn.Linear(128, 2)
        self.audio_gating_fc_layer_stage1 = nn.Linear(128, 2)

        self.video_gating_fc_layer_stage = nn.Linear(256, 2)
        self.text_gating_fc_layer_stage = nn.Linear(128, 2)
        self.audio_gating_fc_layer_stage = nn.Linear(128, 2)


        #self.softmax = nn.LogSoftmax()
                                           
        self.relu = nn.ReLU()
        self.init_weights()

    def init_weights(net, init_type='xavier', init_gain=1):

        if torch.cuda.is_available():
            net.cuda()

        def init_func(m):  # define the initialization function
            classname = m.__class__.__name__
            if hasattr(m, 'weight') and (classname.find('Conv') != -1 or classname.find('Linear') != -1):
                if init_type == 'normal':
                    init.uniform_(m.weight.data, 0.0, init_gain)
                elif init_type == 'xavier':
                    init.xavier_uniform_(m.weight.data, gain=init_gain)
                elif init_type == 'kaiming':
                    init.kaiming_uniform_(m.weight.data, a=0, mode='fan_in')
                elif init_type == 'orthogonal':
                    init.orthogonal_(m.weight.data, gain=init_gain)
                else:
                    raise NotImplementedError('initialization method [%s] is not implemented' % init_type)
                if hasattr(m, 'bias') and m.bias is not None:
                    init.constant_(m.bias.data, 0.0)

        print('initialize network with %s' % init_type)
        net.apply(init_func)  # apply the initialization function <init_func>

    #def first_init(self):
    #    nn.init.xavier_normal_(self.corr_weights)

    def forward(self, f1_norm, f2_norm):
        #f1 = f1.squeeze(1)
        #f2 = f2.squeeze(1)

        #f1_norm = F.normalize(f1_norm, p=2, dim=2, eps=1e-12)
        #f2_norm = F.normalize(f2_norm, p=2, dim=2, eps=1e-12)

        #fin_audio_features = []
        #fin_visual_features = []
        #vsequence_outs = []
        #asequence_outs = []

        #for i in range(f1_norm.shape[0]):
        #aud_fts = f1_norm[i,:,:]#.transpose(0,1)
        #vis_fts = f2_norm[i,:,:]#.transpose(0,1)

        #audfts = self.encoder1(aud_fts)
        #visfts = self.encoder2(vis_fts)

        video = F.normalize(f1_norm, dim=-1)
        audio = F.normalize(f2_norm, dim=-1)
        #text = F.normalize(f3_norm, dim=-1)


        #audio = self.audio_extract(audio)
        #video = self.video_attn(video, audio)
        #video = self.video_extract(video)

        

        atten_video, atten_audio = self.coattn(video, audio)

        #print(atten_video.shape)
       
        # stage 1 gating
        stage1_video_weights = self.video_gating_fc_layer_stage1(atten_video[-2])
        stage1_video_weights = self.softmax(stage1_video_weights/0.1)
        vid1_wts_stage1 = stage1_video_weights[:,:,0].unsqueeze(2).repeat(1,1,video.shape[2])
        vid2_wts_stage1 = stage1_video_weights[:,:,1].unsqueeze(2).repeat(1,1,video.shape[2])
        gated_video_stage1 = torch.mul(vid1_wts_stage1, video) + torch.mul(vid2_wts_stage1, atten_video[-2])
        gated_video_stage1 = self.relu(gated_video_stage1)

        stage1_audio_weights = self.audio_gating_fc_layer_stage1(atten_audio[-2])
        stage1_audio_weights = self.softmax(stage1_audio_weights/0.1)
        aud1_wts_stage1 = stage1_audio_weights[:,:,0].unsqueeze(2).repeat(1,1,audio.shape[2])
        aud2_wts_stage1 = stage1_audio_weights[:,:,1].unsqueeze(2).repeat(1,1,audio.shape[2])
        gated_audio_stage1 = torch.mul(aud1_wts_stage1, audio) + torch.mul(aud2_wts_stage1, atten_audio[-2]) 
        gated_audio_stage1 = self.relu(gated_audio_stage1)

        #stage1_text_weights = self.text_gating_fc_layer_stage1(atten_text[-2])
        #stage1_text_weights = self.softmax(stage1_text_weights/0.1)
        #text1_wts_stage1 = stage1_text_weights[:,:,0].unsqueeze(2).repeat(1,1,text.shape[2])
        #text2_wts_stage1 = stage1_text_weights[:,:,1].unsqueeze(2).repeat(1,1,text.shape[2])
        #gated_text_stage1 = torch.mul(text1_wts_stage1, text) + torch.mul(text2_wts_stage1, atten_text[-2]) 
        #gated_text_stage1 = self.relu(gated_text_stage1)

        # stage 2 gating
        video_weights = self.video_gating_fc_layer_stage2(atten_video[-1])
        video_weights = self.softmax(video_weights/0.1)
        vid1_wts = video_weights[:,:,0].unsqueeze(2).repeat(1,1,video.shape[2])
        vid2_wts = video_weights[:,:,1].unsqueeze(2).repeat(1,1,video.shape[2])
        vid3_wts = video_weights[:,:,2].unsqueeze(2).repeat(1,1,video.shape[2])
        gated_video = torch.mul(vid1_wts, video) + torch.mul(vid2_wts, atten_video[-2]) + torch.mul(vid3_wts, atten_video[-1])
        gated_video = self.relu(gated_video)

        audio_weights = self.audio_gating_fc_layer_stage2(atten_audio[-1])
        audio_weights = self.softmax(audio_weights/0.1)
        aud1_wts = audio_weights[:,:,0].unsqueeze(2).repeat(1,1,audio.shape[2])
        aud2_wts = audio_weights[:,:,1].unsqueeze(2).repeat(1,1,audio.shape[2])
        aud3_wts = audio_weights[:,:,2].unsqueeze(2).repeat(1,1,audio.shape[2])
        gated_audio = torch.mul(aud1_wts, audio) + torch.mul(aud2_wts, atten_audio[-2]) + torch.mul(aud3_wts, atten_audio[-1])
        gated_audio = self.relu(gated_audio)

        #text_weights = self.text_gating_fc_layer_stage2(atten_text[-1])
        #text_weights = self.softmax(text_weights/0.1)
        #text1_wts = text_weights[:,:,0].unsqueeze(2).repeat(1,1,text.shape[2])
        #text2_wts = text_weights[:,:,1].unsqueeze(2).repeat(1,1,text.shape[2])
        #text3_wts = text_weights[:,:,2].unsqueeze(2).repeat(1,1,text.shape[2])
        #gated_text = torch.mul(text1_wts, text) + torch.mul(text2_wts, atten_text[-2]) + torch.mul(text3_wts, atten_text[-1])
        #gated_text = self.relu(gated_text)

        #stage gating 
        stage_video_weights = self.video_gating_fc_layer_stage(atten_video[-1])
        stage_video_weights = self.softmax(stage_video_weights/0.1)
        vid1_wts_stage = stage_video_weights[:,:,0].unsqueeze(2).repeat(1,1,video.shape[2])
        vid2_wts_stage = stage_video_weights[:,:,1].unsqueeze(2).repeat(1,1,video.shape[2])
        gated_video_stage = torch.mul(vid1_wts_stage, gated_video_stage1) + torch.mul(vid2_wts_stage, gated_video)
        gated_video_stage = self.relu(gated_video_stage)

        stage_audio_weights = self.audio_gating_fc_layer_stage(atten_audio[-1])
        stage_audio_weights = self.softmax(stage_audio_weights/0.1)
        aud1_wts_stage = stage_audio_weights[:,:,0].unsqueeze(2).repeat(1,1,audio.shape[2])
        aud2_wts_stage = stage_audio_weights[:,:,1].unsqueeze(2).repeat(1,1,audio.shape[2])
        gated_audio_stage = torch.mul(aud1_wts_stage, gated_audio_stage1) + torch.mul(aud2_wts_stage, gated_audio) 
        gated_audio_stage = self.relu(gated_audio_stage)

        #stage_text_weights = self.text_gating_fc_layer_stage(atten_text[-1])
        #stage_text_weights = self.softmax(stage_text_weights/0.1)
        #text1_wts_stage = stage_text_weights[:,:,0].unsqueeze(2).repeat(1,1,text.shape[2])
        #text2_wts_stage = stage_text_weights[:,:,1].unsqueeze(2).repeat(1,1,text.shape[2])
        #gated_text_stage = torch.mul(text1_wts_stage, gated_text_stage1) + torch.mul(text2_wts_stage, gated_text) 
        #gated_text_stage = self.relu(gated_text_stage)        

        audiovisualfeatures = torch.cat((gated_video_stage, gated_audio_stage), -1)
        #print(audiovisualfeatures.shape)
        #sys.exit()
        #audiovisualfeatures = self.Joint(audiovisualfeatures)

        #vouts = self.vregressor(audiovisualfeatures) #.transpose(0,1))
        #aouts = self.aregressor(audiovisualfeatures) #.transpose(0,1))
        #seq_outs, _ = torch.max(outs,0)
        #print(seq_outs)
        #vsequence_outs.append(vouts)
        #asequence_outs.append(aouts)
        #    #fin_audio_features.append(att_audio_features)
        #   #fin_visual_features.append(att_visual_features)
        #final_aud_feat = torch.stack(fin_audio_features)
        #final_vis_feat = torch.stack(fin_visual_features)
        #vfinal_outs = torch.stack(vsequence_outs)
        #afinal_outs = torch.stack(asequence_outs)

        return audiovisualfeatures #vouts.squeeze(2), aouts.squeeze(2)  #final_aud_feat.transpose(1,2), final_vis_feat.transpose(1,2)
