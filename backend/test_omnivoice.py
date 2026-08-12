import sys
import logging
try:
    from omnivoice import OmniVoice
    import torch
    import sounddevice as sd
    import numpy as np
    
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    model = OmniVoice.from_pretrained("k2-fsa/OmniVoice", device_map=device)
    
    print("Generating audio...")
    out = model.generate("Hello world")
    print("Type of out:", type(out))
    print("Length:", len(out))
    print("Type of out[0]:", type(out[0]))
    
    if isinstance(out, list):
        if isinstance(out[0], torch.Tensor):
            out = out[0].cpu().numpy()
        else:
            out = np.array(out, dtype=np.float32)
            
    print("Shape:", out.shape)
    
    print("Playing audio...")
    sd.play(out, samplerate=24000)
    sd.wait()
    print("Done")
except Exception as e:
    import traceback
    traceback.print_exc()
