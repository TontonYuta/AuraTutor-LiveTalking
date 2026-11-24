import time
import asyncio
import numpy as np
import torch
import torchaudio.functional as F_audio
import soundfile as sf
import edge_tts
from io import BytesIO

from utils.logger import logger
from .base_tts import BaseTTS, State
from registry import register

@register("tts", "edgetts")
class EdgeTTS(BaseTTS):
    def txt_to_audio(self,msg:tuple[str, dict]):
        text,textevent = msg
        voice = self.opt.REF_FILE or "zh-CN-YunxiaNeural" 
        voicename = textevent.get('tts', {}).get('ref_file',voice)
        logger.info(f'txt_to_audio start: voice={voicename}, text={repr(text)}')
        t = time.time()
        
        self.state = State.RUNNING
        self.input_stream.seek(0)
        self.input_stream.truncate()

        try:
            asyncio.run(self.__main(voicename, text))
        except Exception as e:
            logger.warning(f"edge_tts execution warning: {e}")

        logger.info(f'-------edge tts time:{time.time()-t:.4f}s')
        if self.input_stream.getbuffer().nbytes<=0: #edgetts err
            logger.error('edgetts err!!!!!')
            return
        
        self.input_stream.seek(0)
        stream = self.__create_bytes_stream(self.input_stream)
        streamlen = stream.shape[0]
        idx=0
        while streamlen >= self.chunk and self.state==State.RUNNING:
            eventpoint={}
            streamlen -= self.chunk
            if idx==0:
                eventpoint={'status':'start','text':text}
            elif streamlen<self.chunk:
                eventpoint={'status':'end','text':text}
            eventpoint.update(**textevent) #eventpoint={'status':'end','text':text,'msgevent':textevent}
            self.parent.put_audio_frame(stream[idx:idx+self.chunk],eventpoint)
            idx += self.chunk
        #if streamlen>0:  #skip last frame(not 20ms)
        #    self.queue.put(stream[idx:])
        self.input_stream.seek(0)
        self.input_stream.truncate() 

    def __create_bytes_stream(self,byte_stream):
        #byte_stream=BytesIO(buffer)
        stream, sample_rate = sf.read(byte_stream) # [T*sample_rate,] float64
        logger.info(f'[INFO]tts audio stream {sample_rate}: {stream.shape}')
        stream = stream.astype(np.float32)

        if stream.ndim > 1:
            logger.info(f'[WARN] audio has {stream.shape[1]} channels, only use the first.')
            stream = stream[:, 0]
    
        if sample_rate != self.sample_rate and stream.shape[0]>0:
            logger.info(f'[WARN] audio sample rate is {sample_rate}, fast resampling into {self.sample_rate} via torchaudio.')
            t_tensor = torch.from_numpy(stream)
            stream = F_audio.resample(t_tensor, sample_rate, self.sample_rate).numpy()

        return stream
    
    async def __main(self,voicename: str, text: str):
        alt_voice = 'vi-VN-HoaiMyNeural' if voicename == 'vi-VN-NamMinhNeural' else 'vi-VN-NamMinhNeural'
        voices_to_try = [voicename, alt_voice]
        for v in voices_to_try:
            for attempt in range(2):
                if self.state != State.RUNNING:
                    return
                try:
                    communicate = edge_tts.Communicate(text, v)
                    async for chunk in communicate.stream():
                        if self.state != State.RUNNING:
                            return
                        if chunk["type"] == "audio":
                            self.input_stream.write(chunk["data"])
                    if self.input_stream.getbuffer().nbytes > 0:
                        return
                except Exception as e:
                    if self.state != State.RUNNING:
                        return
                    logger.warning(f'edgetts voice {v} attempt {attempt+1} failed ({e}), retrying...')
                    await asyncio.sleep(0.4 * (attempt + 1))
        if self.state == State.RUNNING:
            logger.error(f'edgetts failed all attempts for voice={voicename}, text={text[:40]}...')
