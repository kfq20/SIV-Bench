from huggingface_hub import snapshot_download
from ..smp import *
from .video_base import VideoBaseDataset
from .utils import build_judge, DEBUG_MESSAGE
from ..utils import track_progress_rich


FAIL_MSG = 'Failed to obtain answer via API.'

class SIVBench(VideoBaseDataset):

    MD5 = '98f7df3eb1007fc375ea6fe88a98e2ff'
    SYS = 'You are an AI assistant responsible for answering questions about videos.'
    FRAMES_TMPL_PACK = """
You will be provided with {} separate frames uniformly sampled from a video, \
the frames are provided in chronological order of the video.
Please analyze these images and provide the answers to the \
following multiple-choice questions about the video content.
If multiple questions are provided (with indices Q1, Q2, Q3, ...), \
you should organize your answers in the following json format:
1. [Exact text of the chosen option for question 1],
2. [Exact text of the chosen option for question 2],
...

Do NOT include the question number labels (A, B, C, D, E) in your answer.
Do NOT add any explanations, introductions, or concluding remarks.
"""

    FRAMES_TMPL_NOPACK = """
You will be provided with {} separate frames uniformly sampled from a video, \
the frames are provided in chronological order of the video.
Please analyze these images and provide the answer to the question about the video content.
Please directly reply with your response to the only question.
"""

    TYPE = 'Video-MCQ'

    def __init__(self, dataset='SIV-Bench', pack=True, nframe=16, fps=-1, subtitle_version='origin', **kwargs):
        self.subtitle_version = subtitle_version
        print("subtitle_version", self.subtitle_version)
        super().__init__(dataset=dataset, pack=pack, nframe=nframe, fps=fps)

    @classmethod
    def supported_datasets(cls):
        return ['SIV-Bench'] 

    def prepare_dataset(self, dataset_name='SIV-Bench', repo_id='Fancylalala/SIV-Bench'):
        def check_integrity(pth):
            data_file = osp.join(pth, f'{dataset_name}.tsv')
            if md5(data_file) != self.MD5:
                return False
            data = load(data_file)
            for video_pth in data['video_path']:
                if not osp.exists(osp.join(pth, video_pth)):
                    return False
            return True

        cache_path = get_cache_path(repo_id)
        if cache_path is not None and check_integrity(cache_path):
            dataset_path = cache_path
        else:
            if modelscope_flag_set():
                from modelscope import dataset_snapshot_download
                dataset_path = dataset_snapshot_download(dataset_id=repo_id)
            else:
                dataset_path = snapshot_download(repo_id=repo_id, repo_type='dataset')
        self.video_path = osp.join(dataset_path, f'{self.subtitle_version}/')
        data_file = osp.join(dataset_path, f'{dataset_name}.tsv')
        return dict(data_file=data_file, root=osp.join(dataset_path, f'{self.subtitle_version}'))

    def build_prompt(self, line, video_llm):
        if isinstance(line, int):
            assert line < len(self)
            video = self.videos[line]
        elif isinstance(line, pd.Series):
            video = line['video']
        elif isinstance(line, str):
            video = line
        
        sub = self.data[self.data['video'] == video]
        message = []
        if video_llm:
            message.append(dict(type='video', value=osp.join(self.data_root, video + '.mp4')))
            # qs = {int(sub.iloc[i]['index']): sub.iloc[i]['question'] for i in range(nq)}
            # prompt = prompt.format(json.dumps(qs))
        else:
            frames = self.save_video_frames(video)
            sys_prompt = self.SYS + self.FRAMES_TMPL_PACK.format(len(frames))
            message.append(dict(type='text', value=sys_prompt))
            for im in frames:
                message.append(dict(type='image', value=im))
        
        nq = len(sub)
        prompt = "--- QUESTIONS ---\n"
        for i in range(nq):
            prompt += 'Q{}: {}\n'.format(i + 1, sub.iloc[i]['question'])
            prompt += f'    {sub.iloc[i]["options"]}\n'
        qs = {int(sub.iloc[i]['index']): sub.iloc[i]['question'] for i in range(nq)}
        prompt = prompt.format(json.dumps(qs))
        message.append(dict(type='text', value=prompt))
            
        return message